# 10 项目关系规则（权威）

> 版本：v1.1 | 更新：2026-07-07  
> 机器可读：`schema/edges.yaml`（存储语义）、`web/src/utils/edgeColors.ts`（可视化流向）

本文档汇总 **ETL 存储方向**、**前端可视化箭头**、**实体百科校验**、**探索页筛选** 四类规则，作为项目内关系与数据治理的单一事实来源。

---

## 1. 双层语义：存储 vs 可视化

图谱边在 JSON / Neo4j 中按 **主体 → 客体** 存储（便于索引与 Cypher）；探索页箭头按 **数据/能力/知识流向** 渲染。

| 层级 | 含义 | 示例（ACCEPTS） |
|------|------|-----------------|
| **存储** | `Model` → `FileType` | `esm2` ACCEPTS `fasta` |
| **可视化** | `FileType` → `Model` | 箭头：FASTA → ESM2（输入流入） |

**铁律：** 改可视化方向只改 `orientEdgeForFlow()` / `EDGE_REVERSE_FOR_FLOW`；**不改** `graph_export.json` 边结构与 `build_indexes()` 逻辑。

实现位置：

- ETL 建边：`etl/graph_builder.py` → `_add_edge()`
- 可视化定向：`web/src/data/loadGraph.ts` → `buildCyEdgeData()` → `orientEdgeForFlow()`
- 配置常量：`web/src/utils/edgeColors.ts`

---

## 2. 关系类型与箭头规则

### 2.1 存储方向（ETL）

| 关系 | from → to | 来源字段 | 说明 |
|------|-----------|----------|------|
| `ACCEPTS` | Model/Tool → FileType | `input_format` | 主体接受该输入格式 |
| `PRODUCES` | Model/Tool → FileType | `output_format` | 主体产出该格式 |
| `MEASURES` | Model/Tool → Metric | `task_coverage` | 主体可预测该指标 |
| `TRAINED_ON` | Model → Dataset | `training_data` | 主体在该数据上训练 |
| `BELONGS_TO` | Model → Category | `category` | 模型所属领域 |
| `BASED_ON` | Model → Model | `pretrained_model` / `parent_model` | 衍生模型声明的基座 |
| `INTEGRATES` | Model → Model/Tool | `integrated_with` | 集成方 → 被集成组件 |
| `REQUIRES` | Model → Tool | `used_by_models`（Tool 侧反查） | 模型依赖工具 |
| `SUCCESSOR_OF` | Model → Model | `successor_models` | 当前模型 → 后继版本 |
| `ALTERNATIVE_TO` | Model ↔ Model | `alternative_models` | 无向可替代 |

已废弃、默认不在探索图展示：`DESCRIBED_IN`、`HAS_LICENSE`、`HOSTED_AT`、`USES_MODALITY`、`DEVELOPED_BY`、`IMPLEMENTED_IN`（属性已内嵌 Model/Tool 节点）。

### 2.2 可视化箭头（数据流）

| 关系 | 可视化箭头 | 因果含义 |
|------|------------|----------|
| `ACCEPTS` | **FileType → Model/Tool** | 输入数据流入 |
| `TRAINED_ON` | **Dataset → Model** | 训练语料流入 |
| `BASED_ON` | **基座 Model → 衍生 Model** | 架构/权重继承 |
| `INTEGRATES` | **被集成 Model/Tool → 集成方 Model** | 组件接入管线 |
| `REQUIRES` | **Tool → Model** | 工具支撑执行 |
| `PRODUCES` | Model/Tool → FileType | 输出产物 |
| `MEASURES` | Model/Tool → Metric | 预测结果 |
| `BELONGS_TO` | Model → Category | 分类归属 |
| `SUCCESSOR_OF` | 前代 Model → 后继 Model | 版本演进（与存储同向） |
| `ALTERNATIVE_TO` | 无箭头（虚线） | 可互换 |

### 2.3 典型执行链路

```
Dataset ──TRAINED_ON──► Model ──PRODUCES──► FileType
FileType ──ACCEPTS──► Model ──MEASURES──► Metric
BaseModel ──BASED_ON──► DerivedModel
Tool ──REQUIRES──► Model
Component ──INTEGRATES──► PipelineModel
```

---

## 3. 索引与查询（依赖存储方向）

`etl/export.py` → `build_indexes()` 假定以下方向，**不可与存储语义冲突**：

| 索引键 | 边模式 | 用途 |
|--------|--------|------|
| `by_input_format` | `Model -[:ACCEPTS]-> FileType` | 选型页「输入格式 → 模型」 |
| `by_metric` | `Model -[:MEASURES]-> Metric` | 选型页「指标 → 模型」 |
| `by_metric_tool` | `Tool -[:MEASURES]-> Metric` | 选型页「仅工具预测的指标」（显示为 N 工具） |
| `by_category` | `Model -[:BELONGS_TO]-> Category` | 领域筛选 |
| `by_category_dataset` | `Model -[:TRAINED_ON]-> Dataset` + 领域 | 领域下数据集 |

Cypher 查询编写时使用 **存储方向**；前端展示调用 `orientEdgeForFlow()`。

---

## 4. 实体百科规则

### 4.1 目录与 ETL 加载

| 实体 | 路径 | 入图方式 |
|------|------|----------|
| Model | `bioinformatics/model/**/*.md` | 主 ETL 解析 |
| Metric | `bioinformatics/metrics/*.md` | `entity_catalog.load_metrics_catalog` + `metrics.yaml` 别名 |
| FileType | `bioinformatics/formats/*.md` | `infer_file_types()` 关键词 |
| Dataset | `bioinformatics/datasets/*.md` | 白名单 + `datasets.yaml` 别名 |
| Tool | `bioinformatics/tools/*.md` | `discover_tool_files()` |

