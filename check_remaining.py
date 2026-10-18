from __future__ import annotations
import sys
from pathlib import Path

W = Path(sys.argv[1])

CHECKS = {
    "smali_classes7/com/vk/dto/music/MusicTrack.smali": ["B6()I", "l()Z"],
    "smali/com/vk/toggle/d.smali": ["z(Z)Z", "b()I"],
    "smali/xsna/z6q.smali": ["E(L"],
    "smali_classes8/xsna/gkm.smali": ["d(Lcom/vk/dto/music/MusicTrack;)Z"],
    "smali_classes8/xsna/wll.smali": ["a()Z", "<init>(Lxsna/yy2;)V"],
    "smali_classes8/xsna/phm$a$a.smali": ["b()Z", "c()J"],
}

for rel, needles in CHECKS.items():
    p = W / rel
    print(f"== {rel} exists={p.is_file()} ==")
    if not p.is_file():
        continue
    lines = p.read_text(encoding="utf-8", errors="ignore").split("\n")
    for n in needles:
        hits = [i + 1 for i, l in enumerate(lines) if n in l]
        print(f"   {n}: {hits[:8]}")