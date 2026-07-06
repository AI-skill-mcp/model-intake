"""
实体归一：别名表、FileType、Organization 等 ID 生成。

输入：原始字段文本、aliases.yaml
输出：规范化的节点 ID 与属性
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from etl.parser import slugify

# input_format 关键词 → format_id（fallback；主数据源是 mappings/format-keywords.yaml）
_FORMAT_KEYWORDS: list[tuple[str, str]] = [
    ("fasta", "fasta"),
    ("mmcif", "mmcif"),
    ("pdbx", "mmcif"),
    (".cif", "mmcif"),
    ("pdb", "pdb"),
    ("smiles", "smiles"),
    ("sdf", "pdb"),  # 小分子构象，图谱归并为结构坐标类
    ("mol2", "pdb"),
    ("json", "json"),
    ("csv", "csv"),
    ("tsv", "csv"),
    ("xvg", "csv"),
    ("npy", "npy"),
    ("npz", "npy"),
    (".fa", "fasta"),
    ("python api", "python_api"),
    ("python sdk", "python_api"),
]


def load_format_keywords(mappings_dir: Path | None) -> list[tuple[str, str]]:
    """
    从 mappings/format-keywords.yaml 加载关键词表。

    主数据源是 yaml 文件（收录新格式时只改这里即可）。
    当 yaml 缺失或解析失败时回落到内置 _FORMAT_KEYWORDS。
    """
    if mappings_dir is not None:
        path = mappings_dir / "format-keywords.yaml"
        if path.exists():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                pairs = [
                    (str(item["keyword"]), str(item["format_id"]))
                    for item in (data.get("keywords") or [])
                    if "keyword" in item and "format_id" in item
                ]
                if pairs:
                    return pairs
            except Exception:
                pass
    return list(_FORMAT_KEYWORDS)


def load_aliases(mappings_dir: Path) -> tuple[dict[str, str], dict[str, str], dict]:
    """加载 aliases.yaml，返回 (models, tools, policy)。"""
    path = mappings_dir / "aliases.yaml"
    if not path.exists():
        return {}, {}, {"create_stub": True}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return (
        {str(k): str(v) for k, v in (data.get("models") or {}).items()},
        {str(k): str(v) for k, v in (data.get("tools") or {}).items()},
        data.get("external_policy") or {},
    )


def resolve_model_id(name: str, model_aliases: dict[str, str], known_ids: set[str]) -> str | None:
    """
    将 related_models 中的名称解析为 model_id。

    优先别名表，再 exact match known_ids，再 slugify match。
    """
    name = name.strip()
    if not name or name == "—":
        return None
    if name in model_aliases:
        return model_aliases[name]
    lower_map = {k.lower(): v for k, v in model_aliases.items()}
    if name.lower() in lower_map:
        return lower_map[name.lower()]

    slug = slugify(name)
    if slug in known_ids:
        return slug

    # 尝试去掉 org 前缀
    for kid in known_ids:
        if kid.endswith(slug) or slug.endswith(kid):
            return kid

    return slug


def infer_file_types(text: str, mappings_dir: Path | None = None) -> list[str]:
    """
    从 input_format / output_format 文本推断 FileType ID 列表。

    优先从 mappings/format-keywords.yaml 加载关键词表；
    yaml 缺失时回落到内置 _FORMAT_KEYWORDS。
    """
    if not text:
        return []
    lower = text.lower()
    keywords = load_format_keywords(mappings_dir)
    found: list[str] = []
    for keyword, fmt_id in keywords:
        if keyword in lower and fmt_id not in found:
            found.append(fmt_id)
    return found


def org_id_from_name(name: str) -> str:
    """Organization 节点 ID。"""
    return slugify(name)[:64] or "unknown-org"


def task_id_from_name(name: str) -> str:
    """Task 节点 ID。"""
    base = slugify(name)
    return f"task:{base}" if base else "task:unknown"


def category_id_from_name(name: str) -> str:
    return slugify(name) or "unknown"


def dataset_id_from_text(text: str, aliases: dict[str, str] | None = None) -> str:
    """从 training_data 文本生成 Dataset ID；优先 aliases 精确匹配。"""
    raw = text.strip()
    if not raw:
        return ""
    if aliases:
        if raw in aliases:
            return aliases[raw]
        cleaned = re.sub(r"[()（）]", " ", raw)
        first = cleaned.split("+")[0].strip()
        if first in aliases:
            return aliases[first]

    cleaned = re.sub(r"[()（）]", " ", raw)
    part = cleaned.split("+")[0].split(",")[0].strip()
    return slugify(part)[:48] or slugify(raw)[:48]


def paper_id_from_url(url: str) -> str:
    """从 paper_url 生成 paper_id。"""
    if "doi.org" in url:
        return slugify(url.split("doi.org/")[-1].split("?")[0])
    return slugify(url)[:64]


def license_id_from_name(name: str) -> str:
    return slugify(name.split("（")[0].split("(")[0].strip())[:32]


def derive_display_name(name: str, fallback: str = "") -> str:
    """
    从完整标题派生短显示名。

    规则：冒号/破折号前截断；过长无分隔符则截断加省略号。
    例: "EVOLVEpro — Rapid in silico..." → "EVOLVEpro"
    """
    name = (name or "").strip()
    if not name:
        return fallback
    separators = (":", "：", " — ", " – ", " —", "—", "–", " - ")
    for sep in separators:
        idx = name.find(sep)
        if idx > 0:
            short = name[:idx].strip()
            if short:
                return short
    if len(name) > 45:
        return name[:42].rstrip() + "..."
    return name


def is_valid_paper_url(url: str) -> bool:
    """过滤畸形 paper_url（如 'https:// (待查)'）。"""
    u = (url or "").strip()
    return u.startswith("http") and "待查" not in u and len(u) > 12
