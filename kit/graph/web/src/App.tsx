import { useEffect, useState } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";
import { ExploreFiltersNav } from "./components/ExploreFiltersNav";
import { SearchPanel } from "./components/SearchPanel";
import { ExplorePage } from "./pages/ExplorePage";
import { SelectPage } from "./pages/SelectPage";
import { ModelDetailPage } from "./pages/ModelDetailPage";
import { ExploreFilterProvider } from "./context/ExploreFiltersContext";
import { useGraphData } from "./hooks/useGraphData";
import "./index.css";

/** 应用根组件 */
export default function App() {
  const { graph, error, loading } = useGraphData();
  const location = useLocation();
  const isExplore = location.pathname === "/explore";
  const [searchOpen, setSearchOpen] = useState(false);

  // Cmd+K 全局快捷键
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  if (loading) {
    return <div className="loading-screen">加载知识图谱...</div>;
  }

  if (error || !graph) {
    return (
      <div className="error-screen">
        <h1>加载失败</h1>
        <p>{error ?? "未知错误"}</p>
        <p>
          请先运行: <code>make etl-local</code>
        </p>
      </div>
    );
  }

  return (
    <ExploreFilterProvider graph={graph}>
      <div className="app">
        <nav className="top-nav">
          <Link to="/" className="brand">
            生物学大模型图谱
          </Link>
          <div className="nav-links">
            <Link to="/explore">探索</Link>
            <Link to="/select">选型</Link>
          </div>
          {isExplore && <ExploreFiltersNav />}
          <button
            type="button"
            className="search-trigger"
            onClick={() => setSearchOpen(true)}
            title="搜索 (Cmd+K)"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <path d="m21 21-4.35-4.35" />
            </svg>
            搜索
            <kbd>⌘K</kbd>
          </button>
          <span className="stats">
            {graph.stats.models} 模型 · {graph.stats.edges} 边
          </span>
        </nav>
        <Routes>
          <Route path="/" element={<SelectPage graph={graph} />} />
          <Route path="/explore" element={<ExplorePage />} />
          <Route path="/select" element={<SelectPage graph={graph} />} />
          <Route path="/models/:modelId" element={<ModelDetailPage graph={graph} />} />
        </Routes>
      </div>
      {searchOpen && <SearchPanel graph={graph} isOpen={searchOpen} onClose={() => setSearchOpen(false)} />}
    </ExploreFilterProvider>
  );
}
