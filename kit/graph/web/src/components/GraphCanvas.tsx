import { useCallback, useEffect, useRef, useState } from "react";
import cytoscape, { type StylesheetJsonBlock } from "cytoscape";
// @ts-expect-error cytoscape-fcose 无完整类型
import fcose from "cytoscape-fcose";
import { CATEGORY_META, NODE_TYPE_COLORS } from "../utils/entityColors";
import { edgeColor } from "../utils/edgeColors";

cytoscape.use(fcose);

interface Element {
  nodes: { data: Record<string, string> }[];
  edges: { data: Record<string, string> }[];
}

interface Props {
  elements: Element;
  onNodeClick?: (nodeId: string, nodeType: string, entityId: string) => void;
  focusedNodeId?: string | null;
  height?: string;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  label: string;
  nodeType: string;
  categoryLabel: string;
  summary: string;
}

const ENTITY_SHAPES: Record<string, string> = {
  Model: "round-rectangle",
  Dataset: "barrel",
  Metric: "octagon",
  FileType: "round-hexagon",
  Tool: "diamond",
};

const ENTITY_LABELS: Record<string, string> = {
  Model: "模型",
  Dataset: "数据集",
  Metric: "指标",
  FileType: "格式",
  Tool: "工具",
};

/** 固定编码：填充=领域，边框色+形状=实体类型 */
const NODE_STYLES: StylesheetJsonBlock[] = (() => {
  const base: StylesheetJsonBlock[] = [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-size": "8px",
        color: "#f8fafc",
        "text-outline-width": 1,
        "text-outline-color": "#0f172a",
        "text-wrap": "wrap",
        "text-max-width": "72px",
        width: 52,
        height: 52,
        "background-color": "#374151",
        "border-width": 4,
        "border-color": NODE_TYPE_COLORS.default.border,
      },
    },
    {
      selector: "node.faded",
      style: { opacity: 0.12 },
    },
    {
      selector: "node.focused",
      style: {
        "border-width": 5,
        "border-color": "#f8fafc",
        "z-index": 999,
        opacity: 1,
      },
    },
    {
      selector: "node.neighbor",
      style: { "border-width": 4, opacity: 1 },
    },
    {
      selector: "edge",
      style: {
        width: 1.5,
        "line-color": "#475569",
        "target-arrow-color": "#64748b",
        "target-arrow-shape": "triangle",
        "curve-style": "bezier",
        label: "data(label)",
        "font-size": "7px",
        color: "#94a3b8",
      },
    },
    {
      selector: 'edge[directed = "false"]',
      style: {
        "target-arrow-shape": "none",
        "line-style": "dashed",
      },
    },
    {
      selector: "edge.faded",
      style: { opacity: 0.08 },
    },
    {
      selector: "edge.highlighted",
      style: { width: 2.5, opacity: 1 },
    },
    {
      selector: "node[!category_id]",
      style: {
        "background-color": "#374151",
        "border-style": "dashed",
      },
    },
  ];

  for (const [type, colors] of Object.entries(NODE_TYPE_COLORS)) {
    if (type === "default") continue;
    const shape = ENTITY_SHAPES[type];
    base.push({
      selector: `node[node_type = "${type}"]`,
      style: {
        "border-color": colors.border,
        "border-width": 4,
        width: type === "Model" ? 76 : 52,
        height: type === "Model" ? 40 : 52,
        ...(shape ? { shape: shape as cytoscape.Css.NodeShape } : {}),
      },
    });
  }

  for (const [catId, meta] of Object.entries(CATEGORY_META)) {
    base.push({
      selector: `node[category_id = "${catId}"]`,
      style: { "background-color": meta.color },
    });
  }

  const edgeTypes = [
    "INTEGRATES", "BASED_ON", "ALTERNATIVE_TO", "SUCCESSOR_OF",
    "MEASURES", "ACCEPTS", "PRODUCES", "TRAINED_ON", "BELONGS_TO", "REQUIRES",
  ];
  for (const et of edgeTypes) {
    const c = edgeColor(et);
    base.push({
      selector: `edge[edge_type = "${et}"]`,
      style: {
        "line-color": c,
        "target-arrow-color": c,
        color: c,
      },
    });
  }

  return base;
})();

