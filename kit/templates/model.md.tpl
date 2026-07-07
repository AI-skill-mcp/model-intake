# [模型名称]

[100–300 字概述：核心功能、应用价值、典型用法、与同类模型差异]

**适用场景**：…
**行业应用**：…
**核心优势**：…
**定位**：…

> 可选：1–2 句原理/架构心智（核心思想、实现路径）。缩写首次出现按知识库体例说明。

---

## 核心标识

| 字段 | 值 |
|------|-----|
| `model_id` | `<org-modelname 小写连字符>` |
| `alias` | |
| `name` | |
| `version` | （可选） |
| `organization` | |
| `homepage` | |
| `paper` | |
| `paper_url` | https://doi.org/… |
| `paper_pdf` | （可选）`{rawdata_dir}/paper/10.xxxx-….pdf` |
| `github` | |
| `license` | MIT / Apache-2.0 / CC-BY-NC-4.0 … |

## 基本信息

| 字段 | 值 |
|------|-----|
| `release_date` | YYYY-MM |
| `last_updated` | （可选） |
| `category` | protein / enzyme / rna / genome / single-cell / multi-modal / function / interaction / ptm / expression / cellular |
| `sub_category` | structure / embedding / kcat / go_annotation / … |
| `task_coverage` | [任务1, 任务2] |

## 模型架构

| 字段 | 值 |
|------|-----|
| `architecture_type` | Transformer / CNN / GNN / 扩散模型 / … |
| `backbone` | （可选） |
| `pretrained_model` | （可选） |
| `parameter_count` | |
| `parameter_count_exact` | （可选） |
| `layer_count` | （可选） |
| `hidden_size` | （可选） |

### 分词器与预训练（可选）

| 字段 | 值 |
|------|-----|
| `tokenizer_type` | |
| `vocab_size` | |
| `pretraining_task` | MLM / 对比学习 / … |

## 输入输出规格

| 字段 | 值 |
|------|-----|
| `input_format` | FASTA / PDB / JSON …（须可被 infer_file_types 识别） |
| `output_format` | |
| `input_example` | （可选） |
| `output_example` | （可选） |
| `input_constraints` | （可选）最大长度、模态限制 |
| `context_window` | （可选） |
| `modalities` | [protein_sequence, …] |

## 能力与性能

### Benchmark

| benchmark | 分数 | 排名 | 数据集 | 来源 |
|-----------|------|------|--------|------|
| | | | | 论文 Table X |

### 准确性指标（可选）

| metric | value | domain | dataset | notes |
|--------|-------|--------|---------|-------|
| | | | | |

### 泛化能力（可选）

| 字段 | 值 |
|------|-----|
| `zero_shot` | 是 / 否 |
| `few_shot` | 是 / 否 |
| `transfer_learning` | 是 / 否 |

## 训练信息

| 字段 | 值 |
|------|-----|
| `training_data` | 映射到 datasets/ 白名单的原文表述 |
| `training_data_size` | |
| `training_compute` | （可选） |
| `preprocessing` | （可选） |

## 部署特性

| 字段 | 值 |
|------|-----|
| `quantization` | （可选）FP16 / INT8 / … |
| `gpu_memory_fp16` | |
| `gpu_memory` | （简写，与上二选一或并存） |
| `inference_speed` | |
| `cpu_inference` | （可选） |
| `dependencies` | PyTorch 版本等（可选） |

## 编程接口

| 字段 | 值 |
|------|-----|
| `api_style` | Python SDK / HuggingFace / REST / CLI |
| `python_package` | |
| `installation` | pip install … / docker … |

```python
# quick start 示例
```

## 授权与合规

| 字段 | 值 |
|------|-----|
| `license_type` | open / research_only / proprietary |
| `license_url` | |
| `commercial_use` | true / false / 有条件 |
| `research_use` | true / false |

## 相关资源

| 字段 | 值 |
|------|-----|
| `parent_model` | （可选） |
| `related_models` | [model_id1, model_id2] |
| `successor_models` | （可选） |
| `integrated_with` | [foldx, …] |
| `huggingface` | （可选） |

## 已知限制（可选）

| 字段 | 值 |
|------|-----|
| `known_limitations` | |
| `failure_cases` | |
| `out_of_scope` | |

## 引用信息

```bibtex
@article{...}
```

---

## 填写检查清单

**必填**：model_id, name, organization, release_date, category, task_coverage, input_format, output_format, architecture_type, parameter_count, license / license_type, commercial_use

**推荐**：paper_url, benchmark, gpu_memory, quick start, github, training_data

**可选**：paper_pdf, 量化、API 定价、版本历史、已知限制

*最后更新：{{date}} | 结构参考：meta/MODEL-RECORD-FULL.md*
