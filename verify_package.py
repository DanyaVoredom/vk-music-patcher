from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

logger.remove()

from androguard.core.apk import APK
from androguard.core.dex import DEX

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "VK Музыка_8.44.apk"
PATCHED = ROOT / "VK Музыка_8.44_patched.apk"
COMPONENT_TAGS = ("activity", "activity-alias", "service", "receiver", "provider")


def dex_classes(apk_path: Path) -> set[str]:
    classes: set[str] = set()
    with_apk = APK(str(apk_path))
    for entry in with_apk.get_all_dex():
        dex = DEX(entry)
        for cls in dex.get_classes():
            classes.add(cls.get_name())
    return classes


def manifest_facts(apk_path: Path) -> tuple[str, set[str], set[str], set[str]]:
    apk = APK(str(apk_path))
    manifest = apk.get_android_manifest_xml()
    package = manifest.get("package", "")
    authorities: set[str] = set()
    components: set[str] = set()
    permissions: set[str] = set()
    root = manifest.find("application")
    if root is not None:
        for tag in COMPONENT_TAGS:
            for node in root.findall(tag):
                name = node.get("{http://schemas.android.com/apk/res/android}name", "")
                if name:
                    components.add(name)
        components.add(root.get("{http://schemas.android.com/apk/res/android}name", ""))
    for node in manifest.iter("provider"):
        value = node.get("{http://schemas.android.com/apk/res/android}authorities", "")
        if not value:
            value = node.get(
                "{http://schemas.android.com/apk/res/android}authorities", ""
            )
        if value.startswith("@string/"):
            resource = value.split("/", 1)[1]
            resolved = apk.get_resolved_strings().get(resource)
            value = resolved[0] if resolved else value
        if value:
            authorities.update(part for part in value.split(";") if part)
    for node in manifest.iter("permission"):
        name = node.get("{http://schemas.android.com/apk/res/android}name", "")
        if name:
            permissions.add(name)
    return package, authorities, components, permissions


def missing_classes(components: set[str], classes: set[str]) -> set[str]:
    missing = set()
    for name in components:
        if name.startswith("."):
            continue
        if "." not in name:
            continue
        descriptor = "L" + name.replace(".", "/") + ";"
        if descriptor not in classes:
            missing.add(name)
    return missing


def main() -> int:
    original_classes = dex_classes(ORIGINAL)
    patched_classes = dex_classes(PATCHED)
    original_package, original_authorities, original_components, original_permissions = (
        manifest_facts(ORIGINAL)
    )
    patched_package, patched_authorities, patched_components, patched_permissions = (
        manifest_facts(PATCHED)
    )

    failures = 0

    print(f"original package: {original_package}")
    print(f"patched  package: {patched_package}")
    if original_package == patched_package:
        print("FAIL package name did not change")
        failures += 1

    shared = sorted(original_authorities & patched_authorities)
    print(f"authorities: original={len(original_authorities)} patched={len(patched_authorities)}")
    if shared:
        print(f"FAIL shared authorities: {shared}")
        failures += 1
    else:
        print("OK   no authority collides with the original app")

    shared_permissions = sorted(original_permissions & patched_permissions)
    if shared_permissions:
        print(f"WARN shared custom permissions: {shared_permissions}")
    else:
        print("OK   no custom permission collides with the original app")

    original_missing = missing_classes(original_components, original_classes)
    patched_missing = missing_classes(patched_components, patched_classes)
    broken = sorted(patched_missing - original_missing)
    if broken:
        print(f"FAIL component classes missing only in patched apk: {broken}")
        failures += 1
    else:
        print(f"OK   no new unresolved component classes ({len(patched_missing)} pre-existing)")

    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
