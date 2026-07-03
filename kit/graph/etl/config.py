"""
配置模块：解析路径与环境变量。

输入：环境变量 RAWDATA_DIR / BIOINFORMATICS_DIR、DATA_DIR（可选）
输出：Paths 数据类，含 rawdata（字段名 bioinformatics 保留兼容）等目录
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RAWDATA_REL = "rawdata"


@dataclass(frozen=True)
class Paths:
    """ETL 相关目录路径集合。"""

    root: Path
    bioinformatics: Path  # 实际指向 rawdata 目录，保留字段名供 ETL 代码兼容
    data: Path
    schema: Path
    mappings: Path
    overrides: Path

    @property
    def rawdata(self) -> Path:
        return self.bioinformatics

    @property
    def nodes_jsonl(self) -> Path:
        return self.data / "nodes.jsonl"

    @property
    def edges_jsonl(self) -> Path:
        return self.data / "edges.jsonl"

    @property
    def graph_export(self) -> Path:
        return self.data / "graph_export.json"

    @property
    def etl_report(self) -> Path:
        return self.data / "etl_report.json"

    @property
    def etl_state(self) -> Path:
        return self.data / ".etl_state.json"


def get_paths() -> Paths:
    """
    根据环境变量或默认布局解析路径。

    默认 rawdata 目录为 Graph_Database 同级的 ../rawdata；
    可通过 RAWDATA_DIR 或 BIOINFORMATICS_DIR（兼容）覆盖。
    """
    root = Path(os.environ.get("GRAPH_DB_ROOT", Path(__file__).resolve().parent.parent))
    bio = os.environ.get("RAWDATA_DIR") or os.environ.get("BIOINFORMATICS_DIR")
    data = os.environ.get("DATA_DIR")
    default_bio = root.parent / DEFAULT_RAWDATA_REL
    # 若 rawdata 不存在但 bioinformatics 存在（embedded monorepo），回退
    if not bio and not default_bio.is_dir():
        legacy = root.parent / "bioinformatics"
        if legacy.is_dir():
            default_bio = legacy
    return Paths(
        root=root,
        bioinformatics=Path(bio) if bio else default_bio,
        data=Path(data) if data else root / "data",
        schema=root / "schema",
        mappings=root / "mappings",
        overrides=root / "overrides",
    )
