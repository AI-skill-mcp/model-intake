import { NODE_TYPE_COLORS } from "../utils/entityColors";
import { EXPLORE_ENTITY_TYPES } from "../data/loadGraph";

/** 实体类型图例（边框色 + 形状说明） */
export function EntityLegend() {
  return (
    <div className="entity-legend">
      {EXPLORE_ENTITY_TYPES.map((t) => {
        const c = NODE_TYPE_COLORS[t];
        if (!c) return null;
        return (
          <span key={t} className="legend-item">
            <span
              className="legend-swatch legend-swatch-border"
              style={{ borderColor: c.border }}
            />
            {c.label}
          </span>
        );
      })}
    </div>
  );
}
