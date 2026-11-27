from __future__ import annotations

import sys
from pathlib import Path

import vk_auto

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "build" / "patch_manifest.json"


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: vk_patch.py <decoded-work-dir>")
        return 2
    work = Path(sys.argv[1])
    if not work.is_dir():
        print(f"missing work dir: {work}")
        return 1
    try:
        result = vk_auto.resolve(work)
    except vk_auto.AutoPatchError as error:
        print(f"error: {error}")
        return 1
    failures = 0
    for patch in result.patches:
        try:
            status = vk_auto.patch_file(patch.cls.path, patch.method.header, patch.body)
        except vk_auto.AutoPatchError as error:
            print(f"error: {error}")
            failures += 1
            continue
        print(
            f"{status}: {patch.cls.path.relative_to(work).as_posix()} "
            f"-> {patch.method.signature} [{patch.name}]"
        )
    for warning in result.warnings:
        print(f"warning: {warning}")
    vk_auto.write_manifest(MANIFEST, result.manifest())
    print(f"resolved: {len(result.patches)}")
    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
