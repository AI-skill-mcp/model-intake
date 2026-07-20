import type { GraphEdge, GraphExport, GraphNode, ModelNode } from "../types/graph";
import { modelDisplayName } from "../utils/displayName";
import { HIDDEN_EDGE_TYPES, HIDDEN_NODE_TYPES, edgeLabel, orientEdgeForFlow } from "../utils/edgeColors";
import { labelForCategory } from "../utils/entityColors";

let cache: GraphExport | null = null;

/**
 * 加载 graph_export.json（运行时 fetch，避免打包巨大 JSON）
 */
export async function loadGraph(): Promise<GraphExport> {
  if (cache) return cache;
  const res = await fetch("/data/graph_export.json");
  if (!res.ok) {
    throw new Error("无法加载 graph_export.json，请先运行 make etl-local");
  }
  cache = (await res.json()) as GraphExport;
  return cache;
}

/** 获取语料库内模型（排除外部桩节点） */
export function getCorpusModels(graph: GraphExport): ModelNode[] {
  return graph.nodes.filter(
    (n): n is ModelNode =>
      n.node_type === "Model" && n.in_corpus !== false && !!n.model_id
  );
}

export function getModelById(graph: GraphExport, modelId: string): ModelNode | undefined {
  return graph.nodes.find(
    (n): n is ModelNode => n.node_type === "Model" && n.model_id === modelId
  );
}

/** 解析 Cytoscape 节点 ID（如 Model:esm2） */
export function parseNodeRef(ref: string): { nodeType: string; id: string } {
  const [nodeType, ...parts] = ref.split(":");
  return { nodeType, id: parts.join(":") };
}

/** 按图谱引用查找任意节点 */
export function getNodeByRef(graph: GraphExport, ref: string): GraphNode | undefined {
  const { nodeType, id } = parseNodeRef(ref);
  return findNodeByRef(graph, nodeType, id);
}

/** 与实体相连的语料库内模型（含关系类型） */
export function getLinkedModels(
  graph: GraphExport,
  nodeType: string,
  entityId: string
): { edgeType: string; modelId: string; name: string }[] {
  const seen = new Set<string>();
  const result: { edgeType: string; modelId: string; name: string }[] = [];

  for (const e of graph.edges) {
    let modelId: string | null = null;
    if (e.from.node_type === "Model" && e.to.node_type === nodeType && e.to.id === entityId) {
      modelId = e.from.id;
    } else if (e.to.node_type === "Model" && e.from.node_type === nodeType && e.from.id === entityId) {
      modelId = e.to.id;
    }
    if (!modelId) continue;

    const key = `${e.type}:${modelId}`;
    if (seen.has(key)) continue;
    seen.add(key);

    const m = getModelById(graph, modelId);
    if (m?.in_corpus === false) continue;
    result.push({
      edgeType: e.type,
      modelId,
      name: modelDisplayName(m ?? { name: modelId, model_id: modelId }),
    });
  }

  return result.sort((a, b) => a.name.localeCompare(b.name));
}

/** 获取模型所属 Category ID */
export function getModelCategoryId(graph: GraphExport, modelId: string): string | undefined {
  const edge = graph.edges.find(
    (e) => e.type === "BELONGS_TO" && e.from.id === modelId && e.to.node_type === "Category"
  );
  return edge?.to.id;
}

/** 数据集所属领域（来自 by_category_dataset 或 TRAINED_ON 反查） */
export function getDatasetCategoryId(graph: GraphExport, datasetId: string): string | undefined {
  for (const [catId, dsIds] of Object.entries(graph.indexes.by_category_dataset ?? {})) {
    if (dsIds.includes(datasetId)) return catId;
  }
  return voteCategoryFromLinkedModels(graph, "Dataset", datasetId);
}

/**
 * 为任意节点推断领域：邻接 Model 投票，或 Dataset 索引反查。
 * 输出：领域 ID；多领域时取票数最高者。
 */
export function getNodeCategoryId(
  graph: GraphExport,
  nodeType: string,
  nodeId: string
): string | undefined {
  if (nodeType === "Model") return getModelCategoryId(graph, nodeId);
  if (nodeType === "Dataset") return getDatasetCategoryId(graph, nodeId);
  return voteCategoryFromLinkedModels(graph, nodeType, nodeId);
}

