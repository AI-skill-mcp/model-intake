# {{name}}

独立生物信息学模型/工具知识库（由 model-intake kit 初始化）。

## 目录结构

```
{{name}}/
├── INDEX.md                 # 模型索引
├── {{rawdata_dir}}/
│   ├── model/<category>/    # Model 卡片
│   ├── tools/               # Tool 卡片
│   ├── metrics/             # Metric 词条
│   ├── formats/             # FileType 词条
│   └── datasets/            # Dataset 词条（须 url + paper_doi）
├── meta/                    # 条目模板（撰写参考）
├── .kbase/                  # manifest、检索脚本、规则副本
└── Graph_Database/          # 可选：Neo4j 图谱 ETL
```

## 快速开始

### 检索

```bash
python .kbase/search.py "关键词"
python .kbase/search.py --entity model --list
python .kbase/search.py --entity dataset pdb
```

### 收录新模型

1. 复制 `meta/model.template.md` → `{{rawdata_dir}}/model/<category>/<id>.md`
2. 同步 Metric / Format / Dataset（见 `.kbase/rules/relationship-rules.md`）
3. 更新 `INDEX.md`

### 图谱（若已 `--with-graph` 初始化）

```bash
cd Graph_Database
cp .env.example .env
pip install -r docker/etl/requirements.txt
make up          # 启动 Neo4j
make etl-local   # 生成 data/graph_export.json
make import-local
```

Neo4j Browser: http://localhost:7474

---

*初始化日期：{{date}}*
