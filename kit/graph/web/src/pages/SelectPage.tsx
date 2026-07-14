import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ModelCard } from "../components/ModelCard";
import type { GraphExport, ModelNode } from "../types/graph";
import {
  getModelsByInput,
  getModelsByMetric,
  getModelsByCategory,
  getModelCategoryId,
  getToolsByMetric,
  listInputFormats,
  listMetrics,
  listCategories,
} from "../data/loadGraph";
import { colorForCategory, labelForCategory } from "../utils/entityColors";

interface Props {
  graph: GraphExport;
}

/** 选型页：输入格式 → 领域 → 指标 → 结果（含侧边筛选） */
export function SelectPage({ graph }: Props) {
  const navigate = useNavigate();
  const formats = listInputFormats(graph);
  const metrics = listMetrics(graph);
  const categories = listCategories(graph);

  const [step, setStep] = useState(1);
  const [formatId, setFormatId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [metricId, setMetricId] = useState("");
  // 结果页侧边栏额外筛选项
  const [showAllArch, setShowAllArch] = useState(true);
  const [showAllOrg, setShowAllOrg] = useState(true);

  // 候选模型：先按输入格式，再按领域，再按指标（指标含 Kd↔pKd 近邻合并）
  const candidates = useMemo(() => {
    if (!formatId) return [];
    let models = getModelsByInput(graph, formatId);

    if (categoryId) {
      const catModels = new Set(getModelsByCategory(graph, categoryId).map((m) => m.model_id));
      models = models.filter((m) => catModels.has(m.model_id));
    }

    if (metricId) {
      const metricModels = new Set(getModelsByMetric(graph, metricId, true).map((m) => m.model_id));
      models = models.filter((m) => metricModels.has(m.model_id));
    }
    return models;
  }, [graph, formatId, categoryId, metricId]);

  /** 当前指标下的工具（不依赖输入格式；选型页补充展示） */
  const metricTools = useMemo(() => {
    if (!metricId) return [];
    return getToolsByMetric(graph, metricId, true);
  }, [graph, metricId]);

  // 结果页的侧边筛选统计
  const { archTypes, orgNames, filteredCandidates } = useMemo(() => {
    const archMap = new Map<string, number>();
    const orgMap = new Map<string, number>();
    for (const m of candidates) {
      if (m.architecture_type) {
        archMap.set(m.architecture_type, (archMap.get(m.architecture_type) ?? 0) + 1);
      }
      if (m.organization) {
        orgMap.set(m.organization, (orgMap.get(m.organization) ?? 0) + 1);
      }
    }
    const archSorted = [...archMap.entries()].sort((a, b) => b[1] - a[1]);
    const orgSorted = [...orgMap.entries()].sort((a, b) => b[1] - a[1]);

    const filtered = candidates.filter((m) => {
      if (!showAllArch && m.architecture_type) return false;
      if (!showAllOrg && m.organization) return false;
      return true;
    });

    return { archTypes: archSorted, orgNames: orgSorted, filteredCandidates: filtered };
  }, [candidates, showAllArch, showAllOrg]);

  return (
    <div className="page select-page">
      <header className="wizard-header">
        <h1>模型选型向导</h1>
        <div className="steps">
          <span className={step >= 1 ? "active" : ""}>1. 输入格式</span>
          <span className={step >= 2 ? "active" : ""}>2. 研究领域</span>
          <span className={step >= 3 ? "active" : ""}>3. 指标</span>
          <span className={step >= 4 ? "active" : ""}>4. 结果</span>
        </div>
      </header>

      {/* Step 1: 输入格式 */}
      {step === 1 && (
        <section className="wizard-panel">
          <h2>你的数据格式是什么？</h2>
          <div className="chip-grid">
            {formats.map((f) => (
              <button
                key={f.id}
                type="button"
                className={`chip ${formatId === f.id ? "selected" : ""}`}
                onClick={() => {
                  setFormatId(f.id);
                  setStep(2);
                }}
              >
                {f.id.toUpperCase()} <small>({f.count})</small>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Step 2: 研究领域 */}
      {step === 2 && (
        <section className="wizard-panel">
          <h2>关注哪个研究领域？</h2>
          <p className="muted">已选输入: {formatId.toUpperCase()}</p>
          <div className="chip-grid">
            <button
              type="button"
              className={`chip ${!categoryId ? "selected" : ""}`}
              onClick={() => {
                setCategoryId("");
                setStep(3);
              }}
            >
              不限领域
            </button>
            {categories.map((c) => (
              <button
                key={c.id}
                type="button"
                className={`chip ${categoryId === c.id ? "selected" : ""}`}
                style={
                  categoryId === c.id
                    ? { borderColor: colorForCategory(c.id), background: `${colorForCategory(c.id)}22` }
                    : undefined
                }
                onClick={() => {
                  setCategoryId(c.id);
                  setStep(3);
                }}
              >
                <span
                  className="swatch swatch-category"
                  style={{ background: colorForCategory(c.id) }}
                />
                {labelForCategory(c.id)} <small>({c.count})</small>
              </button>
            ))}
          </div>
          <button type="button" className="btn-secondary" onClick={() => setStep(1)}>
            ← 返回
          </button>
        </section>
      )}

      {/* Step 3: 指标（可选） */}
      {step === 3 && (
        <section className="wizard-panel">
          <h2>要预测什么指标？</h2>
          <p className="muted">
            已选: {formatId.toUpperCase()}
            {categoryId && ` · ${labelForCategory(categoryId)}`}
          </p>
          <div className="chip-grid">
            <button
              type="button"
              className="chip"
              onClick={() => {
                setMetricId("");
                setStep(4);
              }}
            >
              跳过（不限指标）
            </button>
            {metrics.map((m) => (
              <button
                key={m.id}
                type="button"
                className={`chip ${metricId === m.id ? "selected" : ""}`}
                onClick={() => {
                  setMetricId(m.id);
                  setStep(4);
                }}
              >
                {m.name}
                {m.unit ? ` (${m.unit})` : ""} <small>({m.count})</small>
              </button>
            ))}
          </div>
          {metrics.length === 0 && (
            <p className="empty">暂无已归一化的明确指标，请直接跳过。</p>
          )}
          <button type="button" className="btn-secondary" onClick={() => setStep(2)}>
            ← 返回
          </button>
        </section>
      )}

      {/* Step 4: 结果（含侧边筛选） */}
      {step === 4 && (
        <section className="wizard-panel">
          <h2>
            找到 {filteredCandidates.length} 个模型
            {formatId && ` · 输入 ${formatId.toUpperCase()}`}
            {categoryId && ` · ${labelForCategory(categoryId)}`}
          </h2>

          <div className="select-results-layout">
            {/* 侧边筛选面板 */}
            <aside className="select-filters">
              <button type="button" className="btn-secondary" onClick={() => setStep(3)}>
                ← 修改筛选
              </button>

              {archTypes.length > 0 && (
                <div className="filter-section">
                  <p className="filter-label">架构类型</p>
                  <div className="filter-checks">
                    <label className="filter-chip active">
                      <input
                        type="checkbox"
                        checked={showAllArch}
                        onChange={(e) => setShowAllArch(e.target.checked)}
                      />
                      <span className="filter-chip-text">全部</span>
                    </label>
                  </div>
                </div>
              )}

              {orgNames.length > 0 && (
                <div className="filter-section">
                  <p className="filter-label">开发组织</p>
                  <div className="filter-checks">
                    <label className="filter-chip active">
                      <input
                        type="checkbox"
                        checked={showAllOrg}
                        onChange={(e) => setShowAllOrg(e.target.checked)}
                      />
                      <span className="filter-chip-text">全部</span>
                    </label>
                    {orgNames.slice(0, 6).map(([org, count]) => (
                      <label key={org} className="filter-chip">
                        <span className="filter-chip-text">{org}</span>
                        <small>({count})</small>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {(archTypes.length > 0 || orgNames.length > 0) && (
                <p className="hint" style={{ marginTop: "0.5rem" }}>
                  仅统计当前 {candidates.length} 个候选模型
                </p>
              )}
            </aside>

            {/* 模型卡片列表 */}
            <div className="select-results-main">
              <div className="card-grid">
                {filteredCandidates.map((m: ModelNode) => (
                  <ModelCard
                    key={m.model_id}
                    model={m}
                    categoryId={getModelCategoryId(graph, m.model_id)}
                    onClick={() => navigate(`/models/${m.model_id}`)}
                  />
                ))}
              </div>
              {filteredCandidates.length === 0 && (
                <p className="empty">
                  无匹配模型。若选了 Kd，可改试输入格式 <strong>PDB</strong>（结构基）或
                  <strong>FASTA</strong>（序列基 pKd 模型）；亦可跳过「研究领域」。
                </p>
              )}
              {metricId && metricTools.length > 0 && (
                <div className="metric-tools" style={{ marginTop: "1.25rem" }}>
                  <h3>相关工具（{metricTools.length}）</h3>
                  <p className="hint">
                    工具不经「输入格式」过滤；PRODIGY / CSM-AB 等会直接预测或换算 Kd。
                  </p>
                  <ul>
                    {metricTools.map((t) => (
                      <li key={t.id}>
                        <code>{t.id}</code> — {t.name}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
