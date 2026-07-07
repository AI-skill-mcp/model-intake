# [数据集名称]

[100–250 字：数据从哪里来、包含什么、适合训练还是评测、哪些模型用过]

**类型**：training / benchmark / reference / annotation
**规模**：…
**许可**：…

---

## 核心标识

| 字段 | 值 |
|------|-----|
| `dataset_id` | `<小写连字符，与 datasets.yaml 一致>` |
| `name` | |
| `dataset_type` | training / benchmark / reference |
| `version` | （可选） |
| `release_date` | YYYY-MM（可选） |

## 范围与规模

| 字段 | 值 |
|------|-----|
| `description` | 内容与构建方式 |
| `scope` | （可选）边界说明 |
| `size_description` | ~N 条 / N GB |
| `sample_count` | （可选，可核实数量） |
| `modalities` | [protein_sequence, small_molecule, …] |
| `organizations` | （可选）维护方 |

## 组成与划分（可选）

| 字段 | 值 |
|------|-----|
| `composition` | 每条记录典型字段 |
| `splits` | train/val/test 划分 |
| `preprocessing` | 去冗余、单位统一等 |
| `label_quality` | 实验 vs 文献挖掘 |

## 获取与许可

| 字段 | 值 |
|------|-----|
| `url` | https://…（**必填，须可访问**） |
| `paper_doi` | 10.xxxx/…（**必填，须可解析**） |
| `license_note` | |
| `access_restrictions` | （可选） |
| `download_size` | （可选） |

## 关联关系

| 字段 | 值 |
|------|-----|
| `related_datasets` | [brenda, sabio-rk, …] |
| `models_trained_on` | [model_id1] |
| `used_in_benchmarks` | （可选） |
| `related_metrics` | [kcat, km, …] |

## 质量与引用

| 字段 | 说明 |
|------|------|
| `known_issues` | 泄漏、偏倚、缺失字段 |
| `citations` | BibTeX 或 DOI |

## 验证说明

- `url`：YYYY-MM-DD 访问正常
- `paper_doi`：DOI 对应官方文献，描述与该数据集一致
- 规模：与官网/论文一致

---

## 填写检查清单

**必填**：dataset_id, name, dataset_type, description, url, paper_doi

**推荐**：size_description, license_note, composition, models_trained_on

**可选**：splits, preprocessing, known_issues, citations

*最后更新：{{date}} | 结构参考：meta/DATASET-RECORD-FULL.md*
