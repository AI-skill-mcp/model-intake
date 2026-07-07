/**
 * 实体显示名：从完整标题派生短名。
 * 支持冒号、破折号分隔；与 ETL derive_display_name 逻辑对齐。
 */
export function shortDisplayName(
  name: string | undefined,
  fallback = "",
  displayName?: string
): string {
  if (displayName?.trim()) return displayName.trim();
  if (!name?.trim()) return fallback;

  const trimmed = name.trim();
  const separators = [":", "：", " — ", " – ", " —", "—", "–", " - "];
  for (const sep of separators) {
    const idx = trimmed.indexOf(sep);
    if (idx > 0) {
      const short = trimmed.slice(0, idx).trim();
      if (short) return short;
    }
  }
  if (trimmed.length > 45) {
    return `${trimmed.slice(0, 42).trimEnd()}...`;
  }
  return trimmed;
}

/** Model 节点显示名 */
export function modelDisplayName(model: {
  name: string;
  model_id: string;
  display_name?: string;
}): string {
  return shortDisplayName(model.name, model.model_id, model.display_name);
}