/** 按节点规模生成 fcose 布局参数 */
function buildFcoseLayout(nodeCount: number): cytoscape.LayoutOptions {
  const scale = Math.min(2.2, 1 + nodeCount / 35);

  return {
    name: "fcose",
    animate: nodeCount < 100,
    animationDuration: 600,
    randomize: true,
    fit: true,
    padding: 56,
    quality: nodeCount <= 80 ? "proof" : "default",
    nodeDimensionsIncludeLabels: nodeCount <= 80,
    nodeSeparation: Math.round(110 * scale),
    nodeRepulsion: () => Math.round(10000 * scale),
    idealEdgeLength: () => Math.round(100 * scale),
    edgeElasticity: () => 0.42,
    nestingFactor: 0.12,
    gravity: 0.18,
    gravityRange: 4.8,
    tilingPaddingVertical: Math.round(36 * scale),
    tilingPaddingHorizontal: Math.round(36 * scale),
    numIter: 3200,
    packComponents: false,
  } as cytoscape.LayoutOptions;
}

/** 集合差异分析 */
interface DiffResult {
  toAdd: { data: Record<string, string> }[];
  toRemove: Set<string>;
  changedNodes: boolean;
  nodeCountBefore: number;
  nodeCountAfter: number;
}

function diffElements(
  prevEls: Element | null,
  nextEls: Element
): DiffResult {
  if (!prevEls) {
    // 首次：全量
    return {
      toAdd: [],
      toRemove: new Set(),
      changedNodes: false,
      nodeCountBefore: 0,
      nodeCountAfter: nextEls.nodes.length,
    };
  }

  const prevNodeIds = new Set(prevEls.nodes.map((n) => n.data.id));
  const nextNodeIds = new Set(nextEls.nodes.map((n) => n.data.id));
  const prevEdgeIds = new Set(prevEls.edges.map((e) => e.data.id));
  const nextEdgeIds = new Set(nextEls.edges.map((e) => e.data.id));

  // 新的节点和边
  const toAdd: { data: Record<string, string> }[] = [
    ...nextEls.nodes.filter((n) => !prevNodeIds.has(n.data.id)),
    ...nextEls.edges.filter((e) => !prevEdgeIds.has(e.data.id)),
  ];

  // 需要移除的元素
  const toRemove = new Set<string>();
  for (const n of prevEls.nodes) {
    if (!nextNodeIds.has(n.data.id)) toRemove.add(n.data.id);
  }
  for (const e of prevEls.edges) {
    if (!nextEdgeIds.has(e.data.id)) toRemove.add(e.data.id);
  }

  // 判断是否超过 50% 节点变化 → 需要全量重布局
  const turnoverRatio =
    Math.abs(nextEls.nodes.length - prevEls.nodes.length) /
    Math.max(prevEls.nodes.length, 1);
  const changedNodes = turnoverRatio > 0.5;

  return {
    toAdd,
    toRemove,
    changedNodes,
    nodeCountBefore: prevEls.nodes.length,
    nodeCountAfter: nextEls.nodes.length,
  };
}

