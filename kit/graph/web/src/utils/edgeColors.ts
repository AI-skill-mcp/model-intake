/** 关系类型配色（探索图边） */

export const EDGE_TYPE_COLORS: Record<string, { color: string; label: string }> = {
  INTEGRATES: { color: "#8b5cf6", label: "集成" },
  BASED_ON: { color: "#ef4444", label: "基于" },
  ALTERNATIVE_TO: { color: "#f59e0b", label: "替代" },
  SUCCESSOR_OF: { color: "#ec4899", label: "后继" },
  MEASURES: { color: "#10b981", label: "预测指标" },
  ACCEPTS: { color: "#d97706", label: "接受输入" },
  PRODUCES: { color: "#06b6d4", label: "产出格式" },
  TRAINED_ON: { color: "#2563eb", label: "训练数据" },
  REQUIRES: { color: "#a855f7", label: "依赖工具" },
  USES_MODALITY: { color: "#0d9488", label: "使用模态" },
  DEVELOPED_BY: { color: "#7c3aed", label: "开发机构" },
  HOSTED_AT: { color: "#475569", label: "托管" },
  IMPLEMENTED_IN: { color: "#4338ca", label: "实现框架" },
  BELONGS_TO: { color: "#0891b2", label: "所属领域" },
};

/** 探索页默认可选关系 */
export const EXPLORE_EDGE_TYPES = [
  "INTEGRATES",
  "BASED_ON",
  "ALTERNATIVE_TO",
  "SUCCESSOR_OF",
  "MEASURES",
  "ACCEPTS",
  "PRODUCES",
  "TRAINED_ON",
  "REQUIRES",
] as const;

export const DEFAULT_EDGE_TYPES = new Set<string>([
  "INTEGRATES",
  "BASED_ON",
  "ALTERNATIVE_TO",
]);

/** 图中不展示的关系（论文等已内嵌为属性） */
export const HIDDEN_EDGE_TYPES = new Set([
  "DESCRIBED_IN",
  "HAS_LICENSE",
  "INTRODUCES",
  "USES_MODALITY",
  "DEVELOPED_BY",
  "IMPLEMENTED_IN",
  "HOSTED_AT",
]);

/** 图中不展示的节点类型（已内嵌为实体属性） */
export const HIDDEN_NODE_TYPES = new Set([
  "Paper",
  "License",
  "Organization",
  "Modality",
  "Framework",
  "Repository",
]);

/**
 * 可视化时需反转箭头的关系（相对 ETL 存储方向）。
 * ETL 多为「主体 → 客体」语义；下图箭头表示数据/能力/知识的流向。
 */
export const EDGE_REVERSE_FOR_FLOW = new Set([
  "ACCEPTS", // 输入格式 → 模型
  "TRAINED_ON", // 数据集 → 模型
  "BASED_ON", // 基座模型 → 衍生模型
  "INTEGRATES", // 被集成组件 → 集成方
  "REQUIRES", // 工具 → 模型
]);

/** 无方向关系（探索图不显示箭头） */
export const EDGE_UNDIRECTED = new Set(["ALTERNATIVE_TO"]);

export interface OrientedEdgeEndpoints {
  sourceRef: string;
  targetRef: string;
  directed: boolean;
}

/**
 * 按因果/数据流调整 Cytoscape 边的 source/target。
 * 存储语义不变，仅影响可视化箭头方向。
 */
export function orientEdgeForFlow(
  edgeType: string,
  fromType: string,
  fromId: string,
  toType: string,
  toId: string,
  ref: (nodeType: string, id: string) => string
): OrientedEdgeEndpoints {
  const fromRef = ref(fromType, fromId);
  const toRef = ref(toType, toId);

  if (EDGE_UNDIRECTED.has(edgeType)) {
    return { sourceRef: fromRef, targetRef: toRef, directed: false };
  }
  if (EDGE_REVERSE_FOR_FLOW.has(edgeType)) {
    return { sourceRef: toRef, targetRef: fromRef, directed: true };
  }
  // PRODUCES / MEASURES / BELONGS_TO / SUCCESSOR_OF：模型 → 输出/指标/领域/后继
  return { sourceRef: fromRef, targetRef: toRef, directed: true };
}

export function edgeColor(edgeType: string): string {
  return EDGE_TYPE_COLORS[edgeType]?.color ?? "#94a3b8";
}

export function edgeLabel(edgeType: string): string {
  return EDGE_TYPE_COLORS[edgeType]?.label ?? edgeType;
}
