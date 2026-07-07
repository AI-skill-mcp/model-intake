#!/usr/bin/env python3
"""
论文全文 PDF 获取：收录 Model/Tool 时尝试下载开放获取 PDF 到 {rawdata_dir}/paper/。

用法:
  python paper_fetch.py --paper-url "https://doi.org/10.1101/..." --entity-id boltz-2
  python paper_fetch.py --doi "10.1038/s41592-026-03128-4" --output-dir ~/kbase/bioinformatics/paper
  python paper_fetch.py ensure-dir   # 按 workspace.yaml 确保 paper/ 存在

输入: paper_url / doi、可选 entity_id、输出目录
输出: 本地 PDF 路径（成功）或失败原因；stdout 为 JSON 便于 Agent 解析
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent
USER_AGENT = "model-intake-paper-fetch/1.0 (mailto:open@unpaywall.org)"
UNPAYWALL_EMAIL = "open@unpaywall.org"
MIN_PDF_BYTES = 8_192
PDF_MAGIC = b"%PDF"


@dataclass
class PaperFetchResult:
    """PDF 下载结果。"""

    ok: bool
    path: str | None = None
    source: str | None = None
    doi: str | None = None
    error: str | None = None
    skipped: bool = False
    candidates_tried: list[str] = field(default_factory=list)


def extract_doi(paper_url: str = "", doi: str = "") -> str | None:
    """
    从 DOI 字符串或 paper_url 提取规范 DOI。

    输入: paper_url、doi（二选一或同时提供 doi 优先）
    输出: 形如 10.xxxx/... 的 DOI，无法解析则 None
    """
    raw = (doi or "").strip()
    if raw:
        if raw.startswith("http"):
            return extract_doi(paper_url=raw)
        return raw.split("?")[0].strip("/")

    url = (paper_url or "").strip()
    if not url:
        return None
    if url.startswith("10."):
        return url.split("?")[0].strip("/")
    if "doi.org/" in url.lower():
        part = re.split(r"doi\.org/", url, flags=re.I)[-1]
        return part.split("?")[0].strip("/")
    # bioRxiv / medRxiv 内容页：/content/10.1101/...
    m = re.search(r"/content/(10\.\d+/[^\s/?#]+)", url, re.I)
    if m:
        return re.sub(r"v\d+$", "", m.group(1), flags=re.I)
    # Nature / Science 文章路径：/articles/s41586-021-03819-2
    m = re.search(r"/articles/(s\d{5}-\d{3}-\d{5}(?:-\d)?)", url, re.I)
    if m:
        return f"10.1038/{m.group(1)}"
    # PubMed → 留空，由 fetch 走 URL 候选
    return None


def paper_filename(doi: str | None, entity_id: str = "", paper_url: str = "") -> str:
    """
    生成 paper/ 下 PDF 文件名（不含路径）。

    优先 DOI slug；否则 entity_id；最后 paper_url slug。
    """
    if doi:
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", doi).strip("-").lower()
        return f"{slug}.pdf"
    if entity_id:
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", entity_id).strip("-").lower()
        return f"{slug}.pdf"
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", (paper_url or "paper-unknown"))[:64].strip("-").lower()
    return f"{slug or 'paper-unknown'}.pdf"


def _http_get(url: str, *, accept: str = "*/*", timeout: float = 30.0) -> tuple[bytes, str | None]:
    """
    GET 请求；返回 (body, content_type)。

    输入: URL、Accept 头、超时秒数
    输出: 响应体与 Content-Type（失败抛 urllib.error.HTTPError / URLError）
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": accept},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        ctype = resp.headers.get("Content-Type")
        return body, ctype


def _is_pdf(body: bytes, content_type: str | None = None) -> bool:
    """判断响应是否为有效 PDF（魔数 + 最小体积）。"""
    if len(body) < MIN_PDF_BYTES:
        return False
    if body[:4] == PDF_MAGIC:
        return True
    if content_type and "pdf" in content_type.lower():
        return True
    return False


def _arxiv_id_from_doi(doi: str) -> str | None:
    """从 DOI 提取 arXiv 编号（含 10.48550/arXiv.xxxx 与 10.1101/arXiv.xxxx）。"""
    lower = doi.lower()
    if "arxiv." not in lower:
        return None
    tail = doi.split("/")[-1]
    m = re.match(r"(?i)arxiv\.(.+)", tail)
    return m.group(1) if m else None


def _arxiv_id_from_url(url: str) -> str | None:
    """从 arxiv.org URL 提取编号。"""
    m = re.search(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)", url, re.I)
    if m:
        return m.group(1)
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([a-z-]+/\d{7,8}(?:v\d+)?)", url, re.I)
    return m.group(1) if m else None