/** 通过邻接 Model 的 BELONGS_TO 边投票决定领域 */
function voteCategoryFromLinkedModels(
  graph: GraphExport,
  nodeType: string,
  nodeId: string
): string | undefined {
  const votes = new Map<string, number>();
  for (const e of graph.edges) {
    let modelId: string | null = null;
    if (e.from.node_type === "Model" && e.to.node_type === nodeType && e.to.id === nodeId) {
      modelId = e.from.id;
    }
    if (e.to.node_type === "Model" && e.from.node_type === nodeType && e.from.id === nodeId) {
      modelId = e.to.id;
    }
    if (!modelId) continue;
    const cat = getModelCategoryId(graph, modelId);
    if (cat) votes.set(cat, (votes.get(cat) ?? 0) + 1);
  }
  let best: string | undefined;
  let max = 0;
  for (const [cat, n] of votes) {
    if (n > max) {
      max = n;
      best = cat;
    }
  }
  return best;
}

/** 构建 Cytoscape 节点 data（含领域标签） */
function buildCyNodeData(
  graph: GraphExport,
  nodeType: string,
  id: string,
  node: GraphNode,
  options?: { showCategoryTag?: boolean }
): Record<string, string> {
  const data: Record<string, string> = {
    id: nodeRef(nodeType, id),
    label: nodeLabel(node),
    node_type: nodeType,
    entity_id: id,
  };
  if (node.summary) {
    data.summary = node.summary;
  } else if (node.description) {
    data.summary = node.description;
  }
  const catId = getNodeCategoryId(graph, nodeType, id);
  if (catId) {
    data.category_id = catId;
    data.category_label = labelForCategory(catId);
    if (options?.showCategoryTag) {
      data.label = `${data.label}\n〔${data.category_label}〕`;
    }
  }
  if (nodeType === "Model") data.model_id = id;
  return data;
}

export function getNodeId(node: GraphNode): string {
  const map: Record<string, string | undefined> = {
    Model: node.model_id,
    Tool: node.tool_id,
    Category: node.category_id,
    Task: node.task_id,
    Metric: node.metric_id,
    FileType: node.format_id,
    Organization: node.org_id,
    Paper: node.paper_id,
    Dataset: node.dataset_id,
    License: node.license_id,
    Modality: node.modality_id,
    Framework: node.framework_id,
    Repository: node.repo_id,
  };
  return map[node.node_type] ?? node.name ?? "unknown";
}

export function getModelsByInput(graph: GraphExport, formatId: string): ModelNode[] {
  const ids = graph.indexes.by_input_format[formatId] ?? [];
  return ids
    .map((id) => getModelById(graph, id))
    .filter((m): m is ModelNode => !!m);
}

/** 物理量相近、选型时应一并展示的指标（如 Kd ↔ pKd） */
const RELATED_METRICS: Record<string, string[]> = {
  kd: ["pkd", "ddG_bind"],
  pkd: ["kd", "ddG_bind"],
  ki: ["pkd"],
  ddG_bind: ["binding_affinity"],
  binding_affinity: ["kd", "pkd", "ddG_bind"],
};

/**
 * 按指标取模型。默认合并 RELATED_METRICS 中的近邻指标，避免筛 Kd 时漏掉只挂了 pKd 的模型。
 * @param includeRelated 是否合并近邻指标（选型页默认 true）
 */
export function getModelsByMetric(
  graph: GraphExport,
  metricId: string,
  includeRelated = true
): ModelNode[] {
  const index = graph.indexes.by_metric ?? {};
  const metricIds = includeRelated
    ? [metricId, ...(RELATED_METRICS[metricId] ?? [])]
    : [metricId];
  const seen = new Set<string>();
  const out: ModelNode[] = [];
  for (const mid of metricIds) {
    for (const id of index[mid] ?? []) {
      if (seen.has(id)) continue;
      const m = getModelById(graph, id);
      if (m) {
        seen.add(id);
        out.push(m);
      }
    }
  }
  return out;
}

