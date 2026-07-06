"""
ETL 主入口：解析原始数据目录 → 写出 data/。

原始数据目录来自 workspace.yaml 的 rawdata_dir 配置：
- embedded monorepo: bioinformatics/
- standalone: rawdata/

用法: python -m etl.run
"""

from __future__ import annotations

import json
import sys

from etl.config import get_paths
from etl.export import export_all
from etl.graph_builder import build_graph
from etl.validate import validate


def main() -> int:
    """执行全量 ETL 并输出报告。"""
    paths = get_paths()
    paths.data.mkdir(parents=True, exist_ok=True)

    if not paths.bioinformatics.exists():
        print(f"错误: 原始数据目录不存在: {paths.bioinformatics}（workspace.yaml 中 {{{{rawdata_dir}}}} 配置）", file=sys.stderr)
        return 1

    print(f"扫描: {paths.bioinformatics}")
    nodes, edges, file_hashes, parse_warnings = build_graph(paths)
    report = validate(nodes, edges, parse_warnings)

    export_all(paths.data, nodes, edges, file_hashes)
    paths.etl_report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    stats = report["stats"]
    print(f"完成: {stats['models']} 模型, {stats['nodes']} 节点, {stats['edges']} 边")
    print(f"警告: {len(report['warnings'])}, 错误: {len(report['errors'])}")
    print(f"输出: {paths.nodes_jsonl}")
    print(f"报告: {paths.etl_report}")

    return 1 if not report["ok"] else 0


if __name__ == "__main__":
    sys.exit(main())