def _preprint_host(doi: str) -> str | None:
    """判断 bioRxiv / medRxiv DOI 前缀。"""
    if doi.startswith("10.1101/"):
        return "biorxiv"
    if doi.startswith("10.64898/"):
        return "biorxiv"  # 2023+ bioRxiv DOI 前缀
    if doi.startswith("10.6489/") or doi.startswith("10.64890/"):
        return "medrxiv"
    return None


def build_pdf_candidates(
    *,
    paper_url: str = "",
    doi: str | None = None,
) -> list[tuple[str, str]]:
    """
    按优先级构建 PDF 候选 URL 列表。

    输入: paper_url、解析后的 doi
    输出: [(source_label, url), ...]
    """
    candidates: list[tuple[str, str]] = []
    url = (paper_url or "").strip()

    # 已是 PDF 直链
    if url.lower().endswith(".pdf"):
        candidates.append(("direct_pdf_url", url))

    resolved_doi = doi or extract_doi(paper_url=url)
    if resolved_doi:
        candidates.append(("doi_redirect", f"https://doi.org/{resolved_doi}"))

        host = _preprint_host(resolved_doi)
        if host:
            candidates.append((host, f"https://www.{host}.org/content/{resolved_doi}.full.pdf"))
            candidates.append((f"{host}_v1", f"https://www.{host}.org/content/{resolved_doi}v1.full.pdf"))

        arxiv_id = _arxiv_id_from_doi(resolved_doi)
        if arxiv_id:
            clean = re.sub(r"v\d+$", "", arxiv_id, flags=re.I)
            candidates.append(("arxiv", f"https://arxiv.org/pdf/{clean}.pdf"))

    arxiv_from_url = _arxiv_id_from_url(url)
    if arxiv_from_url:
        clean = re.sub(r"v\d+$", "", arxiv_from_url, flags=re.I)
        candidates.append(("arxiv_url", f"https://arxiv.org/pdf/{clean}.pdf"))

    return candidates


def _unpaywall_pdf(doi: str) -> str | None:
    """通过 Unpaywall API 获取开放获取 PDF URL（仅 url_for_pdf，忽略 landing page）。"""
    api = f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi, safe='/')}?email={UNPAYWALL_EMAIL}"
    try:
        body, _ = _http_get(api, accept="application/json", timeout=20.0)
        data = json.loads(body.decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError):
        return None

    loc = data.get("best_oa_location") or {}
    u = (loc.get("url_for_pdf") or "").strip()
    if u:
        return u
    for item in data.get("oa_locations") or []:
        u = (item.get("url_for_pdf") or "").strip()
        if u:
            return u
    return None


def _semantic_scholar_meta(doi: str) -> dict:
    """通过 Semantic Scholar 获取 openAccessPdf 与 externalIds（PMC/PubMed）。"""
    api = (
        "https://api.semanticscholar.org/graph/v1/paper/DOI:"
        f"{doi}?fields=openAccessPdf,externalIds"
    )
    try:
        body, _ = _http_get(api, accept="application/json", timeout=20.0)
        return json.loads(body.decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError):
        return {}


def _semantic_scholar_pdf(doi: str) -> str | None:
    """通过 Semantic Scholar API 获取 openAccessPdf。"""
    data = _semantic_scholar_meta(doi)
    oa = data.get("openAccessPdf") or {}
    return (oa.get("url") or "").strip() or None


def _pmc_pdf_urls(doi: str) -> list[str]:
    """
    从 Semantic Scholar / Europe PMC 解析 PMC 全文 PDF 候选 URL。

    输入: DOI
    输出: PMC PDF URL 列表（含重定向后的直链）
    """
    urls: list[str] = []
    meta = _semantic_scholar_meta(doi)
    ext = meta.get("externalIds") or {}
    pmc_raw = (ext.get("PubMedCentral") or ext.get("PMCID") or "").strip()
    if pmc_raw:
        pmcid = pmc_raw if pmc_raw.upper().startswith("PMC") else f"PMC{pmc_raw}"
        urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/")

    # Europe PMC REST（预印本 PPR、PMC 全文 PDF 链接）
    epmc = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
        f"?query=DOI:{doi}&format=json&resultType=core&pageSize=1"
    )
    try:
        body, _ = _http_get(epmc, accept="application/json", timeout=20.0)
        data = json.loads(body.decode("utf-8"))
        for hit in (data.get("resultList") or {}).get("result") or []:
            pmcid = (hit.get("pmcid") or "").strip()
            if pmcid:
                urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/pdf/")
            for ft in (hit.get("fullTextUrlList") or {}).get("fullTextUrl") or []:
                if (ft.get("documentStyle") or "").lower() == "pdf":
                    u = (ft.get("url") or "").strip()
                    if u and "doi.org/" not in u:
                        urls.append(u)
    except (urllib.error.URLError, json.JSONDecodeError, UnicodeDecodeError):
        pass

    # 去重保序
    seen: set[str] = set()
    out: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


