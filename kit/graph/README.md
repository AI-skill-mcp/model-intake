# Graph_Database

生物学大模型知识图谱 — 从 `bioinformatics/` 构建可查询图数据。

## 快速开始

```bash
cd Graph_Database
cp .env.example .env

# 方式 A：Docker（基础镜像默认走 DaoCloud，pip/npm 走国内源）
make up          # 启动 Neo4j
make etl         # 容器内 ETL
make import      # 容器内导入 Neo4j
make web         # 启动探索前端（后台）

# 方式 B：本地 Python（ETL / 导入）
pip install -r docker/etl/requirements.txt
make up          # 仍需 Docker 跑 Neo4j
make etl-local
make import-local
make web-local   # 本机前端
```

- 探索前端: http://localhost:5173 （`make web` 或 `make web-local`）
- Neo4j Browser: http://localhost:7474 （用户 `neo4j` / 密码见 `.env`）
- ETL 产物: `data/nodes.jsonl`, `data/graph_export.json`, `data/etl_report.json`

## 文档

| 文档 | 说明 |
|------|------|
| [doc/README.md](./doc/README.md) | 文档导航 |
| **[doc/10-relationship-rules.md](./doc/10-relationship-rules.md)** | **关系规则权威**（存储方向、可视化箭头、实体校验） |
| [docs/todo_list.md](./docs/todo_list.md) | **系统优化 Todo**（部署形态、功能路线、成本评估） |
| [schema/edges.yaml](./schema/edges.yaml) | 关系类型 Schema（含 visualization 配置） |

## 目录

```
Graph_Database/
├── doc/           # 技术方案（含 10-relationship-rules.md）
├── etl/           # Python ETL
├── schema/        # 节点/边 Schema
├── mappings/      # 字段映射、metrics/datasets 别名
├── scripts/       # fix_model_io.py 等维护脚本
├── web/           # React 探索前端
├── data/          # ETL 产物（运行后生成）
├── overrides/     # 人工覆盖层
└── docker/        # 容器定义
```

## 当前进度

| 里程碑 | 状态 |
|--------|------|
| M0 文档 + Compose | 完成 |
| M1 ETL → JSONL | 完成（99 模型，21 Dataset，21 Metric） |
| M2 Neo4j 导入 | 完成 |
| M3 Web 前端 | 完成（头部筛选 + 实体抽屉 + 数据流箭头） |
| M5 API | 待开发 |
| M6 MCP | 待开发 |
