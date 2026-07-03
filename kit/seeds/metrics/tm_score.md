# TM-score

蛋白质/RNA 三维结构全局相似度指标，取值 0–1，>0.5 通常表示相同折叠。

**适用领域**：protein, rna  
**典型单位**：无量纲（0–1）  
**优化方向**：数值越大越好

---

## 基本信息

| 字段 | 值 |
|------|-----|
| `metric_id` | tm_score |
| `name` | TM-score |
| `unit` | dimensionless |
| `quantity_kind` | 结构相似度 |
| `higher_is_better` | true |
| `domains` | [protein, rna] |
| `aliases` | TM-score, TM score, TMscore, 结构相似度 |
| `definition` | 基于 TM-align 的结构叠合得分，对长度归一化。 |

---

*最后更新：2026-07-03*
