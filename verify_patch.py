from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

from loguru import logger

logger.remove()

from androguard.core.dex import DEX

ROOT = Path(__file__).resolve().parent
SKIP_NATIVE = "--skip-native" in sys.argv
ARGS = [value for value in sys.argv[1:] if not value.startswith("--")]
APK = Path(ARGS[0]) if ARGS else ROOT / "build" / "VK_Music_patched.apk"

EXPECTED: dict[tuple[str, str], list[str] | None] = {
    ("Lxsna/nnh;", "b()Z"): ["const/4", "return"],
    ("Lxsna/nnh;", "e()J"): ["const-wide", "return-wide"],
    ("Lxsna/jnh$a$a;", "b()Z"): ["const/4", "return"],
    ("Lxsna/jnh$a$a;", "e()J"): ["const-wide", "return-wide"],
    ("Lxsna/m87;", "<init>(ZJ)V"): [
        "invoke-direct",
        "const/4",
        "const-wide",
        "iput-boolean",
        "iput-wide",
        "return-void",
    ],
    ("Lxsna/en6;", "b(I)Z"): ["const/4", "return"],
    ("Lxsna/en6;", "d(I)Z"): ["const/4", "return"],
    ("Lxsna/en6;", "e(I)Z"): ["const/4", "return"],
    ("Lxsna/en6;", "f(I)Z"): ["const/4", "return"],
    ("Lcom/vk/dto/music/MusicTrack;", "x5()I"): ["const/4", "return"],
    ("Lcom/vk/dto/music/MusicTrack;", "r()Z"): ["const/4", "return"],
    ("Lxsna/brk;", "B(Lxsna/o0q;Ljava/util/List;)Z"): ["const/4", "return"],
    ("Lcom/vk/toggle/d;", "z(Z)Z"): ["const/4", "return"],
    ("Lxsna/kqh;", "d(Lcom/vk/dto/music/MusicTrack;)Z"): ["const/4", "return"],
    ("Lxsna/ppg;", "a()Z"): ["const/4", "return"],
    (
        "Lxsna/idv$a;",
        "c(Ljava/lang/String;Lcom/vk/dto/common/id/UserId;Ljava/lang/Throwable;Lkotlin/jvm/functions/Function0;)V",
    ): ["return-void"],
    ("Lxsna/ue4;", "invoke(Ljava/lang/Object;)Ljava/lang/Object;"): None,
    (
        "Lcom/vk/core/preference/Preference;",
        "s(Ljava/lang/String;Ljava/lang/String;Lcom/vk/core/preference/Preference$Type;Ljava/lang/Object;)Lxsna/ktl;",
    ): [
        "sget-object", "invoke-virtual", "move-result-object", "invoke-virtual",
        "const-string", "invoke-virtual", "move-result", "if-eqz",
        "const-string", "invoke-virtual", "move-result", "if-eqz",
        "const-string", "invoke-static", "move-result-object", "goto", "invoke-static", "move-result-object",
        "invoke-static", "move-result-object", "invoke-virtual", "return-object",
        "move-exception", "invoke-virtual", "throw",
    ],
    (
        "Lcom/vk/core/preference/Preference;",
        "u(Ljava/lang/String;Ljava/lang/String;)V",
    ): [
        "sget-object", "sget-object", "invoke-virtual",
        "const-string", "invoke-virtual", "move-result", "if-eqz",
        "const-string", "invoke-virtual", "move-result", "if-eqz",
        "const-string", "invoke-static", "move-result-object", "goto",
        "invoke-static", "move-result-object", "invoke-interface", "move-result", "if-eqz",
        "invoke-interface", "move-result-object", "invoke-interface", "move-result-object",
        "invoke-interface", "return-void",
    ],
}

CONSTANTS: dict[tuple[str, str], str] = {
    ("Lxsna/nnh;", "b()Z"): "v0, 1",
    ("Lxsna/nnh;", "e()J"): "v0, 4102444672",
    ("Lxsna/jnh$a$a;", "b()Z"): "v0, 1",
    ("Lxsna/jnh$a$a;", "e()J"): "v0, 4102444672",
    ("Lxsna/m87;", "<init>(ZJ)V"): "v2, 4102444672",
    ("Lxsna/en6;", "b(I)Z"): "v0, 1",
    ("Lxsna/en6;", "d(I)Z"): "v0, 0",
    ("Lxsna/en6;", "e(I)Z"): "v0, 0",
    ("Lxsna/en6;", "f(I)Z"): "v0, 0",
    ("Lcom/vk/dto/music/MusicTrack;", "x5()I"): "v0, 0",
    ("Lcom/vk/dto/music/MusicTrack;", "r()Z"): "v0, 0",
    ("Lxsna/brk;", "B(Lxsna/o0q;Ljava/util/List;)Z"): "v0, 0",
    ("Lcom/vk/toggle/d;", "z(Z)Z"): "v0, 1",
    ("Lxsna/kqh;", "d(Lcom/vk/dto/music/MusicTrack;)Z"): "v0, 0",
    ("Lxsna/ppg;", "a()Z"): "v0, 0",
    ("Lxsna/ue4;", "invoke(Ljava/lang/Object;)Ljava/lang/Object;"): '"session_management"',
    (
        "Lcom/vk/core/preference/Preference;",
        "s(Ljava/lang/String;Ljava/lang/String;Lcom/vk/core/preference/Preference$Type;Ljava/lang/Object;)Lxsna/ktl;",
    ): "encrypted_key.authorized",
    ("Lcom/vk/core/preference/Preference;", "u(Ljava/lang/String;Ljava/lang/String;)V"): "encrypted_key.authorized",
}

