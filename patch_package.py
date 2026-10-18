from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"

OLD_PACKAGE = "com.uma.musicvk"
NEW_SUFFIX = "patched"
NEW_PACKAGE = f"{OLD_PACKAGE}.{NEW_SUFFIX}"
APP_LABEL = "VK Музыка (патч)"
APP_LABEL_RESOURCE = "app_name_patched"

CAR_AUTHORITY = f"{NEW_PACKAGE}.car.app.connection"
APPREDIRECT_AUTHORITY = f"{NEW_PACKAGE}.appredirect"
FILEPROVIDER_AUTHORITY = f"{NEW_PACKAGE}.fileprovider"

REPAIRS = {
    f'android:name="{CAR_AUTHORITY}.provider"': 'android:name="androidx.car.app.connection.provider"',
    f'"{CAR_AUTHORITY}.action.CAR_CONNECTION_UPDATED"': '"androidx.car.app.connection.action.CAR_CONNECTION_UPDATED"',
}

XML_RENAMES = {
    "com.vk.vkmusic.provider": FILEPROVIDER_AUTHORITY,
    'android:authorities="androidx.car.app.connection"': f'android:authorities="{CAR_AUTHORITY}"',
    'android:authorities="com.vkontakte.android.vk_music_redirect_provider"': f'android:authorities="{APPREDIRECT_AUTHORITY}"',
}

SMALI_RENAMES = {
    '"androidx.car.app.connection"': f'"{CAR_AUTHORITY}"',
    '"com.vkontakte.android.vk_music_redirect_provider"': f'"{APPREDIRECT_AUTHORITY}"',
    '"com.vk.vkmusic.provider"': f'"{FILEPROVIDER_AUTHORITY}"',
}

MANIFEST = "AndroidManifest.xml"
STRINGS = "res/values/strings.xml"
SMALI_TARGETS = (
    "smali/xsna/xt7.smali",
    "smali_classes3/xsna/hry.smali",
    "smali_classes3/xsna/zq5.smali",
    "smali_classes5/com/vk/appredirects/entity/App.smali",
    "smali_classes6/com/vk/core/apps/BuildInfo$a.smali",
)
TARGETS = (MANIFEST, STRINGS, *SMALI_TARGETS)


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), newline


def write_text(path: Path, text: str, newline: str) -> None:
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


def apply_replacements(text: str, table: dict[str, str]) -> tuple[str, int]:
    count = 0
    for old, new in table.items():
        count += text.count(old)
        text = text.replace(old, new)
    return text, count


def rename_package(text: str) -> tuple[str, int]:
    collapsed = re.sub(
        rf"({re.escape(OLD_PACKAGE)})(?:\.{re.escape(NEW_SUFFIX)})+",
        rf"\1.{NEW_SUFFIX}",
        text,
    )
    pattern = re.compile(
        rf"{re.escape(OLD_PACKAGE)}(?!\.{re.escape(NEW_SUFFIX)})"
    )
    count = len(pattern.findall(collapsed))
    return pattern.sub(NEW_PACKAGE, collapsed), count


def patch_manifest(text: str) -> str:
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if not line.lstrip().startswith("<application "):
            continue
        if f'android:label="@string/{APP_LABEL_RESOURCE}"' in line:
            return text
        marker = 'android:label="@string/app_name"'
        if marker not in line:
            raise SystemExit("manifest: application label attribute not found")
        lines[index] = line.replace(marker, f'android:label="@string/{APP_LABEL_RESOURCE}"')
        break
    else:
        raise SystemExit("manifest: <application> element not found")
    return "\n".join(lines)


def patch_strings(text: str) -> str:
    declaration = f'<string name="{APP_LABEL_RESOURCE}">{APP_LABEL}</string>'
    if f'name="{APP_LABEL_RESOURCE}"' in text:
        return text
    if "</resources>" not in text:
        raise SystemExit("strings.xml: </resources> not found")
    return text.replace("</resources>", f"    {declaration}\n</resources>", 1)


def main() -> int:
    for relative in TARGETS:
        path = WORK / relative
        if not path.is_file():
            print(f"missing: {relative}")
            return 1
        text, newline = read_text(path)
        text, repair_hits = apply_replacements(text, REPAIRS)
        text, package_hits = rename_package(text)
        table = XML_RENAMES if relative in (MANIFEST, STRINGS) else SMALI_RENAMES
        text, rename_hits = apply_replacements(text, table)
        if relative == MANIFEST:
            text = patch_manifest(text)
        if relative == STRINGS:
            text = patch_strings(text)
        write_text(path, text, newline)
        print(
            f"{relative}: repair={repair_hits} package={package_hits} rename={rename_hits}"
        )
    print(f"old: {OLD_PACKAGE}")
    print(f"new: {NEW_PACKAGE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
