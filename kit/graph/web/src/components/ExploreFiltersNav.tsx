import { useMemo } from "react";
import { FilterDropdown } from "./FilterDropdown";
import { useExploreFiltersOptional } from "../context/ExploreFiltersContext";
import {
  countEntitiesByType,
  EXPLORE_ENTITY_TYPES,
  listCategories,
} from "../data/loadGraph";
import { EDGE_TYPE_COLORS, EXPLORE_EDGE_TYPES } from "../utils/edgeColors";
import { colorForCategory, colorForNodeType, labelForCategory } from "../utils/entityColors";

const ENTITY_LABELS: Record<string, string> = {
  Model: "模型",
  Dataset: "数据集",
  Metric: "指标",
  FileType: "格式",
};

/** 头部导航：实体 / 领域 / 关系 三个多选下拉 */
export function ExploreFiltersNav() {
  const ctx = useExploreFiltersOptional();
  if (!ctx) return null;

  const {
    graph,
    entityTypes,
    selectedCategories,
    edgeTypes,
    setEntityTypes,
    setSelectedCategories,
    setEdgeTypes,
  } = ctx;

  const entityCounts = useMemo(
    () => countEntitiesByType(graph, selectedCategories),
    [graph, selectedCategories]
  );

  const categoryList = useMemo(() => listCategories(graph), [graph]);

  const entityItems = EXPLORE_ENTITY_TYPES.map((t) => ({
    id: t,
    label: ENTITY_LABELS[t] ?? t,
    count: entityCounts[t] ?? 0,
    adornment: (
      <span
        className="swatch swatch-entity"
        style={{ borderColor: colorForNodeType(t).border }}
      />
    ),
  }));

  const categoryItems = categoryList.map((c) => {
    const dsCount = graph.indexes.by_category_dataset?.[c.id]?.length ?? 0;
    return {
      id: c.id,
      label: labelForCategory(c.id),
      count: dsCount > 0 ? `${c.count}/${dsCount}` : c.count,
      adornment: (
        <span
          className="swatch swatch-category"
          style={{ background: colorForCategory(c.id) }}
        />
      ),
    };
  });

  const edgeItems = EXPLORE_EDGE_TYPES.map((t) => {
    const meta = EDGE_TYPE_COLORS[t];
    return {
      id: t,
      label: meta?.label ?? t,
      adornment: (
        <span
          className="legend-swatch filter-dropdown-swatch"
          style={{ background: meta?.color ?? "#94a3b8" }}
        />
      ),
    };
  });

  return (
    <div className="nav-filters">
      <FilterDropdown
        label="实体"
        items={entityItems}
        selected={entityTypes}
        onChange={setEntityTypes}
        minSelected={1}
        emptyLabel="未选"
      />
      <FilterDropdown
        label="领域"
        items={categoryItems}
        selected={selectedCategories}
        onChange={setSelectedCategories}
        minSelected={1}
        emptyLabel="未选"
      />
      <FilterDropdown
        label="关系"
        items={edgeItems}
        selected={edgeTypes}
        onChange={setEdgeTypes}
        emptyLabel="未选"
      />
    </div>
  );
}
