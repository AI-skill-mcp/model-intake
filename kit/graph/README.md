# Graph Database（model-intake 内置）

本目录是**完整图谱技能包**的实现源码：ETL、Schema、Web 前端、Docker/Makefile。  
bootstrap 时整包复制到用户工作区的 `Graph_Database/`。

> **embedded 开发**：在 monorepo 的 `Graph_Database/` 调试后，须按 `.cursor/rules/graph-database-sync-to-skill.mdc` 回写本目录。

## 目录结构

```
kit/graph/
├── README.md              ← 本文件
├── Makefile               ← etl-local / import-local / web-local
├── docker-compose.yml
├── docker/                ← ETL 镜像
├── etl/                   ← Python 流水线（唯一 ETL 源码）
├── schema/                ← nodes/edges/online_resources + CHANGELOG
├── web/                   ← React + Vite + Cytoscape 探索前端（完整源码）
├── overrides/             ← 手工边覆盖（可选）
└── doc/                   ← 补充说明（可选）
```

映射白名单：`kit/mappings/`（bootstrap 时复制到 `Graph_Database/mappings/`）。

## 构建与运行

### 前置

- Python 3.11+，`pip install -r docker/etl/requirements.txt`
- 原始数据：`{rawdata_dir}/`（embedded 为 `bioinformatics/`）
- Node 18+（Web）

### ETL（生成图谱数据）

```bash
cd Graph_Database   # 或 kit/graph 下 PYTHONPATH=. 指向 etl 包根
make etl-local
# → data/nodes.jsonl, data/edges.jsonl, data/graph_export.json, data/etl_report.json
```

**时机**：每次收录 Model/Tool/Metric/Dataset/Format 并更新 mappings 后；或修改 `etl/`、`mappings/` 后。

**输入**：`../bioinformatics/`（或 `RAWDATA_DIR`）下 md + `mappings/*.yaml`  
**输出**：`data/graph_export.json`（含 `indexes`：`by_metric`、`by_metric_tool` 等）

### Neo4j 导入（可选）

```bash
make up          # 启动 Neo4j
make import-local
```

### Web 探索前端

```bash
make web-install
make web-local   # 开发；build 时 prebuild 复制 graph_export.json → public/data/
```

源码目录：`kit/graph/web/`（React + Vite + Cytoscape.js）。bootstrap 时随 `kit/graph/` 一并部署到 `Graph_Database/web/`。

Docker：`make web`（compose profile web）。

## 数据创建规则（摘要）

完整规则：`kit/rules/relationship-rules.md`。

| 阶段 | 规则 |
|------|------|
| **解析** | `etl/parser.py`：列表支持 `,`/`，`/`、`；表格值外层反引号剥离 |
| **Metric** | `task_coverage` → `metrics.yaml` aliases → `MEASURES` 边；Tool 边入 `by_metric_tool` |
| **Dataset** | 白名单 + 可验证 url/doi；`training_data` 映射失败写 warning |
| **FileType** | `format-keywords.yaml` + `infer_file_types()` |
| **存储 vs 可视化** | JSON/Neo4j 存主体→客体；Web 箭头用 `orientEdgeForFlow()`，不改存储边 |
| **探索可见性** | 默认 Metric 须与 Model 连通；搜索 `?focus=` 用 `forcedVisibleRefs` 强制入图 |
| **搜索聚焦** | Cmd+K → `/explore?focus=Type:id` → 扩展筛选 + `GraphCanvas` 居中目标节点 |

## 版本记录

见 `schema/CHANGELOG.md`。

---

*kit graph package — 与 model-intake skill 同生命周期维护*
