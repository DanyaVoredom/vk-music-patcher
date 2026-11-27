from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "work")

PATCHES = {
    "lib/arm64-v8a/libvkcore.so": [
        {
            "name": "sub_4FD8 verify result",
            "offset": 0x4FD8,
            "expect": bytes.fromhex("fd 7b ba a9"),
            "patch": bytes.fromhex("20 00 80 52 c0 03 5f d6"),
        },
        {
            "name": "sub_7560 exit handler",
            "offset": 0x7560,
            "expect": bytes.fromhex("ff c3 00 d1"),
            "patch": bytes.fromhex("c0 03 5f d6"),
        },
    ],
    "lib/armeabi-v7a/libvkcore.so": [
        {
            "name": "sub_34F0 verify result",
            "offset": 0x34F0,
            "expect": bytes.fromhex("f0 b5 03 af"),
            "patch": bytes.fromhex("01 20 70 47"),
        },
        {
            "name": "sub_5644 exit handler",
            "offset": 0x5644,
            "expect": bytes.fromhex("d0 b5 02 af"),
            "patch": bytes.fromhex("70 47"),
        },
    ],
}


def main() -> int:
    failures = 0
    for relative, entries in PATCHES.items():
        path = WORK / relative
        if not path.is_file():
            print(f"skip: {relative} (not present)")
            continue
        data = bytearray(path.read_bytes())
        for entry in entries:
            offset = entry["offset"]
            expect = entry["expect"]
            patch = entry["patch"]
            current = bytes(data[offset : offset + len(expect)])
            if bytes(data[offset : offset + len(patch)]) == patch:
                print(f"unchanged: {relative} {entry['name']} at {offset:#x}")
                continue
            if current != expect:
                print(
                    f"error: {relative} {entry['name']} at {offset:#x}: "
                    f"expected {expect.hex(' ')}, got {current.hex(' ')}"
                )
                failures += 1
                continue
            data[offset : offset + len(patch)] = patch
            print(
                f"patched: {relative} {entry['name']} at {offset:#x}: "
                f"{expect.hex(' ')} -> {patch.hex(' ')}"
            )
        path.write_bytes(bytes(data))
    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
