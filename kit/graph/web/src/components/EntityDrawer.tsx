import { Link } from "react-router-dom";
import type { GraphExport, GraphNode, ModelNode } from "../types/graph";
import {
  getLinkedModels,
  getModelById,
  getModelCategoryId,
  getNodeByRef,
  parseNodeRef,
} from "../data/loadGraph";
import { modelDisplayName } from "../utils/displayName";
import { colorForNodeType, labelForCategory } from "../utils/entityColors";
import { ResourceLinks } from "./ModelCard";
import { PaperInfo } from "./PaperInfo";

const EDGE_LABELS: Record<string, string> = {
  MEASURES: "预测",
  ACCEPTS: "接受输入",
  PRODUCES: "产出",
  TRAINED_ON: "训练于",
  REQUIRES: "依赖",
  BELONGS_TO: "属于",
  INTEGRATES: "集成",
  BASED_ON: "基于",
};

interface Props {
  graph: GraphExport;
  /** Cytoscape 节点 ID，如 Dataset:pdb */
  nodeRef: string | null;
  onClearFocus?: () => void;
}

function entityIdOf(node: GraphNode): string {
  return (
    node.model_id ??
    node.dataset_id ??
    node.metric_id ??
    node.format_id ??
    node.tool_id ??
    node.category_id ??
    node.name ??
    "unknown"
  );
}

function entityTitle(node: GraphNode): string {
  if (node.node_type === "Model" && node.model_id) {
    return modelDisplayName({
      name: node.name ?? node.model_id,
      model_id: node.model_id,
      display_name: node.display_name,
    });
  }
  return node.name ?? entityIdOf(node);
}

/** 属性行：有值才渲染 */
function Attr({ label, value }: { label: string; value?: string | null }) {
  if (!value?.trim()) return null;
  return (
    <p className="entity-attr">
      <strong>{label}</strong> {value}
    </p>
  );
}

/** 列表属性 */
function AttrList({ label, items }: { label: string; items?: string[] }) {
  if (!items?.length) return null;
  return (
    <p className="entity-attr">
      <strong>{label}</strong> {items.join(" · ")}
    </p>
  );
}

/** 侧边栏实体属性抽屉：模型 / 数据集 / 指标 / 格式 / 工具等 */
export function EntityDrawer({ graph, nodeRef, onClearFocus }: Props) {
  if (!nodeRef) return null;

  const node = getNodeByRef(graph, nodeRef);
  if (!node) return null;

  const { nodeType, id } = parseNodeRef(nodeRef);
  const colors = colorForNodeType(nodeType);
  const linked = nodeType !== "Model" ? getLinkedModels(graph, nodeType, id) : [];
  const categoryId =
    nodeType === "Model" ? getModelCategoryId(graph, id) : undefined;

  const model = nodeType === "Model" ? (node as ModelNode) : undefined;

  return (
    <div className="drawer entity-drawer">
      <span
        className="entity-drawer-badge"
        style={{ borderColor: colors.border, color: colors.border }}
      >
        {colors.label}
      </span>

      <h3>{entityTitle(node)}</h3>
      <code className="entity-id">{entityIdOf(node)}</code>

      {(node.summary || node.description) && (
        <p className="entity-summary">{node.summary ?? node.description}</p>
      )}

      {model && (
        <>
          <PaperInfo paper={model.paper} />
          <Attr label="组织" value={model.organization} />
          <Attr label="框架" value={model.framework} />
          <AttrList label="模态" items={model.modalities} />
          {categoryId && (
            <p className="entity-attr">
              <strong>领域</strong> {labelForCategory(categoryId)}
            </p>
          )}
          <Attr label="架构" value={model.architecture_type} />
          <Attr label="参数量" value={model.parameter_count} />
          <Attr label="商用" value={model.commercial_use} />
          <ResourceLinks resources={model.online_resources} />
          <Link className="drawer-link-btn" to={`/models/${model.model_id}`}>
            查看详情 →
          </Link>
        </>
      )}

      {nodeType === "Dataset" && (
        <>
          <Attr label="类型" value={node.dataset_type} />
          <Attr
            label="标签指标"
            value={
              Array.isArray(node.label_metrics)
                ? node.label_metrics.join(", ")
                : (node.label_metrics as string | undefined)
            }
          />
          <Attr label="分发格式" value={node.file_formats as string | undefined} />
          <Attr label="规模" value={node.size_description} />
          <Attr label="范围" value={node.scope} />
          <AttrList label="维护机构" items={node.organizations} />
          <AttrList label="模态" items={node.modalities} />
          {node.url && (
            <p className="entity-attr">
              <strong>来源</strong>{" "}
              <a href={node.url} target="_blank" rel="noreferrer">
                {node.url.replace(/^https?:\/\//, "").slice(0, 48)}
              </a>
            </p>
          )}
          {node.paper_doi && (
            <p className="entity-attr">
              <strong>DOI</strong>{" "}
              <a
                href={`https://doi.org/${node.paper_doi}`}
                target="_blank"
                rel="noreferrer"
              >
                {node.paper_doi}
              </a>
            </p>
          )}
          <Attr label="许可说明" value={node.license_note} />
        </>
      )}

      {nodeType === "Metric" && (
        <>
          <Attr label="单位" value={node.unit} />
          <Attr label="物理量" value={node.quantity_kind} />
          <Attr label="典型范围" value={node.typical_range} />
          <AttrList label="领域" items={node.domains} />
          {node.higher_is_better != null && (
            <p className="entity-attr">
              <strong>优化方向</strong>{" "}
              {node.higher_is_better ? "越大越好" : "越小越好"}
            </p>
          )}
        </>
      )}

      {nodeType === "FileType" && (
        <p className="muted entity-hint">文件交换格式节点</p>
      )}

      {nodeType === "Tool" && (
        <>
          <Attr label="类型" value={node.tool_type} />
          <Attr label="许可" value={node.license} />
          {node.alias && (
            <Attr
              label="别名"
              value={Array.isArray(node.alias) ? node.alias.join(", ") : node.alias}
            />
          )}
          <ResourceLinks resources={node.online_resources} />
        </>
      )}

      {node.source_path && (
        <p className="entity-source muted">
          文档: <code>{node.source_path}</code>
        </p>
      )}

      {linked.length > 0 && (
        <div className="entity-linked">
          <h4>关联模型 ({linked.length})</h4>
          <ul className="entity-linked-list">
            {linked.slice(0, 12).map((l) => (
              <li key={`${l.edgeType}-${l.modelId}`}>
                <span className="edge-tag">{EDGE_LABELS[l.edgeType] ?? l.edgeType}</span>
                {getModelById(graph, l.modelId) ? (
                  <Link to={`/models/${l.modelId}`}>{l.name}</Link>
                ) : (
                  l.name
                )}
              </li>
            ))}
          </ul>
          {linked.length > 12 && (
            <p className="muted">另有 {linked.length - 12} 个…</p>
          )}
        </div>
      )}

      {onClearFocus && (
        <button type="button" className="btn-secondary drawer-clear" onClick={onClearFocus}>
          取消聚焦
        </button>
      )}
    </div>
  );
}
