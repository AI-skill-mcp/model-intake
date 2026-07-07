import type { PaperRef } from "../types/graph";

interface Props {
  paper?: PaperRef;
}

/** 论文信息（作为模型/工具属性展示） */
export function PaperInfo({ paper }: Props) {
  if (!paper?.title && !paper?.url) return null;

  return (
    <div className="paper-info">
      <h4>论文</h4>
      {paper.url ? (
        <a href={paper.url} target="_blank" rel="noreferrer">
          {paper.title || paper.url}
        </a>
      ) : (
        <span>{paper.title}</span>
      )}
    </div>
  );
}
