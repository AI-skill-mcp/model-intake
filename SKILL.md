---
name: model-intake
description: >-
  收录新底层模型或工具到知识库：收录数据写入 workspace.yaml 指定的用户目录，并可选的基于收录的知识库构建图数据库;首次收录时向用户确认默认路径并持久化配置；尝试下载论文 PDF 到 {rawdata_dir}/paper/。
  当用户说「收录」「纳入」「添加模型」「添加工具」「初始化知识库」时使用。
---

# 模型/工具收录 (Model & Tool Intake)

将新 **Model** 或 **Tool** 纳入知识库。**必须实际调研**，禁止编造数据。

## 目录职责（铁律）

| 位置                           | 存放内容                                      | 禁止                 |
| ------------------------------ | --------------------------------------------- | -------------------- |
| `.cursor/skills/model-intake/` | 模板、kit 代码、**workspace.yaml**            | **禁止写入收录数据** |
| `workspace.root`（用户确认）   | `{rawdata_dir}/`、`Graph_Database/`、INDEX.md | —                    |

> `{rawdata_dir}` 由 `workspace.yaml` 配置，默认 `rawdata`；embedded monorepo 设为 `bioinformatics`。  
> 初始化时会创建 `{rawdata_dir}/paper/`，用于存放可下载的论文全文 PDF。

## 0. 工作区配置（每次收录前先执行）

### 0.1 读取配置

```bash
python .cursor/skills/model-intake/kit/workspace.py show
```

配置文件路径：**`.cursor/skills/model-intake/workspace.yaml`**（Skill 目录下持久化）

### 0.2 首次收录（workspace.yaml 不存在）

1. 生成建议默认路径：
   ```bash
   python .cursor/skills/model-intake/kit/workspace.py propose
   ```
2. **AskQuestion 向用户确认**（可修改）：
   - `workspace.root` — 文档数据根目录
   - `rawdata_dir` — 原始数据相对目录（默认 `rawdata`；monorepo 设为 `bioinformatics`）
   - `graph_database_dir` — 图数据库 ETL 目录（默认 `Graph_Database`）
   - `with_graph` — 是否启用图谱
3. 用户确认后写入 `workspace.yaml` 并初始化：
   ```bash
   python kit/workspace.py init --root "<用户确认路径>" --with-graph
   # embedded monorepo（rawdata_dir=bioinformatics）:
   python kit/workspace.py init --root "/path/to/foundation-models" --mode embedded --with-graph
   python kit/workspace.py set --rawdata-dir bioinformatics
   ```

**默认路径规则**（propose）：
- 含 `bioinformatics/model/` → `root`=项目根，`rawdata_dir=bioinformatics`，`mode=embedded`
- 含 `rawdata/model/` → `rawdata_dir=rawdata`
- 否则 → `root=~/kbase-data`，`rawdata_dir=rawdata`，`mode=standalone`

### 0.3 后续收录

直接读取 `workspace.yaml`，所有读写相对于：

| 键                             | 含义                              |
| ------------------------------ | --------------------------------- |
| `workspace.root`               | 知识库根                          |
| `workspace.rawdata_dir`        | 原始数据目录名（默认 `rawdata`）  |
| `{rawdata_dir}/paper/`         | 论文全文 PDF（开放获取时自动保存） |
| `workspace.graph_database_dir` | 图谱 ETL（默认 `Graph_Database`） |

```python
from pathlib import Path
import yaml
from workspace import get_rawdata_rel  # kit/workspace.py

cfg = yaml.safe_load(open(".cursor/skills/model-intake/workspace.yaml"))
ws = cfg["workspace"]
root = Path(ws["root"])
raw = root / get_rawdata_rel(ws)
graph = root / ws["graph_database_dir"]
```

### 0.4 用户更改目录

```bash
python kit/workspace.py set --root /new/path
python kit/workspace.py init --from-workspace
```

### 0.5 知识图谱同步偏好（每次收录前）

配置块：`workspace.yaml` → `graph_sync.preference`（默认 `ask`）

| 值       | 含义     | 本次收录   | 后续                   |
| -------- | -------- | ---------- | ---------------------- |
| `never`  | **从不** | 不同步 ETL | 不再询问               |
| `ask`    | **再说** | 不同步 ETL | 下次收录再次三选一询问 |
| `always` | **默认** | 同步 ETL   | 以后自动同步，不再询问 |

#### 决策流程

1. 用户指令**已明确**（如「同步图谱」「不要图谱」）→ 按指令执行，**不询问**
2. 读取 `graph_sync.preference`：
   - `never` → 跳过步骤 7（ETL）
   - `always` → 执行步骤 7
   - `ask` → **AskQuestion 三选一**（见下），写入 `workspace.yaml` 后按选择执行

#### AskQuestion 文案（preference=ask 且用户未明确时）

> 是否同步构建知识图谱（ETL → Neo4j）？

| 选项 ID  | 标签                                      | 效果                        |
| -------- | ----------------------------------------- | --------------------------- |
| `never`  | **从不** — 本次不同步，以后不再询问       | preference=never，跳过 ETL  |
| `ask`    | **再说** — 本次不同步，下次添加时再问     | preference=ask，跳过 ETL    |
| `always` | **默认** — 本次同步，以后每次收录默认同步 | preference=always，执行 ETL |

用户选择后立即持久化：

```bash
python kit/workspace.py graph-sync --apply never   # 或 ask / always / 从不 / 再说 / 默认
```

查看/手动修改偏好：

```bash
python kit/workspace.py graph-sync --show
python kit/workspace.py graph-sync --set always
```

