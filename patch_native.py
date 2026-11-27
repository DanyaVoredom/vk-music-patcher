from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "work")
MANIFEST = ROOT / "build" / "patch_manifest.json"

PATCHES = {
    "lib/arm64-v8a/libvkcore.so": [
        {
            "name": "verify result",
            "offset": 0x4FD8,
            "expect": bytes.fromhex("fd 7b ba a9"),
            "patch": bytes.fromhex("20 00 80 52 c0 03 5f d6"),
            "anchor": "signatures",
        },
        {
            "name": "exit handler",
            "offset": 0x7560,
            "expect": bytes.fromhex("ff c3 00 d1"),
            "patch": bytes.fromhex("c0 03 5f d6"),
            "anchor": "error! verify new libraries",
        },
    ],
    "lib/armeabi-v7a/libvkcore.so": [
        {
            "name": "verify result",
            "offset": 0x39E4,
            "expect": bytes.fromhex("f0 b5 03 af"),
            "patch": bytes.fromhex("01 20 70 47"),
            "anchor": "signatures",
        },
        {
            "name": "exit handler",
            "offset": 0x5644,
            "expect": bytes.fromhex("d0 b5 02 af"),
            "patch": bytes.fromhex("70 47"),
            "anchor": "error! verify new libraries",
        },
    ],
}


def load_manifest() -> dict:
    if MANIFEST.is_file():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    return {"smali": []}


def save_manifest(manifest: dict) -> None:
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def apply_entries(path: Path, entries: list[dict]) -> tuple[int, int]:
    data = bytearray(path.read_bytes())
    patched = 0
    unchanged = 0
    for entry in entries:
        offset = entry["offset"]
        patch = entry["patch"]
        if offset < 0 or offset + len(patch) > len(data):
            raise RuntimeError(f"{path}: {entry['name']} at {offset:#x} is outside the file")
        current = bytes(data[offset : offset + len(patch)])
        if current == patch:
            unchanged += 1
            continue
        expect = entry.get("expect")
        if expect is not None:
            current_expect = bytes(data[offset : offset + len(expect)])
            if current_expect != expect:
                raise RuntimeError(
                    f"{path}: {entry['name']} at {offset:#x}: "
                    f"expected {expect.hex(' ')}, got {current_expect.hex(' ')}"
                )
        data[offset : offset + len(patch)] = patch
        patched += 1
        print(f"patched: {path.name} {entry['name']} at {offset:#x}: {current.hex(' ')} -> {patch.hex(' ')}")
    path.write_bytes(bytes(data))
    return patched, unchanged


def auto_entries(path: Path) -> list[dict] | None:
    try:
        import native_auto
    except ImportError as error:
        print(f"auto native unavailable: {error}")
        return None
    try:
        located = native_auto.locate(path)
    except Exception as error:
        print(f"auto native failed for {path.name}: {error}")
        return None
    entries = []
    for item in located:
        entries.append(
            {
                "name": item.anchor,
                "offset": item.offset,
                "expect": None,
                "patch": item.patch,
                "anchor": item.anchor,
            }
        )
    return entries


def main() -> int:
    if not WORK.is_dir():
        print(f"missing work dir: {WORK}")
        return 1
    manifest = load_manifest()
    native_manifest = []
    failures = 0
    for relative, fallback in PATCHES.items():
        path = WORK / relative
        if not path.is_file():
            print(f"skip: {relative} (not present)")
            continue
        entries = auto_entries(path)
        if not entries:
            entries = fallback
        try:
            patched, unchanged = apply_entries(path, entries)
        except RuntimeError as error:
            print(f"error: {error}")
            failures += 1
            continue
        for entry in entries:
            native_manifest.append(
                {
                    "entry": relative,
                    "offset": entry["offset"],
                    "bytes": entry["patch"].hex(" "),
                    "anchor": entry.get("anchor", entry["name"]),
                }
            )
        print(f"{relative}: patched={patched} unchanged={unchanged}")
    manifest["native"] = native_manifest
    save_manifest(manifest)
    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
