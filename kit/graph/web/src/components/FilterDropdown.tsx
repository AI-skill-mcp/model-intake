import { useEffect, useId, useRef, useState } from "react";

export interface FilterDropdownItem {
  id: string;
  label: string;
  count?: number | string;
  /** 左侧色块 / 图标 */
  adornment?: React.ReactNode;
}

interface Props {
  /** 触发按钮前缀标签 */
  label: string;
  items: FilterDropdownItem[];
  selected: Set<string>;
  onChange: (next: Set<string>) => void;
  /** 至少保留选中项数（实体 / 领域用） */
  minSelected?: number;
  /** 空集时的按钮摘要文案 */
  emptyLabel?: string;
}

const MIN_HINT = "至少选择一项";

/**
 * 头部多选下拉筛选器。
 * 输入：选项列表、当前选中集、变更回调
 * 输出：点击展开面板，支持全选 / 逐项勾选
 */
export function FilterDropdown({
  label,
  items,
  selected,
  onChange,
  minSelected = 0,
  emptyLabel = "全部",
}: Props) {
  const [open, setOpen] = useState(false);
  const [hint, setHint] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const hintTimerRef = useRef<number | null>(null);
  const panelId = useId();

  const allIds = items.map((i) => i.id);
  const allSelected =
    allIds.length > 0 && allIds.every((id) => selected.has(id));
  const someSelected = selected.size > 0 && !allSelected;

  const summary = (() => {
    if (selected.size === 0) return emptyLabel;
    if (selected.size === 1) {
      const one = items.find((i) => selected.has(i.id));
      return one?.label ?? "1 项";
    }
    if (allSelected) return "全部";
    return `${selected.size} 项`;
  })();

  const flashHint = (message: string = MIN_HINT) => {
    setHint(message);
    if (hintTimerRef.current != null) {
      window.clearTimeout(hintTimerRef.current);
    }
    hintTimerRef.current = window.setTimeout(() => {
      setHint(null);
      hintTimerRef.current = null;
    }, 2200);
  };

  useEffect(() => {
    return () => {
      if (hintTimerRef.current != null) {
        window.clearTimeout(hintTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const applySelection = (next: Set<string>) => {
    if (minSelected > 0 && next.size < minSelected) {
      flashHint();
      return false;
    }
    onChange(next);
    return true;
  };

  const toggleItem = (id: string) => {
    const next = new Set(selected);
    if (next.has(id)) {
      if (minSelected > 0 && next.size <= minSelected) {
        flashHint();
        return;
      }
      next.delete(id);
    } else {
      next.add(id);
    }
    applySelection(next);
  };

  const toggleAll = () => {
    if (allSelected) {
      if (minSelected > 0 && allIds.length > 0) {
        applySelection(new Set([allIds[0]]));
      } else {
        applySelection(new Set());
      }
      return;
    }
    applySelection(new Set(allIds));
  };

  return (
    <div className="filter-dropdown" ref={rootRef}>
      <button
        type="button"
        className={`filter-dropdown-trigger ${open ? "open" : ""}`}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="filter-dropdown-label">{label}</span>
        <span className="filter-dropdown-summary">{summary}</span>
        <span className="filter-dropdown-caret" aria-hidden>
          ▾
        </span>
      </button>

      {open && (
        <div className="filter-dropdown-panel" id={panelId} role="listbox">
          {hint && <div className="filter-dropdown-hint">{hint}</div>}
          <label className="filter-dropdown-row filter-dropdown-all">
            <input
              type="checkbox"
              checked={allSelected}
              ref={(el) => {
                if (el) el.indeterminate = someSelected;
              }}
              onChange={toggleAll}
            />
            <span>全选</span>
          </label>
          <div className="filter-dropdown-divider" />
          <div className="filter-dropdown-list">
            {items.map((item) => (
              <label key={item.id} className="filter-dropdown-row">
                <input
                  type="checkbox"
                  checked={selected.has(item.id)}
                  onChange={() => toggleItem(item.id)}
                />
                {item.adornment}
                <span className="filter-dropdown-item-label">{item.label}</span>
                {item.count != null && (
                  <small className="filter-dropdown-count">{item.count}</small>
                )}
              </label>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
