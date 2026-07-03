# FASTA

FASTA（FASTA format）是生物序列最常用的纯文本交换格式，每条记录由描述行（以 `>` 开头）与一条或多行序列字符组成。在本知识库中，绝大多数蛋白/RNA/DNA 语言模型与结构预测工具的**序列输入**均支持或要求 FASTA；图谱中对应 `FileType` 节点 `fasta`，关系为模型的 `ACCEPTS` 或 `PRODUCES`。

**典型扩展名**：`.fa`, `.fasta`, `.fna`, `.faa`  
**编码**：文本  
**常见角色**：模型输入、流水线中间交换格式

---

## 基本信息

| 字段 | 值 |
|------|-----|
| `format_id` | fasta |
| `name` | FASTA |
| `typical_extension` | .fa, .fasta, .fna, .faa |
| `encoding` | text |
| `mime_type` | text/x-fasta（常用，非 IANA 强制） |

## 结构说明

| 部分 | 规则 |
|------|------|
| 描述行 | 以 `>` 开头；第一个空白前为 ID，其后为可选描述 |
| 序列行 | 仅含合法字母（蛋白 20 字母或 IUPAC 核酸码）；可折行 |
| 多记录 | 多个 `>` 块顺序拼接 |

**规范参考**：NCBI / INSDC 序列格式惯例

## 约束

| 约束 | 说明 |
|------|------|
| 字符集 | 蛋白：ACDEFGHIKLMNPQRSTVWY 及扩展码；核酸：ATCGN 等 |
| 长度 | 取决于下游模型（如 ESM 有最大长度） |
| 编码 | UTF-8 纯文本；避免 Windows 特殊控制符 |

## 最小示例

```fasta
>sp|P69905|HBA_HUMAN Hemoglobin subunit alpha
MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHLPAEFTPAVHASLDKFLASVSTVLTSKYR
```

## 常用工具

| 工具 | 用途 |
|------|------|
| BioPython `SeqIO` | 读写、校验 |
| seqkit | 统计、去重、格式转换 |
| EMBOSS / samtools faidx | 索引大 FASTA |

## 图谱关联

| 角色 | 说明 |
|------|------|
| `ACCEPTS` | 序列嵌入、功能预测、酶动力学等模型的标准输入 |
| `PRODUCES` | 设计/优化类模型输出突变序列 |
| `related_formats` | 结构预测输出常为 PDB/mmCIF，输入常为 FASTA |

## 备注

- 与 **GenBank flat file** 不同，FASTA 不含特征注释  
- `python_api` 格式表示不经由文件而直接传字符串/API，语义上可视为 FASTA 记录的内存形态

---

*条目路径：`bioinformatics/formats/fasta.md` | 最后更新：2026-07-02*