/** 按指标取工具（Tool -[:MEASURES]-> Metric），含近邻指标 */
export function getToolsByMetric(
  graph: GraphExport,
  metricId: string,
  includeRelated = true
): { id: string; name: string }[] {
  const index = graph.indexes.by_metric_tool ?? {};
  const metricIds = includeRelated
    ? [metricId, ...(RELATED_METRICS[metricId] ?? [])]
    : [metricId];
  const seen = new Set<string>();
  const out: { id: string; name: string }[] = [];
  for (const mid of metricIds) {
    for (const id of index[mid] ?? []) {
      if (seen.has(id)) continue;
      seen.add(id);
      const node = graph.nodes.find((n) => n.node_type === "Tool" && n.tool_id === id);
      out.push({ id, name: node?.name ?? id });
    }
  }
  return out;
}

/** 按指标取数据集（Dataset -[:LABELS]-> Metric），含近邻指标 */
export function getDatasetsByMetric(
  graph: GraphExport,
  metricId: string,
  includeRelated = true
): { id: string; name: string }[] {
  const index = graph.indexes.by_metric_dataset ?? {};
  const metricIds = includeRelated
    ? Array.from(new Set([metricId, ...(RELATED_METRICS[metricId] ?? [])]))
    : [metricId];
  const seen = new Set<string>();
  const out: { id: string; name: string }[] = [];
  for (const mid of metricIds) {
    for (const id of index[mid] ?? []) {
      if (seen.has(id)) continue;
      seen.add(id);
      const node = graph.nodes.find((n) => n.node_type === "Dataset" && n.dataset_id === id);
      out.push({ id, name: node?.name ?? id });
    }
  }
  return out;
}

/** 按文件格式取数据集（Dataset -[:PROVIDES]-> FileType） */
export function getDatasetsByFormat(
  graph: GraphExport,
  formatId: string
): { id: string; name: string }[] {
  const ids = graph.indexes.by_format_dataset?.[formatId] ?? [];
  return ids.map((id) => {
    const node = graph.nodes.find((n) => n.node_type === "Dataset" && n.dataset_id === id);
    return { id, name: node?.name ?? id };
  });
}

/** @deprecated */
export const getModelsByTask = getModelsByMetric;

export function getModelsByCategory(graph: GraphExport, categoryId: string): ModelNode[] {
  const ids = graph.indexes.by_category[categoryId] ?? [];
  return ids
    .map((id) => getModelById(graph, id))
    .filter((m): m is ModelNode => !!m);
}

export function getModelInputs(graph: GraphExport, modelId: string): string[] {
  return graph.edges
    .filter((e) => e.type === "ACCEPTS" && e.from.id === modelId)
    .map((e) => e.to.id);
}

export function getModelOutputs(graph: GraphExport, modelId: string): string[] {
  return graph.edges
    .filter((e) => e.type === "PRODUCES" && e.from.id === modelId)
    .map((e) => e.to.id);
}

export function getModelMetrics(
  graph: GraphExport,
  modelId: string
): { id: string; name: string; unit?: string }[] {
  return graph.edges
    .filter((e) => e.type === "MEASURES" && e.from.id === modelId && e.to.node_type === "Metric")
    .map((e) => {
      const m = graph.nodes.find((n) => n.node_type === "Metric" && n.metric_id === e.to.id);
      return { id: e.to.id, name: m?.name ?? e.to.id, unit: m?.unit };
    });
}

/** @deprecated */
export function getModelTasks(graph: GraphExport, modelId: string): string[] {
  return getModelMetrics(graph, modelId).map((m) => m.name);
}

export function getRelatedModels(
  graph: GraphExport,
  modelId: string,
  relationTypes: string[] = ["INTEGRATES", "BASED_ON", "ALTERNATIVE_TO"]
): { type: string; modelId: string; name: string }[] {
  const result: { type: string; modelId: string; name: string }[] = [];
  for (const e of graph.edges) {
    if (!relationTypes.includes(e.type)) continue;
    if (e.from.node_type === "Model" && e.from.id === modelId && e.to.node_type === "Model") {
      const m = getModelById(graph, e.to.id);
      result.push({ type: e.type, modelId: e.to.id, name: m?.name ?? e.to.id });
    }
    if (e.to.node_type === "Model" && e.to.id === modelId && e.from.node_type === "Model") {
      const m = getModelById(graph, e.from.id);
      result.push({ type: e.type, modelId: e.from.id, name: m?.name ?? e.from.id });
    }
  }
  return result;
}

