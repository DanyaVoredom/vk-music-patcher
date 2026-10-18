from __future__ import annotations

import sys
import zipfile
from pathlib import Path

src_apk = Path(sys.argv[1])
patched_so = Path(sys.argv[2])
out_apk = Path(sys.argv[3])

ENTRY = "lib/arm64-v8a/libvkcore.so"

with zipfile.ZipFile(src_apk, "r") as zin:
    infos = zin.infolist()
    if not any(i.filename == ENTRY for i in infos):
        raise SystemExit(f"missing {ENTRY} in {src_apk}")
    data = patched_so.read_bytes()
    with zipfile.ZipFile(out_apk, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in infos:
            if info.filename == ENTRY:
                continue
            zout.writestr(info, zin.read(info.filename))
        zout.writestr(ENTRY, data)

print(f"repacked {out_apk.name}: {ENTRY} replaced ({len(data)} bytes)")