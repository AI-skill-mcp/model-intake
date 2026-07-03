"""
将 JSONL 导入 Neo4j。

用法: python -m etl.import_neo4j
环境变量: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
"""

from __future__ import annotations

import json
import os
import sys

from etl.config import get_paths

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None  # type: ignore


def _label(node: dict) -> str:
    return node["node_type"]


def _node_id_key(node: dict) -> tuple[str, str]:
    ntype = node["node_type"]
    id_fields = {
        "Model": "model_id",
        "Tool": "tool_id",
        "Category": "category_id",
        "Task": "task_id",
        "Metric": "metric_id",
        "FileType": "format_id",
        "Organization": "org_id",
        "Paper": "paper_id",
        "Dataset": "dataset_id",
        "License": "license_id",
        "Modality": "modality_id",
        "Framework": "framework_id",
        "Repository": "repo_id",
    }
    field = id_fields.get(ntype, "id")
    return ntype, node[field]


def import_graph() -> int:
    """读取 nodes.jsonl / edges.jsonl 并 MERGE 到 Neo4j。"""
    if GraphDatabase is None:
        print("错误: 请安装 neo4j 包", file=sys.stderr)
        return 1

    paths = get_paths()
    if not paths.nodes_jsonl.exists():
        print("错误: 请先运行 python -m etl.run", file=sys.stderr)
        return 1

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "graphdb-dev-password")

    nodes = [json.loads(line) for line in paths.nodes_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    edges = [json.loads(line) for line in paths.edges_jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]

    driver = GraphDatabase.driver(uri, auth=(user, password))

    with driver.session() as session:
        session.run("CREATE CONSTRAINT model_id IF NOT EXISTS FOR (m:Model) REQUIRE m.model_id IS UNIQUE")
        session.run("MATCH (n) DETACH DELETE n")

        for node in nodes:
            label = _label(node)
            ntype, nid = _node_id_key(node)
            props = {k: v for k, v in node.items() if k not in ("node_type",) and not isinstance(v, (dict, list))}
            # 复杂字段 JSON 序列化
            for k, v in node.items():
                if isinstance(v, (dict, list)):
                    props[k] = json.dumps(v, ensure_ascii=False)

            id_field = {
                "Model": "model_id", "Tool": "tool_id", "Category": "category_id",
                "Task": "task_id", "Metric": "metric_id", "FileType": "format_id", "Organization": "org_id",
                "Paper": "paper_id", "Dataset": "dataset_id", "License": "license_id",
                "Modality": "modality_id", "Framework": "framework_id", "Repository": "repo_id",
            }[ntype]

            session.run(
                f"MERGE (n:{label} {{{id_field}: $id}}) SET n += $props",
                id=nid,
                props=props,
            )

        for edge in edges:
            etype = edge["type"]
            ft, fid = edge["from"]["node_type"], edge["from"]["id"]
            tt, tid = edge["to"]["node_type"], edge["to"]["id"]
            from_key = {
                "Model": "model_id", "Tool": "tool_id", "Category": "category_id",
                "Task": "task_id", "Metric": "metric_id", "FileType": "format_id", "Organization": "org_id",
                "Paper": "paper_id", "Dataset": "dataset_id", "License": "license_id",
                "Modality": "modality_id", "Framework": "framework_id", "Repository": "repo_id",
            }[ft]
            to_key = {
                "Model": "model_id", "Tool": "tool_id", "Category": "category_id",
                "Task": "task_id", "Metric": "metric_id", "FileType": "format_id", "Organization": "org_id",
                "Paper": "paper_id", "Dataset": "dataset_id", "License": "license_id",
                "Modality": "modality_id", "Framework": "framework_id", "Repository": "repo_id",
            }[tt]

            session.run(
                f"""
                MATCH (a:{ft} {{{from_key}: $fid}})
                MATCH (b:{tt} {{{to_key}: $tid}})
                MERGE (a)-[r:{etype}]->(b)
                SET r += $props
                """,
                fid=fid,
                tid=tid,
                props=edge.get("properties") or {},
            )

    driver.close()
    print(f"导入完成: {len(nodes)} 节点, {len(edges)} 边 → {uri}")
    return 0


def main() -> int:
    return import_graph()


if __name__ == "__main__":
    sys.exit(main())
