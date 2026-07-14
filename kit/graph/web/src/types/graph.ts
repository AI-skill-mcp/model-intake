/** 图数据类型定义，与 graph_export.json 对齐 */

export interface PaperRef {
  paper_id: string;
  title: string;
  url?: string | null;
}

export interface GraphNode {
  node_type: string;
  model_id?: string;
  tool_id?: string;
  category_id?: string;
  task_id?: string;
  metric_id?: string;
  unit?: string;
  format_id?: string;
  org_id?: string;
  paper_id?: string;
  dataset_id?: string;
  license_id?: string;
  modality_id?: string;
  framework_id?: string;
  repo_id?: string;
  name?: string;
  display_name?: string;
  summary?: string;
  paper?: PaperRef;
  organization?: string;
  framework?: string;
  modalities?: string[];
  organizations?: string[];
  alias?: string[];
  node_subtype?: string;
  release_date?: string;
  parameter_count?: string;
  architecture_type?: string;
  multimodal?: boolean;
  commercial_use?: string;
  source_path?: string | null;
  in_corpus?: boolean;
  online_resources?: Record<string, string | null>;
  online_resources_meta?: Record<string, { status?: string; raw_text?: string }>;
  /** Dataset */
  description?: string;
  url?: string;
  paper_doi?: string;
  dataset_type?: string;
  license_note?: string;
  size_description?: string;
  scope?: string;
  /** Metric */
  quantity_kind?: string;
  domains?: string[];
  typical_range?: string;
  higher_is_better?: boolean;
  /** Tool */
  tool_type?: string;
  license?: string;
}

export interface GraphEdge {
  type: string;
  from: { node_type: string; id: string };
  to: { node_type: string; id: string };
  properties?: Record<string, unknown>;
}

export interface GraphExport {
  schema_version: string;
  generated_at: string;
  stats: { nodes: number; edges: number; models: number };
  nodes: GraphNode[];
  edges: GraphEdge[];
  indexes: {
    by_input_format: Record<string, string[]>;
    by_metric: Record<string, string[]>;
    /** Tool -[:MEASURES]-> Metric */
    by_metric_tool?: Record<string, string[]>;
    /** @deprecated 使用 by_metric */
    by_task?: Record<string, string[]>;
    by_category: Record<string, string[]>;
    by_category_dataset?: Record<string, string[]>;
  };
}

export interface ModelNode extends GraphNode {
  node_type: "Model";
  model_id: string;
  name: string;
  display_name?: string;
  summary: string;
  paper?: PaperRef;
  organization?: string;
  framework?: string;
  modalities?: string[];
}
