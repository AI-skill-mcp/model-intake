import { EDGE_TYPE_COLORS, EXPLORE_EDGE_TYPES } from "../utils/edgeColors";

/** 关系类型图例（可点击切换） */
interface Props {
  selected: Set<string>;
  onToggle: (edgeType: string) => void;
}

export function EdgeLegend({ selected, onToggle }: Props) {
  return (
    <div className="edge-legend">
      <p className="filter-label">关系类型</p>
      {EXPLORE_EDGE_TYPES.map((t) => {
        const meta = EDGE_TYPE_COLORS[t];
        const active = selected.has(t);
        return (
          <label key={t} className={`edge-filter ${active ? "active" : ""}`}>
            <input
              type="checkbox"
              checked={active}
              onChange={() => onToggle(t)}
            />
            <span className="legend-swatch" style={{ background: meta?.color ?? "#94a3b8" }} />
            <span>{meta?.label ?? t}</span>
          </label>
        );
      })}
    </div>
  );
}
