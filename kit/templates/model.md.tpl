# [模型名称]

[100–300 字概述：核心功能、适用场景、与同类模型差异]

**适用场景**：…
**行业应用**：…
**核心优势**：…
**定位**：…

---

## 基本信息

| 字段 | 值 |
|------|-----|
| `model_id` | `<小写连字符>` |
| `name` | |
| `organization` | |
| `release_date` | YYYY-MM |
| `category` | protein / enzyme / rna / … |
| `task_coverage` | [任务1, 任务2] |
| `license` | 许可证名称（如 MIT / Apache-2.0 / CC-BY-NC-4.0） |
| `paper_url` | https://doi.org/… |
| `github` | |

## 模型架构

| 字段 | 值 |
|------|-----|
| `architecture_type` | |
| `parameter_count` | |
| `pretrained_model` | （如有） |

## 输入输出规格

| 字段 | 值 |
|------|-----|
| `input_format` | FASTA / PDB / JSON …（须可被 infer_file_types 识别） |
| `output_format` | |
| `input_example` | （可选） |
| `output_example` | （可选） |

## 能力与性能

| benchmark | 分数 | 来源 |
|-----------|------|------|
| | | 论文 Table X |

## 训练数据详情

| 字段 | 值 |
|------|-----|
| `training_data` | 映射到 datasets/ 白名单的原文表述 |

## 部署特性

| 字段 | 值 |
|------|-----|
| `gpu_memory` | |
| `inference_speed` | |

## 编程接口

```bash
# quick start 命令或代码
```

## 授权与合规

| 字段 | 值 |
|------|-----|
| `license_type` | open / research_only / proprietary（按用途归类；具体协议名见上方 `license` 字段） |
| `license_url` | |
| `commercial_use` | true / false |

## 相关资源

- 论文：
- GitHub：
- HuggingFace：

## 引用信息

```bibtex
@article{...}
```

---

*最后更新：{{date}}*
