---
name: model-intake
description: >-
  在 foundation-models 知识库中收录新底层模型或工具：调研官方信息、按 meta 模板撰写条目、
  同步提取并校验训练数据集/性能指标/输入输出格式、更新索引与 ETL 映射。
  当用户说「收录」「纳入」「追加收录」「添加模型」「添加工具」「加入知识库」时使用。
---

# 模型/工具收录 (Model & Tool Intake)

将新 **Model** 或 **Tool** 纳入 `foundation-models` 知识库的标准工作流。**必须实际调研**，禁止编造 benchmark、许可证、数据集 URL 或链接。

## 触发识别

用户意图示例：
- 「收录 RNAbpFlow」
- 「纳入 ESM3 大模型」
- 「添加 bpRNA 工具」
- 「把这个模型加入知识库」

提取：**名称**（必填）、**类型**（Model / Tool，默认 Model）、**分类提示**（可选）、**特殊要求**（可选）。

## 工作流

```
进度:
- [ ] 1. 查重与定位
- [ ] 2. 信息调研
- [ ] 3. 确定路径与 ID
- [ ] 4. 撰写主条目（Model / Tool）
- [ ] 5. 关联实体同步（指标 / 格式 / 数据集）  ← 必做
- [ ] 6. 更新索引与映射
- [ ] 7. ETL 校验
- [ ] 8. 验收检查
```

### 1. 查重与定位

1. 在仓库内搜索名称 / 别名 / model_id / tool_id：
   ```bash
   rg -i "<name>" --glob "*.md"
   ```
2. 已存在 → 告知路径，询问是**更新**还是**跳过**。
3. 不存在 → 继续。

### 2. 信息调研（必做，不可跳过）

按优先级检索并交叉验证：

| 来源 | 获取内容 |
|------|----------|
| 官方 GitHub | README、LICENSE、安装/推理命令、依赖、checkpoint、data/ |
| 论文 / bioRxiv / Nature 等 | 架构、benchmark、**训练数据**、**评价指标**、发表日期 |
| HuggingFace / Model Card | 参数量、量化、API、训练数据说明 |
| 官方主页 / Zenodo | 权重下载、数据集链接 |

**调研原则**：
- 有官方数据 → 写入并标注来源（论文 Table X、GitHub README 等）
- 无法确认 → 写 `需参考官方` / `需评估`，**不要猜测数值**
- benchmark 至少 2–3 条（有则写，无则注明「论文未报告标准 benchmark」）
- 许可证必须从 LICENSE 文件或官方声明读取
- **同步记录**：`training_data`、`input_format`、`output_format`、`task_coverage` 的原文表述（供步骤 5 映射）

工具：WebSearch、WebFetch、GitHub raw README/LICENSE；必要时读已有同类条目作风格参考。

### 3. 确定路径与 ID

**ID 规则**：小写 + 连字符，与文件名一致，如 `rnabpflow`、`bprna`。

**Model 分类路由**（详见 [reference.md](reference.md)）：

| 模型类型 | 目录 |
|----------|------|
| 蛋白质结构/序列/设计 | `bioinformatics/model/protein/` |
| 酶动力学/kcat 等 | `bioinformatics/model/enzyme/` |
| RNA | `bioinformatics/model/rna/` |
| DNA/基因组 | `bioinformatics/model/genome/` |
| 单细胞 | `bioinformatics/model/single-cell/` |
| 蛋白功能/GO | `bioinformatics/model/function/` |
| 蛋白-配体/核酸相互作用 | `bioinformatics/model/interaction/` |
| PTM | `bioinformatics/model/ptm/` |
| 表达/溶解度 | `bioinformatics/model/expression/` |
| 亚细胞定位等 | `bioinformatics/model/cellular/` |
| DNA-RNA-蛋白多模态 | `bioinformatics/model/multi-modal/` |
| 开源 LLM | `llm/open-source/` |
| 闭源 API LLM | `llm/proprietary/` |
| Embedding / VLM / Audio | `embedding/` / `vlm/` / `audio/` |

**Tool 路径**：`bioinformatics/tools/<tool_id>.md`

新子分类目录不存在时：创建目录 + 可选 README，并更新根 `README.md` 目录树。

### 4. 撰写主条目

**模板依据**（按优先级）：
1. 同分类已有条目（如 `bioinformatics/model/rna/rnabpflow.md`、`bioinformatics/tools/bprna.md`）
2. `meta/MODEL-RECORD-TEMPLATE.md` / Tool 参照 bprna 结构
3. `meta/MODEL-METADATA.md` — YAML 核心字段速查

**Model 文档结构**（与现有条目保持一致）：

```markdown
# [模型名称]
[概述 + 适用场景/行业应用/核心优势/定位]
---
## 基本信息
## 模型架构
## 输入输出规格          ← input_format / output_format 必填
## 能力与性能            ← benchmark + task_coverage
## 部署特性
## 训练数据详情          ← training_data 必填（有则写来源）
...
```

**必填字段**（缺失则调研补全或显式标注待确认）：

- Model：`model_id`, `name`, `organization`, `release_date`, `category`, `task_coverage`
- Model：`architecture_type`, `parameter_count`（或说明未知）
- Model：`input_format`, `output_format`
- Model：`license_type`, `license_url`, `commercial_use`
- Tool：`tool_id`, `name`, `tool_type`, `input_format`, `output_format`, `task_coverage`
- 应用场景标签（至少 1 个）

