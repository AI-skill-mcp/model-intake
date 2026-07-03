# 实体同步 — 指标 / 格式 / 数据集

收录 Model 或 Tool 时，除主条目外**必须同步提取并落库**三类关联实体，以便 ETL 建边与探索页展示。

```
关联实体提取:
- [ ] A. 性能指标 (Metric)
- [ ] B. 输入输出格式 (FileType)
- [ ] C. 训练数据集 (Dataset)
- [ ] D. 映射表与 ETL 校验
```

---

## A. 性能指标 (Metric)

### A.1 提取来源

| 来源 | 字段 |
|------|------|
| 模型 `task_coverage` | 每条任务 → 对应预测指标 |
| 论文 benchmark 表 | Table X 中的 metric 名称 |
| Tool `task_coverage` | 同上 |

**原则**：只收录**可量化、可复现**的预测指标；纯描述性任务（如「结构预测」）映射到已有标准指标（如 `tm-score`、`plddt`），无法映射则记录为待扩展项。

### A.2 查重与映射

1. 列出 `bioinformatics/metrics/` 已有词条：
   ```bash
   ls bioinformatics/metrics/
   rg -i "<metric-name>" bioinformatics/metrics/ Graph_Database/mappings/metrics.yaml
   ```
2. 读取 `Graph_Database/mappings/metrics.yaml`，用 `aliases` 匹配中文/英文变体。
3. **已存在** → 在模型 `task_coverage` 中使用与白名单一致的表述（便于 ETL 建 `PREDICTS` 边）。
4. **不存在** → 执行 A.3 自动扩展。

### A.3 自动新建 Metric 词条

按 `meta/METRIC-RECORD-TEMPLATE.md` 创建 `bioinformatics/metrics/<metric_id>.md`：

| 必填 | 说明 |
|------|------|
| `metric_id` | 小写连字符，与文件名一致 |
| `name`, `label` | 标准符号与 UI 名 |
| `definition` | 生物学/化学定义（有官方来源） |
| `quantity_kind` | 物理量类别 |
| `unit` | 单位（无量纲写 `dimensionless`） |
| `direction` | higher_is_better / lower_is_better / context_dependent |
| `aliases` | ETL 别名列表（含中英文、论文常用写法） |

同步更新 `Graph_Database/mappings/metrics.yaml`：

```yaml
  new-metric-id:
    label: 显示名
    unit: 单位
    aliases:
      - 论文中的写法
      - 中文任务描述
```

**禁止**：无定义来源时捏造公式或 benchmark 数值；新建词条只定义指标本身，不写入模型分数。

---

## B. 输入输出格式 (FileType)

### B.1 提取来源

模型/Tool 条目中：

| 字段 | 说明 |
|------|------|
| `input_format` | 推理/训练输入（扩展名、MIME、API 类型） |
| `output_format` | 推理输出 |

从 README 安装示例、CLI `--help`、论文 Methods 补充细节。

### B.2 查重与映射

1. 列出 `bioinformatics/formats/`：
   ```bash
   ls bioinformatics/formats/
   rg -i "<format>" bioinformatics/formats/ Graph_Database/etl/normalize.py
   ```
2. `infer_file_types()` 通过 `_FORMAT_KEYWORDS` 做子串匹配；模型文档中的关键词须能被识别。
3. **已存在且关键词已覆盖** → 在模型条目中使用标准名称（如 FASTA、PDB、JSON）。
4. **不存在或关键词未覆盖** → 执行 B.3 自动扩展。

### B.3 自动新建 FileType 词条

按 `meta/FORMAT-RECORD-TEMPLATE.md` 创建 `bioinformatics/formats/<format_id>.md`：

| 必填 | 说明 |
|------|------|
| `format_id` | 小写，与文件名一致 |
| `name` | 人类可读名 |
| `typical_extension` | 扩展名列表 |
| `encoding` | text / binary |
| `description` | 记录结构与语义 |
| `common_role` | input / output / both |

**必须同步** `Graph_Database/etl/normalize.py` → `_FORMAT_KEYWORDS`：

```python
("新关键词", "format_id"),   # 小写子串，勿与已有项冲突
(".ext", "format_id"),
```

新增后本地验证：

```bash
cd Graph_Database && python -c "
from etl.normalize import infer_file_types
print(infer_file_types('<模型 input_format 原文>'))
print(infer_file_types('<模型 output_format 原文>'))
"
```

---

## C. 训练数据集 (Dataset)

### C.1 提取来源

| 来源 | 字段 |
|------|------|
| 模型 `training_data` / `## 训练数据详情` | 主来源 |
| 论文 Data Availability / Methods | 补充规模、版本 |
| GitHub README `data/` 说明 | 下载路径 |

**原则**（与 `Graph_Database/doc/10-relationship-rules.md` 一致）：

- 优先映射到**权威公开数据库**（PDB、UniRef、BRENDA…），禁止从 `training_data` 自由文本「猜」出一个无官方页面的伪数据集。
- 复合描述（`PDB + AlphaFold DB`）按 `+` 拆分，分别映射；整句优先于拆分（见 `resolve_training_dataset_ids`）。

### C.2 查重

```bash
ls bioinformatics/datasets/
rg -i "<dataset>" bioinformatics/datasets/ Graph_Database/mappings/datasets.yaml
```

### C.3 验证数据集（必做）