### 4.2 Dataset 白名单

- 必须含可验证 `url` + `paper_doi`
- 模型 `training_data` 仅当映射到白名单数据集时建 `TRAINED_ON`
- 无独立公开发布的复述（如「2300 万 RNA 序列」）**不建节点**，映射到权威库（如 `rnacentral`）
- 配置：`mappings/datasets.yaml` → `training_text_aliases`

### 4.3 Metric 白名单

- `task_coverage` 条目经 `mappings/metrics.yaml` 别名映射为 `metric_id`
- 解析：`etl/parser.py` → `parse_list_field()` 支持 `,` / `，` / `、` 分隔；推荐方括号列表 `[a, b]`
- 表格值外层反引号自动剥离（`tool_id` 勿写 `` `prodigy` ``）
- 未命中别名则忽略（不建 `MEASURES`）
- Model 与 Tool 均建 `MEASURES` 边；仅 Tool 有边时指标入 `by_metric_tool` 而非 `by_metric`
- `bioinformatics/metrics/*.md` 词条经 `entity_catalog` **始终合并入图**，但无 `MEASURES` 边时探索页默认不可见（搜索可强制聚焦）
- 当前指标见 `bioinformatics/metrics/README.md`

### 4.4 Model 输入/输出校验

每个模型卡片须满足（ETL 警告 `ACCEPTS` / `MEASURES` 为空）：

| 字段 | 要求 |
|------|------|
| `input_format` | 含 `infer_file_types()` 可识别关键词（FASTA、PDB、JSON…） |
| `output_format` | 同上 |
| `task_coverage` | 至少一条可映射到 Metric 别名 |

批量补全脚本：`Graph_Database/scripts/fix_model_io.py`

### 4.5 FileType 关键词

定义于 `etl/normalize.py` → `_FORMAT_KEYWORDS`；新增格式须同步 `formats/<id>.md` 与关键词表。

---

## 5. 探索页 UI 规则

### 5.1 头部筛选（仅 `/explore`）

| 筛选 | 默认 | 约束 |
|------|------|------|
| 实体 | `Model` | 至少 1 项；全选后再点全选 → 仅保留第一项 |
| 领域 | `protein` | 至少 1 项；同上 |
| 关系 | `INTEGRATES`、`BASED_ON`、`ALTERNATIVE_TO` | 可空 |

实现：`ExploreFilterProvider`、`FilterDropdown`、`ExploreFiltersNav`

### 5.2 节点交互

- 点击节点：聚焦邻域 + 左侧 `EntityDrawer` 展示属性
- 支持 Model / Dataset / Metric / FileType / Tool
- **全局搜索**（Cmd+K）：跳转 `/explore?focus=<NodeType>:<id>`，自动扩展实体/领域筛选，`forcedVisibleRefs` 强制入图，`GraphCanvas` 将目标节点居中

### 5.3 探索图可见性

探索子图种子节点规则（`buildExploreElements`）：

| 实体 | 默认入图条件 |
|------|----------------|
| Model | 选中领域内的语料库模型 |
| Dataset | 选中领域 + 实体类型含 Dataset |
| Metric / FileType | 与领域内 Model 经选定关系边连通 |
| Tool | 默认**不在**探索实体类型中；经 Model `REQUIRES` 扩展可见 |

搜索聚焦时 bypass：目标 ref 写入 `forcedVisibleRefs`，即使无 Model 连通也会渲染该节点。

### 5.4 边样式

- 有向边：实线 + 三角箭头（颜色按 `EDGE_TYPE_COLORS`）
- 无向边（`ALTERNATIVE_TO`）：虚线、无箭头
- 边标签：中文（`edgeLabel()`）

---

## 6. 维护检查清单

新增或变更关系时：

1. 更新 `schema/edges.yaml`（存储 `from`/`to`/`directed`）
2. 若影响数据流展示，更新 `edgeColors.ts` 中 `EDGE_REVERSE_FOR_FLOW` / `EDGE_UNDIRECTED`
3. 若新增 ETL 建边，确认 `build_indexes()` 是否需要扩展
4. 同步本文档 §2 表格
5. `make etl-local && make web` 验证探索图箭头

新增 Dataset / Metric：

1. 词条 md + `mappings/*.yaml` 别名
2. 更新对应 `bioinformatics/*/README.md` 索引
3. 运行 ETL 检查 `etl_report.json`

---

## 7. 相关文件索引

| 文件 | 用途 |
|------|------|
| [schema/edges.yaml](../schema/edges.yaml) | 关系类型 Schema |
| [mappings/metrics.yaml](../mappings/metrics.yaml) | 指标别名 |
| [mappings/datasets.yaml](../mappings/datasets.yaml) | 数据集别名 |
| [etl/parser.py](../graph/etl/parser.py) | Markdown 字段 / 列表解析 |
| [etl/export.py](../graph/etl/export.py) | 索引构建（含 by_metric_tool） |
| [etl/graph_builder.py](../graph/etl/graph_builder.py) | 建边逻辑 |
| [etl/validate.py](../graph/etl/validate.py) | 模型/工具 IO 校验 |
| [web/src/utils/edgeColors.ts](../graph/web/src/utils/edgeColors.ts) | 可视化流向 |
| [kit/graph/README.md](../graph/README.md) | 构建、ETL 时机、包结构 |

---

*最后更新：2026-07-07*
