"""pytrends fetcher with sqlite cache and polite rate-limiting.

LLMs never see raw data from this module — it writes parquet/JSON to disk
and the stats layer digests from there.
"""
from __future__ import annotations

import hashlib
import json
import random
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pytrends.request import TrendReq

CACHE_DB = Path(__file__).resolve().parent.parent / "cache.db"
MIN_DELAY = 15.0
MAX_DELAY = 25.0
MAX_RETRIES = 4
INITIAL_BACKOFF = 30.0


@dataclass
class FetchConfig:
    geo: str = "IL"
    hl: str = "he-IL"
    tz: int = 120
    timeframe: str = "today 5-y"


def _cache_key(kind: str, terms: list[str], cfg: FetchConfig) -> str:
    payload = json.dumps(
        {"kind": kind, "terms": sorted(terms), "geo": cfg.geo, "tf": cfg.timeframe},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _init_cache() -> None:
    con = sqlite3.connect(CACHE_DB)
    con.execute(
        "CREATE TABLE IF NOT EXISTS cache ("
        "key TEXT PRIMARY KEY, kind TEXT, terms TEXT, payload TEXT, fetched_at REAL)"
    )
    con.commit()
    con.close()


def _cache_get(key: str) -> Any | None:
    con = sqlite3.connect(CACHE_DB)
    row = con.execute("SELECT payload FROM cache WHERE key = ?", (key,)).fetchone()
    con.close()
    return json.loads(row[0]) if row else None


def _cache_put(key: str, kind: str, terms: list[str], payload: Any) -> None:
    con = sqlite3.connect(CACHE_DB)
    con.execute(
        "INSERT OR REPLACE INTO cache VALUES (?, ?, ?, ?, ?)",
        (key, kind, json.dumps(terms, ensure_ascii=False), json.dumps(payload, default=str, ensure_ascii=False), time.time()),
    )
    con.commit()
    con.close()


def _sleep() -> None:
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def _with_backoff(fn, *args, on_rate_limit=None, **kwargs):
    """Retry fn with exponential backoff. On 429, optionally call on_rate_limit()
    (used to refresh the pytrends session after repeated 429s)."""
    delay = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if "429" in msg or "too many" in msg or "rate" in msg:
                print(f"  rate limited, sleeping {delay:.0f}s (attempt {attempt + 1}/{MAX_RETRIES})", flush=True)
                time.sleep(delay)
                delay = min(delay * 2, 300)
                # After 2 rate-limit hits in a row, refresh session
                if on_rate_limit is not None and attempt >= 1:
                    try:
                        on_rate_limit()
                        print("  refreshed pytrends session")
                    except Exception as re_err:
                        print(f"  session refresh failed: {re_err}")
                continue
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(5)
    raise RuntimeError("max retries exceeded")


class Fetcher:
    def __init__(self, cfg: FetchConfig | None = None) -> None:
        self.cfg = cfg or FetchConfig()
        self._new_session()
        _init_cache()

    def _new_session(self) -> None:
        self.py = TrendReq(hl=self.cfg.hl, tz=self.cfg.tz, retries=2, backoff_factor=0.5, timeout=(10, 30))

    def _build(self, terms: list[str]) -> None:
        self.py.build_payload(terms, timeframe=self.cfg.timeframe, geo=self.cfg.geo)

    def interest_over_time(self, terms: list[str]) -> dict[str, Any]:
        """Max 5 terms per request. Returns dict with 'dates' and per-term value lists."""
        assert 1 <= len(terms) <= 5, "pytrends accepts 1-5 terms"
        key = _cache_key("iot", terms, self.cfg)
        if (hit := _cache_get(key)) is not None:
            return hit
        print(f"  [iot] {terms}", flush=True)
        _with_backoff(self._build, terms, on_rate_limit=self._new_session)
        df: pd.DataFrame = _with_backoff(self.py.interest_over_time, on_rate_limit=self._new_session)
        _sleep()
        if df.empty:
            result = {"dates": [], "series": {t: [] for t in terms}, "empty": True}
        else:
            df = df.drop(columns=["isPartial"], errors="ignore")
            result = {
                "dates": [d.isoformat() for d in df.index],
                "series": {t: df[t].astype(int).tolist() for t in terms if t in df.columns},
                "empty": False,
            }
        _cache_put(key, "iot", terms, result)
        return result

    def related_queries(self, term: str) -> dict[str, Any]:
        key = _cache_key("rq", [term], self.cfg)
        if (hit := _cache_get(key)) is not None:
            return hit
        print(f"  [rq]  {term}", flush=True)
        _with_backoff(self._build, [term], on_rate_limit=self._new_session)
        try:
            raw = _with_backoff(self.py.related_queries, on_rate_limit=self._new_session)
        except (IndexError, KeyError, ValueError) as e:
            print(f"  [rq]  no data ({type(e).__name__})")
            raw = {}
        _sleep()
        section = raw.get(term, {}) or {}

        def _df_to_rows(df):
            if df is None or getattr(df, "empty", True):
                return []
            return df.to_dict(orient="records")

        result = {
            "term": term,
            "top": _df_to_rows(section.get("top")),
            "rising": _df_to_rows(section.get("rising")),
        }
        _cache_put(key, "rq", [term], result)
        return result

    def related_topics(self, term: str) -> dict[str, Any]:
        key = _cache_key("rt", [term], self.cfg)
        if (hit := _cache_get(key)) is not None:
            return hit
        print(f"  [rt]  {term}", flush=True)
        _with_backoff(self._build, [term], on_rate_limit=self._new_session)
        try:
            raw = _with_backoff(self.py.related_topics, on_rate_limit=self._new_session)
        except (IndexError, KeyError, ValueError) as e:
            print(f"  [rt]  no data ({type(e).__name__})")
            raw = {}
        _sleep()
        section = raw.get(term, {}) or {}

        def _df_to_rows(df):
            if df is None or getattr(df, "empty", True):
                return []
            return df.to_dict(orient="records")

        result = {
            "term": term,
            "top": _df_to_rows(section.get("top")),
            "rising": _df_to_rows(section.get("rising")),
        }
        _cache_put(key, "rt", [term], result)
        return result


def fetch_brief(brief: dict, out_dir: Path) -> dict:
    """Pull all data specified by the brief. Writes raw JSON to out_dir/raw/.

    Returns a manifest dict listing what was fetched.
    """
    cfg = FetchConfig(
        geo=brief.get("geo", "IL"),
        hl=brief.get("hl", "he-IL"),
        timeframe=brief.get("timeframe", "today 5-y"),
    )
    fetcher = Fetcher(cfg)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict = {"iot": {}, "related": {}}
    buckets = brief.get("buckets", {})

    def _chunk(items, n=5):
        for i in range(0, len(items), n):
            yield items[i : i + n]

    def _write(name: str, data: dict) -> None:
        (raw_dir / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Interest over time — chunk into batches of 5
    iot_jobs: list[tuple[str, list[str]]] = []
    if brand := buckets.get("brand_terms"):
        iot_jobs.append(("brand_terms", brand[:5]))
    if comps := buckets.get("competitor_terms"):
        # Each competitor block is already <=5 terms; if dict, take head term per competitor for comparison
        if isinstance(comps, dict):
            head_per = [v[0] for v in comps.values() if v][:5]
            if head_per:
                iot_jobs.append(("competitors_head", head_per))
            for name, terms in comps.items():
                if terms:
                    iot_jobs.append((f"competitor_{name}", terms[:5]))
        elif isinstance(comps, list):
            for i, chunk in enumerate(_chunk(comps, 5)):
                iot_jobs.append((f"competitors_{i}", chunk))
    if cat := buckets.get("category_terms"):
        for i, chunk in enumerate(_chunk(cat, 5)):
            iot_jobs.append((f"category_{i}", chunk))
    if adj := buckets.get("adjacent_terms"):
        for i, chunk in enumerate(_chunk(adj, 5)):
            iot_jobs.append((f"adjacent_{i}", chunk))
    for i, pair in enumerate(buckets.get("comparison_pairs", []) or []):
        iot_jobs.append((f"compare_{i}", list(pair)[:5]))

    for name, terms in iot_jobs:
        try:
            data = fetcher.interest_over_time(terms)
            _write(f"iot_{name}", data)
            manifest["iot"][name] = {"terms": terms, "empty": data.get("empty", False)}
        except Exception as e:
            print(f"  [iot] {name} FAILED: {e}", flush=True)
            manifest["iot"][name] = {"terms": terms, "failed": str(e)}
            # Write an empty payload so stats layer doesn't choke
            _write(f"iot_{name}", {"dates": [], "series": {t: [] for t in terms}, "empty": True, "failed": True})

    # Related queries + topics for a curated set (head terms only, avoid blowup)
    related_terms: list[str] = []
    if brand := buckets.get("brand_terms"):
        related_terms.append(brand[0])
    if comps := buckets.get("competitor_terms"):
        if isinstance(comps, dict):
            related_terms.extend(v[0] for v in comps.values() if v)
        elif isinstance(comps, list):
            related_terms.extend(comps[:3])
    if cat := buckets.get("category_terms"):
        related_terms.extend(cat[:3])
    if adj := buckets.get("adjacent_terms"):
        related_terms.extend(adj[:3])
    related_terms = list(dict.fromkeys(related_terms))  # dedupe, preserve order

    for term in related_terms:
        safe = hashlib.md5(term.encode("utf-8")).hexdigest()[:10]
        try:
            rq = fetcher.related_queries(term)
            _write(f"rq_{safe}", rq)
        except Exception as e:
            print(f"  [rq] {term} FAILED: {e}", flush=True)
            _write(f"rq_{safe}", {"term": term, "top": [], "rising": [], "failed": True})
        try:
            rt = fetcher.related_topics(term)
            _write(f"rt_{safe}", rt)
        except Exception as e:
            print(f"  [rt] {term} FAILED: {e}", flush=True)
            _write(f"rt_{safe}", {"term": term, "top": [], "rising": [], "failed": True})
        manifest["related"][term] = {"file_prefix": safe}

    (out_dir / "raw" / "_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
