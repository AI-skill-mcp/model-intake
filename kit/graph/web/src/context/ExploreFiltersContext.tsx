import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { GraphExport } from "../types/graph";
import {
  buildExploreElements,
  getNodeByRef,
  getNodeCategoryId,
  parseNodeRef,
} from "../data/loadGraph";
import { DEFAULT_EDGE_TYPES } from "../utils/edgeColors";

interface ExploreFiltersContextValue {
  graph: GraphExport;
  entityTypes: Set<string>;
  selectedCategories: Set<string>;
  edgeTypes: Set<string>;
  setEntityTypes: (next: Set<string>) => void;
  setSelectedCategories: (next: Set<string>) => void;
  setEdgeTypes: (next: Set<string>) => void;
  elements: ReturnType<typeof buildExploreElements>;
  clearNodeSelection: () => void;
  focusedNodeId: string | null;
  selectedNodeRef: string | null;
  setFocusedNode: (nodeId: string | null) => void;
  setSelectedNode: (nodeRef: string | null) => void;
  focusNodeFromSearch: (nodeRef: string) => void;
}

const ExploreFiltersContext = createContext<ExploreFiltersContextValue | null>(null);

/** 探索页筛选与节点选中状态 Provider */
export function ExploreFilterProvider({
  graph,
  children,
}: {
  graph: GraphExport;
  children: ReactNode;
}) {
  const [entityTypes, setEntityTypesRaw] = useState<Set<string>>(new Set(["Model"]));
  const [selectedCategories, setSelectedCategoriesRaw] = useState<Set<string>>(
    new Set(["protein"])
  );
  const [edgeTypes, setEdgeTypesRaw] = useState<Set<string>>(new Set(DEFAULT_EDGE_TYPES));
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [selectedNodeRef, setSelectedNodeRef] = useState<string | null>(null);
  const [pendingFocusRef, setPendingFocusRef] = useState<string | null>(null);
  const [forcedVisibleRefs, setForcedVisibleRefs] = useState<Set<string>>(new Set());

  const clearNodeSelection = useCallback(() => {
    setFocusedNodeId(null);
    setSelectedNodeRef(null);
  }, []);

  const setEntityTypes = useCallback(
    (next: Set<string>) => {
      if (next.size === 0) return;
      setEntityTypesRaw(next);
      clearNodeSelection();
    },
    [clearNodeSelection]
  );

  const setSelectedCategories = useCallback(
    (next: Set<string>) => {
      if (next.size === 0) return;
      setSelectedCategoriesRaw(next);
      clearNodeSelection();
    },
    [clearNodeSelection]
  );

  const setEdgeTypes = useCallback((next: Set<string>) => {
    setEdgeTypesRaw(next);
    setFocusedNodeId(null);
  }, []);

  const elements = useMemo(
    () =>
      buildExploreElements(graph, {
        entityTypes,
        categories: selectedCategories,
        edgeTypes,
        showCategoryTag: selectedCategories.size > 1,
        forcedVisibleRefs,
      }),
    [graph, entityTypes, selectedCategories, edgeTypes, forcedVisibleRefs]
  );

  const focusNodeFromSearch = useCallback(
    (nodeRef: string) => {
      const node = getNodeByRef(graph, nodeRef);
      if (!node) return;

      const { nodeType, id } = parseNodeRef(nodeRef);

      setEntityTypesRaw((prev) => {
        if (prev.has(nodeType)) return prev;
        return new Set([...prev, nodeType]);
      });

      const catId =
        getNodeCategoryId(graph, nodeType, id) ??
        (node.node_type === "Metric" && node.domains?.[0]) ??
        undefined;
      if (catId) {
        setSelectedCategoriesRaw((prev) => {
          if (prev.has(catId)) return prev;
          return new Set([...prev, catId]);
        });
      }

      setForcedVisibleRefs((prev) => {
        if (prev.has(nodeRef)) return prev;
        return new Set([...prev, nodeRef]);
      });
      setPendingFocusRef(nodeRef);
    },
    [graph]
  );

  useEffect(() => {
    if (!pendingFocusRef) return;
    const visible = elements.nodes.some((n) => n.data.id === pendingFocusRef);
    if (!visible) return;

    setFocusedNodeId(pendingFocusRef);
    setSelectedNodeRef(pendingFocusRef);
    setPendingFocusRef(null);
  }, [pendingFocusRef, elements]);

  const value = useMemo(
    () => ({
      graph,
      entityTypes,
      selectedCategories,
      edgeTypes,
      setEntityTypes,
      setSelectedCategories,
      setEdgeTypes,
      elements,
      clearNodeSelection,
      focusedNodeId,
      selectedNodeRef,
      setFocusedNode: setFocusedNodeId,
      setSelectedNode: setSelectedNodeRef,
      focusNodeFromSearch,
    }),
    [
      graph,
      entityTypes,
      selectedCategories,
      edgeTypes,
      setEntityTypes,
      setSelectedCategories,
      setEdgeTypes,
      elements,
      clearNodeSelection,
      focusedNodeId,
      selectedNodeRef,
      focusNodeFromSearch,
    ]
  );

  return (
    <ExploreFiltersContext.Provider value={value}>
      {children}
    </ExploreFiltersContext.Provider>
  );
}

export function useExploreFilters(): ExploreFiltersContextValue {
  const ctx = useContext(ExploreFiltersContext);
  if (!ctx) {
    throw new Error("useExploreFilters 须在 ExploreFilterProvider 内使用");
  }
  return ctx;
}

export function useExploreFiltersOptional(): ExploreFiltersContextValue | null {
  return useContext(ExploreFiltersContext);
}
