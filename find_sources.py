from __future__ import annotations

import sys
from pathlib import Path

WORK = Path(sys.argv[1])

SOURCES = [
    "MusicSubscriptionProviderImpl.kt",
    "CurrentAccountInformation.kt",
    "ContextFlags.kt",
    "PlayerModelImpl.kt",
]


def main() -> None:
    hits: dict[str, list[str]] = {s: [] for s in SOURCES}
    for path in WORK.rglob("*.smali"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        head = text[:400]
        for s in SOURCES:
            if f'.source "{s}"' in head:
                hits[s].append(path.relative_to(WORK).as_posix())
    for s in SOURCES:
        print(f"== {s} ==")
        for h in hits[s]:
            print(f"    {h}")


if __name__ == "__main__":
    main()