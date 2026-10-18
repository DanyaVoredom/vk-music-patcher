from __future__ import annotations

import sys
from pathlib import Path

WORK = Path(sys.argv[1])

TARGETS = {
    "subscription": [
        ("Lxsna/gdm;", ".method public final b()Z"),
        ("Lxsna/gdm;", ".method public final c()J"),
        ("Lxsna/cdm$a$a;", ".method public final b()Z"),
        ("Lxsna/cdm$a$a;", ".method public final c()J"),
        ("Lxsna/rm9;", ".method public constructor <init>(ZJ)V"),
        ("Lxsna/wz8;", ".method public static final b(I)Z"),
        ("Lxsna/wz8;", ".method public static final d(I)Z"),
        ("Lxsna/wz8;", ".method public static final e(I)Z"),
        ("Lxsna/wz8;", ".method public static final f(I)Z"),
        ("Lcom/vk/dto/music/MusicTrack;", ".method public final B6()I"),
        ("Lcom/vk/dto/music/MusicTrack;", ".method public final l()Z"),
        ("Lxsna/c1q;", ".method public static E(Lxsna/c8w;Ljava/util/List;)Z"),
        ("Lcom/vk/toggle/d;", ".method public static z(Z)Z"),
        ("Lxsna/xfm;", ".method public static final d(Lcom/vk/dto/music/MusicTrack;)Z"),
        ("Lxsna/mhl;", ".method public final a()Z"),
    ],
    "package": [
        ("Lxsna/xt7;", None),
        ("Lxsna/hry;", None),
        ("Lxsna/zq5;", None),
        ("Lcom/vk/appredirects/entity/App;", None),
        ("Lcom/vk/core/apps/BuildInfo$a;", None),
    ],
}


def find_class_file(desc: str) -> list[Path]:
    decl = f".class public final {desc}"
    decl2 = f".class public {desc}"
    decl3 = f".class final {desc}"
    hits = []
    for path in WORK.rglob("*.smali"):
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if decl in head or decl2 in head or decl3 in head or f".class {desc}" in head:
            hits.append(path)
    return hits


def main() -> None:
    for group, items in TARGETS.items():
        print(f"== {group} ==")
        for desc, method in items:
            files = find_class_file(desc)
            if not files:
                print(f"  MISSING CLASS {desc}")
                continue
            for f in files:
                rel = f.relative_to(WORK).as_posix()
                if method is None:
                    print(f"  {desc} -> {rel}")
                else:
                    text = f.read_text(encoding="utf-8", errors="ignore")
                    has = method in text
                    print(f"  {desc} {method} -> {rel} {'OK' if has else 'NO-METHOD'}")


if __name__ == "__main__":
    main()