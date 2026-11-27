from __future__ import annotations

import io
import re
import struct
from dataclasses import dataclass
from pathlib import Path

from elftools.elf.elffile import ELFFile


class NativeAutoError(RuntimeError):
    pass


@dataclass
class NativePatch:
    offset: int
    expect: bytes
    patch: bytes
    anchor: str
    function: int


def _read_elf(path: Path):
    raw = path.read_bytes()
    return raw, ELFFile(io.BytesIO(raw))


def _eh_frame_starts(elf: ELFFile) -> list[int]:
    section = elf.get_section_by_name(".eh_frame_hdr")
    if section is None:
        return []
    data = section.data()
    base = section["sh_addr"]
    if len(data) < 4:
        return []
    version, eh_enc, count_enc, table_enc = data[0], data[1], data[2], data[3]
    if version != 1:
        raise NativeAutoError(f"unsupported .eh_frame_hdr version {version}")
    pos = 4

    def read_value(encoding: int) -> int:
        nonlocal pos
        fmt = encoding & 0x0F
        if fmt == 0x03:
            value = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            return value
        if fmt == 0x0B:
            value = struct.unpack_from("<i", data, pos)[0]
            pos += 4
            return value
        raise NativeAutoError(f"unsupported .eh_frame_hdr encoding {encoding:#x}")

    if eh_enc:
        read_value(eh_enc)
    else:
        pos += 4
    count = read_value(count_enc)
    starts = []
    for _ in range(count):
        pc = read_value(table_enc)
        _fde = read_value(table_enc)
        starts.append((base + pc) & 0xFFFFFFFFFFFFFFFF)
    return sorted(set(starts))


def _exidx_starts(elf: ELFFile) -> list[int]:
    section = elf.get_section_by_name(".ARM.exidx")
    text = elf.get_section_by_name(".text")
    if section is None or text is None:
        return []
    data = section.data()
    base = section["sh_addr"]
    text_base = text["sh_addr"]
    text_end = text_base + len(text.data())
    starts = []
    for offset in range(0, len(data), 8):
        word = struct.unpack_from("<I", data, offset)[0]
        if word == 1:
            continue
        value = word & 0x7FFFFFFF
        if value & 0x40000000:
            value -= 0x80000000
        address = (base + offset + value) & 0xFFFFFFFF
        if text_base <= address < text_end:
            starts.append(address)
    return sorted(set(starts))


def _strings(elf: ELFFile) -> dict[int, str]:
    section = elf.get_section_by_name(".rodata")
    if section is None:
        return {}
    out = {}
    for match in re.finditer(rb"[ -~]{4,}", section.data()):
        out[section["sh_addr"] + match.start()] = match.group().decode("ascii", "ignore")
    return out


def _find_string(addresses: dict[int, str], needle: str) -> tuple[int, str]:
    hits = [(address, value) for address, value in addresses.items() if needle in value]
    if len(hits) != 1:
        raise NativeAutoError(f"native anchor {needle!r}: expected 1 string, got {len(hits)}")
    return hits[0]


def _enclosing(starts: list[int], address: int, text_end: int) -> int:
    import bisect

    index = bisect.bisect_right(starts, address) - 1
    if index < 0:
        raise NativeAutoError(f"native anchor at {address:#x} is outside functions")
    start = starts[index]
    end = starts[index + 1] if index + 1 < len(starts) else text_end
    if not (start <= address < end):
        raise NativeAutoError(f"native anchor at {address:#x} is outside {start:#x}..{end:#x}")
    return start


def _arm64_refs(path: Path, targets: dict[str, int]) -> dict[str, list[int]]:
    from capstone import Cs, CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN
    from capstone.arm64 import ARM64_OP_IMM

    _raw, elf = _read_elf(path)
    text = elf.get_section_by_name(".text")
    if text is None:
        raise NativeAutoError(f"{path}: .text not found")
    data = text.data()
    base = text["sh_addr"]
    md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    page: dict[int, int] = {}
    refs: dict[str, list[int]] = {}
    for ins in md.disasm(data, base):
        if ins.mnemonic == "adrp" and len(ins.operands) == 2 and ins.operands[1].type == ARM64_OP_IMM:
            page[ins.operands[0].reg] = ins.operands[1].imm
        elif ins.mnemonic == "add" and len(ins.operands) == 3 and ins.operands[2].type == ARM64_OP_IMM:
            reg = ins.operands[1].reg
            if reg in page:
                address = page[reg] + ins.operands[2].imm
                for needle, target in targets.items():
                    if address == target:
                        refs.setdefault(needle, []).append(ins.address)
        elif ins.mnemonic == "ldr" and len(ins.operands) == 2 and ins.operands[1].type == 3:
            mem = ins.operands[1].mem
            if mem.base in page:
                address = page[mem.base] + mem.disp
                for needle, target in targets.items():
                    if address == target:
                        refs.setdefault(needle, []).append(ins.address)
    return refs


