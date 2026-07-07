import { useCallback, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import { GraphCanvas } from "../components/GraphCanvas";
import { EntityDrawer } from "../components/EntityDrawer";
import { EntityLegend } from "../components/EntityLegend";
import { EdgeLegend } from "../components/EdgeLegend";
import { useExploreFilters } from "../context/ExploreFiltersContext";
import { listCategories } from "../data/loadGraph";
import { colorForCategory, labelForCategory } from "../utils/entityColors";

/** 探索页：图谱 + 侧边实体属性抽屉 */
export function ExplorePage() {
  const {
    graph,
    elements,
    focusedNodeId,
    selectedNodeRef,
    edgeTypes,
    setFocusedNode,
    setSelectedNode,
    setEdgeTypes,
    clearNodeSelection,
    focusNodeFromSearch,
  } = useExploreFilters();

  const [searchParams, setSearchParams] = useSearchParams();
  const focusParam = searchParams.get("focus");

  useEffect(() => {
    if (!focusParam) return;
    focusNodeFromSearch(focusParam);
    const next = new URLSearchParams(searchParams);
    next.delete("focus");
    setSearchParams(next, { replace: true });
  }, [focusParam, focusNodeFromSearch, searchParams, setSearchParams]);

  const handleEdgeToggle = useCallback(
    (edgeType: string) => {
      const next = new Set(edgeTypes);
      if (next.has(edgeType)) {
        next.delete(edgeType);
      } else {
        next.add(edgeType);
      }
      setEdgeTypes(next);
    },
    [edgeTypes, setEdgeTypes]
  );

  const categoryList = useMemo(() => listCategories(graph), [graph]);

  return (
    <div className="page explore-page">
      <aside className="sidebar">
        {/* 图例区域 */}
        <details className="legend-section" open>
          <summary className="legend-section-title">图例说明</summary>

          <div className="legend-group">
            <p className="legend-group-label">实体类型</p>
            <EntityLegend />
          </div>

          <div className="legend-group">
            <p className="legend-group-label">领域色彩</p>
            <div className="category-legend-grid">
              {categoryList.map((c) => (
                <span key={c.id} className="legend-item">
                  <span
                    className="legend-swatch"
                    style={{ background: colorForCategory(c.id) }}
                  />
                  {labelForCategory(c.id)}
                </span>
              ))}
            </div>
          </div>

          <div className="legend-group">
            <EdgeLegend selected={edgeTypes} onToggle={handleEdgeToggle} />
          </div>
        </details>

        <div className="sidebar-divider" />

        <h2>实体详情</h2>
        <p className="hint">
          点击节点聚焦并查看属性 · {elements.nodes.length} 节点 · {elements.edges.length} 边
        </p>

        <EntityDrawer
          graph={graph}
          nodeRef={selectedNodeRef}
          onClearFocus={clearNodeSelection}
        />

        {!selectedNodeRef && (
          <p className="muted explore-empty-hint">在右侧图谱中点击任意节点</p>
        )}
      </aside>

      <main className="graph-area">
        <GraphCanvas
          elements={elements}
          height="calc(100vh - 56px)"
          focusedNodeId={focusedNodeId}
          onNodeClick={(nodeId) => {
            setFocusedNode(nodeId);
            setSelectedNode(nodeId);
          }}
        />
      </main>
    </div>
  );
}
