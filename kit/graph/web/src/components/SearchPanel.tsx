import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import type { GraphExport } from "../types/graph";
import { NODE_TYPE_COLORS } from "../utils/entityColors";
import { modelDisplayName } from "../utils/displayName";

interface SearchItem {
  id: string;
  label: string;
  secondary: string;
  nodeType: string;
  category: string;
  /** 点击行为 */
  action: () => void;
}

const ENTITY_LABELS: Record<string, string> = {
  Model: "模型",
  Dataset: "数据集",
  Metric: "指标",
  FileType: "格式",
};

function buildSearchItems(
  graph: GraphExport,
  navigate: (path: string) => void
): SearchItem[] {
  const items: SearchItem[] = [];

  for (const node of graph.nodes) {
    const nt = node.node_type;
    // 只搜索主要实体类型
    if (!["Model", "Dataset", "Metric", "FileType"].includes(nt)) continue;

    const name = nt === "Model" && node.model_id
      ? modelDisplayName({ name: node.name ?? node.model_id, model_id: node.model_id, display_name: node.display_name })
      : (node.name ?? "");

    const id = nt === "Model" ? node.model_id ?? ""
      : nt === "Dataset" ? node.dataset_id ?? ""
      : nt === "Metric" ? node.metric_id ?? ""
      : nt === "FileType" ? node.format_id ?? ""
      : "";

    if (!name && !id) continue;

    items.push({
      id: `${nt}:${id}`,
      label: name || id,
      secondary: id !== name ? id : "",
      nodeType: nt,
      category: ENTITY_LABELS[nt] ?? nt,
      action: () => {
        navigate(`/explore?focus=${encodeURIComponent(`${nt}:${id}`)}`);
      },
    });
  }

  return items;
}

/** 简单模糊匹配评分 */
function fuzzyScore(query: string, text: string): number {
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  if (t === q) return 100;
  if (t.startsWith(q)) return 80;
  if (t.includes(q)) return 60;
  // 首字母匹配
  const initials = t.split(/\s+/).map(w => w[0]).join("");
  if (initials === q) return 40;
  // 字符顺序匹配
  let qi = 0;
  for (let i = 0; i < t.length && qi < q.length; i++) {
    if (t[i] === q[qi]) qi++;
  }
  if (qi === q.length) return 20;
  return 0;
}

interface SearchPanelProps {
  graph: GraphExport;
  isOpen: boolean;
  onClose: () => void;
}

/** 全局搜索命令面板 (Cmd+K 或点击触发) */
export function SearchPanel({ graph, isOpen, onClose }: SearchPanelProps) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const allItems = useMemo(
    () => buildSearchItems(graph, (path) => { navigate(path); onClose(); }),
    [graph, navigate, onClose]
  );

  const results = useMemo(() => {
    if (!query.trim()) return allItems.slice(0, 8);
    const scored = allItems
      .map((item) => {
        const nameScore = fuzzyScore(query, item.label);
        const idScore = fuzzyScore(query, item.secondary);
        const descScore = fuzzyScore(query, item.category);
        return { item, score: Math.max(nameScore, idScore * 0.7, descScore * 0.4) };
      })
      .filter((s) => s.score > 0)
      .sort((a, b) => b.score - a.score);
    return scored.slice(0, 12).map((s) => s.item);
  }, [query, allItems]);

  // Esc 关闭
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  // 自动聚焦
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIdx((i) => Math.min(i + 1, results.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIdx((i) => Math.max(i - 1, 0));
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (results[selectedIdx]) {
          results[selectedIdx].action();
        }
      }
    },
    [results, selectedIdx]
  );

  if (!isOpen) return null;

  return (
    <div className="search-overlay" onClick={onClose}>
      <div className="search-panel" onClick={(e) => e.stopPropagation()}>
        <div className="search-input-wrap">
          <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            ref={inputRef}
            className="search-input"
            type="text"
            placeholder="搜索模型、数据集、指标..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIdx(0);
            }}
            onKeyDown={handleKeyDown}
          />
          <kbd className="search-kbd">Esc</kbd>
        </div>

        {results.length === 0 && query.trim() && (
          <div className="search-empty">无匹配结果</div>
        )}

        <div className="search-results">
          {results.map((item, idx) => {
            const colors = NODE_TYPE_COLORS[item.nodeType] ?? NODE_TYPE_COLORS.default;
            return (
              <button
                key={item.id}
                type="button"
                className={`search-result-item ${idx === selectedIdx ? "selected" : ""}`}
                onClick={() => item.action()}
                onMouseEnter={() => setSelectedIdx(idx)}
              >
                <span
                  className="search-result-badge"
                  style={{ borderColor: colors.border, color: colors.border }}
                >
                  {item.category}
                </span>
                <span className="search-result-label">{item.label}</span>
                {item.secondary && (
                  <span className="search-result-id">{item.secondary}</span>
                )}
              </button>
            );
          })}
        </div>

        <div className="search-footer">
          <span><kbd>↑↓</kbd> 导航</span>
          <span><kbd>↵</kbd> 选择</span>
          <span><kbd>Esc</kbd> 关闭</span>
        </div>
      </div>
    </div>
  );
}
