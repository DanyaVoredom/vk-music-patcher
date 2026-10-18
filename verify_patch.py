from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

from loguru import logger

logger.remove()

from androguard.core.dex import DEX

APK = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent / "VK Музыка_8.44_patched.apk")

EXPECTED: dict[tuple[str, str], list[str]] = {
    ("Lxsna/gdm;", "b()Z"): ["const/4", "return"],
    ("Lxsna/gdm;", "c()J"): ["const-wide", "return-wide"],
    ("Lxsna/cdm$a$a;", "b()Z"): ["const/4", "return"],
    ("Lxsna/cdm$a$a;", "c()J"): ["const-wide", "return-wide"],
    ("Lxsna/rm9;", "<init>(ZJ)V"): [
        "invoke-direct",
        "const/4",
        "const-wide",
        "iput-boolean",
        "iput-wide",
        "return-void",
    ],
    ("Lxsna/wz8;", "b(I)Z"): ["const/4", "return"],
    ("Lxsna/wz8;", "d(I)Z"): ["const/4", "return"],
    ("Lxsna/wz8;", "e(I)Z"): ["const/4", "return"],
    ("Lxsna/wz8;", "f(I)Z"): ["const/4", "return"],
    ("Lcom/vk/dto/music/MusicTrack;", "B6()I"): ["const/4", "return"],
    ("Lcom/vk/dto/music/MusicTrack;", "l()Z"): ["const/4", "return"],
    ("Lxsna/c1q;", "E(Lxsna/c8w;Ljava/util/List;)Z"): ["const/4", "return"],
    ("Lcom/vk/toggle/d;", "z(Z)Z"): ["const/4", "return"],
    ("Lxsna/xfm;", "d(Lcom/vk/dto/music/MusicTrack;)Z"): ["const/4", "return"],
    ("Lxsna/mhl;", "a()Z"): ["const/4", "return"],
}

CONSTANTS: dict[tuple[str, str], str] = {
    ("Lxsna/gdm;", "b()Z"): "v1, 1",
    ("Lxsna/gdm;", "c()J"): "v1, 4102444672",
    ("Lxsna/cdm$a$a;", "b()Z"): "v1, 1",
    ("Lxsna/cdm$a$a;", "c()J"): "v1, 4102444672",
    ("Lxsna/rm9;", "<init>(ZJ)V"): "v2, 4102444672",
    ("Lxsna/wz8;", "b(I)Z"): "v1, 1",
    ("Lxsna/wz8;", "d(I)Z"): "v1, 0",
    ("Lxsna/wz8;", "e(I)Z"): "v1, 0",
    ("Lxsna/wz8;", "f(I)Z"): "v1, 0",
    ("Lcom/vk/dto/music/MusicTrack;", "B6()I"): "v1, 0",
    ("Lcom/vk/dto/music/MusicTrack;", "l()Z"): "v1, 0",
    ("Lxsna/c1q;", "E(Lxsna/c8w;Ljava/util/List;)Z"): "v2, 0",
    ("Lcom/vk/toggle/d;", "z(Z)Z"): "v1, 1",
    ("Lxsna/xfm;", "d(Lcom/vk/dto/music/MusicTrack;)Z"): "v1, 0",
    ("Lxsna/mhl;", "a()Z"): "v1, 0",
}

REGISTER_PATTERN = re.compile(r"\bv(\d+)\b")


def register_overflow(text: str, registers_size: int) -> list[int]:
    used = {int(number) for number in REGISTER_PATTERN.findall(text)}
    return sorted(register for register in used if register >= registers_size)


def main() -> int:
    if not APK.is_file():
        print(f"missing apk: {APK}")
        return 1
    remaining = dict(EXPECTED)
    with zipfile.ZipFile(APK) as archive:
        dex_names = [n for n in archive.namelist() if n.endswith(".dex")]
        for dex_name in dex_names:
            dex = DEX(archive.read(dex_name))
            for cls in dex.get_classes():
                key_class = cls.get_name()
                for method in cls.get_methods():
                    signature = method.get_name() + method.get_descriptor().replace(" ", "")
                    key = (key_class, signature)
                    if key not in EXPECTED:
                        continue
                    code = method.get_code()
                    if code is None:
                        print(f"FAIL {key_class}->{key[1]}: no code")
                        remaining.pop(key, None)
                        continue
                    instructions = list(code.get_bc().get_instructions())
                    names = [i.get_name() for i in instructions]
                    text = " | ".join(f"{i.get_name()} {i.get_output()}" for i in instructions)
                    overflow = register_overflow(text, code.get_registers_size())
                    ok = (
                        names == EXPECTED[key]
                        and CONSTANTS[key] in text
                        and not overflow
                    )
                    note = "" if not overflow else f" OVERFLOW {overflow} of {code.get_registers_size()}"
                    print(
                        f"{'OK  ' if ok else 'FAIL'} [{dex_name}] "
                        f"{key_class}->{key[1]}: {text}{note}"
                    )
                    remaining.pop(key, None)
    for key in remaining:
        print(f"MISSING {key[0]}->{key[1]}")
    print(f"verified: {len(EXPECTED) - len(remaining)}/{len(EXPECTED)}")
    return 1 if remaining else 0


if __name__ == "__main__":
    sys.exit(main())
