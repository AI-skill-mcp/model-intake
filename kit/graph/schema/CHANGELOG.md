# Schema 变更日志

遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2026-07-02

### 新增

- 16 类节点：`nodes.yaml`
- 关系类型全集：`edges.yaml`
- Model/Tool 共有属性：`summary`、`online_resources`、`online_resources_meta`
- 在线资源 11 渠道规范：`online_resources.yaml`
- Markdown 字段映射：`mappings/field_to_node.yaml`

### 说明

- 首版覆盖 `bioinformatics/` 约 96 个模型条目
- ETL 实现：`etl/` 包，`make etl` 或 `make etl-local`
- M1 实测：98 模型 → 515 节点、1285 边（2026-07-02）

## [0.1.2] - 2026-07-02

### 新增

- M3 Web 前端：`web/`（React + Vite + Cytoscape.js）
- 探索页、选型向导、模型详情页
- `make web-local` / `make web-install` 本地启动

### 新增

- Python ETL 流水线（`etl.run`）
- Neo4j 导入（`etl.import_neo4j`）
- Docker Compose + Makefile 容器化基座

## 2026-07-20 — Dataset LABELS / PROVIDES

- 新增边：`LABELS`（Dataset→Metric）、`PROVIDES`（Dataset→FileType）
- Dataset 字段：`label_metrics`、`file_formats`
- 索引：`by_metric_dataset`、`by_format_dataset`
- 选型页展示相关数据集；探索图默认可选 LABELS/PROVIDES

