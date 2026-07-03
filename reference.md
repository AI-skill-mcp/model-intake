# 模型收录 — 分类与字段参考

## 目录结构（当前有效）

```
foundation-models/
├── INDEX.md                    ← 全库索引，收录后必更新
├── README.md                   ← 顶层说明与目录树
├── meta/
│   ├── MODEL-METADATA.md       ← YAML 核心字段
│   ├── MODEL-RECORD-TEMPLATE.md ← 全量字段清单
│   ├── MODEL-RECORD-FULL.md    ← 完整示例
│   ├── ENTITY-CATALOG-PLAN.md  ← 指标/格式/数据集维度规划
│   ├── METRIC-RECORD-TEMPLATE.md / METRIC-METADATA.md / METRIC-RECORD-FULL.md
│   ├── FORMAT-RECORD-TEMPLATE.md / FORMAT-METADATA.md / FORMAT-RECORD-FULL.md
│   └── DATASET-RECORD-TEMPLATE.md / DATASET-METADATA.md / DATASET-RECORD-FULL.md
└── bioinformatics/                 # 实体类型与顶层目录一一对应
    ├── model/                      # Model 卡片（按领域分子目录）
    │   ├── protein/      (36+)
    │   ├── enzyme/       (24)
    │   ├── rna/          (+ README.md 子索引)
    │   ├── genome/
    │   ├── single-cell/
    │   ├── multi-modal/
    │   ├── function/
    │   ├── interaction/
    │   ├── ptm/
    │   ├── expression/
    │   └── cellular/
    ├── metrics/        # Metric 词条
    ├── formats/        # FileType 词条
    └── datasets/       # Dataset 词条
```

**收录时实体同步细则**：`.cursor/skills/model-intake/entity-sync.md`  
**独立模式 / 全新目录**：`.cursor/skills/model-intake/standalone.md` + `kit/bootstrap.py`

**ETL 映射文件**（收录后须同步）：

| 实体 | 映射文件 |
|------|----------|
| Metric | `Graph_Database/mappings/metrics.yaml` |
| Dataset | `Graph_Database/mappings/datasets.yaml` |
| FileType | `Graph_Database/etl/normalize.py` → `_FORMAT_KEYWORDS` |

顶层待建分类（README 已规划、目录可能为空）：`llm/`、`embedding/`、`vlm/`、`multimodal/`、`audio/`。

## model_id 命名

| 规则 | 示例 |
|------|------|
| 全小写 | `esm2`, `rnabpflow` |
| 多词用连字符 | `rhofold-plus`, `nucleotide-transformer` |
| 与文件名一致 | `bioinformatics/model/rna/rnabpflow.md` → `rnabpflow` |
| 避免版本号入 id | 版本放 `version` 字段，非文件名 |

## 分类决策树

```
是否生信专用？
├─ 否 → llm / embedding / vlm / audio / multimodal
└─ 是 →
    ├─ 蛋白质序列/结构/设计/亲和力 → protein/
    ├─ 酶动力学/Kcat/Km/特异性 → enzyme/
    ├─ RNA/mRNA/siRNA → rna/
    ├─ DNA/基因组/核苷酸 → genome/
    ├─ 单细胞 → single-cell/
    ├─ DNA+RNA+蛋白联合 → multi-modal/
    ├─ GO/功能注释 → function/
    ├─ 蛋白-配体/DNA/RNA 结合 → interaction/
    ├─ 翻译后修饰 → ptm/
    ├─ 溶解度/表达 → expression/
    └─ 亚细胞定位等 → cellular/
```

边界模糊时：参考 `INDEX.md` 已有条目；优先与**主要任务**一致。

## 必填字段清单

来自 `meta/MODEL-RECORD-TEMPLATE.md` 填写检查清单：

### 必须填写
- model_id, name, organization, release_date, category, task_coverage
- input_format, output_format
- architecture_type, parameter_count
- license_type, license_url, commercial_use

### 强烈推荐
- paper, paper_url
- benchmarks（2–3 条，附 source）
- gpu_memory / inference_speed（官方或实测；否则标注需评估）
- github / huggingface 链接
- quick_start 代码或命令
- related_models, alternatives
- bibtex 引用

### 应用场景标签（至少选一个）

| 标签 | 含义 |
|------|------|
| research_exploration | 探索性研究 |
| commercial_production | 商业化（需 license 支持） |
| rapid_prototyping | 快速原型 |
| high_throughput | 高通量 |
| low_resource | 低资源部署 |