/** Cytoscape 图：增量更新 + 悬停 Tooltip */
export function GraphCanvas({
  elements,
  onNodeClick,
  focusedNodeId,
  height = "100%",
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const onNodeClickRef = useRef(onNodeClick);
  onNodeClickRef.current = onNodeClick;
  const tooltipTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const prevElementsRef = useRef<Element | null>(null);
  const layoutTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsBoundRef = useRef(false);

  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    label: "",
    nodeType: "",
    categoryLabel: "",
    summary: "",
  });

  const hideTooltip = useCallback(() => {
    if (tooltipTimerRef.current) {
      clearTimeout(tooltipTimerRef.current);
      tooltipTimerRef.current = null;
    }
    setTooltip((prev) => (prev.visible ? { ...prev, visible: false } : prev));
  }, []);

  // --- 首次初始化 Cytoscape ---
  useEffect(() => {
    if (!containerRef.current || cyRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...elements.nodes, ...elements.edges],
      style: NODE_STYLES,
      minZoom: 0.15,
      maxZoom: 2.5,
    });

    // 事件绑定（只绑一次）
    cy.on("tap", "node", (evt) => {
      hideTooltip();
      const data = evt.target.data();
      onNodeClickRef.current?.(data.id, data.node_type, data.entity_id ?? data.model_id);
    });

    cy.on("mouseover", "node", (evt) => {
      const data = evt.target.data();
      const nodeType = data.node_type ?? "";
      const catLabel = data.category_label ? ` · ${data.category_label}` : "";
      const summary = data.summary ?? "";
      const shortSummary = summary.length > 100
        ? `${summary.slice(0, summary.indexOf("。", 60) > 0 ? summary.indexOf("。", 60) + 1 : 97).trimEnd()}...`
        : summary;
      const renderedPos = evt.target.renderedPosition();

      tooltipTimerRef.current = setTimeout(() => {
        setTooltip({
          visible: true,
          x: renderedPos.x,
          y: renderedPos.y - 18,
          label: data.label ?? "",
          nodeType,
          categoryLabel: catLabel,
          summary: shortSummary,
        });
      }, 400);
    });

    cy.on("mouseout", "node", () => hideTooltip());
    cy.on("grab", "node", () => hideTooltip());
    cy.on("tap", (evt) => {
      if (evt.target === cy) hideTooltip();
    });

    cyRef.current = cy;
    prevElementsRef.current = elements;
    eventsBoundRef.current = true;

    // 首轮布局
    const layout = cy.layout(buildFcoseLayout(elements.nodes.length));
    layout.one("layoutstop", () => cy.fit(undefined, 56));
    layout.run();

    return () => {
      if (tooltipTimerRef.current) clearTimeout(tooltipTimerRef.current);
      if (layoutTimerRef.current) clearTimeout(layoutTimerRef.current);
      cy.destroy();
      cyRef.current = null;
      prevElementsRef.current = null;
      eventsBoundRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- 增量更新（elements 变化时） ---
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy || !eventsBoundRef.current) return;

    const prev = prevElementsRef.current;
    const diff = diffElements(prev, elements);

    // 如果没有变化，跳过
    if (diff.toAdd.length === 0 && diff.toRemove.size === 0) return;

    cy.batch(() => {
      // 移除废弃元素
      for (const id of diff.toRemove) {
        const el = cy.getElementById(id);
        if (el.length) el.remove();
      }

      // 添加新元素
      if (diff.toAdd.length > 0) {
        cy.add(diff.toAdd.map((el) => ({ group: el.data.source ? "edges" : "nodes", data: el.data })));
      }
    });

    prevElementsRef.current = elements;

    // 防抖布局：大规模变化或节点数翻倍时重布局
    if (layoutTimerRef.current) clearTimeout(layoutTimerRef.current);

    const needFullLayout =
      diff.changedNodes ||
      (prev === null) ||
      (diff.nodeCountAfter > 0 && diff.nodeCountBefore === 0);

    layoutTimerRef.current = setTimeout(() => {
      const c = cyRef.current;
      if (!c) return;
      const layout = c.layout(buildFcoseLayout(c.nodes().length));
      layout.one("layoutstop", () => {
        if (!needFullLayout) c.fit(undefined, 56);
      });
      layout.run();
    }, needFullLayout ? 0 : 300);

    return () => {
      if (layoutTimerRef.current) clearTimeout(layoutTimerRef.current);
    };
  }, [elements]);

  // --- 聚焦节点：高亮邻域并将目标节点居中到视口 ---
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.elements().removeClass("focused neighbor faded highlighted");

    if (!focusedNodeId) return;

    const applyFocus = (): boolean => {
      const node = cy.getElementById(focusedNodeId);
      if (!node.length) return false;

      const hood = node.closedNeighborhood();
      cy.elements().not(hood).addClass("faded");
      node.addClass("focused");
      node.neighborhood("node").addClass("neighbor");
      hood.edges().addClass("highlighted");

      const targetZoom = Math.min(Math.max(cy.zoom(), 1.15), 1.75);
      cy.animate(
        { center: { eles: node }, zoom: targetZoom },
        { duration: 400 }
      );
      return true;
    };

    if (!applyFocus()) {
      const onLayoutStop = () => {
        if (applyFocus()) cy.off("layoutstop", onLayoutStop);
      };
      cy.on("layoutstop", onLayoutStop);
      return () => {
        cy.off("layoutstop", onLayoutStop);
      };
    }
  }, [focusedNodeId, elements]);

  return (
    <div ref={containerRef} className="graph-canvas" style={{ height, position: "relative" }}>
      {tooltip.visible && (
        <div
          className="graph-tooltip"
          style={{
            left: tooltip.x + 8,
            top: tooltip.y,
          }}
        >
          <div className="graph-tooltip-header">
            <span
              className="graph-tooltip-badge"
              style={{ borderColor: NODE_TYPE_COLORS[tooltip.nodeType]?.border ?? "#9ca3af" }}
            >
              {ENTITY_LABELS[tooltip.nodeType] ?? tooltip.nodeType}
            </span>
            {tooltip.categoryLabel && (
              <span className="graph-tooltip-category">{tooltip.categoryLabel}</span>
            )}
          </div>
          <div className="graph-tooltip-name">{tooltip.label}</div>
          {tooltip.summary && (
            <div className="graph-tooltip-summary">{tooltip.summary}</div>
          )}
        </div>
      )}
    </div>
  );
}
