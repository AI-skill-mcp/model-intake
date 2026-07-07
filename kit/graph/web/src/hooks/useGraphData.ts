import { useEffect, useState } from "react";
import type { GraphExport } from "../types/graph";
import { loadGraph } from "../data/loadGraph";

/** 全局图数据 Hook */
export function useGraphData() {
  const [graph, setGraph] = useState<GraphExport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadGraph()
      .then(setGraph)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { graph, error, loading };
}