## INDEX.md 更新规范

1. 找到对应 `### Category（N 个）` 小节
2. `N` 加 1
3. 按字母或既有顺序插入链接行：
   ```markdown
   - [model-id](./bioinformatics/<cat>/model-id.md) — 简短描述
   ```
4. 更新页脚：`*最后更新：YYYY-MM-DD（新增 XXX 模型）*`

## 子分类 README 更新（以 rna/ 为例）

若 `bioinformatics/model/<cat>/README.md` 存在，同步更新：
- 知识库结构代码块中的文件行
- 模型总览表格（模型名、类型、机构、任务、推荐度、许可证）
- 「详细模型卡片」推荐段落（若属重点模型）
- 选型方案图（若与现有 workflow 相关）
- `_最后更新_` 日期

## 调研来源优先级

1. 官方 GitHub README + LICENSE
2.  peer-reviewed 论文 / Nature Methods 等
3. bioRxiv / arXiv 预印本
4. HuggingFace Model Card
5. 权威媒体报道（仅作补充，benchmark 以论文为准）
6. 同类知识库条目（仅作格式参考，数据仍须独立核实）

## Tool 收录

| 项 | 规则 |
|----|------|
| 路径 | `bioinformatics/tools/<tool_id>.md` |
| ID | `tool_id`，小写连字符 |
| 必填 | `name`, `tool_type`, `input_format`, `output_format`, `task_coverage` |
| 关系 | `used_by_models`（被哪些 Model 依赖）、`REQUIRES`（ETL 自动建边） |
| 训练数据 | 通常无；若依赖 benchmark 集，走 Dataset 同步流程 |

参照：`bioinformatics/tools/bprna.md`

## 关联实体同步（Model / Tool 共用）

收录主条目后**必须**完成三类实体处理，细则见 [entity-sync.md](entity-sync.md)。

### Metric（性能指标）

| 步骤 | 动作 |
|------|------|
| 查重 | `bioinformatics/metrics/` + `Graph_Database/mappings/metrics.yaml` |
| 来源 | `task_coverage`、论文 benchmark 表 |
| 缺失时 | 按 `meta/METRIC-RECORD-TEMPLATE.md` 新建词条 + 更新 `metrics.yaml` aliases |
| ETL 边 | Model/Tool → Metric：`PREDICTS` |

### FileType（输入输出格式）

| 步骤 | 动作 |
|------|------|
| 查重 | `bioinformatics/formats/` + `etl/normalize.py` → `_FORMAT_KEYWORDS` |
| 来源 | `input_format`、`output_format` |
| 缺失时 | 按 `meta/FORMAT-RECORD-TEMPLATE.md` 新建词条 + 扩展 `_FORMAT_KEYWORDS` |
| 验证 | `infer_file_types('<原文>')` 返回预期 format_id |
| ETL 边 | Model/Tool → FileType：`ACCEPTS` / `PRODUCES` |

### Dataset（训练数据集）

| 步骤 | 动作 |
|------|------|
| 查重 | `bioinformatics/datasets/` + `Graph_Database/mappings/datasets.yaml` |
| 来源 | `training_data`、`## 训练数据详情`、论文 Data Availability |
| 入库条件 | **必须**同时具备可验证 `url` + `paper_doi` |
| 验证 | WebFetch 访问 url；doi.org 解析 DOI；规模/模态交叉核对 |
| 缺失时（验证通过） | 按 `meta/DATASET-RECORD-TEMPLATE.md` 新建 + 更新 `training_text_aliases` |
| 无法验证时 | **AskQuestion 向用户确认**，禁止静默入库 |
| ETL 边 | Model → Dataset：`TRAINED_ON`（仅白名单内） |

### ETL 收尾

```bash
cd Graph_Database && make etl-local && make import-local
```

检查 `etl_report.json`：`errors` 为空；`training_data` warning 已处理。

## 禁止事项

- 不捏造 benchmark 分数、显存需求、参数量
- 不复制其他条目数据而不核实
- 不跳过 INDEX 更新（Model）
- 不跳过关联实体同步（Metric / Format / Dataset）
- 不添加无法验证 url/doi 的数据集（须用户确认）
- 不从 training_data 自由文本臆造无官方页面的伪数据集
- 不擅自 commit（除非用户明确要求）
- 不默认更新 MODEL-COMPREHENSIVE-SUMMARY（体量大，需单独授权）
