from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "work")
PACKAGE = sys.argv[2] if len(sys.argv) > 2 else "com.uma.musicvk.patched"

TRACE_PATH = f"/sdcard/Android/data/{PACKAGE}/files/trace.txt"
HELPER = "smali/xsna/ztrace.smali"
APP_CONTEXT = "Lxsna/ho1;->a:Landroid/content/Context;"
ZTRACE = "Lxsna/ztrace;"

START_SITE = ("smali/com/vk/music/app/VkMusicApplication.smali", "onCreate()V")

HELPER_TEMPLATE = """.class public final Lxsna/ztrace;
.super Ljava/lang/Object;

.method public constructor <init>()V
    .locals 0

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method
__MARKERS__
.method public static mStart(Landroid/content/Context;)V
    .locals 1

    const-string v0, "app onCreate"

    invoke-static {p0, v0}, Lxsna/ztrace;->w(Landroid/content/Context;Ljava/lang/String;)V

    return-void
.end method
.method private static w(Landroid/content/Context;Ljava/lang/String;)V
    .locals 6

    :try_start_0
    new-instance v0, Ljava/lang/StringBuilder;

    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V

    invoke-virtual {v0, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    const-string v1, "\\n"

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    new-instance v1, Ljava/lang/Thread;

    invoke-static {}, Ljava/lang/Thread;->currentThread()Ljava/lang/Thread;

    move-result-object v1

    invoke-virtual {v1}, Ljava/lang/Thread;->getStackTrace()[Ljava/lang/StackTraceElement;

    move-result-object v1

    invoke-static {v1}, Ljava/util/Arrays;->toString([Ljava/lang/Object;)Ljava/lang/String;

    move-result-object v1

    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;

    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;

    move-result-object v0

    const-string v1, "ztrace"

    invoke-static {v1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    if-eqz p0, :ctx_static

    goto :ctx_ready

    :ctx_static
    sget-object p0, __CONTEXT__

    if-eqz p0, :ctx_ready

    :ctx_ready
    if-eqz p0, :goto_0

    invoke-virtual {p0, v1}, Landroid/content/Context;->getExternalFilesDir(Ljava/lang/String;)Ljava/io/File;

    move-result-object p0

    if-eqz p0, :goto_0

    new-instance v1, Ljava/io/File;

    const-string v2, "trace.txt"

    invoke-direct {v1, p0, v2}, Ljava/io/File;-><init>(Ljava/io/File;Ljava/lang/String;)V

    new-instance p0, Ljava/io/FileOutputStream;

    const/4 v2, 0x1

    invoke-direct {p0, v1, v2}, Ljava/io/FileOutputStream;-><init>(Ljava/io/File;Z)V

    const-string v1, "UTF-8"

    invoke-virtual {v0, v1}, Ljava/lang/String;->getBytes(Ljava/lang/String;)[B

    move-result-object v0

    invoke-virtual {p0, v0}, Ljava/io/FileOutputStream;->write([B)V

    invoke-virtual {p0}, Ljava/io/FileOutputStream;->close()V
    :try_end_0
    .catch Ljava/lang/Throwable; {:try_start_0 .. :try_end_0} :catch_0

    goto :goto_0

    :catch_0
    move-exception v0

    const-string v1, "ztrace"

    const-string v0, "trace failed"

    invoke-static {v1, v0}, Landroid/util/Log;->e(Ljava/lang/String;Ljava/lang/String;)I

    :goto_0
    return-void
.end method
"""

MARKER_TEMPLATE = """
.method public static m__INDEX__()V
    .locals 2

    const/4 v0, 0x0

    const-string v1, "__NAME__"

    invoke-static {v0, v1}, Lxsna/ztrace;->w(Landroid/content/Context;Ljava/lang/String;)V

    return-void
.end method
"""

CALL = "    invoke-static {}, Lxsna/ztrace;->m__INDEX__()V"
START_CALL = f"    invoke-static {{p0}}, {ZTRACE}->mStart(Landroid/content/Context;)V"


def marker(index: int, site: str) -> str:
    return MARKER_TEMPLATE.replace("__INDEX__", str(index)).replace("__NAME__", site)


def call(index: int) -> str:
    return CALL.replace("__INDEX__", str(index))


def collect_sites() -> list[tuple[Path, str, int]]:
    sites: list[tuple[Path, str, int]] = []
    for path in sorted(WORK.rglob("*.smali")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Ljava/lang/System;->exit" in text or "Ljava/lang/Runtime;->exit" in text:
            method = ""
            method_line = -1
            for index, line in enumerate(text.split("\n")):
                if line.startswith(".method"):
                    method = line.strip()
                    method_line = index
                    continue
                if "Ljava/lang/System;->exit" in line or "Ljava/lang/Runtime;->exit" in line:
                    sites.append((path, method, method_line))
    return sites


def find_start_site() -> tuple[Path, str, int] | None:
    path = WORK / START_SITE[0]
    if not path.is_file():
        return None
    for index, line in enumerate(path.read_text(encoding="utf-8").split("\n")):
        if line.startswith(".method") and START_SITE[1] in line:
            return path, line.strip(), index
    return None


def clean() -> None:
    helper = WORK / HELPER
    if helper.is_file():
        helper.unlink()
        print(f"removed: {HELPER}")
    touched = 0
    for path in sorted(WORK.rglob("*.smali")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "Lxsna/ztrace;" not in text:
            continue
        lines = [line for line in text.split("\n") if "Lxsna/ztrace;" not in line]
        path.write_text("\n".join(lines), encoding="utf-8")
        touched += 1
    if touched:
        print(f"cleaned: {touched} files")


def insert(entries: list[tuple[Path, str, int]], line_for: dict[int, str]) -> None:
    grouped: dict[Path, list[tuple[int, int]]] = {}
    for index, (path, _, method_line) in enumerate(entries):
        grouped.setdefault(path, []).append((method_line, index))
    for path, items in grouped.items():
        lines = path.read_text(encoding="utf-8").split("\n")
        for method_line, index in sorted(items, key=lambda item: -item[0]):
            at = method_line + 1
            while at < len(lines) and not lines[at].strip().startswith(
                (".locals", ".registers")
            ):
                at += 1
            lines.insert(at + 1, line_for[index])
        path.write_text("\n".join(lines), encoding="utf-8")
        print(f"instrumented: {path.relative_to(WORK)} ({len(items)} sites)")


def main() -> int:
    clean()
    if len(sys.argv) > 2 and sys.argv[2] == "--clean":
        print("clean only")
        return 0
    sites = collect_sites()
    start = find_start_site()
    if not sites and start is None:
        print("no sites found")
        return 1
    markers = "".join(
        marker(index, f"{path.relative_to(WORK).as_posix()} {method}")
        for index, (path, method, _) in enumerate(sites)
    )
    helper_text = (
        HELPER_TEMPLATE.replace("__MARKERS__", markers).replace("__CONTEXT__", APP_CONTEXT)
    )
    helper = WORK / HELPER
    helper.parent.mkdir(parents=True, exist_ok=True)
    helper.write_text(helper_text, encoding="utf-8")
    print(f"helper: {HELPER} -> {TRACE_PATH}")
    insert(sites, {index: call(index) for index in range(len(sites))})
    if start is not None:
        insert([start], {0: START_CALL})
    print(f"sites: {len(sites)}, start: {start is not None}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