export function listInputFormats(graph: GraphExport): { id: string; count: number }[] {
  return Object.entries(graph.indexes.by_input_format)
    .map(([id, ids]) => ({ id, count: ids.length }))
    .sort((a, b) => b.count - a.count);
}

export function listMetrics(
  graph: GraphExport
): { id: string; name: string; unit?: string; count: number }[] {
  const index = graph.indexes.by_metric ?? {};
  return Object.entries(index)
    .map(([id, ids]) => {
      const node = graph.nodes.find((n) => n.node_type === "Metric" && n.metric_id === id);
      return { id, name: node?.name ?? id, unit: node?.unit, count: ids.length };
    })
    .filter((m) => m.count > 0)
    .sort((a, b) => b.count - a.count);
}

/** @deprecated */
export const listTasks = listMetrics;

export function listCategories(graph: GraphExport): { id: string; name: string; count: number }[] {
  return Object.entries(graph.indexes.by_category)
    .map(([id, ids]) => {
      const node = graph.nodes.find((n) => n.node_type === "Category" && n.category_id === id);
      return { id, name: node?.name ?? id, count: ids.length };
    })
    .sort((a, b) => b.count - a.count);
}

/** 探索页可选实体类型 */
export const EXPLORE_ENTITY_TYPES = [
  "Model",
  "Dataset",
  "Metric",
  "FileType",
] as const;

export interface ExploreFilters {
  entityTypes: Set<string>;
  /** 空集 = 不限领域；非空 = 所选领域的并集 */
  categories: Set<string>;
  edgeTypes: Set<string>;
  showCategoryTag?: boolean;
  forcedVisibleRefs?: Set<string>;
}

/** 根据所选领域汇总模型 ID；空集返回 null 表示不限 */
function selectedCategoryModelIds(
  graph: GraphExport,
  categories: Set<string>
): Set<string> | null {
  if (categories.size === 0) return null;
  const ids = new Set<string>();
  for (const cat of categories) {
    for (const mid of graph.indexes.by_category[cat] ?? []) {
      ids.add(mid);
    }
  }
  return ids;
}

/** 根据所选领域汇总数据集 ID；空集返回 null 表示不限 */
function selectedCategoryDatasetIds(
  graph: GraphExport,
  categories: Set<string>
): Set<string> | null {
  if (categories.size === 0) return null;
  const ids = new Set<string>();
  for (const cat of categories) {
    for (const ds of graph.indexes.by_category_dataset?.[cat] ?? []) {
      ids.add(ds);
    }
  }
  return ids;
}

function nodeRef(nodeType: string, id: string): string {
  return `${nodeType}:${id}`;
}

/** 构建 Cytoscape 边（按数据流调整箭头方向） */
function buildCyEdgeData(e: GraphEdge): Record<string, string> {
  const { sourceRef, targetRef, directed } = orientEdgeForFlow(
    e.type,
    e.from.node_type,
    e.from.id,
    e.to.node_type,
    e.to.id,
    nodeRef
  );
  const storageKey = `${nodeRef(e.from.node_type, e.from.id)}->${e.type}->${nodeRef(e.to.node_type, e.to.id)}`;
  return {
    id: storageKey,
    source: sourceRef,
    target: targetRef,
    label: edgeLabel(e.type),
    edge_type: e.type,
    directed: directed ? "true" : "false",
  };
}

function parseRef(ref: string): { nodeType: string; id: string } {
  return parseNodeRef(ref);
}

