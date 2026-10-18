from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "work")

TARGET = "smali/xsna/gpe.smali"

START = "    instance-of p1, p1, Lkotlin/Result$Failure;"
END = "    xor-int/2addr p1, v3"
REPLACEMENT = "    const/4 p1, 0x1"


def main() -> int:
    path = WORK / TARGET
    if not path.is_file():
        print(f"missing: {TARGET}")
        return 1
    lines = path.read_text(encoding="utf-8").split("\n")
    starts = [i for i, line in enumerate(lines) if line == START]
    if not starts:
        if REPLACEMENT in lines:
            print(f"unchanged: {TARGET}")
            return 0
        print(f"error: start line not found in {TARGET}")
        return 1
    if len(starts) > 1:
        print(f"error: {len(starts)} start lines in {TARGET}")
        return 1
    begin = starts[0]
    stop = next(
        (i for i in range(begin + 1, len(lines)) if lines[i] == END),
        None,
    )
    if stop is None:
        print(f"error: end line not found in {TARGET}")
        return 1
    lines[begin : stop + 1] = [REPLACEMENT]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"patched: {TARGET} -> hpe.b forced to true")
    return 0


if __name__ == "__main__":
    sys.exit(main())
