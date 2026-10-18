from __future__ import annotations
import sys
from pathlib import Path

W = Path(sys.argv[1])
NEEDLES = [
    "com.uma.musicvk",
    "androidx.car.app.connection",
    "com.vkontakte.android.vk_music_redirect_provider",
    "com.vk.vkmusic.provider",
]

found: dict[str, list[tuple[str, int]]] = {n: [] for n in NEEDLES}
for p in W.rglob("*.smali"):
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for n in NEEDLES:
        if n in text:
            found[n].append((p.relative_to(W).as_posix(), text.count(n)))
for n in NEEDLES:
    print(f"== {n} ==")
    for rel, c in found[n]:
        print(f"   {c}x {rel}")