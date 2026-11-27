from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UPDATER_SMALI = ROOT / "updater" / "smali"
MAIN_ACTIVITY = Path("smali/com/vk/music/screens/main/MainActivity.smali")
MANIFEST = Path("AndroidManifest.xml")
REVISION_RESOURCE = Path("res/values/vk_mod_revision.xml")
METHOD = ".method public final onCreate(Landroid/os/Bundle;)V"
INVOKE = "    invoke-static {p0}, Lcom/vk/music/updater/UpdateChecker;->check(Landroid/app/Activity;)V"
PERMISSION = '    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES"/>'


def read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes().decode("utf-8")
    newline = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), newline


def write_text(path: Path, text: str, newline: str) -> None:
    path.write_bytes(text.replace("\n", newline).encode("utf-8"))


def revision() -> int:
    value = os.environ.get("VKM_MOD_REVISION", "0").strip()
    if not value.isdigit():
        raise SystemExit(f"VKM_MOD_REVISION must be an integer, got {value!r}")
    return int(value)


def install_smali(work: Path) -> None:
    target = work / "smali" / "com" / "vk" / "music" / "updater"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(UPDATER_SMALI / "com" / "vk" / "music" / "updater", target)
    repo = os.environ.get("VKM_UPDATE_REPO", "DanyaVoredom/DanyExternal-Releases")
    default_api = "https://api.github.com/repos/DanyaVoredom/DanyExternal-Releases/releases?per_page=100"
    api = os.environ.get("VKM_UPDATE_API", "https://api.github.com/repos/{repo}/releases?per_page=100").format(repo=repo)
    for path in target.glob("*.smali"):
        text = path.read_text(encoding="utf-8")
        replaced = text.replace(default_api, api).replace("DanyaVoredom/DanyExternal-Releases", repo)
        if replaced != text:
            path.write_text(replaced, encoding="utf-8")
    print(f"copied updater smali: {target.relative_to(work).as_posix()} api={api}")


def install_revision(work: Path, value: int) -> None:
    path = work / REVISION_RESOURCE
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        "<resources>\n"
        f'    <integer name="vk_mod_revision">{value}</integer>\n'
        "</resources>\n"
    )
    path.write_text(text, encoding="utf-8")
    print(f"mod revision: {value}")


def install_permission(work: Path) -> None:
    path = work / MANIFEST
    text, newline = read_text(path)
    if "android.permission.REQUEST_INSTALL_PACKAGES" in text:
        print("manifest: install permission present")
        return
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.lstrip().startswith("<application "):
            lines.insert(index, PERMISSION)
            break
    else:
        raise SystemExit("manifest: application element not found")
    write_text(path, "\n".join(lines), newline)
    print("manifest: install permission added")


def install_call(work: Path) -> None:
    path = work / MAIN_ACTIVITY
    if not path.is_file():
        raise SystemExit(f"missing activity: {path}")
    text, newline = read_text(path)
    lines = text.split("\n")
    start = next((i for i, line in enumerate(lines) if line.strip() == METHOD), None)
    if start is None:
        raise SystemExit(f"{MAIN_ACTIVITY}: onCreate not found")
    stop = next((i for i in range(start + 1, len(lines)) if lines[i].strip() == ".end method"), None)
    if stop is None:
        raise SystemExit(f"{MAIN_ACTIVITY}: onCreate end not found")
    if any("Lcom/vk/music/updater/UpdateChecker;->check" in line for line in lines[start:stop]):
        print("MainActivity: updater call present")
        return
    super_at = next(
        (
            i
            for i in range(start + 1, stop)
            if lines[i].strip().startswith("invoke-super")
            and "->onCreate(Landroid/os/Bundle;)V" in lines[i]
        ),
        None,
    )
    if super_at is None:
        raise SystemExit(f"{MAIN_ACTIVITY}: super.onCreate not found")
    lines.insert(super_at + 1, INVOKE)
    write_text(path, "\n".join(lines), newline)
    print("MainActivity: updater call added")


def main() -> int:
    work = Path(sys.argv[1])
    if not work.is_dir():
        print(f"missing work dir: {work}")
        return 1
    value = revision()
    install_smali(work)
    install_revision(work, value)
    install_permission(work)
    install_call(work)
    return 0


if __name__ == "__main__":
    sys.exit(main())
