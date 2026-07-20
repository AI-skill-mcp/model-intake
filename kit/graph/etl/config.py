"""
配置模块：解析路径与环境变量。

输入：环境变量 BIOINFORMATICS_DIR、DATA_DIR（可选）
输出：Paths 数据类，含 bioinformatics、data、schema、mappings 等目录
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Paths:
    """ETL 相关目录路径集合。"""

    root: Path
    bioinformatics: Path
    data: Path
    schema: Path
    mappings: Path
    overrides: Path

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

    容器内默认 /app；本地开发默认 Graph_Database/ 目录。
    """
    root = Path(os.environ.get("GRAPH_DB_ROOT", Path(__file__).resolve().parent.parent))
    bio = os.environ.get("BIOINFORMATICS_DIR")
    data = os.environ.get("DATA_DIR")
    return Paths(
        root=root,
        bioinformatics=Path(bio) if bio else root.parent / "bioinformatics",
        data=Path(data) if data else root / "data",
        schema=root / "schema",
        mappings=root / "mappings",
        overrides=root / "overrides",
    )
