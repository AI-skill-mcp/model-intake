#!/usr/bin/env python3
"""
知识库检索工具：从 workspace.yaml 定位 rawdata 目录。

用法:
  python search.py "esm2"
  python search.py --entity model --list
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_KIT_DIR = Path(__file__).resolve().parent
if str(_KIT_DIR) not in sys.path:
    sys.path.insert(0, str(_KIT_DIR))

from workspace import (  # noqa: E402
    DEFAULT_RAWDATA_DIR,
    WORKSPACE_YAML,
    get_rawdata_rel,
    load_workspace_config,
    propose_defaults,
    resolve_paths,
)

ENTITY_SUBPATHS = {
    "model": "model",
    "tool": "tools",
    "metric": "metrics",
    "format": "formats",
    "dataset": "datasets",
}


def _rawdata_root(explicit_root: Path | None = None) -> tuple[Path, str]:
    """返回 (workspace_root, rawdata_rel)。"""
    if explicit_root:
        return explicit_root.resolve(), DEFAULT_RAWDATA_DIR
    if WORKSPACE_YAML.exists():
        paths = resolve_paths()
        return paths.root, paths.rawdata_rel
    script = Path(__file__).resolve()
    if script.parent.name == ".kbase":
        kbase_root = script.parent.parent
        manifest = kbase_root / ".kbase" / "manifest.json"
        if manifest.exists():
            import json
            m = json.loads(manifest.read_text(encoding="utf-8"))
            rel = m.get("rawdata_dir") or m.get("bioinformatics_dir") or DEFAULT_RAWDATA_DIR
            return kbase_root, rel
    detected = propose_defaults()
    ws = detected["workspace"]
    return Path(ws["root"]), get_rawdata_rel(ws)


def find_workspace_root(explicit_root: Path | None = None) -> Path:
    root, rel = _rawdata_root(explicit_root)
    return root / rel


def iter_md_files(rawdata_base: Path, entity: str | None) -> list[Path]:
    files: list[Path] = []
    if entity:
        base = rawdata_base / ENTITY_SUBPATHS[entity]
        if entity == "model":
            return sorted(base.rglob("*.md")) if base.is_dir() else []
        return sorted(base.glob("*.md")) if base.is_dir() else []

    for key, sub in ENTITY_SUBPATHS.items():
        base = rawdata_base / sub
        if not base.exists():
            continue
        if key == "model":
            files.extend(sorted(base.rglob("*.md")))
        else:
            files.extend(sorted(base.glob("*.md")))
    return files


def extract_title(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def search(rawdata_base: Path, query: str, entity: str | None, list_only: bool) -> list[tuple[Path, str, list[str]]]:
    results: list[tuple[Path, str, list[str]]] = []
    pattern = re.compile(re.escape(query), re.IGNORECASE) if query else None

    for path in iter_md_files(rawdata_base, entity):
        if list_only and query and query.lower() not in path.stem.lower():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        title = extract_title(text)
        if list_only and not query:
            results.append((path, title, []))
            continue
        if not pattern:
            results.append((path, title, []))
            continue
        hits = [ln.strip() for ln in text.splitlines() if pattern.search(ln)][:3]
        if hits or pattern.search(path.stem) or pattern.search(title):
            results.append((path, title, hits))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="知识库实体检索（rawdata 目录由 workspace.yaml 指定）")
    parser.add_argument("query", nargs="?", default="", help="搜索关键词")
    parser.add_argument("--entity", "-e", choices=list(ENTITY_SUBPATHS.keys()))
    parser.add_argument("--list", "-l", action="store_true")
    parser.add_argument("--root", type=Path, default=None, help="覆盖 workspace 根目录")
    args = parser.parse_args()

    ws_root, raw_rel = _rawdata_root(args.root)
    rawdata_base = ws_root / raw_rel
    if not rawdata_base.is_dir():
        raise SystemExit(f"原始数据目录不存在: {rawdata_base}（rawdata_dir={raw_rel}）")

    hits = search(rawdata_base, args.query, args.entity, args.list or not args.query)
    if not hits:
        print("无匹配结果")
        return 1

    for path, title, lines in hits:
        rel = path.relative_to(ws_root)
        print(f"{rel}\t{title or path.stem}")
        for ln in lines:
            print(f"  | {ln[:120]}")
    print(f"\n共 {len(hits)} 条（root={ws_root}, rawdata_dir={raw_rel}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
