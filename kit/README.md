# model-intake kit

Skill 内置工具包：**仅模板与代码**，不含用户收录数据。

用户数据目录由 Skill 根目录的 `workspace.yaml` 指定（首次收录时用户确认后生成）。

## 组件

| 文件 | 功能 |
|------|------|
| `workspace.py` | 读/写 workspace.yaml，propose 默认路径，禁止写入 Skill 目录 |
| `bootstrap.py` | 在用户 workspace.root 初始化目录结构 |
| `search.py` | 按 workspace.yaml 检索实体 |
| `paper_fetch.py` | 尝试下载论文 PDF 到 `{rawdata_dir}/paper/` |
| `templates/` | Model/Tool/Metric/Format/Dataset 模板（结构对齐 `meta/*-RECORD-FULL.md`） |
| `mappings/` | starter 别名（bootstrap 时复制到用户 Graph_Database/mappings/） |
| `seeds/` | starter 示例词条（仅 bootstrap 时复制到用户 bioinformatics/） |
| `graph/` | 便携 ETL + Web + docker-compose（**完整图谱技能包**） |
| `rules/relationship-rules.md` | 关系、索引、探索页、ETL 数据规则（权威长文） |
| `graph/README.md` | 构建命令、ETL 时机、数据规则摘要 |

## 工作区 CLI

```bash
# 建议默认路径（首次收录前展示给用户）
python workspace.py propose

# 用户确认后：写入 workspace.yaml + bootstrap
python workspace.py init --root ~/kbase-data --with-graph

# embedded：复用 foundation-models
python workspace.py init --root /path/to/foundation-models --mode embedded --with-graph

# 查看 / 修改
python workspace.py show
python workspace.py set --root /new/path
python workspace.py init --from-workspace

# 论文 PDF
python paper_fetch.py ensure-dir
python paper_fetch.py fetch --paper-url "https://doi.org/10.1101/..." --entity-id boltz-2
python paper_fetch.py backfill              # 批量补全已收录 model/tools
python paper_fetch.py backfill --dry-run    # 仅扫描
```

## 禁止事项

- **禁止**在 `.cursor/skills/model-intake/` 下写入收录 md、ETL 产物
- **禁止**将 `workspace.root` 设为 Skill 目录或其子目录
- 仅 `workspace.yaml` 持久化在 Skill 目录

## bootstrap

```bash
python bootstrap.py                    # 从 workspace.yaml 读取 target
python bootstrap.py ~/kbase --with-graph
```

---

*kit version: 1.3 | 2026-07-07 — skills 为图谱唯一事实来源；rule 仅约束本地→kit 回写*