**前提**：`workspace.with_graph: true` 且 `Graph_Database/` 已部署；否则仅更新文档与 mappings，跳过 ETL。

## 触发识别

- 「收录 RNAbpFlow」「添加 bpRNA 工具」「初始化知识库」

提取：**名称**、**类型**（Model/Tool）、**分类提示**、**特殊要求**。

## 工作流

```
进度:
- [ ] 0. 工作区（workspace.yaml 确认 / 读取）
- [ ] 1. 查重与定位
- [ ] 2. 信息调研
- [ ] 2b. 论文 PDF（若有 paper_url / doi）
- [ ] 3. 确定路径与 ID
- [ ] 4. 撰写主条目 → 写入 workspace.root
- [ ] 5. 关联实体同步
- [ ] 6. 更新索引与映射
- [ ] 7. ETL 校验（graph_database_dir）
- [ ] 8. 验收检查
```

### 1. 查重与定位

```bash
python .cursor/skills/model-intake/kit/search.py "<name>"
```

`search.py` 会同时扫描 rawdata 目录、INDEX.md 和 mappings，输出已收录的全部匹配条目。

### 2–4. 调研 / 路径 / 撰写

模板来源（**只在 Skill/kit 读取，写入 workspace.root**；章节结构对齐 `meta/*-RECORD-FULL.md`）：

| 用途    | Skill 内模板                   |
| ------- | ------------------------------ |
| Model   | `kit/templates/model.md.tpl`   |
| Tool    | `kit/templates/tool.md.tpl`    |
| Metric  | `kit/templates/metric.md.tpl`  |
| Format  | `kit/templates/format.md.tpl`  |
| Dataset | `kit/templates/dataset.md.tpl` |

写入路径（均在 `workspace.root` 下，`{rawdata_dir}` 来自配置）：
- Model → `{rawdata_dir}/model/<cat>/<id>.md`
- Tool → `{rawdata_dir}/tools/<id>.md`
- 等

embedded 模式可额外参考 monorepo 的 `meta/*-TEMPLATE.md`。

### 2b. 论文全文 PDF（调研后、撰写前）

调研得到 `paper_url` 或 `paper_doi` 时，**尝试下载开放获取 PDF**（闭源/付费墙则跳过，不阻塞收录）：

```bash
# 确保 paper/ 存在（bootstrap 已创建；旧工作区可补建）
python .cursor/skills/model-intake/kit/paper_fetch.py ensure-dir

# 下载（stdout 为 JSON）
python .cursor/skills/model-intake/kit/paper_fetch.py fetch \
  --paper-url "https://doi.org/10.1101/..." \
  --entity-id "<model_id 或 tool_id>"
```

**策略**（按序尝试，首个有效 PDF 即保存）：
1. Unpaywall / Semantic Scholar 开放获取链接
2. PubMed Central（经 Semantic Scholar / Europe PMC 解析 PMCID）
3. arXiv / bioRxiv / medRxiv 直链（bioRxiv 可能受 Cloudflare 限制）
4. DOI 落地页内嵌 PDF 链接

**保存位置**：`{rawdata_dir}/paper/<doi-slug>.pdf`（无 DOI 时用 entity_id 命名）

**写入条目**：主条目「基本信息」表增加（下载成功时）：

| 字段 | 值 |
|------|-----|
| `paper_pdf` | `{rawdata_dir}/paper/10.xxxx-....pdf`（相对 workspace.root） |

下载失败时在汇报中说明原因（如闭源），**不填** `paper_pdf`，收录照常进行。

Dataset 的 `paper_doi` 若对应独立文献且尚未收录 PDF，可用同一命令 `--doi` 尝试下载（文件名按 DOI）。

**批量补全**（对已收录 model/tools 一次性尝试下载并回写 `paper_pdf`）：

```bash
python .cursor/skills/model-intake/kit/paper_fetch.py backfill
python .cursor/skills/model-intake/kit/paper_fetch.py backfill --dry-run
```

### 5. 关联实体同步

见 [entity-sync.md](entity-sync.md)。映射文件位于 `{root}/{graph_database_dir}/mappings/`。

### 6. 更新索引

- `{root}/INDEX.md`
- `{graph_database_dir}/mappings/*.yaml`
- `{graph_database_dir}/etl/normalize.py`（新格式关键词）

### 7. ETL 校验

按 **0.5 图谱同步偏好** 决定是否执行。`run_etl=true` 时：

```bash
cd "$(yaml root)/Graph_Database" && make etl-local
make import-local   # Neo4j 可用时
```

`run_etl=false` 或 `with_graph: false` 时跳过，汇报中注明。

### 8. 验收

```
- [ ] 收录数据未写入 Skill 目录
- [ ] workspace.yaml 路径与 graph_sync 偏好正确
- [ ] 必填字段 / 实体同步
- [ ] 论文 PDF：已下载并填 paper_pdf，或已说明无法获取
- [ ] ETL：按偏好执行或已跳过并说明
```

## 参考资源

- [README.md](README.md) — Skill 总览
- [workspace.yaml.example](workspace.yaml.example) — 配置示例
- [kit/workspace.py](kit/workspace.py) — 路径管理 CLI
- [kit/paper_fetch.py](kit/paper_fetch.py) — 论文 PDF 下载
- [standalone.md](standalone.md) / [entity-sync.md](entity-sync.md) / [examples.md](examples.md)
- 关系规则：embedded → `{root}/Graph_Database/doc/10-relationship-rules.md`；standalone → `{root}/.kbase/rules/`
