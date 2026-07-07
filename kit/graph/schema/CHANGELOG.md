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

## [0.1.3] - 2026-07-07

### 变更

- **ETL 解析**：`parse_list_field` 支持顿号 `、` 分隔；表格值外层反引号自动剥离
- **索引**：`build_indexes()` 新增 `by_metric_tool`（Tool → Metric）
- **映射**：starter `metrics.yaml` 补充 `kd`、`binding_affinity` 别名
- **Web**：探索页搜索聚焦（`forcedVisibleRefs` + 节点居中）；选型页指标含仅工具预测项

### 变更

- **Web 源码**：纳入 `kit/graph/web/`（探索页、搜索聚焦、by_metric_tool 选型指标）
- 本地 `Graph_Database/` 优化须回写 `kit/graph/`（见项目 rule `graph-database-sync-to-skill.mdc`）

### 收录注意

- Tool `task_coverage` 推荐 `[项1, 项2]`；`tool_id` 表格值勿写反引号
- Metric 词条可无 Model 边（仅 Tool 预测）；须同步 metrics.yaml aliases + 验证 edges.jsonl
- 本地 `Graph_Database/` 优化须回写 `kit/graph/`（见项目 rule `graph-database-sync-to-skill.mdc`）

## [0.1.2] - 2026-07-02

### 新增

- M3 Web 前端：`web/`（React + Vite + Cytoscape.js）
- 探索页、选型向导、模型详情页
- `make web-local` / `make web-install` 本地启动

### 新增

- Python ETL 流水线（`etl.run`）
- Neo4j 导入（`etl.import_neo4j`）
- Docker Compose + Makefile 容器化基座
