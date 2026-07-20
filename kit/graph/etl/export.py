"""
导出 JSONL 与 graph_export.json。

输入：nodes、edges
输出：写入 data/ 目录
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_jsonl(path: Path, records: list[dict]) -> None:
    """将记录列表写入 JSONL 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def build_indexes(nodes: list[dict], edges: list[dict]) -> dict[str, dict[str, list[str]]]:
    """
    构建前端筛选索引。

    返回 by_input_format, by_metric, by_metric_tool, by_metric_dataset,
    by_format_dataset, by_category, by_category_dataset 映射。
    """
    models = {n["model_id"] for n in nodes if n.get("node_type") == "Model" and n.get("in_corpus", True) is not False}
    by_input: dict[str, list[str]] = {}
    by_metric: dict[str, list[str]] = {}
    by_metric_tool: dict[str, list[str]] = {}
    by_metric_dataset: dict[str, list[str]] = {}
    by_format_dataset: dict[str, list[str]] = {}
    by_category: dict[str, list[str]] = {}
    by_category_dataset: dict[str, list[str]] = {}
    model_to_categories: dict[str, list[str]] = {}

    for e in edges:
        if e["type"] == "ACCEPTS" and e["from"]["node_type"] == "Model":
            mid = e["from"]["id"]
            fid = e["to"]["id"]
            if mid in models:
                by_input.setdefault(fid, [])
                if mid not in by_input[fid]:
                    by_input[fid].append(mid)
        elif e["type"] == "MEASURES" and e["from"]["node_type"] == "Model":
            mid = e["from"]["id"]
            metric_id = e["to"]["id"]
            if mid in models:
                by_metric.setdefault(metric_id, [])
                if mid not in by_metric[metric_id]:
                    by_metric[metric_id].append(mid)
        elif e["type"] == "MEASURES" and e["from"]["node_type"] == "Tool":
            tool_id = e["from"]["id"]
            metric_id = e["to"]["id"]
            by_metric_tool.setdefault(metric_id, [])
            if tool_id not in by_metric_tool[metric_id]:
                by_metric_tool[metric_id].append(tool_id)
        elif e["type"] == "LABELS" and e["from"]["node_type"] == "Dataset":
            ds_id = e["from"]["id"]
            metric_id = e["to"]["id"]
            by_metric_dataset.setdefault(metric_id, [])
            if ds_id not in by_metric_dataset[metric_id]:
                by_metric_dataset[metric_id].append(ds_id)
        elif e["type"] == "PROVIDES" and e["from"]["node_type"] == "Dataset":
            ds_id = e["from"]["id"]
            fid = e["to"]["id"]
            by_format_dataset.setdefault(fid, [])
            if ds_id not in by_format_dataset[fid]:
                by_format_dataset[fid].append(ds_id)
        elif e["type"] == "BELONGS_TO":
            mid = e["from"]["id"]
            cid = e["to"]["id"]
            if mid in models:
                by_category.setdefault(cid, [])
                if mid not in by_category[cid]:
                    by_category[cid].append(mid)
                model_to_categories.setdefault(mid, [])
                if cid not in model_to_categories[mid]:
                    model_to_categories[mid].append(cid)
        elif e["type"] == "TRAINED_ON" and e["from"]["node_type"] == "Model":
            mid = e["from"]["id"]
            ds_id = e["to"]["id"]
            if mid not in models:
                continue
            for cid in model_to_categories.get(mid, []):
                by_category_dataset.setdefault(cid, [])
                if ds_id not in by_category_dataset[cid]:
                    by_category_dataset[cid].append(ds_id)

    return {
        "by_input_format": by_input,
        "by_metric": by_metric,
        "by_metric_tool": by_metric_tool,
        "by_metric_dataset": by_metric_dataset,
        "by_format_dataset": by_format_dataset,
        "by_category": by_category,
        "by_category_dataset": by_category_dataset,
    }


def export_all(
    data_dir: Path,
    nodes: dict[str, dict],
    edges: list[dict],
    file_hashes: dict[str, str],
    schema_version: str = "0.1.0",
) -> None:
    """写出 nodes.jsonl、edges.jsonl、graph_export.json、.etl_state.json。"""
    data_dir.mkdir(parents=True, exist_ok=True)
    node_list = list(nodes.values())

    write_jsonl(data_dir / "nodes.jsonl", node_list)
    write_jsonl(data_dir / "edges.jsonl", edges)

    export_doc = {
        "schema_version": schema_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats": {
            "nodes": len(node_list),
            "edges": len(edges),
            "models": sum(1 for n in node_list if n.get("node_type") == "Model"),
        },
        "nodes": node_list,
        "edges": edges,
        "indexes": build_indexes(node_list, edges),
    }
    (data_dir / "graph_export.json").write_text(
        json.dumps(export_doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (data_dir / ".etl_state.json").write_text(
        json.dumps(file_hashes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
