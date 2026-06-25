import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

# Minimal client for our internal Firecrawl-like service (fork)
# Exposes: fetch, crawl, extract, discover
# Reads base URL and API key from env.

# Allow multiple env var aliases so users can supply FIRECRAWLER_* without renaming.
BASE_URL = (
    os.getenv("CRAWLER_BASE_URL")
    or os.getenv("FIRECRAWLER_BASE_URL")
    or os.getenv("FIRECRAWLER_URL")
    or "http://localhost:7071"
)
API_KEY = (
    os.getenv("CRAWLER_API_KEY")
    or os.getenv("FIRECRAWLER_API_KEY")
    or os.getenv("FIRECRAWLER_KEY")
    or ""
)
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

DEFAULT_TIMEOUT = float(os.getenv("CRAWLER_HTTP_TIMEOUT", "20"))
SESSION = requests.Session()


def _headers() -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h


def _post(path: str, payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    url = BASE_URL.rstrip("/") + path
    last_err: Optional[Exception] = None
    # Simple retry: up to 3 attempts with backoff (0s, 1s, 3s)
    for attempt in range(3):
        try:
            resp = SESSION.post(url, headers=_headers(), data=json.dumps(payload), timeout=timeout)
            try:
                data = resp.json()
            except Exception:
                data = {"success": False, "status": resp.status_code, "text": resp.text[:1000]}
            if resp.status_code >= 400:
                last_err = RuntimeError(f"crawler POST {path} failed: {resp.status_code} {data}")
            else:
                return data
        except Exception as e:
            last_err = e
        # backoff before next try
        if attempt < 2:
            time.sleep(1 if attempt == 0 else 3)
    # all attempts failed
    if last_err:
        raise last_err
    return {"success": False, "error": "unknown"}


# ============ Core surface ============

def fetch(url: str, render: bool = True, timeout: Optional[float] = None) -> Dict[str, Any]:
    """Render-fetch a single URL via the service (/v2/scrape). Returns metadata and content lengths."""
    # We request HTML only to reduce payloads.
    payload = {
        "url": url,
        "formats": ["html"],
    }
    to = timeout or DEFAULT_TIMEOUT
    # Map to /v2/scrape for upstream compatibility
    return _post("/v2/scrape", payload, timeout=to)


def crawl(seed_url: str, limit: int = 8, depth: int = 2, timeout: Optional[float] = None) -> Dict[str, Any]:
    """Crawl limited pages via the service (/v2/crawl)."""
    payload = {
        "url": seed_url,
        "limit": max(1, min(int(limit), 25)),
        "scrapeOptions": {"formats": ["html"]},
    }
    to = timeout or DEFAULT_TIMEOUT
    return _post("/v2/crawl", payload, timeout=to)


def extract(schema: str, *, url: Optional[str] = None, html: Optional[str] = None, text: Optional[str] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
    """Extract structured data via the service (/v2/extract)."""
    payload: Dict[str, Any] = {"schema": schema}
    # Upstream expects urls or content via formats; we'll pass url for now.
    if url:
        payload["urls"] = [url]
    if html or text:
        # For now we don't pass raw HTML/text to upstream; future: support local content endpoint.
        pass
    to = timeout or DEFAULT_TIMEOUT
    return _post("/v2/extract", payload, timeout=to)


# ============ Discovery helper ============
# Combines Tavily + heuristics; optionally calls fetch once to confirm/canonicalize.

TRUST_TLDS = {"com", "io", "ai", "dev", "co"}


def _brand_tokens(name: str) -> List[str]:
    import re
    n = name.lower()
    n = re.sub(r"[^a-z0-9 ]+", " ", n)
    parts = [p for p in n.split() if p and p not in {"inc", "ltd", "corp", "co", "plc"}]
    return parts


def _guess_homepage_candidates(name: str) -> List[str]:
    toks = _brand_tokens(name)
    joined = "".join(toks)
    hyphen = "-".join(toks)
    cands = [
        f"https://{joined}.com",
        f"https://{joined}.ai",
        f"https://{joined}.io",
        f"https://{hyphen}.com",
        f"https://{hyphen}.ai",
        f"https://{hyphen}.io",
    ]
    return cands


def _common_careers_from_homepage(homepage: str) -> List[str]:
    from urllib.parse import urljoin
    paths = ["/careers", "/jobs", "/join", "/join-us", "/work-with-us", "/open-roles"]
    return [urljoin(homepage, p) for p in paths]


def _score_domain(url: str, tokens: List[str]) -> int:
    try:
        from urllib.parse import urlparse
        host = (urlparse(url).netloc or "").lower()
        tld = host.split(".")[-1]
        token_score = sum(20 for t in tokens if t and t in host)
        tld_score = 10 if tld in TRUST_TLDS else 0
        return max(0, min(100, token_score + tld_score))
    except Exception:
        return 0


def discover(name: str, tier: Optional[str] = None, confirm_with_fetch: bool = True) -> Dict[str, Any]:
    """Return best homepage and careers picks using Tavily + heuristics; optionally confirm with one fetch.
    Output: { homepage?: {url, score, final_url?}, careers?: {url, score, final_url?}, sources:{...} }
    """
    # 1) Heuristics
    toks = _brand_tokens(name)
    h_guesses = _guess_homepage_candidates(name)
    scored = sorted(((u, _score_domain(u, toks)) for u in h_guesses), key=lambda x: x[1], reverse=True)
    h_best: Optional[Tuple[str, int]] = scored[0] if scored else None

    # 2) Tavily (optional)
    tav_home: Optional[Tuple[str, int]] = None
    tav_careers: Optional[Tuple[str, int]] = None
    tav_used = False
    if TAVILY_API_KEY:
        try:
            from .tavily_client import search_homepage, search_careers  # type: ignore
            tav_used = True
            t_home = search_homepage(name, tier) or []
            t_careers = search_careers(name) or []
            def pick(lst: List[Dict[str, Any]]) -> Optional[Tuple[str, int]]:
                best_u, best_s = None, -1
                for it in lst:
                    u = it.get("url")
                    if not u:
                        continue
                    s = _score_domain(u, toks)
                    if s > best_s:
                        best_u, best_s = u, s
                return (best_u, best_s) if best_u else None
            tav_home = pick(t_home)
            tav_careers = pick(t_careers)
        except Exception:
            pass

    # 3) Choose best homepage
    picks = [p for p in [tav_home, h_best] if p]
    picks.sort(key=lambda x: x[1], reverse=True)
    homepage_pick = picks[0] if picks else None

    # 4) Careers: derive from homepage + tavily
    careers_candidates: List[Tuple[str, int]] = []
    if homepage_pick:
        for u in _common_careers_from_homepage(homepage_pick[0]):
            careers_candidates.append((u, _score_domain(u, toks)))
    if tav_careers:
        careers_candidates.append(tav_careers)
    careers_candidates.sort(key=lambda x: x[1], reverse=True)
    careers_pick = careers_candidates[0] if careers_candidates else None

    out: Dict[str, Any] = {"sources": {"tavily_used": tav_used, "heuristics_used": True}}

    def confirm(u_pick: Optional[Tuple[str, int]]) -> Optional[Dict[str, Any]]:
        if not u_pick:
            return None
        u, s = u_pick
        final_url = None
        if confirm_with_fetch and BASE_URL:
            try:
                resp = fetch(u)
                # Upstream returns { success, data: { html, metadata: { statusCode, sourceURL, ... } } }
                data = resp.get("data") or {}
                meta = data.get("metadata") or {}
                status = int(meta.get("statusCode") or 0)
                if status in (200, 301, 302, 403):
                    final_url = meta.get("sourceURL") or meta.get("ogUrl") or u
                else:
                    # if non-2xx and low score, drop it
                    if s < 40:
                        return None
            except Exception:
                # fetch failed; keep candidate if score is strong
                if s < 60:
                    return None
        return {"url": u, "score": s, **({"final_url": final_url} if final_url else {})}

    hp = confirm(homepage_pick)
    cp = confirm(careers_pick)
    if hp:
        out["homepage"] = hp
    if cp:
        out["careers"] = cp
    return out
