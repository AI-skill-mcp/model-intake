import type { ModelNode } from "../types/graph";
import { modelDisplayName } from "../utils/displayName";
import { colorForCategory, colorForNodeType, labelForCategory } from "../utils/entityColors";

const CHANNEL_LABELS: Record<string, string> = {
  github: "GitHub",
  huggingface: "HuggingFace",
  zenodo: "Zenodo",
  homepage: "主页",
  docker: "Docker",
  colab: "Colab",
  pypi: "PyPI",
  modelscope: "ModelScope",
};

interface ResourceProps {
  resources?: Record<string, string | null>;
}

/** 在线资源链接按钮组 */
export function ResourceLinks({ resources }: ResourceProps) {
  if (!resources) return null;
  const entries = Object.entries(resources).filter(([, url]) => url);
  if (entries.length === 0) return <span className="muted">暂无在线链接</span>;

  return (
    <div className="resource-links">
      {entries.map(([key, url]) => (
        <a
          key={key}
          href={url!.startsWith("http") ? url! : undefined}
          target="_blank"
          rel="noreferrer"
          className={url!.startsWith("http") ? "btn-link" : "btn-link disabled"}
        >
          {CHANNEL_LABELS[key] ?? key}
        </a>
      ))}
    </div>
  );
}

interface CardProps {
  model: ModelNode;
  categoryId?: string;
  onClick?: () => void;
}

/** 模型卡片 */
export function ModelCard({ model, categoryId, onClick }: CardProps) {
  const displayName = modelDisplayName(model);
  const accent = categoryId ? colorForCategory(categoryId) : colorForNodeType("Model").bg;
  const typeLabel = colorForNodeType("Model").label;

  return (
    <article
      className="model-card"
      onClick={onClick}
      role={onClick ? "button" : undefined}
      style={{
        borderLeftColor: accent,
        background: `linear-gradient(135deg, ${accent}18 0%, var(--surface) 45%)`,
      }}
    >
      <div className="card-type-badge" style={{ background: accent }}>
        {typeLabel}
      </div>
      <h3>{displayName}</h3>
      <code className="model-id">{model.model_id}</code>
      <p className="summary">{model.summary}</p>
      <div className="meta">
        {categoryId && (
          <span className="tag tag-category" style={{ borderLeft: `3px solid ${accent}` }}>
            {labelForCategory(categoryId)}
          </span>
        )}
        {model.node_subtype && <span className="tag">{model.node_subtype}</span>}
        {model.commercial_use && <span className="tag">{model.commercial_use}</span>}
      </div>
      <ResourceLinks resources={model.online_resources} />
    </article>
  );
}
