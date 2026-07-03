"""
ETL 结果校验。

输入：nodes、edges、warnings
输出：errors、warnings、stats
"""

from __future__ import annotations

from typing import Any


def validate(nodes: dict[str, dict], edges: list[dict],
             parse_warnings: list[dict]) -> dict[str, Any]:
    """
    校验图数据质量。

    返回 etl_report 结构。
    """
    errors: list[dict] = []
    warnings: list[dict] = list(parse_warnings)

    models = [n for n in nodes.values() if n.get("node_type") == "Model" and n.get("in_corpus", True) is not False]
    tools = [n for n in nodes.values() if n.get("node_type") == "Tool"]

    for m in models:
        mid = m["model_id"]
        if not m.get("summary"):
            errors.append({"model_id": mid, "field": "summary", "message": "summary 为空"})
        if not m.get("source_path"):
            warnings.append({"model_id": mid, "field": "source_path", "message": "无 source_path"})

        has_measures = any(
            e["type"] == "MEASURES" and e["from"]["id"] == mid for e in edges
        )
        has_accepts = any(
            e["type"] == "ACCEPTS" and e["from"]["id"] == mid for e in edges
        )
        if not has_measures:
            warnings.append({"model_id": mid, "field": "task_coverage", "message": "无明确指标（MEASURES）"})
        if not has_accepts:
            warnings.append({"model_id": mid, "field": "input_format", "message": "无 ACCEPTS 边"})

    for t in tools:
        tid = t["tool_id"]
        if not t.get("summary"):
            warnings.append({"tool_id": tid, "field": "summary", "message": "summary 为空"})
        has_accepts = any(
            e["type"] == "ACCEPTS" and e["from"]["id"] == tid for e in edges
        )
        has_produces = any(
            e["type"] == "PRODUCES" and e["from"]["id"] == tid for e in edges
        )
        if not has_accepts:
            warnings.append({"tool_id": tid, "field": "input_format", "message": "无 ACCEPTS 边"})
        if not has_produces:
            warnings.append({"tool_id": tid, "field": "output_format", "message": "无 PRODUCES 边"})

    stats = {
        "models": len(models),
        "models_external": sum(1 for n in nodes.values() if n.get("node_type") == "Model" and n.get("in_corpus") is False),
        "tools": len(tools),
        "nodes": len(nodes),
        "edges": len(edges),
    }

    return {
        "errors": errors,
        "warnings": warnings,
        "stats": stats,
        "ok": len(errors) == 0,
    }
