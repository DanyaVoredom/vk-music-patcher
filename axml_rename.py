from __future__ import annotations

import struct
import sys
import zipfile
from pathlib import Path

RES_STRING_POOL_TYPE = 0x0001
RES_XML_TYPE = 0x0003
UTF8_FLAG = 0x00000100


def _decode_utf8_len(data: bytes, off: int) -> tuple[int, int]:
    b0 = data[off]
    if b0 & 0x80:
        b1 = data[off + 1]
        return ((b0 & 0x7F) << 8) | b1, 2
    return b0, 1


def _decode_utf16_len(data: bytes, off: int) -> tuple[int, int]:
    v0 = struct.unpack_from("<H", data, off)[0]
    if v0 & 0x8000:
        v1 = struct.unpack_from("<H", data, off + 2)[0]
        return ((v0 & 0x7FFF) << 16) | v1, 4
    return v0, 2


def _encode_utf8_len(value: int) -> bytes:
    if value > 0x7F:
        return bytes([((value >> 8) & 0x7F) | 0x80, value & 0xFF])
    return bytes([value])


def _encode_utf16_len(value: int) -> bytes:
    if value > 0x7FFF:
        return struct.pack("<HH", ((value >> 16) & 0x7FFF) | 0x8000, value & 0xFFFF)
    return struct.pack("<H", value)


def parse_string_pool(chunk: bytes, is_utf8: bool) -> list[str]:
    string_count = struct.unpack_from("<I", chunk, 8)[0]
    offsets = struct.unpack_from(f"<{string_count}I", chunk, 28)
    strings_start = struct.unpack_from("<I", chunk, 20)[0]
    strings: list[str] = []
    for rel in offsets:
        off = strings_start + rel
        if is_utf8:
            _, n1 = _decode_utf8_len(chunk, off)
            off += n1
            byte_len, n2 = _decode_utf8_len(chunk, off)
            off += n2
            raw = chunk[off : off + byte_len]
            strings.append(raw.decode("utf-8", errors="replace"))
        else:
            char_len, n = _decode_utf16_len(chunk, off)
            off += n
            raw = chunk[off : off + char_len * 2]
            strings.append(raw.decode("utf-16-le", errors="replace"))
    return strings


def build_string_pool(original: bytes, strings: list[str], is_utf8: bool) -> bytes:
    style_count = struct.unpack_from("<I", original, 12)[0]
    styles_start = struct.unpack_from("<I", original, 24)[0]
    flags = struct.unpack_from("<I", original, 16)[0]

    encoded: list[bytes] = []
    for s in strings:
        if is_utf8:
            raw = s.encode("utf-8")
            u16_len = len(s.encode("utf-16-le")) // 2
            encoded.append(
                _encode_utf8_len(u16_len) + _encode_utf8_len(len(raw)) + raw + b"\x00"
            )
        else:
            raw = s.encode("utf-16-le")
            encoded.append(_encode_utf16_len(len(raw) // 2) + raw + b"\x00\x00")

    offsets = bytearray()
    data = bytearray()
    for enc in encoded:
        offsets += struct.pack("<I", len(data))
        data += enc
    while len(data) % 4:
        data += b"\x00"

    styles = bytearray()
    if style_count and styles_start:
        styles = bytearray(original[styles_start : struct.unpack_from("<I", original, 4)[0]])

    header_size = 28
    strings_start = header_size + 4 * len(strings) + 4 * style_count
    styles_off = strings_start + len(data) if style_count else 0

    header = struct.pack(
        "<HHIIIIII",
        RES_STRING_POOL_TYPE,
        header_size,
        strings_start + len(data) + len(styles),
        len(strings),
        style_count,
        flags,
        strings_start,
        styles_off,
    )
    return header + bytes(offsets) + (struct.pack(f"<{style_count}I", *([0] * style_count)) if style_count else b"") + bytes(data) + bytes(styles)


def iter_chunks(data: bytes):
    off = struct.unpack_from("<H", data, 2)[0]
    total = len(data)
    while off + 8 <= total:
        ctype, hsize, csize = struct.unpack_from("<HHI", data, off)
        yield off, ctype, hsize, csize
        if csize == 0:
            break
        off += csize


def rename_axml(data: bytes, old: str, new: str) -> bytes:
    header_size = struct.unpack_from("<H", data, 2)[0]
    file_size = struct.unpack_from("<I", data, 4)[0]
    assert struct.unpack_from("<H", data, 0)[0] == RES_XML_TYPE, "not AXML"

    for off, ctype, hsize, csize in iter_chunks(data):
        if ctype != RES_STRING_POOL_TYPE:
            continue
        is_utf8 = bool(struct.unpack_from("<I", data, off + 16)[0] & UTF8_FLAG)
        chunk = data[off : off + csize]
        strings = parse_string_pool(chunk, is_utf8)
        changed = [s.replace(old, new) if old in s else s for s in strings]
        if changed == strings:
            return data
        new_pool = build_string_pool(chunk, changed, is_utf8)
        new_data = data[:off] + new_pool + data[off + csize :]
        new_size = len(new_data)
        new_data = (
            new_data[:4] + struct.pack("<I", new_size) + new_data[8:]
        )
        return new_data

    return data


def repack(src_apk: Path, out_apk: Path, old: str, new: str, replace_entries: dict[str, Path]) -> None:
    with zipfile.ZipFile(src_apk, "r") as zin:
        infos = zin.infolist()
        with zipfile.ZipFile(out_apk, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in infos:
                if info.filename in replace_entries:
                    zout.writestr(info, replace_entries[info.filename].read_bytes())
                    continue
                payload = zin.read(info.filename)
                if info.filename == "AndroidManifest.xml":
                    payload = rename_axml(payload, old, new)
                zout.writestr(info, payload)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2])
    old = sys.argv[3]
    new = sys.argv[4]
    entries: dict[str, Path] = {}
    for spec in sys.argv[5:]:
        name, _, path = spec.partition("=")
        entries[name] = Path(path)
    repack(src, out, old, new, entries)
    print(f"repacked {out.name} with {len(entries)} replaced entries")