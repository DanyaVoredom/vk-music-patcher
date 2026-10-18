from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "work")

FAR_FUTURE = "0xf4865680L"


def bool_body(value: int, register: str = "v1", locals_count: int = 1) -> str:
    return (
        f"    .locals {locals_count}\n"
        "\n"
        f"    const/4 {register}, 0x{value:x}\n"
        "\n"
        f"    return {register}\n"
    )


def long_body(register: str = "v1", locals_count: int = 2) -> str:
    return (
        f"    .locals {locals_count}\n"
        "\n"
        f"    const-wide {register}, {FAR_FUTURE}\n"
        "\n"
        f"    return-wide {register}\n"
    )


def current_account_info_ctor_body() -> str:
    return (
        "    .locals 0\n"
        "\n"
        "    invoke-direct {p0}, Ljava/lang/Object;-><init>()V\n"
        "\n"
        "    const/4 p1, 0x1\n"
        "\n"
        f"    const-wide p2, {FAR_FUTURE}\n"
        "\n"
        "    iput-boolean p1, p0, Lxsna/rm9;->a:Z\n"
        "\n"
        "    iput-wide p2, p0, Lxsna/rm9;->b:J\n"
        "\n"
        "    return-void\n"
    )


PATCHES: list[tuple[str, str, str]] = [
    (
        r"smali\xsna\gdm.smali",
        ".method public final b()Z",
        bool_body(1),
    ),
    (
        r"smali\xsna\gdm.smali",
        ".method public final c()J",
        long_body(),
    ),
    (
        r"smali_classes8\xsna\cdm$a$a.smali",
        ".method public final b()Z",
        bool_body(1),
    ),
    (
        r"smali_classes8\xsna\cdm$a$a.smali",
        ".method public final c()J",
        long_body(),
    ),
    (
        r"smali_classes7\xsna\rm9.smali",
        ".method public constructor <init>(ZJ)V",
        current_account_info_ctor_body(),
    ),
    (
        r"smali_classes7\xsna\wz8.smali",
        ".method public static final b(I)Z",
        bool_body(1),
    ),
    (
        r"smali_classes7\xsna\wz8.smali",
        ".method public static final d(I)Z",
        bool_body(0),
    ),
    (
        r"smali_classes7\xsna\wz8.smali",
        ".method public static final e(I)Z",
        bool_body(0),
    ),
    (
        r"smali_classes7\xsna\wz8.smali",
        ".method public static final f(I)Z",
        bool_body(0),
    ),
    (
        r"smali_classes7\com\vk\dto\music\MusicTrack.smali",
        ".method public final B6()I",
        bool_body(0),
    ),
    (
        r"smali_classes7\com\vk\dto\music\MusicTrack.smali",
        ".method public final l()Z",
        bool_body(0),
    ),
    (
        r"smali\xsna\c1q.smali",
        ".method public static E(Lxsna/c8w;Ljava/util/List;)Z",
        bool_body(0, "v2", 2),
    ),
    (
        r"smali\com\vk\toggle\d.smali",
        ".method public static z(Z)Z",
        bool_body(1),
    ),
    (
        r"smali_classes8\xsna\xfm.smali",
        ".method public static final d(Lcom/vk/dto/music/MusicTrack;)Z",
        bool_body(0),
    ),
    (
        r"smali_classes8\xsna\mhl.smali",
        ".method public final a()Z",
        bool_body(0),
    ),
]


def split_lines(raw: bytes) -> tuple[list[str], str]:
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n").split("\n"), newline


def patch_file(path: Path, method_line: str, body: str) -> str:
    lines, newline = split_lines(path.read_bytes())
    start = [i for i, line in enumerate(lines) if line.strip() == method_line]
    if len(start) != 1:
        raise SystemExit(f"{path}: method {method_line!r} found {len(start)} times")
    begin = start[0]
    stop = next(
        (i for i in range(begin + 1, len(lines)) if lines[i].strip() == ".end method"),
        None,
    )
    if stop is None:
        raise SystemExit(f"{path}: no .end method for {method_line!r}")
    if newline == "\n" and lines[stop] != ".end method":
        raise SystemExit(f"{path}: malformed .end method for {method_line!r}")
    body_lines = body.rstrip("\n").split("\n")
    if lines[begin + 1 : stop] == body_lines:
        return "unchanged"
    lines[begin + 1 : stop] = body_lines
    path.write_bytes(newline.join(lines).encode("utf-8"))
    return "patched"


def main() -> int:
    failed = 0
    for relative, method_line, body in PATCHES:
        path = WORK / relative
        if not path.is_file():
            print(f"missing: {relative}")
            failed += 1
            continue
        try:
            status = patch_file(path, method_line, body)
        except SystemExit as error:
            print(f"error: {error}")
            failed += 1
            continue
        print(f"{status}: {relative} -> {method_line}")
    print(f"patches: {len(PATCHES)}, failures: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
