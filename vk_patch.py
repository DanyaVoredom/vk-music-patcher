from __future__ import annotations

import sys
from pathlib import Path

import vk_targets as T
from vk_resolve import resolve_by_source, resolve_by_name


def split_lines(raw: bytes) -> tuple[list[str], str]:
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n").split("\n"), newline


def class_descriptor(path: Path) -> str:
    lines, _ = split_lines(path.read_bytes())
    for line in lines:
        if line.startswith(".class "):
            for token in reversed(line.split()):
                if token.startswith("L") and token.endswith(";"):
                    return token[1:-1]
    raise SystemExit(f"no class descriptor in {path}")


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
    body_lines = body.rstrip("\n").split("\n")
    if lines[begin + 1 : stop] == body_lines:
        return "unchanged"
    lines[begin + 1 : stop] = body_lines
    path.write_bytes(newline.join(lines).encode("utf-8"))
    return "patched"


def patch_source_targets(work: Path, targets: list[dict]) -> int:
    failed = 0
    for t in targets:
        try:
            path = resolve_by_source(work, t["source"], t["method"])
            cls = class_descriptor(path)
            status = patch_file(path, t["method"], T.body_for(t["body"], cls))
        except SystemExit as e:
            print(f"error: {e}")
            failed += 1
            continue
        print(f"{status}: {path.relative_to(work).as_posix()} -> {t['method']}")
    return failed


def patch_path_targets(work: Path, targets: list[dict]) -> int:
    failed = 0
    for t in targets:
        try:
            path = resolve_by_name(work, t["path"])
            status = patch_file(path, t["method"], T.body_for(t["body"]))
        except SystemExit as e:
            print(f"error: {e}")
            failed += 1
            continue
        print(f"{status}: {path.relative_to(work).as_posix()} -> {t['method']}")
    return failed


def patch_migration(work: Path) -> int:
    from vk_resolve import rg_files

    files = rg_files(work, f'.source "{T.MIGRATION["source"]}"')
    cands = []
    for rel in files:
        text = rel.read_text(encoding="utf-8", errors="ignore")
        if T.MIGRATION["start"] in text and T.MIGRATION["end"] in text:
            cands.append(rel)
    if not cands:
        patched = [
            rel
            for rel in files
            if T.MIGRATION["replacement"]
            in rel.read_text(encoding="utf-8", errors="ignore").split("\n")
        ]
        if len(patched) == 1:
            print(f"unchanged: {patched[0].relative_to(work).as_posix()} migration")
            return 0
    if len(cands) != 1:
        print(f"error: migration matched {len(cands)} files")
        return 1
    path = cands[0]
    lines, newline = split_lines(path.read_bytes())
    begin = next(i for i, line in enumerate(lines) if line == T.MIGRATION["start"])
    stop = next(i for i in range(begin + 1, len(lines)) if lines[i] == T.MIGRATION["end"])
    if lines[begin : stop + 1] == [T.MIGRATION["replacement"]]:
        print(f"unchanged: {path.relative_to(work).as_posix()} migration")
        return 0
    lines[begin : stop + 1] = [T.MIGRATION["replacement"]]
    path.write_bytes(newline.join(lines).encode("utf-8"))
    print(f"patched: {path.relative_to(work).as_posix()} migration")
    return 0


def patch_preference_scope(work: Path) -> int:
    target = T.PREFERENCE_SCOPE
    try:
        path = resolve_by_name(work, target["path"])
        lines, newline = split_lines(path.read_bytes())
        if f'.source "{target["source"]}"' not in lines:
            raise SystemExit(f"{path}: unexpected source")
        starts = [i for i, line in enumerate(lines) if line.strip() == target["method"]]
        if len(starts) != 1:
            raise SystemExit(f"{path}: scope method matched {len(starts)} times")
        begin = starts[0] + 1
        stop = next((i for i in range(begin, len(lines)) if lines[i].strip() == ".end method"), None)
        if stop is None:
            raise SystemExit(f"{path}: missing scope method end")
        body = "\n".join(lines[begin:stop])
        old_count = body.count(target["old"])
        new_count = body.count(target["new"])
        if old_count == 0 and new_count == 1:
            print(f"unchanged: {path.relative_to(work).as_posix()} session scope")
            return 0
        if old_count != 1 or new_count:
            raise SystemExit(f"{path}: unexpected scope literals ({old_count}, {new_count})")
        lines[begin:stop] = body.replace(target["old"], target["new"]).split("\n")
        path.write_bytes(newline.join(lines).encode("utf-8"))
        print(f"patched: {path.relative_to(work).as_posix()} session scope")
        return 0
    except SystemExit as error:
        print(f"error: {error}")
        return 1


def main() -> int:
    work = Path(sys.argv[1])
    if not work.is_dir():
        print(f"missing work dir: {work}")
        return 1
    failed = 0
    failed += patch_source_targets(work, T.TARGETS)
    failed += patch_source_targets(work, T.PLAYER_TARGETS)
    failed += patch_path_targets(work, T.MUSICTRACK_TARGETS)
    failed += patch_migration(work)
    failed += patch_preference_scope(work)
    print(f"failures: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
