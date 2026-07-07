/** 实体类型配色（边框 / 实体优先模式下的填充） */

export const NODE_TYPE_COLORS: Record<
  string,
  { bg: string; border: string; label: string }
> = {
  Model: { bg: "#4f46e5", border: "#818cf8", label: "模型" },
  Tool: { bg: "#64748b", border: "#94a3b8", label: "工具" },
  Category: { bg: "#0891b2", border: "#22d3ee", label: "领域" },
  Task: { bg: "#059669", border: "#34d399", label: "任务" },
  FileType: { bg: "#d97706", border: "#fbbf24", label: "文件格式" },
  Dataset: { bg: "#2563eb", border: "#60a5fa", label: "数据集" },
  Paper: { bg: "#ca8a04", border: "#facc15", label: "论文" },
  Organization: { bg: "#7c3aed", border: "#a78bfa", label: "组织" },
  License: { bg: "#be185d", border: "#f472b6", label: "许可" },
  Modality: { bg: "#0d9488", border: "#2dd4bf", label: "模态" },
  Framework: { bg: "#4338ca", border: "#818cf8", label: "框架" },
  Repository: { bg: "#475569", border: "#94a3b8", label: "托管" },
  Benchmark: { bg: "#c026d3", border: "#e879f9", label: "评测" },
  Metric: { bg: "#ea580c", border: "#fb923c", label: "指标" },
  default: { bg: "#6b7280", border: "#9ca3af", label: "其他" },
};

/** 领域元数据：高对比色相，避免多个蓝色系混淆 */
export const CATEGORY_META: Record<string, { color: string; label: string }> = {
  protein: { color: "#2563EB", label: "蛋白" },
  enzyme: { color: "#059669", label: "酶" },
  rna: { color: "#DB2777", label: "RNA" },
  genome: { color: "#7C3AED", label: "基因组" },
  interaction: { color: "#D97706", label: "相互作用" },
  expression: { color: "#0891B2", label: "表达" },
  function: { color: "#EA580C", label: "功能" },
  ptm: { color: "#CA8A04", label: "PTM" },
  cellular: { color: "#0D9488", label: "细胞" },
  "single-cell": { color: "#9333EA", label: "单细胞" },
  "multi-modal": { color: "#DC2626", label: "多模态" },
};

/** @deprecated 使用 CATEGORY_META */
export const CATEGORY_COLORS: Record<string, string> = Object.fromEntries(
  Object.entries(CATEGORY_META).map(([k, v]) => [k, v.color])
);

export function colorForNodeType(nodeType: string): { bg: string; border: string; label: string } {
  return NODE_TYPE_COLORS[nodeType] ?? NODE_TYPE_COLORS.default;
}

export function colorForCategory(categoryId: string | undefined): string {
  if (!categoryId) return NODE_TYPE_COLORS.default.bg;
  return CATEGORY_META[categoryId]?.color ?? NODE_TYPE_COLORS.default.bg;
}

export function labelForCategory(categoryId: string | undefined): string {
  if (!categoryId) return "未分类";
  return CATEGORY_META[categoryId]?.label ?? categoryId;
}

export function listCategoryMeta(): { id: string; color: string; label: string }[] {
  return Object.entries(CATEGORY_META).map(([id, meta]) => ({
    id,
    color: meta.color,
    label: meta.label,
  }));
}
