# 模型收录 — 示例

## 示例 A：RNAbpFlow（Model + 实体同步）

### 用户请求

> 参考项目结构，追加收录 RNAbpFlow 大模型

### Agent 执行摘要

#### 1. 查重
```bash
rg -i "rnabpflow" --glob "*.md"  # 无结果 → 新建
```

#### 2. 调研来源
- GitHub: https://github.com/Bhattacharya-Lab/RNAbpFlow
- 论文: Nature Methods 2026, DOI 10.1038/s41592-026-03128-4
- LICENSE: GPL-3.0
- Checkpoint: Zenodo 10.5281/zenodo.18305861
- 训练数据：论文 Methods — RNAcentral + RNA 3D DB
- I/O：输入 FASTA + 碱基配对 JSON；输出 PDB/mmCIF
- 指标：task_coverage → RNA 3D结构预测、构象集合采样 → 映射 `tm-score`、`plddt`

#### 2b. 论文 PDF
```bash
python .cursor/skills/model-intake/kit/paper_fetch.py fetch \
  --paper-url "https://doi.org/10.1038/s41592-026-03128-4" \
  --entity-id rnabpflow
# → 成功则 bioinformatics/paper/10.1038-s41592-026-03128-4.pdf，条目填 paper_pdf
```

#### 3. 分类决策
- 主任务：RNA 3D 结构生成
- 路径：`bioinformatics/model/rna/rnabpflow.md`
- model_id：`rnabpflow`

#### 4. 主条目产出
- `bioinformatics/model/rna/rnabpflow.md`

#### 5. 关联实体同步

**5a. 指标** — 均已存在，确认 task_coverage 表述：
```yaml
# metrics.yaml 已有
tm-score, plddt
```

**5b. 格式** — FASTA/PDB/mmCIF/JSON 均已存在；验证：
```bash
python -c "from etl.normalize import infer_file_types; \
  print(infer_file_types('FASTA + JSON（碱基配对）')); \
  print(infer_file_types('PDB / mmCIF'))"
# → ['fasta', 'json'], ['pdb', 'mmcif']
```

**5c. 数据集**

| 候选 | 验证 | 动作 |
|------|------|------|
| RNAcentral | url ✓ https://rnacentral.org/；doi ✓ 10.1093/nar/gkx1034 | 已有 `rnacentral.md`，补 alias |
| RNA 3D DB | url ✓；doi ✓ | 已有 `rna3db.md`，补 alias |
| bpRNA（工具非数据集） | — | 收录 Tool `bprna.md`，建 `REQUIRES` 边 |

`datasets.yaml` 新增：
```yaml
  "RNAcentral (~2300万条RNA序列)": rnacentral
  "RNA 3D DB": rna3db
```

#### 6. 索引与 ETL
- `INDEX.md` — RNA（5→6）
- `bioinformatics/model/rna/README.md`
- `make etl-local` → 0 errors；TRAINED_ON 2 条

#### 7. 用户汇报

```
已完成 RNAbpFlow 收录：

- 条目：bioinformatics/model/rna/rnabpflow.md
- 分类：rna / model_id: rnabpflow
- 定位：MSA-free RNA 3D ensemble 生成
- 关联实体：
  - Dataset：rnacentral、rna3db（alias 已补）
  - Metric：tm-score、plddt（已有）
  - Format：fasta、json、pdb、mmcif（已有）
- 索引：INDEX.md、rna/README.md 已更新
- ETL：0 errors
- 待确认：（无）
```

---

## 示例 B：新指标自动扩展

收录酶动力学模型，论文报告 **kcat/Km** 与 **turnover number**：

1. `kcat`、`km` 已在 `metrics.yaml` → 直接使用
2. 发现新指标 **kcat/Km ratio**（催化效率）不在白名单：
   - 创建 `bioinformatics/metrics/kcat-km-ratio.md`
   - 更新 `metrics.yaml`：
     ```yaml
       kcat-km-ratio:
         label: kcat/Km
         unit: M⁻¹·s⁻¹
         aliases:
           - 催化效率
           - kcat/Km
           - kcat/Km ratio
     ```
3. 模型 `task_coverage` 写入 `kcat/Km预测`

---

## 示例 C：新格式自动扩展

模型输出 **dot-bracket** 文本（RNA 二级结构）：

1. `infer_file_types('dot-bracket 文本')` → `[]`（未识别）
2. 创建 `bioinformatics/formats/dot-bracket.md`
3. 更新 `normalize.py`：
   ```python
   ("dot-bracket", "dot-bracket"),
   ("dot bracket", "dot-bracket"),
   ```
4. 验证通过后写入模型 `output_format`

---

## 示例 D：数据集无法验证 — 暂停确认

模型 `training_data` 写「内部湿实验闭环数据，未公开」：

1. 搜索无官方 url / DOI → **验证失败**
2. **不创建** `bioinformatics/datasets/` 词条
3. AskQuestion：
   > 数据集「内部湿实验数据」无法验证官方 url 与 paper_doi。
   > 选项：A) 仅保留 training_data 文本、不建 Dataset 节点
   >       B) 您提供官方链接后重新验证
   >       C) 跳过该训练数据描述
4. 用户选 A → 模型条目保留原文；ETL 预期 warning；不写入 datasets.yaml

---

## 示例 E：Tool 收录（bpRNA）

```
- 条目：bioinformatics/tools/bprna.md
- tool_id: bprna
- I/O：FASTA → JSON + CSV
- task_coverage：碱基配对注释 → 无独立 Metric 节点（描述性任务）
- used_by_models：[rnabpflow]
- ETL：Tool 节点 + REQUIRES 边（若模型声明依赖）
```

---

## 条目开头示例（格式参考）

```markdown
# RNAbpFlow

RNAbpFlow 是 ... [100-300 字概述]

**适用场景**：RNA 3D 结构预测、构象集合采样
**行业应用**：RNA 结构生物学、RNA 药物设计
**核心优势**：无需 MSA、碱基配对条件化、全原子端到端
**定位**：MSA-free RNA 3D 结构生成，可与序列嵌入模型联合使用

---

## 基本信息

| 字段 | 值 |
|------|-----|
| `model_id` | rnabpflow |
| `name` | RNAbpFlow |
| `organization` | Bhattacharya Lab, Oklahoma State University |
| `paper_url` | https://doi.org/10.1038/s41592-026-03128-4 |
| `category` | rna |
| `task_coverage` | [RNA 3D结构预测, 构象集合采样] |
| `input_format` | FASTA + JSON（碱基配对，bpRNA 导出） |
| `output_format` | PDB / mmCIF |
| `license` | GPL-3.0 |
```

完整条目见：`bioinformatics/model/rna/rnabpflow.md`

---

## 更新 vs 新建

**用户说「更新 ESM2 信息」**：
1. 打开 `bioinformatics/model/protein/esm2.md`
2. 仅修改需补充章节；**同步检查** Metric/Format/Dataset 映射是否仍有效
3. INDEX 无需改计数；跑 `make etl-local` 验证

**用户说「收录 ESM2」且已存在**：
- 告知已收录路径，询问是否改为更新模式
