# [格式名称]

[80–150 字：该格式存什么、在生信流水线中的位置、哪些模型输入/输出使用]

**典型扩展名**：`.ext1`, `.ext2`
**编码**：text / binary
**常见角色**：input / output / both

---

## 核心标识

| 字段 | 值 |
|------|-----|
| `format_id` | `<小写，与 format-keywords.yaml 一致>` |
| `name` | |
| `typical_extension` | .fa, .fasta |
| `mime_type` | （可选） |
| `encoding` | text / binary |

## 结构与规范

| 字段 | 值 |
|------|-----|
| `description` | 记录结构与语义 |
| `record_structure` | （可选）header + body 等 |
| `schema_url` | （可选）官方规范链接 |
| `variants` | （可选）常见变体 |

### 约束

| 约束 | 说明 |
|------|------|
| 字符集 | |
| 长度 | |
| 编码 | UTF-8 等 |

## 最小示例

```text
（合法最小示例）
```

## 常用工具（可选）

| 工具 | 用途 |
|------|------|
| BioPython SeqIO | 读写、校验 |

## 图谱关联

| 字段 | 值 |
|------|-----|
| `role` | input / output / both |
| `related_formats` | pdb, mmcif, … |
| `models_using` | [model_id1]（可由 ETL 反查） |

## 备注

- 与 API 内存对象、非文件形态的区分：
- 与相近格式的区别：

---

## 填写检查清单

**必填**：format_id, name, encoding, description, 最小合法示例

**推荐**：typical_extension, constraints, role, common_tools

**可选**：schema_url, models_using

*最后更新：{{date}} | 结构参考：meta/FORMAT-RECORD-FULL.md*
