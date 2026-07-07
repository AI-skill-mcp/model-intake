"""
Markdown 解析：从模型条目中抽取表格字段与概述。

输入：Markdown 文件路径与文本
输出：字段字典、概述 summary、章节映射
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path


# 匹配 | `field` | value | 形式的表格行
_FIELD_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*(.+?)\s*\|")
_LIST_IN_BRACKETS = re.compile(r"\[([^\]]+)\]")
_PLACEHOLDER_PATTERNS = [
    re.compile(r"^需确认$"),
    re.compile(r"^需搜索"),
    re.compile(r"^搜索\s"),
    re.compile(r"^✅"),
]


def file_content_hash(path: Path) -> str:
    """计算文件内容 SHA256，用于增量 ETL。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strip_field_value(value: str) -> str:
    """去除表格值外层包裹的反引号（如 `prodigy` → prodigy）。"""
    val = value.strip()
    if len(val) >= 2 and val.startswith("`") and val.endswith("`") and val.count("`") == 2:
        return val[1:-1].strip()
    return val


def parse_markdown_fields(content: str) -> dict[str, str]:
    """
    解析 Markdown 中所有 `字段` | 值 表格行。

    同一字段多次出现时保留最后一次（通常基本信息表优先）。
    值若被单反引号包裹则自动剥离（避免 tool_id 等写入图谱时带 `` ` ``）。
    """
    fields: dict[str, str] = {}
    for line in content.splitlines():
        m = _FIELD_ROW.match(line.strip())
        if m:
            key, val = m.group(1).strip(), _strip_field_value(m.group(2))
            fields[key] = val
    return fields


def extract_summary(content: str, max_length: int = 500) -> str:
    """
    从概述区提取 summary：首段正文，或 **定位** 行。

    跳过标题与元数据行。
    """
    lines = content.splitlines()
    # 跳过 # 标题
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# ") and not line.startswith("##"):
            start = i + 1
            break

    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("**定位**：") or stripped.startswith("**定位**:"):
            text = re.sub(r"^\*\*定位\*\*[：:]\s*", "", stripped)
            return text[:max_length]
        if stripped.startswith("---") or stripped.startswith("##"):
            continue
        if stripped.startswith("**") and "：" in stripped:
            continue
        if len(stripped) > 40 and not stripped.startswith("|"):
            return stripped[:max_length]

    return ""


def parse_list_field(value: str) -> list[str]:
    """
    解析 [a, b, c] 或逗号/顿号分隔列表。

    支持分隔符：英文逗号 `,`、中文逗号 `，`、顿号 `、`。
    """
    if not value or value in ("—", "-", "null", "None"):
        return []
    m = _LIST_IN_BRACKETS.search(value)
    if m:
        inner = m.group(1)
    else:
        inner = value
    parts = re.split(r"[,，、]", inner)
    return [_strip_field_value(p.strip().strip("'\"")) for p in parts if p.strip()]


def is_placeholder_url(value: str) -> bool:
    """判断 URL 字段是否为占位符文本。"""
    if not value:
        return True
    for pat in _PLACEHOLDER_PATTERNS:
        if pat.search(value.strip()):
            return True
    return False


def normalize_url_field(key: str, value: str) -> tuple[str | None, dict | None]:
    """
    归一化在线资源 URL。

    返回 (url 或 None, meta 字典或 None)
    """
    if not value or value in ("—", "-"):
        return None, None
    if is_placeholder_url(value):
        status = "placeholder"
        if value.startswith("✅"):
            status = "unverified"
        return None, {"status": status, "raw_text": value}
    if key == "python_package" and not value.startswith("http"):
        return value, None
    if value.startswith("http") or "github.com" in value or "doi.org" in value:
        return value, {"status": "verified"}
    return value, {"status": "unverified", "raw_text": value}


def slugify(name: str) -> str:
    """将显示名转为 candidate model_id。"""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def discover_tool_files(bio_dir: Path) -> list[Path]:
    """扫描 bioinformatics/tools 下工具词条 md（排除 README）。"""
    tools_dir = bio_dir / "tools"
    if not tools_dir.is_dir():
        return []
    return [
        p for p in sorted(tools_dir.glob("*.md"))
        if p.name.upper() != "README.MD"
    ]


def discover_model_files(bio_dir: Path) -> list[Path]:
    """扫描 bioinformatics/model 下模型条目 md（排除 README、实体目录与汇总）。"""
    model_dir = bio_dir / "model"
    scan_root = model_dir if model_dir.is_dir() else bio_dir
    files: list[Path] = []
    for path in sorted(scan_root.rglob("*.md")):
        name = path.name.upper()
        if name == "README.MD":
            continue
        if "SUMMARY" in name:
            continue
        # 调研报告等非模型卡片
        head = path.read_text(encoding="utf-8")[:800]
        if "类型：调研报告" in head or "类型: 调研报告" in head:
            continue
        files.append(path)
    return files