REQUIRED_TEXT = {
    ("Lxsna/ue4;", "invoke(Ljava/lang/Object;)Ljava/lang/Object;"): (
        '"encrypted_session_management"', '"plain_session_management"',
    ),
    (
        "Lcom/vk/core/preference/Preference;",
        "s(Ljava/lang/String;Ljava/lang/String;Lcom/vk/core/preference/Preference$Type;Ljava/lang/Object;)Lxsna/ktl;",
    ): ('"EncryptedPreferenceMeta"', '"plain_session_management"'),
    ("Lcom/vk/core/preference/Preference;", "u(Ljava/lang/String;Ljava/lang/String;)V"): (
        '"EncryptedPreferenceMeta"', '"plain_session_management"',
    ),
}

FORBIDDEN_TEXT = {
    ("Lxsna/ue4;", "invoke(Ljava/lang/Object;)Ljava/lang/Object;"): ('"session_management_unencrypted"',),
}

NATIVE: dict[str, list[tuple[int, bytes]]] = {
    "lib/arm64-v8a/libvkcore.so": [
        (0x4FD8, bytes.fromhex("20 00 80 52 c0 03 5f d6")),
        (0x7560, bytes.fromhex("c0 03 5f d6")),
    ],
    "lib/armeabi-v7a/libvkcore.so": [
        (0x34F0, bytes.fromhex("01 20 70 47")),
        (0x5644, bytes.fromhex("70 47")),
    ],
}

UPDATER_CLASS = "Lcom/vk/music/updater/UpdateChecker;"
UPDATER_METHOD = "check(Landroid/app/Activity;)V"
MAIN_ACTIVITY = "Lcom/vk/music/screens/main/MainActivity;"
MAIN_CREATE = "onCreate(Landroid/os/Bundle;)V"

REGISTER_PATTERN = re.compile(r"\bv(\d+)\b")


def register_overflow(text: str, registers_size: int) -> list[int]:
    used = {int(number) for number in REGISTER_PATTERN.findall(text)}
    return sorted(register for register in used if register >= registers_size)


def verify_native(archive: zipfile.ZipFile) -> int:
    failures = 0
    names = set(archive.namelist())
    for entry, patches in NATIVE.items():
        if entry not in names:
            print(f"FAIL {entry}: missing")
            failures += 1
            continue
        data = archive.read(entry)
        for offset, expected in patches:
            current = data[offset : offset + len(expected)]
            if current != expected:
                print(f"FAIL {entry} at {offset:#x}: {current.hex(' ')} != {expected.hex(' ')}")
                failures += 1
            else:
                print(f"OK   {entry} at {offset:#x}")
    return failures


def main() -> int:
    if not APK.is_file():
        print(f"missing apk: {APK}")
        return 1
    remaining = dict(EXPECTED)
    updater_class = False
    updater_call = False
    with zipfile.ZipFile(APK) as archive:
        failures = 0 if SKIP_NATIVE else verify_native(archive)
        dex_names = [n for n in archive.namelist() if n.endswith(".dex")]
        for dex_name in dex_names:
            dex = DEX(archive.read(dex_name))
            for cls in dex.get_classes():
                key_class = cls.get_name()
                for method in cls.get_methods():
                    signature = method.get_name() + method.get_descriptor().replace(" ", "")
                    if key_class == UPDATER_CLASS and signature == UPDATER_METHOD:
                        updater_class = True
                    if key_class == MAIN_ACTIVITY and signature == MAIN_CREATE:
                        code = method.get_code()
                        if code is not None:
                            text = " | ".join(
                                f"{i.get_name()} {i.get_output()}"
                                for i in code.get_bc().get_instructions()
                            )
                            if "Lcom/vk/music/updater/UpdateChecker;->check" in text:
                                updater_call = True
                    key = (key_class, signature)
                    if key not in EXPECTED:
                        continue
                    code = method.get_code()
                    if code is None:
                        print(f"FAIL {key_class}->{key[1]}: no code")
                        remaining.pop(key, None)
                        failures += 1
                        continue
                    instructions = list(code.get_bc().get_instructions())
                    names = [i.get_name() for i in instructions]
                    text = " | ".join(f"{i.get_name()} {i.get_output()}" for i in instructions)
                    overflow = register_overflow(text, code.get_registers_size())
                    constant = CONSTANTS.get(key)
                    ok = (
                        (EXPECTED[key] is None or names == EXPECTED[key])
                        and not overflow
                        and (constant is None or constant in text)
                        and all(value in text for value in REQUIRED_TEXT.get(key, ()))
                        and all(value not in text for value in FORBIDDEN_TEXT.get(key, ()))
                    )
                    note = "" if not overflow else f" OVERFLOW {overflow} of {code.get_registers_size()}"
                    print(
                        f"{'OK  ' if ok else 'FAIL'} [{dex_name}] "
                        f"{key_class}->{key[1]}: {text if EXPECTED[key] is not None else 'scope literals'}{note}"
                    )
                    if not ok:
                        failures += 1
                    remaining.pop(key, None)
    if updater_class:
        print("OK   updater class")
    else:
        print("FAIL updater class missing")
        failures += 1
    if updater_call:
        print("OK   updater call in MainActivity")
    else:
        print("FAIL updater call missing in MainActivity")
        failures += 1
    for key in remaining:
        print(f"MISSING {key[0]}->{key[1]}")
        failures += 1
    print(f"verified: {len(EXPECTED) - len(remaining)}/{len(EXPECTED)}")
    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
