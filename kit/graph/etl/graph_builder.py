"""
图构建：将解析后的模型条目转为节点与边。

输入：模型文件列表、aliases、overrides
输出：nodes 列表、edges 列表
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from etl.config import Paths
from etl.entity_catalog import (
    load_dataset_training_aliases,
    load_datasets_catalog,
    load_metrics_catalog,
    merge_node_props,
    resolve_training_dataset_ids,
)
from etl.metrics import extract_metrics_from_task_coverage, load_metrics
from etl.normalize import (
    category_id_from_name,
    dataset_id_from_text,
    derive_display_name,
    infer_file_types,
    is_valid_paper_url,
    license_id_from_name,
    load_aliases,
    paper_id_from_url,
    resolve_model_id,
)
from etl.parser import (
    discover_model_files,
    discover_tool_files,
    extract_summary,
    file_content_hash,
    normalize_url_field,
    parse_list_field,
    parse_markdown_fields,
)

RESOURCE_KEYS = [
    "github",
    "huggingface",
    "zenodo",
    "homepage",
    "docker",
    "colab",
    "python_package",
    "modelscope",
    "papers_with_code",
    "api_endpoint",
    "weights",
]

RELATION_LIST_FIELDS = {
    "related_models": "RELATED_TO",
    "alternative_models": "ALTERNATIVE_TO",
    "successor_models": "SUCCESSOR_OF",
    "integrated_with": "INTEGRATES",
}

SINGLE_MODEL_FIELDS = {
    "pretrained_model": "BASED_ON",
    "parent_model": "BASED_ON",
}


def _node_key(node_type: str, node_id: str) -> str:
    return f"{node_type}:{node_id}"


def _add_node(nodes: dict[str, dict], node: dict) -> None:
    ntype = node["node_type"]
    if ntype == "Model":
        nid = node["model_id"]
    elif ntype == "Tool":
        nid = node["tool_id"]
    elif ntype == "Category":
        nid = node["category_id"]
    elif ntype == "Metric":
        nid = node["metric_id"]
    elif ntype == "FileType":
        nid = node["format_id"]
    elif ntype == "Organization":
        nid = node["org_id"]
    elif ntype == "Paper":
        nid = node["paper_id"]
    elif ntype == "Dataset":
        nid = node["dataset_id"]
    elif ntype == "License":
        nid = node["license_id"]
    elif ntype == "Modality":
        nid = node["modality_id"]
    elif ntype == "Framework":
        nid = node["framework_id"]
    else:
        nid = node.get("id", "unknown")
    nodes[_node_key(ntype, nid)] = node


def _add_edge(edges: list[dict], edge_type: str, from_type: str, from_id: str,
              to_type: str, to_id: str, properties: dict | None = None) -> None:
    edges.append({
        "type": edge_type,
        "from": {"node_type": from_type, "id": from_id},
        "to": {"node_type": to_type, "id": to_id},
        "properties": properties or {},
    })


def load_overrides(overrides_dir: Path) -> dict[str, dict]:
    """加载 overrides/{model_id}.yaml。"""
    result: dict[str, dict] = {}
    if not overrides_dir.exists():
        return result
    for path in overrides_dir.glob("*.yaml"):
        if path.name.startswith("."):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if data and "model_id" in data:
            result[data["model_id"]] = data
    return result


def _attach_file_io_edges(
    edges: list[dict],
    nodes: dict[str, dict],
    entity_type: str,
    entity_id: str,
    fields: dict[str, str],
) -> None:
    """为 Model / Tool 节点建立 ACCEPTS / PRODUCES 边。"""
    for fmt in infer_file_types(fields.get("input_format", "")):
        _add_node(nodes, {
            "node_type": "FileType",
            "format_id": fmt,
            "name": fmt.upper(),
        })
        _add_edge(edges, "ACCEPTS", entity_type, entity_id, "FileType", fmt, {"required": True})

    for fmt in infer_file_types(fields.get("output_format", "")):
        _add_node(nodes, {
            "node_type": "FileType",
            "format_id": fmt,
            "name": fmt.upper(),
        })
        _add_edge(edges, "PRODUCES", entity_type, entity_id, "FileType", fmt)


def build_graph(paths: Paths) -> tuple[dict[str, dict], list[dict], dict[str, str], list[dict]]:
    """
    构建完整图。

    返回 (nodes_by_key, edges, file_hashes, warnings)
    """
    model_aliases, tool_aliases, external_policy = load_aliases(paths.mappings)
    metrics_by_id, metric_aliases = load_metrics(paths.mappings)
    metrics_catalog = load_metrics_catalog(paths.bioinformatics)
    datasets_catalog = load_datasets_catalog(paths.bioinformatics)
    training_ds_aliases = load_dataset_training_aliases(paths.mappings)
    overrides = load_overrides(paths.overrides)
    md_files = discover_model_files(paths.bioinformatics)

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    warnings: list[dict] = []
    file_hashes: dict[str, str] = {}

    # 第一遍：收集所有 model_id
    known_model_ids: set[str] = set()
    parsed_entries: list[tuple[Path, dict[str, str], str]] = []

    for md_path in md_files:
        rel = str(md_path.relative_to(paths.bioinformatics.parent))
        content = md_path.read_text(encoding="utf-8")
        file_hashes[rel] = file_content_hash(md_path)
        fields = parse_markdown_fields(content)
        model_id = fields.get("model_id", "").strip()
        if not model_id:
            warnings.append({
                "file": rel,
                "field": "model_id",
                "message": "缺失 model_id，跳过",
            })
            continue
        known_model_ids.add(model_id)
        parsed_entries.append((md_path, fields, content))

    for md_path, fields, content in parsed_entries:
        rel = str(md_path.relative_to(paths.bioinformatics.parent))
        model_id = fields["model_id"].strip()
        override = overrides.get(model_id, {})

        summary = override.get("summary") or extract_summary(content)
        if not summary:
            summary = fields.get("name", model_id)

        online_resources: dict[str, str | None] = {}
        online_resources_meta: dict[str, dict] = {}

        for key in RESOURCE_KEYS:
            raw = override.get("online_resources", {}).get(key) or fields.get(key)
            if raw is None:
                continue
            url, meta = normalize_url_field(key, str(raw))
            map_key = "pypi" if key == "python_package" else key
            if url:
                online_resources[map_key] = url
            if meta:
                online_resources_meta[map_key] = meta

        multimodal_raw = fields.get("multimodal", "")
        multimodal = multimodal_raw.strip() in ("是", "true", "True", "yes")

        commercial = fields.get("commercial_use", "unknown")
        if "✅" in commercial or "是" in commercial:
            commercial_use = "allowed"
        elif "❌" in commercial or "否" in commercial:
            commercial_use = "denied"
        elif "⚠️" in commercial:
            commercial_use = "restricted"
        else:
            commercial_use = "unknown"

        sub_category = fields.get("sub_category", "")
        node_subtype = "pipeline" if "pipeline" in sub_category or "binder-design" in sub_category else "downstream"
        if "embedding" in sub_category or model_id.startswith("meta-"):
            node_subtype = "foundation"

        raw_name = fields.get("name", model_id)
        org = fields.get("organization", "").strip()
        fw = fields.get("framework", "").strip()
        modalities = parse_list_field(fields.get("modalities", ""))

        model_node: dict[str, Any] = {
            "node_type": "Model",
            "model_id": model_id,
            "name": raw_name,
            "display_name": derive_display_name(raw_name, model_id),
            "alias": parse_list_field(fields.get("alias", "")),
            "summary": summary[:500],
            "version": fields.get("version"),
            "node_subtype": node_subtype,
            "release_date": fields.get("release_date"),
            "parameter_count": fields.get("parameter_count"),
            "architecture_type": fields.get("architecture_type"),
            "multimodal": multimodal,
            "commercial_use": commercial_use,
            "source_path": rel,
            "content_hash": file_hashes.get(rel),
            "online_resources": online_resources,
            "online_resources_meta": online_resources_meta,
        }
        if org:
            model_node["organization"] = org
        if fw:
            model_node["framework"] = fw
        if modalities:
            model_node["modalities"] = modalities
        _add_node(nodes, model_node)

        # Category
        cat = fields.get("category", "").strip()
        if cat:
            cid = category_id_from_name(cat)
            _add_node(nodes, {"node_type": "Category", "category_id": cid, "name": cat})
            _add_edge(edges, "BELONGS_TO", "Model", model_id, "Category", cid)

        # 指标（由 task_coverage 映射，仅白名单内明确指标）
        for metric_id in extract_metrics_from_task_coverage(
            fields.get("task_coverage", ""), metric_aliases
        ):
            meta = metrics_by_id[metric_id]
            metric_node: dict[str, Any] = {
                "node_type": "Metric",
                "metric_id": metric_id,
                "name": meta["name"],
                "unit": meta.get("unit"),
            }
            if metric_id in metrics_catalog:
                merge_node_props(metric_node, metrics_catalog[metric_id])
            _add_node(nodes, metric_node)
            _add_edge(edges, "MEASURES", "Model", model_id, "Metric", metric_id)

        # FileTypes input/output
        _attach_file_io_edges(edges, nodes, "Model", model_id, fields)

        # Paper → 嵌入 Model 属性，不创建独立 Paper 节点
        paper_title = fields.get("paper", "").strip()
        paper_url = fields.get("paper_url", "").strip()
        if paper_title or paper_url:
            valid_url = paper_url if is_valid_paper_url(paper_url) else ""
            pid = (
                paper_id_from_url(valid_url)
                if valid_url
                else slugify_paper(paper_title or model_id)
            )
            model_node["paper"] = {
                "paper_id": pid,
                "title": paper_title or pid,
                "url": valid_url or None,
            }

        # License（保留节点，图中默认隐藏）
        lic = fields.get("license", fields.get("license_type", "")).strip()
        if lic and lic not in ("—", "-"):
            lid = license_id_from_name(lic)
            _add_node(nodes, {"node_type": "License", "license_id": lid, "name": lic[:80]})
            _add_edge(edges, "HAS_LICENSE", "Model", model_id, "License", lid)

        # Training data → Dataset（仅白名单内可验证数据源）
        td = fields.get("training_data", "").strip()
        if td and td not in ("—", "-"):
            ds_ids = resolve_training_dataset_ids(td, training_ds_aliases, datasets_catalog)
            if not ds_ids:
                warnings.append({
                    "file": rel,
                    "field": "training_data",
                    "message": f"未映射到可验证数据集，已跳过: {td[:100]}",
                })
            for ds_id in ds_ids:
                ds_key = _node_key("Dataset", ds_id)
                if ds_key not in nodes:
                    cat = datasets_catalog[ds_id]
                    ds_node: dict[str, Any] = {
                        "node_type": "Dataset",
                        "dataset_id": ds_id,
                        "name": cat.get("name", ds_id),
                        "dataset_type": cat.get("dataset_type", "training"),
                    }
                    merge_node_props(ds_node, cat)
                    nodes[ds_key] = ds_node
                ds_node = nodes[ds_key]
                if org:
                    orgs: list[str] = list(ds_node.get("organizations") or [])
                    if org not in orgs:
                        orgs.append(org)
                        ds_node["organizations"] = orgs
                if modalities:
                    mods: list[str] = list(ds_node.get("modalities") or [])
                    for mod in modalities:
                        if mod not in mods:
                            mods.append(mod)
                    ds_node["modalities"] = mods
                _add_edge(edges, "TRAINED_ON", "Model", model_id, "Dataset", ds_id)

        # online_resources 已内嵌于 Model 节点，不再生成 Repository / HOSTED_AT

        # Model-Model relations
        for field, edge_type in RELATION_LIST_FIELDS.items():
            for target_name in parse_list_field(fields.get(field, "")):
                target_id = resolve_model_id(target_name, model_aliases, known_model_ids)
                if not target_id:
                    continue
                if target_id not in known_model_ids:
                    if external_policy.get("create_stub", True):
                        stub = {
                            "node_type": "Model",
                            "model_id": target_id,
                            "name": target_name,
                            "summary": f"外部引用模型（库外）: {target_name}",
                            "in_corpus": False,
                            "node_subtype": "external",
                            "source_path": None,
                        }
                        _add_node(nodes, stub)
                    else:
                        warnings.append({
                            "file": rel,
                            "field": field,
                            "message": f"无法解析: {target_name}",
                        })
                        continue
                _add_edge(edges, edge_type, "Model", model_id, "Model", target_id)

        for field, edge_type in SINGLE_MODEL_FIELDS.items():
            raw = fields.get(field, "").strip()
            if not raw:
                continue
            target_id = resolve_model_id(raw.split("+")[0].strip(), model_aliases, known_model_ids)
            if target_id:
                if target_id not in known_model_ids and external_policy.get("create_stub", True):
                    _add_node(nodes, {
                        "node_type": "Model",
                        "model_id": target_id,
                        "name": raw,
                        "summary": f"外部引用: {raw}",
                        "in_corpus": False,
                        "node_subtype": "external",
                        "source_path": None,
                    })
                _add_edge(edges, edge_type, "Model", model_id, "Model", target_id)

        # Override edges
        for edge_def in override.get("edges", []):
            _add_edge(
                edges,
                edge_def["type"],
                "Model",
                model_id,
                edge_def["to"]["node_type"],
                edge_def["to"]["id"],
                edge_def.get("properties"),
            )

    # Tool 词条（bioinformatics/tools/*.md）
    for tool_path in discover_tool_files(paths.bioinformatics):
        rel = str(tool_path.relative_to(paths.bioinformatics.parent))
        content = tool_path.read_text(encoding="utf-8")
        file_hashes[rel] = file_content_hash(tool_path)
        fields = parse_markdown_fields(content)
        tool_id = fields.get("tool_id", "").strip()
        if not tool_id:
            warnings.append({
                "file": rel,
                "field": "tool_id",
                "message": "缺失 tool_id，跳过",
            })
            continue

        summary = extract_summary(content, max_length=300)
        if not summary:
            summary = fields.get("description", "").strip() or fields.get("name", tool_id)

        online_resources: dict[str, Any] = {}
        online_resources_meta: dict[str, Any] = {}
        for key in RESOURCE_KEYS:
            raw = fields.get(key, "").strip()
            url, meta = normalize_url_field(key, raw)
            if url:
                online_resources[key] = url
            if meta:
                online_resources_meta[key] = meta

        tool_node: dict[str, Any] = {
            "node_type": "Tool",
            "tool_id": tool_id,
            "name": fields.get("name", tool_id).strip(),
            "summary": summary,
            "tool_type": fields.get("tool_type", "utility").strip(),
            "source_path": rel,
            "online_resources": online_resources,
            "online_resources_meta": online_resources_meta,
        }
        if fields.get("alias"):
            tool_node["alias"] = fields["alias"].strip()
        if fields.get("license"):
            tool_node["license"] = fields["license"].strip()
        _add_node(nodes, tool_node)

        _attach_file_io_edges(edges, nodes, "Tool", tool_id, fields)

        for metric_id in extract_metrics_from_task_coverage(
            fields.get("task_coverage", ""), metric_aliases
        ):
            meta = metrics_by_id[metric_id]
            metric_node: dict[str, Any] = {
                "node_type": "Metric",
                "metric_id": metric_id,
                "name": meta["name"],
                "unit": meta.get("unit"),
            }
            if metric_id in metrics_catalog:
                merge_node_props(metric_node, metrics_catalog[metric_id])
            _add_node(nodes, metric_node)
            _add_edge(edges, "MEASURES", "Tool", tool_id, "Metric", metric_id)

        for model_name in parse_list_field(fields.get("used_by_models", "")):
            mid = resolve_model_id(model_name, model_aliases, known_model_ids)
            if mid and mid in known_model_ids:
                _add_edge(edges, "REQUIRES", "Model", mid, "Tool", tool_id)

    # 合并实体百科：补全未在模型流中出现的 Metric / Dataset 词条
    for mid, cat in metrics_catalog.items():
        key = _node_key("Metric", mid)
        if key not in nodes:
            nodes[key] = {"node_type": "Metric", **cat}
        else:
            merge_node_props(nodes[key], cat)

    for ds_id, cat in datasets_catalog.items():
        key = _node_key("Dataset", ds_id)
        if key not in nodes:
            nodes[key] = {"node_type": "Dataset", **cat}
        else:
            merge_node_props(nodes[key], cat)

    return nodes, edges, file_hashes, warnings


def slugify_paper(title: str) -> str:
    import re
    s = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    return s[:64] or "paper-unknown"
