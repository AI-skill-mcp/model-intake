import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { GraphCanvas } from "../components/GraphCanvas";
import { EntityDrawer } from "../components/EntityDrawer";
import { ResourceLinks } from "../components/ModelCard";
import { PaperInfo } from "../components/PaperInfo";
import { EntityLegend } from "../components/EntityLegend";
import type { GraphExport } from "../types/graph";
import {
  buildSubgraphElements,
  getModelById,
  getModelCategoryId,
  getModelInputs,
  getModelOutputs,
  getModelMetrics,
  getRelatedModels,
} from "../data/loadGraph";
import { modelDisplayName } from "../utils/displayName";
import { colorForCategory, colorForNodeType, labelForCategory } from "../utils/entityColors";

interface Props {
  graph: GraphExport;
}

/** 模型详情页 */
export function ModelDetailPage({ graph }: Props) {
  const { modelId } = useParams<{ modelId: string }>();
  const model = modelId ? getModelById(graph, modelId) : undefined;

  if (!model) {
    return (
      <div className="page">
        <p>未找到模型: {modelId}</p>
        <Link to="/select">返回选型</Link>
      </div>
    );
  }

  const inputs = getModelInputs(graph, model.model_id);
  const outputs = getModelOutputs(graph, model.model_id);
  const metrics = getModelMetrics(graph, model.model_id);
  const related = getRelatedModels(graph, model.model_id);
  const subgraph = buildSubgraphElements(graph, model.model_id, 1);
  const categoryId = getModelCategoryId(graph, model.model_id);
  const accent = categoryId ? colorForCategory(categoryId) : colorForNodeType("Model").bg;
  const displayName = modelDisplayName(model);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [selectedNodeRef, setSelectedNodeRef] = useState<string | null>(null);

  return (
    <div className="page detail-page">
      <Link to="/explore" className="back-link">
        ← 返回探索
      </Link>
      <header
        className="detail-header"
        style={{
          borderLeftColor: accent,
          background: `linear-gradient(135deg, ${accent}14 0%, transparent 60%)`,
        }}
      >
        <div className="card-type-badge" style={{ background: accent }}>
          {colorForNodeType("Model").label}
        </div>
        <h1>{displayName}</h1>
        {model.name !== displayName && <p className="full-title muted">{model.name}</p>}
        <code>{model.model_id}</code>
        <p className="summary">{model.summary}</p>
        <div className="meta-row">
          {categoryId && (
            <span className="tag tag-category" style={{ borderLeft: `3px solid ${accent}` }}>
              {labelForCategory(categoryId)}
            </span>
          )}
          {model.node_subtype && <span className="tag">{model.node_subtype}</span>}
          {model.architecture_type && <span className="tag">{model.architecture_type}</span>}
          {model.commercial_use && <span className="tag">{model.commercial_use}</span>}
        </div>
        <ResourceLinks resources={model.online_resources} />
        <PaperInfo paper={model.paper} />
        {(model.organization || model.framework || (model.modalities?.length ?? 0) > 0) && (
          <div className="attrs-inline">
            {model.organization && <p><strong>组织</strong> {model.organization}</p>}
            {model.framework && <p><strong>框架</strong> {model.framework}</p>}
            {(model.modalities?.length ?? 0) > 0 && (
              <p><strong>模态</strong> {model.modalities!.join(" · ")}</p>
            )}
          </div>
        )}
        {model.source_path && (
          <p className="source">
            源文件: <code>{model.source_path}</code>
          </p>
        )}
      </header>

      <section className="detail-grid">
        <div className="detail-box">
          <h3>输入</h3>
          <ul>{inputs.map((i) => <li key={i}>{i}</li>)}</ul>
        </div>
        <div className="detail-box">
          <h3>输出</h3>
          <ul>{outputs.map((o) => <li key={o}>{o}</li>)}</ul>
        </div>
        <div className="detail-box">
          <h3>预测指标</h3>
          <ul>
            {metrics.map((m) => (
              <li key={m.id}>
                {m.name}
                {m.unit ? ` (${m.unit})` : ""}
              </li>
            ))}
          </ul>
          {metrics.length === 0 && <p className="muted">暂无明确指标映射</p>}
        </div>
      </section>

      {related.length > 0 && (
        <section>
          <h3>相关模型</h3>
          <table className="simple-table">
            <thead>
              <tr>
                <th>关系</th>
                <th>模型</th>
              </tr>
            </thead>
            <tbody>
              {related.map((r) => (
                <tr key={`${r.type}-${r.modelId}`}>
                  <td>{r.type}</td>
                  <td>
                    <Link to={`/models/${r.modelId}`}>
                      {modelDisplayName({ name: r.name, model_id: r.modelId })}
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section>
        <h3>关系子图</h3>
        <EntityLegend />
        <p className="hint">点击子图节点查看实体属性</p>
        <GraphCanvas
          elements={subgraph}
          height="400px"
          focusedNodeId={focusedNodeId}
          onNodeClick={(nodeId) => {
            setFocusedNodeId(nodeId);
            setSelectedNodeRef(nodeId);
          }}
        />
        <EntityDrawer
          graph={graph}
          nodeRef={selectedNodeRef}
          onClearFocus={() => {
            setFocusedNodeId(null);
            setSelectedNodeRef(null);
          }}
        />
      </section>
    </div>
  );
}