def _arm32_refs(path: Path, targets: dict[str, int]) -> dict[str, list[int]]:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_LITTLE_ENDIAN, CS_MODE_THUMB
    from capstone.arm import ARM_OP_IMM, ARM_OP_MEM, ARM_OP_REG, ARM_REG_PC

    _raw, elf = _read_elf(path)
    text = elf.get_section_by_name(".text")
    if text is None:
        raise NativeAutoError(f"{path}: .text not found")
    data = text.data()
    base = text["sh_addr"]
    text_end = base + len(data)
    starts = _exidx_starts(elf)
    if not starts:
        raise NativeAutoError(f"{path}: .ARM.exidx has no functions")
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_LITTLE_ENDIAN)
    md.detail = True
    refs: dict[str, list[int]] = {}
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else text_end
        registers: dict[int, int] = {}
        for ins in md.disasm(data[start - base : end - base], start):
            if (
                ins.mnemonic == "ldr"
                and len(ins.operands) == 2
                and ins.operands[1].type == ARM_OP_MEM
                and ins.operands[1].mem.base == ARM_REG_PC
            ):
                literal = ((ins.address + 4) & ~3) + ins.operands[1].mem.disp
                if base <= literal < text_end:
                    registers[ins.operands[0].reg] = struct.unpack_from("<I", data, literal - base)[0]
            elif (
                ins.mnemonic == "add"
                and ins.operands
                and ins.operands[-1].type == ARM_OP_REG
                and ins.operands[-1].reg == ARM_REG_PC
            ):
                operands = ins.operands
                if len(operands) == 2 and operands[0].type == ARM_OP_REG and operands[0].reg in registers:
                    address = (registers[operands[0].reg] + ins.address + 4) & 0xFFFFFFFF
                elif (
                    len(operands) == 3
                    and operands[0].type == ARM_OP_REG
                    and operands[2].type == ARM_OP_IMM
                    and operands[0].reg in registers
                ):
                    address = (registers[operands[0].reg] + ins.address + 4 + operands[2].imm) & 0xFFFFFFFF
                else:
                    continue
                for needle, target in targets.items():
                    if address == target:
                        refs.setdefault(needle, []).append(start)
    return refs


VERIFY_BYTES = {
    "arm64": bytes.fromhex("20 00 80 52 c0 03 5f d6"),
    "arm32": bytes.fromhex("01 20 70 47"),
}
EXIT_BYTES = {
    "arm64": bytes.fromhex("c0 03 5f d6"),
    "arm32": bytes.fromhex("70 47"),
}
ANCHORS = {
    "verify": "signatures",
    "exit": "error! verify new libraries",
}


def locate(path: Path) -> list[NativePatch]:
    _raw, elf = _read_elf(path)
    arch = "arm64" if elf.elfclass == 64 else "arm32"
    strings = _strings(elf)
    targets = {name: _find_string(strings, needle)[0] for name, needle in ANCHORS.items()}
    if arch == "arm64":
        starts = _eh_frame_starts(elf)
        refs = _arm64_refs(path, targets)
    else:
        starts = _exidx_starts(elf)
        refs = _arm32_refs(path, targets)
    if not starts:
        raise NativeAutoError(f"{path}: function table is empty")
    text = elf.get_section_by_name(".text")
    text_end = text["sh_addr"] + len(text.data())
    patches = []
    for name, needle in ANCHORS.items():
        candidates = refs.get(name, [])
        if not candidates:
            raise NativeAutoError(f"{path}: string {needle!r} is not referenced")
        functions = {_enclosing(starts, address, text_end) for address in candidates}
        if len(functions) != 1:
            raise NativeAutoError(f"{path}: string {needle!r} referenced from {len(functions)} functions")
        function = next(iter(functions))
        patch_bytes = VERIFY_BYTES[arch] if name == "verify" else EXIT_BYTES[arch]
        expect = bytes.fromhex("fd 7b ba a9") if (arch == "arm64" and name == "verify") else None
        # The first bytes are only a sanity hint; the function start comes from the unwind table.
        if arch == "arm64":
            expect = bytes.fromhex("fd 7b ba a9") if name == "verify" else bytes.fromhex("ff c3 00 d1")
        else:
            expect = bytes.fromhex("f0 b5 03 af") if name == "verify" else bytes.fromhex("d0 b5 02 af")
        patches.append(NativePatch(function, expect, patch_bytes, needle, function))
    return patches
