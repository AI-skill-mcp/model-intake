"""
实体百科加载：从 bioinformatics/metrics 与 bioinformatics/datasets 读取词条。

输入：bioinformatics 根目录
输出：metric_id / dataset_id → 节点属性字典（供 graph_builder 合并）
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from etl.normalize import dataset_id_from_text
from etl.parser import extract_summary, parse_list_field, parse_markdown_fields


def _parse_bool(value: str | None) -> bool | None:
    if value is None or value in ("—", "-", "", "null"):
        return None
    lower = value.strip().lower()
    if lower in ("true", "是", "yes"):
        return True
    if lower in ("false", "否", "no"):
        return False
    return None


def _metric_node(fields: dict[str, str], content: str, stem: str) -> dict:
    """将指标 Markdown 表格字段转为 Metric 节点属性。"""
    metric_id = fields.get("metric_id", stem).strip()
    description = fields.get("definition", "").strip()
    if not description:
        description = extract_summary(content, max_length=400)

    node: dict = {
        "metric_id": metric_id,
        "name": fields.get("name", fields.get("label", metric_id)).strip(),
    }
    if fields.get("unit"):
        node["unit"] = fields["unit"].strip()
    if description:
        node["description"] = description
    if fields.get("quantity_kind"):
        node["quantity_kind"] = fields["quantity_kind"].strip()
    domains = parse_list_field(fields.get("domains", ""))
    if domains:
        node["domains"] = domains
    if fields.get("typical_range"):
        node["typical_range"] = fields["typical_range"].strip()
    hib = _parse_bool(fields.get("higher_is_better"))
    if hib is not None:
        node["higher_is_better"] = hib
    if fields.get("source_path"):
        node["source_path"] = fields["source_path"].strip()
    return node


def _dataset_node(fields: dict[str, str], content: str, stem: str) -> dict:
    """将数据集 Markdown 表格字段转为 Dataset 节点属性。"""
    dataset_id = fields.get("dataset_id", stem).strip() or stem
    description = fields.get("description", "").strip()
    if not description:
        description = extract_summary(content, max_length=500)

    node: dict = {
        "dataset_id": dataset_id,
        "name": fields.get("name", dataset_id).strip(),
        "dataset_type": fields.get("dataset_type", "training").strip() or "training",
    }
    if description:
        node["description"] = description
    for key in ("size_description", "scope", "url", "paper_doi", "license_note", "release_date", "version", "composition", "splits", "preprocessing"):
        if fields.get(key) and fields[key].strip() not in ("—", "-", ""):
            node[key] = fields[key].strip()
    orgs = parse_list_field(fields.get("organizations", ""))
    if orgs:
        node["organizations"] = orgs
    mods = parse_list_field(fields.get("modalities", ""))
    if mods:
        node["modalities"] = mods
    if fields.get("source_path"):
        node["source_path"] = fields["source_path"].strip()
    return node


def load_metrics_catalog(bio_dir: Path) -> dict[str, dict]:
    """
    加载 metrics/*.md。

    返回 metric_id → 节点属性（不含 node_type）。
    """
    metrics_dir = bio_dir / "metrics"
    if not metrics_dir.is_dir():
        return {}

    catalog: dict[str, dict] = {}
    for path in sorted(metrics_dir.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        content = path.read_text(encoding="utf-8")
        fields = parse_markdown_fields(content)
        node = _metric_node(fields, content, path.stem)
        rel = str(path.relative_to(bio_dir.parent))
        node["source_path"] = rel
        catalog[node["metric_id"]] = node
    return catalog


def load_datasets_catalog(bio_dir: Path) -> dict[str, dict]:
    """
    加载 datasets/*.md（须含可验证 url 或 paper_doi）。

    返回 dataset_id → 节点属性（不含 node_type）。
    """
    datasets_dir = bio_dir / "datasets"
    if not datasets_dir.is_dir():
        return {}

    catalog: dict[str, dict] = {}
    for path in sorted(datasets_dir.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        content = path.read_text(encoding="utf-8")
        fields = parse_markdown_fields(content)
        url = (fields.get("url") or "").strip()
        doi = (fields.get("paper_doi") or "").strip()
        if (not url or url in ("—", "-")) and (not doi or doi in ("—", "-")):
            continue
        node = _dataset_node(fields, content, path.stem)
        rel = str(path.relative_to(bio_dir.parent))
        node["source_path"] = rel
        catalog[node["dataset_id"]] = node
    return catalog


def resolve_training_dataset_ids(
    text: str,
    aliases: dict[str, str],
    catalog: dict[str, dict],
) -> list[str]:
    """
    从 training_data 文本解析可验证 dataset_id 列表。

    多来源用「+」拆分；单条描述优先整句别名匹配。
    """
    raw = text.strip()
    if not raw or raw in ("—", "-"):
        return []

    whole_id = dataset_id_from_text(raw, aliases)
    if whole_id and whole_id in catalog:
        return [whole_id]

    parts = [p.strip() for p in re.split(r"\s*\+\s*", raw) if p.strip()]
    if len(parts) <= 1:
        return []

    seen: list[str] = []
    for part in parts:
        ds_id = dataset_id_from_text(part, aliases)
        if ds_id and ds_id in catalog and ds_id not in seen:
            seen.append(ds_id)
    return seen


def load_dataset_training_aliases(mappings_dir: Path) -> dict[str, str]:
    """
    加载 training_data 原文 → 规范 dataset_id 映射。

    用于将模型卡片 training_data 映射到可验证数据集白名单。
    """
    path = mappings_dir / "datasets.yaml"
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return {str(k).strip(): str(v).strip() for k, v in (data.get("training_text_aliases") or {}).items()}


def merge_node_props(base: dict, overlay: dict) -> None:
    """将 overlay 中非空字段合并进 base（不覆盖已有列表的并集）。"""
    list_keys = {"organizations", "modalities", "domains"}
    for key, val in overlay.items():
        if key in ("node_type", "metric_id", "dataset_id"):
            continue
        if val is None or val == "":
            continue
        if key in list_keys and key in base and isinstance(base[key], list):
            merged = list(base[key])
            for item in val if isinstance(val, list) else [val]:
                if item not in merged:
                    merged.append(item)
            base[key] = merged
        elif key not in base or not base[key]:
            base[key] = val
