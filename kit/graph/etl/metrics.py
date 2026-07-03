"""
指标（Metric）归一：从 task_coverage 解析并映射到白名单指标。

输入：task_coverage 文本片段、metrics.yaml
输出：规范 metric_id 列表（仅明确指标）
"""

from __future__ import annotations

from pathlib import Path

import yaml

from etl.parser import parse_list_field


def load_metrics(mappings_dir: Path) -> tuple[dict[str, dict], dict[str, str]]:
    """
    加载 metrics.yaml。

    返回 (metrics_by_id, alias_to_id)。
    """
    path = mappings_dir / "metrics.yaml"
    if not path.exists():
        return {}, {}

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    metrics_by_id: dict[str, dict] = {}
    alias_to_id: dict[str, str] = {}

    for mid, meta in (data.get("metrics") or {}).items():
        metrics_by_id[mid] = {
            "metric_id": mid,
            "name": meta.get("label", mid),
            "unit": meta.get("unit"),
        }
        alias_to_id[mid.lower()] = mid
        alias_to_id[meta.get("label", mid).lower()] = mid
        for alias in meta.get("aliases") or []:
            alias_to_id[str(alias).strip().lower()] = mid

    return metrics_by_id, alias_to_id


def resolve_metric_id(text: str, alias_to_id: dict[str, str]) -> str | None:
    """将 task_coverage 单项文本解析为 metric_id；无法映射则返回 None。"""
    text = text.strip()
    if not text or text in ("—", "-"):
        return None
    return alias_to_id.get(text.lower())


def extract_metrics_from_task_coverage(
    task_coverage: str,
    alias_to_id: dict[str, str],
) -> list[str]:
    """
    从 task_coverage 字段提取去重后的 metric_id 列表。

    仅保留白名单内明确指标，忽略任务类描述（设计、模拟、embedding 等）。
    """
    seen: set[str] = set()
    result: list[str] = []
    for item in parse_list_field(task_coverage):
        mid = resolve_metric_id(item, alias_to_id)
        if mid and mid not in seen:
            seen.add(mid)
            result.append(mid)
    return result