def _try_download(url: str, *, depth: int = 0) -> tuple[bytes | None, str | None]:
    """
    尝试下载 PDF；跟随 HTTP 重定向（含 PMC 301 到具体文件名）。

    输出: (pdf_bytes, error_message)
    """
    if depth > 5:
        return None, "重定向次数过多"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=45.0) as resp:
            final_url = resp.geturl()
            ctype = resp.headers.get("Content-Type")
            chunks: list[bytes] = []
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            body = b"".join(chunks)
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            loc = exc.headers.get("Location")
            if loc:
                return _try_download(urllib.parse.urljoin(url, loc), depth=depth + 1)
        return None, f"HTTP {exc.code}: {url}"
    except urllib.error.URLError as exc:
        return None, str(exc.reason)

    if _is_pdf(body, ctype):
        return body, None

    # 非 PDF 但 URL 已变（如 PMC /pdf/ → /pdf/xxx.pdf），再 GET 一次
    if final_url != url and depth < 5:
        return _try_download(final_url, depth=depth + 1)

    # HTML 落地页：尝试从页面中提取 .pdf 链接（bioRxiv / 出版商常见）
    try:
        text = body.decode("utf-8", errors="ignore")
    except Exception:
        return None, "响应非 PDF 且无法解析为 HTML"

    pdf_links = re.findall(r'href=["\']([^"\']+\.pdf[^"\']*)["\']', text, re.I)
    for link in pdf_links[:5]:
        full = urllib.parse.urljoin(url, link)
        try:
            b2, c2 = _http_get(full, accept="application/pdf,*/*", timeout=30.0)
            if _is_pdf(b2, c2):
                return b2, None
        except urllib.error.URLError:
            continue

    return None, "响应非 PDF（可能需订阅或人工获取）"


def fetch_paper_pdf(
    *,
    output_dir: Path,
    paper_url: str = "",
    doi: str = "",
    entity_id: str = "",
    overwrite: bool = False,
) -> PaperFetchResult:
    """
    尝试下载论文 PDF 并保存到 output_dir。

    输入:
      output_dir — {rawdata_dir}/paper 绝对路径
      paper_url / doi — 文献标识（至少其一）
      entity_id — 用于文件命名 fallback
      overwrite — 是否覆盖已有文件
    输出: PaperFetchResult（ok=True 时 path 为相对或绝对 PDF 路径）
    """
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    resolved_doi = extract_doi(paper_url=paper_url, doi=doi)
    if not resolved_doi and not (paper_url or "").strip():
        return PaperFetchResult(ok=False, error="缺少 paper_url 或 doi")

    fname = paper_filename(resolved_doi, entity_id, paper_url)
    dest = output_dir / fname

    if dest.exists() and not overwrite:
        return PaperFetchResult(
            ok=True,
            path=str(dest),
            source="existing",
            doi=resolved_doi,
            skipped=True,
        )

    tried: list[str] = []
    # API 源（通常比盲目猜 URL 更准）
    if resolved_doi:
        for label, getter in (
            ("unpaywall", lambda d: _unpaywall_pdf(d)),
            ("semantic_scholar", lambda d: _semantic_scholar_pdf(d)),
        ):
            pdf_url = getter(resolved_doi)
            if not pdf_url:
                continue
            tried.append(f"{label}:{pdf_url}")
            body, err = _try_download(pdf_url)
            if body:
                dest.write_bytes(body)
                return PaperFetchResult(
                    ok=True,
                    path=str(dest),
                    source=label,
                    doi=resolved_doi,
                    candidates_tried=tried,
                )

        for pmc_url in _pmc_pdf_urls(resolved_doi):
            tried.append(f"pmc:{pmc_url}")
            body, err = _try_download(pmc_url)
            if body:
                dest.write_bytes(body)
                return PaperFetchResult(
                    ok=True,
                    path=str(dest),
                    source="pmc",
                    doi=resolved_doi,
                    candidates_tried=tried,
                )

    for label, url in build_pdf_candidates(paper_url=paper_url, doi=resolved_doi):
        tried.append(f"{label}:{url}")
        body, err = _try_download(url)
        if body:
            dest.write_bytes(body)
            return PaperFetchResult(
                ok=True,
                path=str(dest),
                source=label,
                doi=resolved_doi,
                candidates_tried=tried,
            )

    return PaperFetchResult(
        ok=False,
        doi=resolved_doi,
        error="无法获取开放全文 PDF（可能闭源或需机构访问）",
        candidates_tried=tried,
    )


