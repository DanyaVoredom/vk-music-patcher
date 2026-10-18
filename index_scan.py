from __future__ import annotations

import re
import sys
from pathlib import Path

WORK = Path(sys.argv[1])

CLS_RE = re.compile(r"^\.class\s+(?:public\s+|final\s+|abstract\s+|synthetic\s+)*L([\w$/]+);")
METHOD_RE = re.compile(r"^\.method\s+.*?(\S+?)(\(.*?\)\S+)$")


def index() -> dict[str, dict]:
    classes: dict[str, dict] = {}
    for path in WORK.rglob("*.smali"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        desc = None
        methods: set[str] = set()
        for line in text.split("\n"):
            if line.startswith(".class "):
                m = CLS_RE.match(line)
                if m:
                    desc = "L" + m.group(1) + ";"
            elif line.startswith(".method "):
                parts = line.split()
                if parts:
                    methods.add(parts[-1])
        if desc:
            classes[desc] = {"file": path.relative_to(WORK).as_posix(), "methods": methods}
    return classes


def find(classes: dict[str, dict], needed: list[str]) -> list[tuple[str, str]]:
    out = []
    need = set(needed)
    for desc, info in classes.items():
        if need <= info["methods"]:
            out.append((desc, info["file"]))
    return out


def main() -> None:
    classes = index()
    print(f"classes indexed: {len(classes)}")

    groups = {
        "gdm (b()Z + c()J)": ["b()Z", "c()J"],
        "wz8 (b(I)Z,d(I)Z,e(I)Z,f(I)Z)": ["b(I)Z", "d(I)Z", "e(I)Z", "f(I)Z"],
        "rm9 (<init>(ZJ)V)": ["<init>(ZJ)V"],
        "c1q (E(Lxsna/c8w;Ljava/util/List;)Z)": ["E(Lxsna/c8w;Ljava/util/List;)Z"],
        "toggle.z (z(Z)Z)": ["z(Z)Z"],
        "xfm.d (d(Lcom/vk/dto/music/MusicTrack;)Z)": ["d(Lcom/vk/dto/music/MusicTrack;)Z"],
        "mhl.a (a()Z)": ["a()Z"],
        "MusicTrack (B6()I + l()Z)": ["B6()I", "l()Z"],
    }
    for name, needed in groups.items():
        hits = find(classes, needed)
        print(f"== {name} == {len(hits)}")
        for desc, file in hits[:40]:
            print(f"    {desc} -> {file}")

    for desc in ("Lxsna/cdm$a$a;", "Lxsna/cdm;", "Lxsna/gpe;", "Lxsna/xt7;",
                 "Lxsna/hry;", "Lxsna/zq5;", "Lcom/vk/core/apps/BuildInfo$a;"):
        info = classes.get(desc)
        print(f"{desc}: {info['file'] if info else 'MISSING'}")


if __name__ == "__main__":
    main()