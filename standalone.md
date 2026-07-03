# 独立模式与工作区配置

Skill 目录**仅存模板与工具**；收录数据一律写入 `workspace.yaml` 指定的 `workspace.root`。

## 配置文件

路径：`.cursor/skills/model-intake/workspace.yaml`

```yaml
version: "1.0"
workspace:
  root: /absolute/path/to/kbase-data      # 文档数据根目录
  rawdata_dir: rawdata        # monorepo 设为 bioinformatics
  graph_database_dir: Graph_Database      # 图数据库 ETL 目录
  with_graph: true
  mode: standalone                        # embedded | standalone
  name: kbase-data
  created_at: "2026-07-03"
  updated_at: "2026-07-03"

graph_sync:
  preference: ask        # never | ask | always（默认 ask）
  preference_set_at: "2026-07-03"
```

## 图谱同步偏好

用户未明确是否构建知识图谱时，按 `graph_sync.preference` 决策：

| 选项 | preference | 本次 | 后续 |
|------|------------|------|------|
| 从不 | never | 不同步 | 不再询问 |
| 再说 | ask | 不同步 | 下次再询问 |
| 默认 | always | 同步 | 以后自动同步 |

```bash
python kit/workspace.py graph-sync --show
python kit/workspace.py graph-sync --apply 从不   # 持久化用户选择
```

示例见 [workspace.yaml.example](../workspace.yaml.example)。

## 首次收录（必做）

1. **提议默认路径**
   ```bash
   python kit/workspace.py propose
   ```
   - 工作区已有 `bioinformatics/model/` → `root` = 当前 monorepo，`mode=embedded`
   - 否则 → `root` = `{cwd}/kbase-data`，`mode=standalone`

2. **AskQuestion 用户确认**（可修改 root、是否启用图谱）

3. **持久化并初始化**
   ```bash
   python kit/workspace.py init --root "<用户路径>" --with-graph
   ```
   - 写入 `workspace.yaml`（Skill 目录下）
   - bootstrap 用户目录（**不在 Skill 内创建数据**）

4. 后续收录直接读 `workspace.yaml`

## 数据写入路径（均在 workspace.root 下）

| 实体 | 路径 |
|------|------|
| Model | `{rawdata_dir}/model/<cat>/<id>.md` |
| Tool | `{rawdata_dir}/tools/<id>.md` |
| Metric / Format / Dataset | `{rawdata_dir}/{metrics,formats,datasets}/` |
| 索引 | `INDEX.md` |
| 图谱 ETL | `Graph_Database/` |
| 映射 | `Graph_Database/mappings/*.yaml` |

## 检索

```bash
python kit/search.py "<name>"           # 自动读 workspace.yaml
python kit/search.py --entity model --list
```

## 更改默认目录

```bash
python kit/workspace.py set --root /new/path
python kit/workspace.py init --from-workspace
```

## embedded vs standalone

| mode | 说明 |
|------|------|
| embedded | 复用已有 monorepo（如 foundation-models）的 bioinformatics/ + Graph_Database/ |
| standalone | bootstrap 在新目录创建完整结构 |

模板始终从 Skill `kit/templates/` 读取；**never** 把收录 md 写入 Skill 目录。

---

*最后更新：2026-07-03*
