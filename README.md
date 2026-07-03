# model-intake

收录 **Model / Tool** 的 Cursor Agent Skill。

**Skill 目录只存模板与工具代码**；所有收录数据写入 `workspace.yaml` 指定的用户目录（首次收录时向用户确认默认路径并持久化）。

## 核心文件

| 文件 | 用途 |
|------|------|
| [SKILL.md](./SKILL.md) | Agent 工作流（含步骤 0 工作区配置） |
| [workspace.yaml.example](./workspace.yaml.example) | 工作区配置示例 |
| `workspace.yaml` | **运行时生成**，持久化用户数据目录（gitignore） |
| [kit/workspace.py](./kit/workspace.py) | 路径 propose / init / show / set |
| [kit/](./kit/) | 模板、bootstrap、search、图谱代码 |

## 首次收录流程

```
1. python kit/workspace.py propose     → 建议默认 root
2. AskQuestion 用户确认或修改路径
3. python kit/workspace.py init --root "<路径>" [--with-graph]
   → 写入 workspace.yaml + bootstrap 用户目录
4. 按 SKILL.md 收录，数据写入 workspace.root
```

## 目录职责

| 位置 | 内容 |
|------|------|
| `.cursor/skills/model-intake/` | 模板、kit 代码、workspace.yaml |
| `workspace.root` | `{rawdata_dir}/`、INDEX.md、Graph_Database/ |

## 常用命令

```bash
python kit/workspace.py show
python kit/workspace.py graph-sync --show
python kit/workspace.py graph-sync --apply 从不   # 三选一后持久化
python kit/search.py --entity model --list
```

## 图谱同步偏好（graph_sync）

| preference | 含义 |
|------------|------|
| `ask`（默认） | 每次收录三选一询问 |
| `never` | 从不同步，不再询问 |
| `always` | 每次默认同步，不再询问 |

未明确是否构建图谱时，Agent 按上表决策；详见 SKILL.md §0.5。

---

*最后更新：2026-07-03*