对每个候选数据集执行**双重核验**：

| 检查项 | 方法 | 通过标准 |
|--------|------|----------|
| 官方 URL | `WebFetch` / `curl -I` | HTTP 200 或官方重定向至有效页；非 404/5xx |
| 文献 DOI | `WebFetch` https://doi.org/... | 可解析，且描述与该数据集一致 |
| 名称与规模 | 交叉对照论文/官网 | 模型条目中引用的规模、模态与官方一致（数量级即可） |
| 许可 | LICENSE / 官网 Terms | 记录于 `license_note`，不猜测 |

验证记录写入数据集条目 `## 验证说明`：

```markdown
## 验证说明

- `url`：2026-07-03 访问正常（RCSB 首页）
- `paper_doi`：10.1093/nar/gkab1023 对应 wwPDB 2022 NAR 论文
- 规模：与官网 ">200,000 structures" 一致
```

### C.4 决策分支

```
数据集候选
├─ 已在 bioinformatics/datasets/ + datasets.yaml
│   └─ 在模型 training_data 中使用可映射原文；必要时补 aliases
├─ 验证通过（url + paper_doi 均可确认）
│   └─ 新建 datasets/<id>.md → 更新 datasets.yaml → 模型 training_data 引用
└─ 验证失败 / 无法访问 / 无 DOI / 仅内部数据
    └─ **暂停**：用 AskQuestion 向用户确认是否仍要收录及如何处理
        ├─ 用户提供官方 url + doi → 重新验证后入库
        ├─ 用户确认「仅保留 training_data 文本、不建 Dataset 节点」→ 写 warning 预期
        └─ 用户要求跳过该数据集 → 不写入
```

**AskQuestion 须包含**：数据集名称、当前掌握的 url/doi、验证失败原因、建议操作。

### C.5 新建 Dataset 词条

按 `meta/DATASET-RECORD-TEMPLATE.md` 创建 `bioinformatics/datasets/<dataset_id>.md`：

| 必填 | 说明 |
|------|------|
| `dataset_id` | 小写连字符 |
| `name` | 官方名称 |
| `dataset_type` | training / benchmark / reference / annotation |
| `description` | 内容与构建方式 |
| `url` | **可访问**官方入口 |
| `paper_doi` | **可解析**文献 DOI |
| `license_note` | 许可摘要 |

同步 `Graph_Database/mappings/datasets.yaml` → `training_text_aliases`：

```yaml
  "论文/模型中的原文表述": dataset_id
  "常见缩写或变体": dataset_id
```

---

## D. 映射表与 ETL 校验

### D.1 收录后必跑

```bash
cd Graph_Database
make etl-local
make import-local   # 若 Neo4j 可用
```

检查 `Graph_Database/etl_report.json`：

| 检查 | 期望 |
|------|------|
| `errors` | 空 |
| `warnings` 中 training_data | 新收录模型的 training_data 均已映射 |
| 节点计数 | Dataset / Metric / FileType 增量符合预期 |
| 边 | Model→Dataset `TRAINED_ON`、Model→Metric `PREDICTS`、Model→FileType `ACCEPTS`/`PRODUCES` |

### D.2 Tool 收录差异

| 项 | Model | Tool |
|----|-------|------|
| 路径 | `bioinformatics/model/<cat>/` | `bioinformatics/tools/` |
| ID 字段 | `model_id` | `tool_id` |
| 训练数据 | `TRAINED_ON` | 通常无；若有 benchmark 数据写 `requires_datasets` |
| 关系 | — | `REQUIRES`（依赖其他 Tool）、`used_by_models` |

Tool 同样须完成 **B（I/O 格式）** 与 **A（task_coverage 指标）**；数据集仅在 Tool 明确依赖评测集时收录。

### D.3 索引更新（实体维度）

实体词条**不写入** `INDEX.md`（该文件仅索引 Model）；图谱通过 ETL 自动 ingest。若项目后续有 `bioinformatics/metrics/README.md` 等子索引，按既有惯例更新。

---

## 快速对照表

| 实体 | 词条路径 | 映射文件 | 无法确认时 |
|------|----------|----------|------------|
| Metric | `bioinformatics/metrics/<id>.md` | `Graph_Database/mappings/metrics.yaml` 或 standalone 同路径 | 自动新建（需有定义来源） |
| FileType | `bioinformatics/formats/<id>.md` | `etl/normalize.py` `_FORMAT_KEYWORDS` | 自动新建 + 加关键词 |
| Dataset | `bioinformatics/datasets/<id>.md` | `Graph_Database/mappings/datasets.yaml` | **AskQuestion**，禁止静默入库 |

### 模式差异

| 资源 | embedded | standalone |
|------|----------|------------|
| 数据根目录 | `workspace.yaml` → `workspace.root` | 同左 |
| 指标模板 | `kit/templates/metric.md.tpl` 或 monorepo `meta/` | `kit/templates/` 或 `{root}/meta/*.template.md` |
| 关系规则 | `{root}/Graph_Database/doc/` 或 `{root}/.kbase/rules/` | 同左 |
| 映射 | `{root}/Graph_Database/mappings/` | 同左 |

**铁律**：收录 md / ETL 产物只写 `workspace.root`，不写 Skill 目录。配置持久化在 `.cursor/skills/model-intake/workspace.yaml`。

工作区 CLI：`python kit/workspace.py propose|init|show|set`
