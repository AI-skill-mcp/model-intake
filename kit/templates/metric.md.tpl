# [指标名称]

[100–200 字：衡量什么、在模型选型中为何重要、与相近指标的区别]

**适用领域**：…
**典型单位**：…
**优化方向**：数值越大越好 / 越小越好 / 视任务而定

> 缩写与公式按 LaTeX 体例；段末注释说明非显然符号。

---

## 核心标识

| 字段 | 值 |
|------|-----|
| `metric_id` | `<小写连字符，与 metrics.yaml 一致>` |
| `name` | |
| `label` | （可选）UI 显示名 |
| `aliases` | 别名1, 别名2 |

## 定义与公式

| 字段 | 值 |
|------|-----|
| `definition` | |
| `quantity_kind` | |
| `formula` | （可选 LaTeX） |

### 与相近指标

| 指标 | 关系 |
|------|------|
| | |

## 单位与数值范围

| 字段 | 值 |
|------|-----|
| `unit` | |
| `typical_range` | （可选） |
| `log_scale` | true / false |
| `higher_is_better` | true / false |
| `unit_conversions` | （可选） |

## 实验测定（可选）

| 方法 | 说明 |
|------|------|
| | |

**实验条件**：pH、温度、底物饱和性等报告规范。

## 领域与模型关联

| 字段 | 值 |
|------|-----|
| `domains` | [enzyme, protein, …] |
| `related_metrics` | [km, ki, …] |
| `models_measuring` | [model_id1]（可与 ETL / metrics.yaml 同步） |
| `typical_benchmarks` | |

## 引用与备注

- 定义来源（教材、综述、数据库）：
- 备注（歧义、单位换算、与 ML 损失函数区别）：

---

## 填写检查清单

**必填**：metric_id, name, definition, quantity_kind, unit, domains

**推荐**：aliases, typical_range, higher_is_better, 与相近指标对比表

**可选**：formula, models_measuring, measurement_methods

*最后更新：{{date}} | 结构参考：meta/METRIC-RECORD-FULL.md*
