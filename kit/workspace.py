#!/usr/bin/env python3
"""
工作区路径管理：读取/写入 Skill 目录下的 workspace.yaml。

Skill 目录仅存模板与工具；收录数据一律写入 workspace.root。

用法:
  python workspace.py show
  python workspace.py propose
  python workspace.py init --root ~/kbase-data --with-graph
  python workspace.py init --from-workspace   # 按 workspace.yaml bootstrap
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

SKILL_ROOT = Path(__file__).resolve().parent.parent
KIT_ROOT = Path(__file__).resolve().parent
WORKSPACE_YAML = SKILL_ROOT / "workspace.yaml"
WORKSPACE_EXAMPLE = SKILL_ROOT / "workspace.yaml.example"

# 知识图谱同步偏好
GRAPH_SYNC_NEVER = "never"   # 从不：默认不同步，不再询问
GRAPH_SYNC_ASK = "ask"       # 再说：每次收录询问（默认）
GRAPH_SYNC_ALWAYS = "always" # 默认：每次收录同步，不再询问
GRAPH_SYNC_PREFERENCES = (GRAPH_SYNC_NEVER, GRAPH_SYNC_ASK, GRAPH_SYNC_ALWAYS)
DEFAULT_GRAPH_SYNC_PREFERENCE = GRAPH_SYNC_ASK

# 原始数据目录（相对 workspace.root）；默认 rawdata，embedded monorepo 可配置为 bioinformatics
DEFAULT_RAWDATA_DIR = "rawdata"
LEGACY_RAWDATA_KEY = "bioinformatics_dir"  # 旧键名，仍兼容读取


def _today() -> str:
    return date.today().isoformat()


def _default_graph_sync_block() -> dict:
    """graph_sync 默认配置块。"""
    return {
        "preference": DEFAULT_GRAPH_SYNC_PREFERENCE,
        "preference_set_at": _today(),
    }


def normalize_graph_sync(config: dict) -> dict:
    """确保 config 含合法 graph_sync 块。"""
    gs = config.setdefault("graph_sync", {})
    pref = gs.get("preference", DEFAULT_GRAPH_SYNC_PREFERENCE)
    if pref not in GRAPH_SYNC_PREFERENCES:
        pref = DEFAULT_GRAPH_SYNC_PREFERENCE
    gs["preference"] = pref
    if "preference_set_at" not in gs:
        gs["preference_set_at"] = _today()
    return config


def get_graph_sync_preference(config: dict | None = None) -> str:
    """读取图谱同步偏好：never | ask | always。"""
    if config is None:
        config = load_workspace_config() or {}
    normalize_graph_sync(config)
    return config["graph_sync"]["preference"]


def set_graph_sync_preference(config: dict, preference: str) -> dict:
    """设置图谱同步偏好。preference ∈ never | ask | always。"""
    if preference not in GRAPH_SYNC_PREFERENCES:
        raise ValueError(f"非法 preference: {preference}")
    config = normalize_graph_sync(config)
    config["graph_sync"]["preference"] = preference
    config["graph_sync"]["preference_set_at"] = _today()
    return config


def resolve_intake_graph_sync(
    config: dict | None = None,
    *,
    explicit: bool | None = None,
) -> dict:
    """
    解析本次收录是否执行图谱 ETL。

    explicit: 用户指令中明确要/不要图谱；None 表示未说明。
    返回: run_etl, need_ask, ask_kind, preference
    """
    if config is None:
        config = load_workspace_config() or {}
    config = normalize_graph_sync(config)
    pref = config["graph_sync"]["preference"]

    if explicit is not None:
        return {
            "run_etl": explicit,
            "need_ask": False,
            "ask_kind": None,
            "preference": pref,
        }
    if pref == GRAPH_SYNC_NEVER:
        return {"run_etl": False, "need_ask": False, "ask_kind": None, "preference": pref}
    if pref == GRAPH_SYNC_ALWAYS:
        return {"run_etl": True, "need_ask": False, "ask_kind": None, "preference": pref}
    return {"run_etl": None, "need_ask": True, "ask_kind": "three_options", "preference": pref}


def apply_graph_sync_choice(config: dict, choice: str) -> tuple[dict, bool]:
    """
    应用用户三选一，返回 (config, 本次 run_etl)。

    never/从不 — 本次不同步，以后不再询问
    ask/再说   — 本次不同步，下次继续询问
    always/默认 — 本次同步，以后默认同步不再询问
    """
    mapping = {
        GRAPH_SYNC_NEVER: (GRAPH_SYNC_NEVER, False),
        GRAPH_SYNC_ASK: (GRAPH_SYNC_ASK, False),
        GRAPH_SYNC_ALWAYS: (GRAPH_SYNC_ALWAYS, True),
        "从不": (GRAPH_SYNC_NEVER, False),
        "再说": (GRAPH_SYNC_ASK, False),
        "默认": (GRAPH_SYNC_ALWAYS, True),
    }
    if choice not in mapping:
        raise ValueError(f"非法 choice: {choice}")
    pref, run_etl = mapping[choice]
    config = set_graph_sync_preference(config, pref)
    return config, run_etl


@dataclass(frozen=True)
class WorkspacePaths:
    """解析后的工作区绝对路径。"""

    root: Path
    rawdata: Path
    rawdata_rel: str
    graph_database: Path | None
    with_graph: bool
    mode: str
    name: str

    @property
    def bioinformatics(self) -> Path:
        """兼容旧称；与 rawdata 同路径。"""
        return self.rawdata

    @property
    def paper_dir(self) -> Path:
        """论文全文 PDF 目录：{rawdata_dir}/paper/。"""
        return self.rawdata / "paper"

    @property
    def mappings_dir(self) -> Path | None:
        if self.graph_database:
            return self.graph_database / "mappings"
        return None

    @property
    def rules_path(self) -> Path:
        return self.root / ".kbase" / "rules" / "relationship-rules.md"

    @property
    def search_script(self) -> Path:
        return self.root / ".kbase" / "search.py"


def get_rawdata_rel(ws: dict) -> str:
    """
    从 workspace 配置块读取原始数据相对目录名。

    优先 rawdata_dir；兼容旧键 bioinformatics_dir；默认 rawdata。
    """
    return ws.get("rawdata_dir") or ws.get(LEGACY_RAWDATA_KEY) or DEFAULT_RAWDATA_DIR


def _detect_embedded_root(cur: Path) -> tuple[Path, str, str] | None:
    """检测 embedded 布局，返回 (root, mode, rawdata_dir)。"""
    if (cur / "bioinformatics" / "model").is_dir():
        return cur, "embedded", "bioinformatics"
    if (cur / "rawdata" / "model").is_dir():
        return cur, "standalone", DEFAULT_RAWDATA_DIR
    parent = cur.parent
    if (parent / "bioinformatics" / "model").is_dir():
        return parent.resolve(), "embedded", "bioinformatics"
    if (parent / "rawdata" / "model").is_dir():
        return parent.resolve(), "standalone", DEFAULT_RAWDATA_DIR
    return None


def load_workspace_config() -> dict | None:
    """读取 workspace.yaml；不存在返回 None。"""
    if not WORKSPACE_YAML.exists():
        return None
    data = yaml.safe_load(WORKSPACE_YAML.read_text(encoding="utf-8")) or {}
    return data


def save_workspace_config(config: dict) -> Path:
    """
    写入 workspace.yaml 到 Skill 目录。

    输入: 完整配置 dict
    输出: 写入的文件路径
    """
    ws = config.setdefault("workspace", {})
    ws["updated_at"] = _today()
    if "created_at" not in ws:
        ws["created_at"] = _today()
    if "version" not in config:
        config["version"] = "1.0"
    normalize_graph_sync(config)

    WORKSPACE_YAML.parent.mkdir(parents=True, exist_ok=True)
    WORKSPACE_YAML.write_text(
        yaml.dump(config, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return WORKSPACE_YAML


def propose_defaults(cwd: Path | None = None) -> dict:
    """
    根据当前环境提议默认工作区路径（供用户确认）。

    规则:
    1. 当前目录含 bioinformatics/model/ → embedded，root=该目录
    2. 父目录含 bioinformatics/model/ → embedded，root=父目录
    3. 否则 → standalone，root=~/kbase-data（若在 Skill 目录内则强制用 Home，避免写入 Skill）
    """
    cur = (cwd or Path.cwd()).resolve()
    skill = SKILL_ROOT.resolve()

    detected = _detect_embedded_root(cur)
    if detected:
        root, mode, rawdata_dir = detected
    else:
        mode = "standalone"
        rawdata_dir = DEFAULT_RAWDATA_DIR
        try:
            cur.relative_to(skill)
            root = (Path.home() / "kbase-data").resolve()
        except ValueError:
            candidate = (cur / "kbase-data").resolve()
            try:
                candidate.relative_to(skill)
                root = (Path.home() / "kbase-data").resolve()
            except ValueError:
                root = candidate

    validate_not_skill_dir(root)

    graph_dir = root / "Graph_Database"
    with_graph = graph_dir.is_dir() or mode == "standalone"

    return {
        "version": "1.0",
        "workspace": {
            "name": root.name,
            "root": str(root),
            "rawdata_dir": rawdata_dir,
            "graph_database_dir": "Graph_Database",
            "with_graph": with_graph,
            "mode": mode,
            "created_at": _today(),
            "updated_at": _today(),
        },
        "graph_sync": _default_graph_sync_block(),
    }


def resolve_paths(config: dict | None = None) -> WorkspacePaths:
    """
    将 workspace 配置解析为绝对路径。

    输入: 配置 dict；None 时从 workspace.yaml 加载
    输出: WorkspacePaths
    """
    if config is None:
        config = load_workspace_config()
    if not config or "workspace" not in config:
        raise SystemExit(
            "未配置工作区：workspace.yaml 不存在。"
            "首次收录请运行: python kit/workspace.py propose"
            " 并向用户确认后 init"
        )

    ws = config["workspace"]
    root = Path(ws["root"]).expanduser().resolve()
    raw_rel = get_rawdata_rel(ws)
    graph_rel = ws.get("graph_database_dir", "Graph_Database")
    with_graph = bool(ws.get("with_graph", True))

    graph_path = (root / graph_rel).resolve() if with_graph else None

    return WorkspacePaths(
        root=root,
        rawdata=(root / raw_rel).resolve(),
        rawdata_rel=raw_rel,
        graph_database=graph_path,
        with_graph=with_graph,
        mode=str(ws.get("mode", "standalone")),
        name=str(ws.get("name", root.name)),
    )


def validate_not_skill_dir(target: Path) -> None:
    """禁止将收录数据写入 Skill 目录。"""
    target = target.resolve()
    skill = SKILL_ROOT.resolve()
    try:
        target.relative_to(skill)
        raise SystemExit(
            f"禁止将数据目录设在 Skill 内: {target}\n"
            f"请选择 Skill 外的路径，例如 ~/kbase-data"
        )
    except ValueError:
        pass


def build_config_from_args(
    root: Path,
    *,
    name: str = "",
    with_graph: bool = True,
    mode: str = "standalone",
    rawdata_dir: str = DEFAULT_RAWDATA_DIR,
    graph_database_dir: str = "Graph_Database",
) -> dict:
    """从 CLI 参数构建 workspace 配置。"""
    root = root.expanduser().resolve()
    validate_not_skill_dir(root)
    detected = _detect_embedded_root(root)
    if detected and mode == "standalone":
        _, mode, rawdata_dir = detected
    return {
        "version": "1.0",
        "workspace": {
            "name": name or root.name,
            "root": str(root),
            "rawdata_dir": rawdata_dir,
            "graph_database_dir": graph_database_dir,
            "with_graph": with_graph,
            "mode": mode,
            "created_at": _today(),
            "updated_at": _today(),
        },
        "graph_sync": _default_graph_sync_block(),
    }


def ensure_bootstrapped(paths: WorkspacePaths, *, with_seeds: bool = True, force: bool = False) -> None:
    """若工作区未初始化则调用 bootstrap。"""
    manifest = paths.root / ".kbase" / "manifest.json"
    if manifest.exists() and not force:
        return

    # 延迟导入避免循环依赖
    from bootstrap import init_kbase  # noqa: WPS433

    init_kbase(
        paths.root,
        name=paths.name,
        with_graph=paths.with_graph,
        rawdata_dir=paths.rawdata_rel,
        with_seeds=with_seeds,
        force=force,
    )


def cmd_show(_: argparse.Namespace) -> int:
    config = load_workspace_config()
    if not config:
        print("workspace.yaml: 未配置")
        print("\n建议默认路径:")
        print(yaml.dump(propose_defaults(), allow_unicode=True, default_flow_style=False))
        return 1
    paths = resolve_paths(config)
    print(yaml.dump(config, allow_unicode=True, default_flow_style=False))
    print("解析路径:")
    print(f"  root:           {paths.root}")
    print(f"  rawdata:        {paths.rawdata}  (rel={paths.rawdata_rel})")
    print(f"  paper_dir:      {paths.paper_dir}")
    print(f"  graph_database: {paths.graph_database or '(未启用)'}")
    pref = get_graph_sync_preference(config)
    labels = {GRAPH_SYNC_NEVER: "从不", GRAPH_SYNC_ASK: "再说(每次询问)", GRAPH_SYNC_ALWAYS: "默认(每次同步)"}
    print(f"  graph_sync:     {pref} ({labels.get(pref, pref)})")
    print(f"  skill_root:     {SKILL_ROOT}  ← 仅存模板，不存收录数据")
    return 0


def cmd_propose(_: argparse.Namespace) -> int:
    print(yaml.dump(propose_defaults(), allow_unicode=True, default_flow_style=False))
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    if args.from_workspace:
        config = load_workspace_config()
        if not config:
            print("错误: workspace.yaml 不存在，无法 --from-workspace", file=sys.stderr)
            return 1
    else:
        if not args.root:
            print("错误: 请指定 --root 或使用 --from-workspace", file=sys.stderr)
            return 1
        config = build_config_from_args(
            args.root,
            name=args.name or "",
            with_graph=not args.no_graph,
            mode=args.mode or "standalone",
        )
        save_workspace_config(config)

    paths = resolve_paths(config)
    ensure_bootstrapped(paths, with_seeds=not args.no_seeds, force=args.force)
    print(f"✓ 工作区已就绪: {paths.root}")
    print(f"  配置已保存: {WORKSPACE_YAML}")
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    config = load_workspace_config() or propose_defaults()
    ws = config.setdefault("workspace", {})

    if args.root:
        validate_not_skill_dir(Path(args.root))
        ws["root"] = str(Path(args.root).expanduser().resolve())
        if not args.name:
            ws["name"] = Path(args.root).name
    if args.name:
        ws["name"] = args.name
    if args.no_graph:
        ws["with_graph"] = False
    if args.mode:
        ws["mode"] = args.mode
    if args.rawdata_dir:
        ws["rawdata_dir"] = args.rawdata_dir

    save_workspace_config(config)
    paths = resolve_paths(config)
    print(f"✓ 已更新 workspace.yaml")
    print(f"  root: {paths.root}")
    return 0


def cmd_graph_sync(args: argparse.Namespace) -> int:
    config = load_workspace_config() or propose_defaults()

    if args.show:
        normalize_graph_sync(config)
        gs = config["graph_sync"]
        print(f"preference: {gs['preference']}")
        print(f"set_at:     {gs.get('preference_set_at', '—')}")
        resolved = resolve_intake_graph_sync(config, explicit=None)
        print(f"next_intake: need_ask={resolved['need_ask']} run_etl={resolved['run_etl']}")
        return 0

    if args.set:
        config = set_graph_sync_preference(config, args.set)
        save_workspace_config(config)
        print(f"✓ graph_sync.preference = {args.set}")
        return 0

    if args.resolve:
        explicit = {"yes": True, "no": False}.get(args.resolve)
        if args.resolve not in ("yes", "no"):
            print("--resolve 须为 yes 或 no", file=sys.stderr)
            return 1
        r = resolve_intake_graph_sync(config, explicit=explicit)
        print(yaml.dump(r, allow_unicode=True, default_flow_style=False))
        return 0

    if args.apply:
        config, run_etl = apply_graph_sync_choice(config, args.apply)
        save_workspace_config(config)
        print(f"✓ preference={config['graph_sync']['preference']} run_etl={run_etl}")
        return 0

    print("请指定 --show | --set | --apply | --resolve", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="model-intake 工作区配置")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_show = sub.add_parser("show", help="显示当前 workspace.yaml")
    p_show.set_defaults(func=cmd_show)

    p_prop = sub.add_parser("propose", help="输出建议默认路径")
    p_prop.set_defaults(func=cmd_propose)

    p_init = sub.add_parser("init", help="确认并初始化工作区")
    p_init.add_argument("--root", type=Path, help="知识库根目录（绝对或 ~ 路径）")
    p_init.add_argument("--name", default="", help="显示名称")
    p_init.add_argument("--mode", choices=["embedded", "standalone"], help="工作模式")
    p_init.add_argument("--with-graph", action="store_true", help="部署 Graph_Database（默认启用；与 --no-graph 冲突时以 --no-graph 为准）")
    p_init.add_argument("--no-graph", action="store_true", help="不部署 Graph_Database")
    p_init.add_argument("--no-seeds", action="store_true", help="不复制 starter seeds")
    p_init.add_argument("--force", action="store_true", help="强制补充 bootstrap")
    p_init.add_argument("--from-workspace", action="store_true", help="按已有 workspace.yaml 初始化")
    p_init.set_defaults(func=cmd_init)

    p_set = sub.add_parser("set", help="更新 workspace.yaml 中的路径")
    p_set.add_argument("--root", type=Path, help="新的知识库根目录")
    p_set.add_argument("--name", default="", help="显示名称")
    p_set.add_argument("--mode", choices=["embedded", "standalone"])
    p_set.add_argument("--no-graph", action="store_true")
    p_set.add_argument("--rawdata-dir", default="", help="原始数据相对目录名（默认 rawdata，monorepo 用 bioinformatics）")
    p_set.set_defaults(func=cmd_set)

    p_gs = sub.add_parser("graph-sync", help="知识图谱同步偏好")
    p_gs.add_argument("--show", action="store_true", help="显示当前偏好")
    p_gs.add_argument("--set", choices=list(GRAPH_SYNC_PREFERENCES), help="设置偏好 never|ask|always")
    p_gs.add_argument("--apply", help="应用三选一: never|ask|always|从不|再说|默认")
    p_gs.add_argument("--resolve", choices=["yes", "no"], help="模拟用户明确要/不要图谱")
    p_gs.set_defaults(func=cmd_graph_sync)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
