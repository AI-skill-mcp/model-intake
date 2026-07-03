# pLDDT

AlphaFold 系列等结构预测模型输出的 per-residue 置信度分数（predicted LDDT），范围通常 0–100，用于筛选高置信结构域。

**适用领域**：protein, rna  
**典型单位**：0–100  
**优化方向**：数值越大越好

---

## 基本信息

| 字段 | 值 |
|------|-----|
| `metric_id` | plddt |
| `name` | pLDDT |
| `unit` | 0-100 |
| `quantity_kind` | 结构置信度 |
| `higher_is_better` | true |
| `domains` | [protein, rna] |
| `aliases` | pLDDT置信度, pLDDT, 置信度评估, 结构置信度 |
| `definition` | 结构预测模型输出的残基级置信度，反映局部坐标可信度。 |

---

*最后更新：2026-07-03*