**写作风格**：中文为主，技术专有名词保留英文；与邻近条目语气、粒度一致。

### 5. 关联实体同步（必做）

收录 Model/Tool 时，**除主条目外必须同步处理**三类关联实体。详细规则见 [entity-sync.md](entity-sync.md)。

```
关联实体:
- [ ] 5a. 性能指标 (Metric) — 从 task_coverage / benchmark 提取
- [ ] 5b. 输入输出格式 (FileType) — 从 input_format / output_format 提取
- [ ] 5c. 训练数据集 (Dataset) — 从 training_data / 论文提取并验证
```

#### 5a. 性能指标

1. 将 `task_coverage` 每条任务映射到 `Graph_Database/mappings/metrics.yaml` 白名单。
2. **已有** → 模型条目使用与白名单一致的表述。
3. **缺失** → 按 `meta/METRIC-RECORD-TEMPLATE.md` 自动创建 `bioinformatics/metrics/<metric_id>.md`，并更新 `metrics.yaml` 别名。

#### 5b. 输入输出格式

1. 用 `infer_file_types()`（`Graph_Database/etl/normalize.py`）验证关键词是否可识别。
2. **已有** → 模型条目使用标准格式名（FASTA、PDB、JSON…）。
3. **缺失** → 按 `meta/FORMAT-RECORD-TEMPLATE.md` 自动创建 `bioinformatics/formats/<format_id>.md`，并扩展 `_FORMAT_KEYWORDS`。

#### 5c. 训练数据集

1. 从 `training_data`、论文 Data Availability 提取候选数据集。
2. **已有**（`bioinformatics/datasets/` + `datasets.yaml`）→ 补 `training_text_aliases` 若需。
3. **新候选** → **必须验证**：
   - 官方 `url` 可访问（WebFetch / curl）
   - `paper_doi` 可解析且描述一致
   - 规模/模态与官方交叉核对
4. **验证通过** → 创建 `bioinformatics/datasets/<dataset_id>.md`（须含 `url` + `paper_doi`），更新 `datasets.yaml`。
5. **验证失败** → **暂停并用 AskQuestion 向用户确认**后再决定是否入库；禁止静默添加无法验证的数据集。

### 6. 更新索引与映射

按顺序更新（存在则改，不存在则跳过）：

| 文件 | 动作 |
|------|------|
| `INDEX.md` | Model 分类下新增链接；更新计数；更新页脚日期 |
| `<category>/README.md` | 目录树、总览表（如有） |
| 根 `README.md` | 目录树（新分类时）；`Last updated` |
| `Graph_Database/mappings/metrics.yaml` | 新指标别名 |
| `Graph_Database/mappings/datasets.yaml` | 新数据集 training_text_aliases |
| `Graph_Database/etl/normalize.py` | 新格式 `_FORMAT_KEYWORDS` |

Tool 不写入 `INDEX.md`（除非项目惯例变更）；通过 ETL ingest。

**不默认更新**：`MODEL-COMPREHENSIVE-SUMMARY.md`、`protein-enzymology-index.md`。

### 7. ETL 校验

```bash
cd Graph_Database && make etl-local
# Neo4j 可用时：
make import-local
```

检查 `etl_report.json`：
- `errors` 为空
- 新模型 `training_data` 无未映射 warning（或已记录为用户确认的例外）
- 预期边：`TRAINED_ON`、`PREDICTS`、`ACCEPTS`/`PRODUCES`

### 8. 验收检查

```
收录验收:
- [ ] 文件路径与 model_id / tool_id 一致
- [ ] 无重复条目
- [ ] 必填字段已填或标注待确认
- [ ] input_format / output_format 可被 infer_file_types 识别
- [ ] task_coverage 可映射到 metrics.yaml
- [ ] training_data 已映射或经用户确认跳过
- [ ] 新 Dataset 均有 url + paper_doi 且已验证
- [ ] 许可证有来源（非猜测）
- [ ] INDEX.md 已更新（Model）
- [ ] ETL 无 error
- [ ] 未捏造 benchmark / 显存 / 参数量 / 数据集链接
```

## 输出给用户

完成后简要汇报：
1. 新建/更新文件路径（Model/Tool + 关联实体）
2. 分类与 ID
3. 核心定位（1–2 句）
4. 同步新建的 Metric / Format / Dataset 列表
5. 已更新的索引与映射文件
6. ETL 结果摘要
7. **待用户确认项**（无法验证的数据集、需实测项）

## 参考资源

- 本 Skill 目录说明：[README.md](README.md)
- 分类与索引：[reference.md](reference.md)
- **实体同步细则**：[entity-sync.md](entity-sync.md)
- 收录示例：[examples.md](examples.md)
- 关系规则：`Graph_Database/doc/10-relationship-rules.md`
- 模板：`meta/MODEL-RECORD-TEMPLATE.md`、`meta/METRIC-RECORD-TEMPLATE.md`、`meta/FORMAT-RECORD-TEMPLATE.md`、`meta/DATASET-RECORD-TEMPLATE.md`
