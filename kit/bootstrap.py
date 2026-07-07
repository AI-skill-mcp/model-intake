#!/usr/bin/env python3
"""
初始化独立知识库目录（model-intake kit bootstrap）。

用法:
  python bootstrap.py /path/to/new-kbase
  python bootstrap.py . --with-graph
  python bootstrap.py ~/my-models --name my-models --with-graph --no-seeds

输入: 目标目录路径、可选 flags
输出: 完整 kbase 目录结构、.kbase/manifest.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import date
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent
TODAY = date.today().isoformat()

MODEL_SUBCATS = [
    "protein", "enzyme", "rna", "genome", "single-cell", "multi-modal",
    "function", "interaction", "ptm", "expression", "cellular",
]


def _copy_tree(src: Path, dst: Path) -> None:
    """递归复制目录，目标已存在则合并。"""
    if not src.exists():
        raise FileNotFoundError(f"源不存在: {src}")
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        target = dst / item.name
        if item.is_dir():
            _copy_tree(item, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def _render_template(tpl_path: Path, ctx: dict[str, str]) -> str:
    """简单 {{key}} 模板渲染。"""
    text = tpl_path.read_text(encoding="utf-8")
    for key, val in ctx.items():
        text = text.replace("{{" + key + "}}", val)
    return text


def _write_if_missing(path: Path, content: str) -> bool:
    """文件不存在时写入，返回是否新建。"""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def init_kbase(
    target: Path,
    *,
    name: str,
    with_graph: bool,
    with_seeds: bool,
    force: bool,
    rawdata_dir: str = "rawdata",
) -> dict:
    """
    在 target 目录初始化知识库（用户工作区，非 Skill 目录）。

    返回 manifest 字典。
    """
    target = target.resolve()

    # 禁止写入 Skill 目录
    skill_root = KIT_ROOT.parent.resolve()
    try:
        target.relative_to(skill_root)
    except ValueError:
        pass
    else:
        raise ValueError(
            f"禁止在 Skill 目录内初始化数据: {target}\n"
            f"请使用 workspace.yaml 指定 Skill 外的路径"
        )
    ctx = {"name": name, "date": TODAY, "rawdata_dir": rawdata_dir}

    # 检测是否已初始化
    manifest_path = target / ".kbase" / "manifest.json"
    if manifest_path.exists() and not force:
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        # 补建旧工作区缺失的 paper/ 目录
        paper_dir = target / rawdata_dir / "paper"
        paper_dir.mkdir(parents=True, exist_ok=True)
        gitkeep = paper_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("", encoding="utf-8")
        print(f"已初始化: {target} (mode={existing.get('mode')})")
        print("使用 --force 覆盖非 manifest 缺失项")
        return existing

    target.mkdir(parents=True, exist_ok=True)
    (target / ".kbase").mkdir(exist_ok=True)

    created: list[str] = []

    # 原始数据目录树（默认 rawdata，可由 workspace.rawdata_dir 配置为 bioinformatics）
    bio = target / rawdata_dir
    for sub in MODEL_SUBCATS:
        d = bio / "model" / sub
        d.mkdir(parents=True, exist_ok=True)
    for sub in ("metrics", "formats", "datasets", "tools", "paper"):
        d = bio / sub
        d.mkdir(parents=True, exist_ok=True)
        if sub == "paper":
            gitkeep = d / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.write_text("", encoding="utf-8")

    # 根 README / INDEX
    tpl_dir = KIT_ROOT / "templates"
    for tpl_name, out_name in [("README.md.tpl", "README.md"), ("INDEX.md.tpl", "INDEX.md")]:
        out = target / out_name
        if _write_if_missing(out, _render_template(tpl_dir / tpl_name, ctx)):
            created.append(str(out.relative_to(target)))

    # meta 软链接式副本（模板参考，standalone 不依赖仓库 meta/）
    meta = target / "meta"
    meta.mkdir(exist_ok=True)
    for tpl in ("model.md.tpl", "tool.md.tpl", "metric.md.tpl", "format.md.tpl", "dataset.md.tpl"):
        src = tpl_dir / tpl
        dst = meta / tpl.replace(".tpl", ".template.md")
        if _write_if_missing(dst, src.read_text(encoding="utf-8")):
            created.append(str(dst.relative_to(target)))

    # seeds
    if with_seeds:
        for kind in ("formats", "metrics", "datasets"):
            seed_src = KIT_ROOT / "seeds" / kind
            if seed_src.exists():
                for f in seed_src.glob("*.md"):
                    dst = bio / kind / f.name
                    if _write_if_missing(dst, f.read_text(encoding="utf-8")):
                        created.append(str(dst.relative_to(target)))

    # 图谱（可选）
    graph_deployed = False
    if with_graph:
        graph_dst = target / "Graph_Database"
        graph_src = KIT_ROOT / "graph"
        _copy_tree(graph_src, graph_dst)

        # mappings 从 kit 复制（覆盖 graph 内空 mappings）
        mappings_dst = graph_dst / "mappings"
        mappings_dst.mkdir(parents=True, exist_ok=True)
        for f in (KIT_ROOT / "mappings").glob("*.yaml"):
            shutil.copy2(f, mappings_dst / f.name)

        # .env.example
        env_example = graph_dst / ".env.example"
        if not env_example.exists():
            env_example.write_text(
                f"NEO4J_AUTH=neo4j/graphdb-dev-password\n"
                f"NEO4J_PASSWORD=graphdb-dev-password\n"
                f"NEO4J_HTTP_PORT=7474\n"
                f"NEO4J_BOLT_PORT=7687\n"
                f"RAWDATA_DIR=../{rawdata_dir}\n"
                f"# 兼容旧变量名\n"
                f"BIOINFORMATICS_DIR=../{rawdata_dir}\n",
                encoding="utf-8",
            )
            created.append(str(env_example.relative_to(target)))

        graph_deployed = True

    # kit 规则副本（standalone 不依赖 Graph_Database/doc/）
    rules_dst = target / ".kbase" / "rules"
    rules_dst.mkdir(parents=True, exist_ok=True)
    rules_src = KIT_ROOT / "rules" / "relationship-rules.md"
    if rules_src.exists():
        shutil.copy2(rules_src, rules_dst / "relationship-rules.md")

    # 复制 search 脚本
    search_src = KIT_ROOT / "search.py"
    if search_src.exists():
        search_dst = target / ".kbase" / "search.py"
        shutil.copy2(search_src, search_dst)
        created.append(str(search_dst.relative_to(target)))

    manifest = {
        "version": "1.0",
        "mode": "standalone",
        "name": name,
        "created": TODAY,
        "root": str(target),
        "rawdata_dir": rawdata_dir,
        "bioinformatics_dir": rawdata_dir,
        "graph_enabled": graph_deployed,
        "graph_dir": "Graph_Database" if graph_deployed else None,
        "kit_version": "1.0",
        "paths": {
            "templates": "meta/*.template.md",
            "paper_pdfs": f"{rawdata_dir}/paper",
            "mappings": "Graph_Database/mappings" if graph_deployed else "kit/mappings",
            "rules": ".kbase/rules/relationship-rules.md",
            "search": ".kbase/search.py",
        },
        "created_files": created,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✓ 知识库已初始化: {target}")
    print(f"  模式: standalone | 图谱: {'是' if graph_deployed else '否'}")
    print(f"  新建文件: {len(created)}")
    if graph_deployed:
        print("\n图谱快速开始:")
        print(f"  cd {target / 'Graph_Database'}")
        print("  cp .env.example .env")
        print("  pip install -r docker/etl/requirements.txt")
        print("  make up && make etl-local")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 model-intake 用户工作区（非 Skill 目录）")
    parser.add_argument("target", type=Path, nargs="?", help="目标目录；省略时从 workspace.yaml 读取")
    parser.add_argument("--name", default="", help="知识库名称（默认用目录名）")
    parser.add_argument("--with-graph", action="store_true", help="部署 Graph_Database（Neo4j ETL）")
    parser.add_argument("--no-seeds", action="store_true", help="不复制 starter seeds")
    parser.add_argument("--force", action="store_true", help="允许在已初始化目录补充缺失项")
    args = parser.parse_args()

    if args.target is None:
        sys.path.insert(0, str(KIT_ROOT))
        from workspace import load_workspace_config, resolve_paths  # noqa: WPS433

        cfg = load_workspace_config()
        if not cfg:
            print("错误: 未指定 target 且 workspace.yaml 不存在", file=sys.stderr)
            print("请先: python kit/workspace.py init --root <路径>", file=sys.stderr)
            return 1
        target = resolve_paths(cfg).root
        paths = resolve_paths(cfg)
        with_graph = paths.with_graph
        rawdata_dir = paths.rawdata_rel
    else:
        target = args.target
        with_graph = args.with_graph
        rawdata_dir = "rawdata"
        sys.path.insert(0, str(KIT_ROOT))
        try:
            from workspace import load_workspace_config, get_rawdata_rel  # noqa: WPS433
            cfg = load_workspace_config()
            if cfg:
                rawdata_dir = get_rawdata_rel(cfg["workspace"])
        except Exception:
            pass

    name = args.name or target.resolve().name
    try:
        init_kbase(
            target,
            name=name,
            with_graph=with_graph,
            rawdata_dir=rawdata_dir,
            with_seeds=not args.no_seeds,
            force=args.force,
        )
    except Exception as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