/** 按实体类型 + 领域构建种子节点 */
function buildSeedRefs(graph: GraphExport, filters: ExploreFilters): Set<string> {
  const seeds = new Set<string>();
  const categoryModels = selectedCategoryModelIds(graph, filters.categories);

  if (filters.entityTypes.has("Model")) {
    for (const m of getCorpusModels(graph)) {
      if (categoryModels && !categoryModels.has(m.model_id)) continue;
      seeds.add(nodeRef("Model", m.model_id));
    }
  }

  if (filters.entityTypes.has("Dataset")) {
    const categoryDatasets = selectedCategoryDatasetIds(graph, filters.categories);
    for (const n of graph.nodes) {
      if (n.node_type !== "Dataset" || !n.dataset_id) continue;
      if (categoryDatasets && !categoryDatasets.has(n.dataset_id)) continue;
      seeds.add(nodeRef("Dataset", n.dataset_id));
    }
  }

  for (const etype of filters.entityTypes) {
    if (etype === "Model" || etype === "Dataset") continue;
    if (categoryModels) {
      for (const e of graph.edges) {
        if (HIDDEN_EDGE_TYPES.has(e.type)) continue;
        if (e.from.node_type === "Model" && categoryModels.has(e.from.id) && e.to.node_type === etype) {
          seeds.add(nodeRef(etype, e.to.id));
        }
        if (e.to.node_type === "Model" && categoryModels.has(e.to.id) && e.from.node_type === etype) {
          seeds.add(nodeRef(etype, e.from.id));
        }
      }
    } else {
      for (const n of graph.nodes) {
        if (n.node_type !== etype) continue;
        seeds.add(nodeRef(etype, getNodeId(n)));
      }
    }
  }

  return seeds;
}

/** 从种子经选定关系扩展可见节点 */
function expandVisibleRefs(
  graph: GraphExport,
  seeds: Set<string>,
  edgeTypes: Set<string>
): Set<string> {
  const visible = new Set(seeds);
  let changed = true;

  while (changed) {
    changed = false;
    for (const e of graph.edges) {
      if (HIDDEN_EDGE_TYPES.has(e.type) || !edgeTypes.has(e.type)) continue;
      if (HIDDEN_NODE_TYPES.has(e.from.node_type) || HIDDEN_NODE_TYPES.has(e.to.node_type)) continue;

      const fromRef = nodeRef(e.from.node_type, e.from.id);
      const toRef = nodeRef(e.to.node_type, e.to.id);
      if (!visible.has(fromRef) && !visible.has(toRef)) continue;

      for (const ref of [fromRef, toRef]) {
        const { nodeType } = parseRef(ref);
        if (HIDDEN_NODE_TYPES.has(nodeType)) continue;
        if (!visible.has(ref)) {
          visible.add(ref);
          changed = true;
        }
      }
    }
  }

  return visible;
}

/** 构建探索页 Cytoscape 元素 */
export function buildExploreElements(
  graph: GraphExport,
  filters: ExploreFilters
): { nodes: { data: Record<string, string> }[]; edges: { data: Record<string, string> }[] } {
  const seeds = buildSeedRefs(graph, filters);
  const visible = expandVisibleRefs(graph, seeds, filters.edgeTypes);

  for (const ref of filters.forcedVisibleRefs ?? []) {
    visible.add(ref);
  }

  const cyNodes: { data: Record<string, string> }[] = [];
  for (const ref of visible) {
    const { nodeType, id } = parseRef(ref);
    const node = findNodeByRef(graph, nodeType, id);
    if (!node) continue;

    const data = buildCyNodeData(graph, nodeType, id, node, {
      showCategoryTag: filters.showCategoryTag,
    });
    cyNodes.push({ data });
  }

  const nodeIds = new Set(visible);
  const cyEdges: { data: Record<string, string> }[] = [];
  const edgeSeen = new Set<string>();

  for (const e of graph.edges) {
    if (HIDDEN_EDGE_TYPES.has(e.type) || !filters.edgeTypes.has(e.type)) continue;
    const fromRef = nodeRef(e.from.node_type, e.from.id);
    const toRef = nodeRef(e.to.node_type, e.to.id);
    if (!nodeIds.has(fromRef) || !nodeIds.has(toRef)) continue;

    const key = `${fromRef}->${e.type}->${toRef}`;
    if (edgeSeen.has(key)) continue;
    edgeSeen.add(key);

    cyEdges.push({ data: buildCyEdgeData(e) });
  }

  return { nodes: cyNodes, edges: cyEdges };
}