def ensure_paper_dir(config: dict | None = None) -> Path:
    """
    确保 workspace 下 {rawdata_dir}/paper/ 存在。

    输入: workspace 配置 dict；None 时从 workspace.yaml 加载
    输出: paper 目录绝对路径
    """
    sys.path.insert(0, str(KIT_ROOT))
    from workspace import load_workspace_config, resolve_paths  # noqa: WPS433

    if config is None:
        config = load_workspace_config()
    if not config:
        raise SystemExit("workspace.yaml 未配置，无法定位 paper 目录")
    paths = resolve_paths(config)
    paper_dir = paths.rawdata / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)
    gitkeep = paper_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")
    return paper_dir


def cmd_fetch(args: argparse.Namespace) -> int:
    if args.output_dir:
        out = Path(args.output_dir).expanduser().resolve()
    else:
        out = ensure_paper_dir()

    result = fetch_paper_pdf(
        output_dir=out,
        paper_url=args.paper_url or "",
        doi=args.doi or "",
        entity_id=args.entity_id or "",
        overwrite=args.overwrite,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0 if result.ok else 1


def cmd_ensure_dir(_: argparse.Namespace) -> int:
    paper_dir = ensure_paper_dir()
    print(json.dumps({"ok": True, "paper_dir": str(paper_dir)}, ensure_ascii=False))
    return 0


def is_fetchable_paper_url(url: str) -> bool:
    """判断 paper_url 是否值得尝试下载。"""
    u = (url or "").strip()
    if not u.startswith("http") or "待查" in u or len(u) <= 12:
        return False
    lower = u.lower()
    if "github.com" in lower:
        return False
    if lower.startswith("https:// (") or lower.startswith("http:// ("):
        return False
    host = urllib.parse.urlparse(u).netloc
    if not host or "." not in host:
        return False
    return True


def _parse_md_field(content: str, field: str) -> str:
    """从 Markdown 表格行提取字段值。"""
    m = re.search(rf"\| `{re.escape(field)}` \| ([^\n|]+) \|", content)
    return m.group(1).strip() if m else ""


def scan_model_tool_entries(rawdata: Path) -> list[dict]:
    """
    扫描 model/ 与 tools/ 下条目，提取 entity_id 与 paper_url。

    输入: rawdata 根目录（如 bioinformatics/）
    输出: [{path, entity_id, paper_url, paper_pdf}, ...]
    """
    entries: list[dict] = []
    for sub, id_field in (("model", "model_id"), ("tools", "tool_id")):
        base = rawdata / sub
        if not base.is_dir():
            continue
        for md in sorted(base.rglob("*.md")):
            if md.name.upper() == "README.MD" or "SUMMARY" in md.name.upper():
                continue
            text = md.read_text(encoding="utf-8")
            paper_url = _parse_md_field(text, "paper_url")
            if not paper_url:
                continue
            entity_id = _parse_md_field(text, id_field) or md.stem
            entries.append(
                {
                    "path": md,
                    "entity_id": entity_id,
                    "paper_url": paper_url,
                    "paper_pdf": _parse_md_field(text, "paper_pdf"),
                }
            )
    return entries


def inject_paper_pdf(content: str, rel_path: str) -> str:
    """
    向条目 Markdown 写入或更新 paper_pdf 字段（紧跟 paper_url 之后）。

    输入: 原文、相对 workspace.root 的路径
    输出: 更新后的 Markdown 文本
    """
    if "`paper_pdf`" in content:
        return re.sub(
            r"\| `paper_pdf` \| [^\n|]* \|",
            f"| `paper_pdf` | {rel_path} |",
            content,
            count=1,
        )
    pattern = r"(\| `paper_url` \| [^\n]+ \|\n)"
    if re.search(pattern, content):
        return re.sub(
            pattern,
            rf"\1| `paper_pdf` | {rel_path} |\n",
            content,
            count=1,
        )
    return content


def run_backfill(
    *,
    rawdata: Path,
    paper_dir: Path,
    rawdata_rel: str,
    dry_run: bool = False,
    overwrite: bool = False,
    limit: int = 0,
) -> dict:
    """
    批量补全 model/tools 的论文 PDF 并回写 paper_pdf 字段。

    返回汇总: {ok, failed, skipped, updated_files, details}
    """
    ensure_paper_dir()
    entries = scan_model_tool_entries(rawdata)
    summary = {
        "total": 0,
        "ok": 0,
        "failed": 0,
        "skipped": 0,
        "updated_files": [],
        "details": [],
    }

    for ent in entries:
        if limit and summary["total"] >= limit:
            break
        paper_url = ent["paper_url"]
        if not is_fetchable_paper_url(paper_url):
            summary["skipped"] += 1
            summary["details"].append(
                {"entity_id": ent["entity_id"], "status": "skip_invalid_url", "paper_url": paper_url}
            )
            continue

        summary["total"] += 1
        existing_pdf = ent["paper_pdf"]
        if existing_pdf and not overwrite:
            pdf_path = rawdata.parent / existing_pdf if not Path(existing_pdf).is_absolute() else Path(existing_pdf)
            if pdf_path.exists():
                summary["skipped"] += 1
                summary["details"].append(
                    {"entity_id": ent["entity_id"], "status": "skip_exists", "paper_pdf": existing_pdf}
                )
                continue

        if dry_run:
            summary["details"].append(
                {"entity_id": ent["entity_id"], "status": "dry_run", "paper_url": paper_url}
            )
            continue

        result = fetch_paper_pdf(
            output_dir=paper_dir,
            paper_url=paper_url,
            entity_id=ent["entity_id"],
            overwrite=overwrite,
        )
        detail = {
            "entity_id": ent["entity_id"],
            "paper_url": paper_url,
            "ok": result.ok,
            "source": result.source,
            "doi": result.doi,
            "error": result.error,
        }
        summary["details"].append(detail)

        if result.ok and result.path:
            rel_pdf = f"{rawdata_rel}/paper/{Path(result.path).name}"
            md_path: Path = ent["path"]
            new_content = inject_paper_pdf(md_path.read_text(encoding="utf-8"), rel_pdf)
            if new_content != md_path.read_text(encoding="utf-8"):
                md_path.write_text(new_content, encoding="utf-8")
                summary["updated_files"].append(str(md_path.relative_to(rawdata.parent)))
            summary["ok"] += 1
        else:
            summary["failed"] += 1

    return summary


def cmd_backfill(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(KIT_ROOT))
    from workspace import load_workspace_config, resolve_paths  # noqa: WPS433

    config = load_workspace_config()
    if not config:
        raise SystemExit("workspace.yaml 未配置")
    paths = resolve_paths(config)
    summary = run_backfill(
        rawdata=paths.rawdata,
        paper_dir=paths.paper_dir,
        rawdata_rel=paths.rawdata_rel,
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        limit=args.limit or 0,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["failed"] == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="收录时获取论文 PDF 到 {rawdata_dir}/paper/")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_fetch = sub.add_parser("fetch", help="尝试下载 PDF")
    p_fetch.add_argument("--paper-url", default="", help="paper_url 或 DOI 链接")
    p_fetch.add_argument("--doi", default="", help="DOI（10.xxxx/...）")
    p_fetch.add_argument("--entity-id", default="", help="model_id / tool_id，用于文件命名")
    p_fetch.add_argument("--output-dir", default="", help="覆盖默认 paper 目录")
    p_fetch.add_argument("--overwrite", action="store_true", help="覆盖已有 PDF")
    p_fetch.set_defaults(func=cmd_fetch)

    # 兼容: python paper_fetch.py --paper-url ... （无子命令）
    p_legacy = sub.add_parser("legacy-root", help=argparse.SUPPRESS)

    p_ensure = sub.add_parser("ensure-dir", help="创建 {rawdata_dir}/paper/")
    p_ensure.set_defaults(func=cmd_ensure_dir)

    p_backfill = sub.add_parser("backfill", help="批量补全 model/tools 论文 PDF")
    p_backfill.add_argument("--dry-run", action="store_true", help="仅扫描，不下载")
    p_backfill.add_argument("--overwrite", action="store_true", help="覆盖已有 PDF 并更新条目")
    p_backfill.add_argument("--limit", type=int, default=0, help="最多处理 N 条（0=全部）")
    p_backfill.set_defaults(func=cmd_backfill)

    # 无子命令时若带 --paper-url / --doi 则走 fetch
    if len(sys.argv) > 1 and sys.argv[1] not in ("fetch", "ensure-dir", "backfill", "-h", "--help"):
        if any(a.startswith("--paper-url") or a.startswith("--doi") for a in sys.argv[1:]):
            sys.argv.insert(1, "fetch")

    args = parser.parse_args()
    if args.cmd == "legacy-root":
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
