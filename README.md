# model-intake

在 `foundation-models` 知识库中**收录 Model 或 Tool** 的 Cursor Agent Skill。

触发词示例：收录、纳入、追加收录、添加模型、添加工具、加入知识库。

## 文件结构

| 文件 | 用途 |
|------|------|
| [SKILL.md](./SKILL.md) | 主工作流（8 步），Agent 执行入口 |
| [entity-sync.md](./entity-sync.md) | 关联实体同步细则：Metric / FileType / Dataset |
| [reference.md](./reference.md) | 分类路由、字段清单、索引规范、ETL 映射路径 |
| [examples.md](./examples.md) | 收录示例（含实体扩展与数据集待确认场景） |

## 工作流概览

```
1. 查重与定位
2. 信息调研（官方来源，禁止编造）
3. 确定路径与 model_id / tool_id
4. 撰写主条目
5. 关联实体同步 ← 必做
   ├─ Metric（task_coverage / benchmark）
   ├─ FileType（input_format / output_format）
   └─ Dataset（training_data，须验证 url + paper_doi）
6. 更新 INDEX 与 mappings
7. ETL 校验（make etl-local）
8. 验收检查
```

## 产出路径

| 类型 | 路径 |
|------|------|
| Model | `bioinformatics/model/<subcat>/<id>.md` |
| Tool | `bioinformatics/tools/<id>.md` |
| Metric | `bioinformatics/metrics/<id>.md` |
| FileType | `bioinformatics/formats/<id>.md` |
| Dataset | `bioinformatics/datasets/<id>.md` |

## ETL 映射（收录后须同步）

| 实体 | 文件 |
|------|------|
| Metric | `Graph_Database/mappings/metrics.yaml` |
| Dataset | `Graph_Database/mappings/datasets.yaml` |
| FileType | `Graph_Database/etl/normalize.py` → `_FORMAT_KEYWORDS` |

## 实体处理策略

| 实体 | 缺失时 | 无法验证时 |
|------|--------|------------|
| Metric | 自动新建词条 + 更新 aliases | 需有定义来源 |
| FileType | 自动新建词条 + 扩展关键词 | `infer_file_types()` 验证 |
| Dataset | 验证通过后入库 | **AskQuestion 向用户确认**，禁止静默添加 |

## 相关文档

- 关系规则：`Graph_Database/doc/10-relationship-rules.md`
- 模型模板：`meta/MODEL-RECORD-TEMPLATE.md`
- 指标模板：`meta/METRIC-RECORD-TEMPLATE.md`
- 格式模板：`meta/FORMAT-RECORD-TEMPLATE.md`
- 数据集模板：`meta/DATASET-RECORD-TEMPLATE.md`

---

*最后更新：2026-07-03*
