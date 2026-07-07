# [工具名称]

[80–200 字概述：工具功能、在流水线中的位置、与同类工具差异]

**适用场景**：…
**类型**：predictor / annotator / converter / pipeline / …

> 可选：方法一句话（算法/力场/ML 框架）。

---

## 核心标识

| 字段 | 值 |
|------|-----|
| `tool_id` | `<小写连字符>` |
| `name` | |
| `alias` | （可选） |
| `tool_type` | predictor / annotator / converter / pipeline |
| `organization` | |
| `homepage` | |
| `paper` | （可选） |
| `paper_url` | https://doi.org/… |
| `paper_pdf` | （可选）`{rawdata_dir}/paper/….pdf` |
| `github` | （可选；无独立论文时可留空） |
| `license` | |

## 核心方法

| 字段 | 值 |
|------|-----|
| `method` | |
| `algorithm` | （可选） |
| `key_reference` | 作者, 期刊, 年份 |

## 输入输出规格

| 字段 | 值 |
|------|-----|
| `input_format` | PDB / FASTA / …（须可被 infer_file_types 识别） |
| `output_format` | JSON / PDB / CSV / … |
| `input_constraints` | （可选） |
| `task_coverage` | [ΔΔGbind预测, …] |

## 关系

| 字段 | 值 |
|------|-----|
| `used_by_models` | [model_id1] |
| `used_by_tools` | （可选）[tool_id1] |
| `requires_tools` | （可选）[foldx] |
| `integrated_with` | （可选） |

## 编程接口（可选）

| 字段 | 值 |
|------|-----|
| `api_style` | Web 服务 / CLI / Python |
| `installation` | |

```bash
# 使用示例
```

## 授权与合规

| 字段 | 值 |
|------|-----|
| `license_type` | open / research_only / proprietary |
| `license_url` | （可选） |
| `commercial_use` | true / false / ⚠️ 见站点条款 |
| `research_use` | true / false |

## 引用信息（可选）

```bibtex
@article{...}
```

---

## 填写检查清单

**必填**：tool_id, name, tool_type, organization, input_format, output_format, task_coverage, license

**推荐**：paper_url, homepage, method, used_by_models / requires_tools

**可选**：paper_pdf, github, key_reference

*最后更新：{{date}} | 结构参考：meta/MODEL-RECORD-FULL.md（Tool 子集）*