/** 统计各实体类型数量（可按领域过滤） */
export function countEntitiesByType(
  graph: GraphExport,
  categories?: Set<string>
): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const t of EXPLORE_ENTITY_TYPES) counts[t] = 0;

  const filters: ExploreFilters = {
    entityTypes: new Set(EXPLORE_ENTITY_TYPES),
    categories: categories ?? new Set(),
    edgeTypes: new Set(),
  };
  const seeds = buildSeedRefs(graph, filters);
  for (const ref of seeds) {
    const { nodeType } = parseRef(ref);
    counts[nodeType] = (counts[nodeType] ?? 0) + 1;
  }
  return counts;
}

/** 构建子图元素（Cytoscape）：从中心模型向外扩展，包含各类型邻居节点 */
export function buildSubgraphElements(
  graph: GraphExport,
  centerModelId: string,
  depth = 1
): { nodes: { data: Record<string, string> }[]; edges: { data: Record<string, string> }[] } {
  const centerRef = `Model:${centerModelId}`;
  const visited = new Set<string>([centerRef]);
  let frontier = new Set<string>([centerRef]);
  const selectedEdges: typeof graph.edges = [];

  for (let d = 0; d < depth; d++) {
    const nextFrontier = new Set<string>();
    for (const e of graph.edges) {
      if (HIDDEN_EDGE_TYPES.has(e.type)) continue;
      const fromRef = `${e.from.node_type}:${e.from.id}`;
      const toRef = `${e.to.node_type}:${e.to.id}`;
      if (HIDDEN_NODE_TYPES.has(e.from.node_type) || HIDDEN_NODE_TYPES.has(e.to.node_type)) continue;
      if (!frontier.has(fromRef) && !frontier.has(toRef)) continue;

      selectedEdges.push(e);
      for (const ref of [fromRef, toRef]) {
        if (!visited.has(ref)) {
          visited.add(ref);
          nextFrontier.add(ref);
        }
      }
    }
    frontier = nextFrontier;
    if (frontier.size === 0) break;
  }

  const cyNodes: { data: Record<string, string> }[] = [];
  const cyEdges: { data: Record<string, string> }[] = [];

  for (const ref of visited) {
    const [nodeType, ...idParts] = ref.split(":");
    const nodeId = idParts.join(":");
    if (HIDDEN_NODE_TYPES.has(nodeType)) continue;
    const node = findNodeByRef(graph, nodeType, nodeId);
    if (!node) continue;

    cyNodes.push({
      data: buildCyNodeData(graph, nodeType, nodeId, node, { showCategoryTag: true }),
    });
  }

  const edgeSeen = new Set<string>();
  for (const e of selectedEdges) {
    if (HIDDEN_EDGE_TYPES.has(e.type)) continue;
    const storageKey = `${nodeRef(e.from.node_type, e.from.id)}->${e.type}->${nodeRef(e.to.node_type, e.to.id)}`;
    if (edgeSeen.has(storageKey)) continue;
    edgeSeen.add(storageKey);
    cyEdges.push({ data: buildCyEdgeData(e) });
  }

  return { nodes: cyNodes, edges: cyEdges };
}

const NODE_ID_FIELDS: Record<string, string> = {
  Model: "model_id",
  Tool: "tool_id",
  Category: "category_id",
  Task: "task_id",
  Metric: "metric_id",
  FileType: "format_id",
  Organization: "org_id",
  Paper: "paper_id",
  Dataset: "dataset_id",
  License: "license_id",
  Modality: "modality_id",
  Framework: "framework_id",
  Repository: "repo_id",
};

/** 按类型与 ID 查找节点 */
function findNodeByRef(graph: GraphExport, nodeType: string, id: string): GraphNode | undefined {
  const field = NODE_ID_FIELDS[nodeType];
  if (!field) return undefined;
  return graph.nodes.find((n) => {
    if (n.node_type !== nodeType) return false;
    const value = (n as unknown as Record<string, string | undefined>)[field];
    return value === id;
  });
}

/** 节点在图中的显示标签 */
function nodeLabel(node: GraphNode): string {
  if (node.node_type === "Model" && node.model_id) {
    return modelDisplayName({
      name: node.name ?? node.model_id,
      model_id: node.model_id,
      display_name: node.display_name,
    });
  }
  const name = node.name ?? "";
  if (name.length > 40) return `${name.slice(0, 37).trimEnd()}...`;
  return name || node.dataset_id || node.metric_id || node.task_id || node.format_id || node.node_type;
}
