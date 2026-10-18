from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

RG = shutil.which("rg") or "rg"


def rg_files(work: Path, pattern: str, glob: str = "*.smali") -> list[Path]:
    proc = subprocess.run(
        [RG, "-l", "--no-messages", "-F", "-g", glob, pattern, str(work)],
        capture_output=True,
        text=True,
    )
    return [Path(line) for line in proc.stdout.splitlines() if line]


def rg_files_by_name(work: Path, name: str) -> list[Path]:
    proc = subprocess.run(
        [RG, "--files", "-g", name, str(work)],
        capture_output=True,
        text=True,
    )
    return [Path(line) for line in proc.stdout.splitlines() if line]


def read_methods(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []
    return [line.strip() for line in text.split("\n") if line.startswith(".method ")]


def resolve_by_source(work: Path, source: str, method: str) -> Path:
    cands = rg_files(work, f'.source "{source}"')
    if not cands:
        raise SystemExit(f"resolve: no class with .source {source!r}")
    hits = [p for p in cands if method in read_methods(p)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise SystemExit(f"resolve: no {method!r} in .source {source!r} ({len(cands)} files)")
    raise SystemExit(f"resolve: ambiguous {method!r} in {source!r}: {[str(p) for p in hits]}")


def resolve_by_name(work: Path, suffix: str) -> Path:
    name = Path(suffix).name
    hits = [p for p in rg_files_by_name(work, name) if p.as_posix().endswith(suffix)]
    if len(hits) == 1:
        return hits[0]
    raise SystemExit(f"resolve: {suffix!r} matched {len(hits)}")


if __name__ == "__main__":
    mode = sys.argv[1]
    work = Path(sys.argv[2])
    if mode == "resolve":
        print(resolve_by_source(work, sys.argv[3], sys.argv[4]).relative_to(work).as_posix())
    else:
        raise SystemExit(2)