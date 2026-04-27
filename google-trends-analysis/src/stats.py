"""Deterministic stats layer. Digests raw JSON into compact summaries
that sub-agents can reason about without ever seeing the raw time series.

This is where most token savings come from.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _iot_to_df(iot: dict) -> pd.DataFrame:
    if iot.get("empty") or not iot.get("dates"):
        return pd.DataFrame()
    idx = pd.to_datetime(iot["dates"])
    return pd.DataFrame(iot["series"], index=idx)


def _summarize_series(s: pd.Series) -> dict[str, Any]:
    """Deterministic summary of a single term's interest-over-time series."""
    s = s.dropna()
    if s.empty or s.sum() == 0:
        return {"empty": True}

    # Linear trend
    x = np.arange(len(s), dtype=float)
    y = s.astype(float).values
    if len(s) >= 2 and y.std() > 0:
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_res = ((y - y_pred) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
        # normalize slope into "points per year" (data is weekly-ish for 5y)
        slope_per_year = float(slope * 52)
    else:
        slope = 0.0
        r2 = 0.0
        slope_per_year = 0.0

    # YoY: last 52w mean vs prior 52w mean
    if len(s) >= 104:
        last_year = float(s.iloc[-52:].mean())
        prior_year = float(s.iloc[-104:-52].mean())
        yoy = (last_year - prior_year) / prior_year * 100 if prior_year > 0 else 0.0
    else:
        last_year = float(s.iloc[-min(52, len(s)) :].mean()) if len(s) else 0.0
        prior_year = 0.0
        yoy = 0.0

    # Peak
    peak_idx = s.idxmax()
    peak = {"date": peak_idx.strftime("%Y-%m-%d"), "value": int(s.loc[peak_idx])}

    # Top 5 spikes (local maxima above 1.5x rolling median)
    rolling_med = s.rolling(8, center=True, min_periods=3).median()
    spikes_df = s[(s > rolling_med * 1.5) & (s >= 50)]
    spikes = [
        {"date": d.strftime("%Y-%m-%d"), "value": int(v)}
        for d, v in spikes_df.sort_values(ascending=False).head(5).items()
    ]

    # Seasonality: mean by month (1-12)
    monthly = s.groupby(s.index.month).mean()
    if monthly.max() > 0:
        seasonal_index = (monthly / monthly.mean()).round(2).to_dict()
        peak_month = int(monthly.idxmax())
        low_month = int(monthly.idxmin())
        seasonality_strength = float((monthly.max() - monthly.min()) / monthly.mean())
    else:
        seasonal_index = {}
        peak_month = None
        low_month = None
        seasonality_strength = 0.0

    return {
        "empty": False,
        "mean": round(float(s.mean()), 1),
        "max": int(s.max()),
        "min": int(s.min()),
        "trend": {
            "slope_per_year": round(slope_per_year, 2),
            "r2": round(r2, 3),
            "direction": "up" if slope_per_year > 2 else "down" if slope_per_year < -2 else "flat",
        },
        "yoy_change_pct": round(yoy, 1),
        "last_52w_mean": round(last_year, 1),
        "prior_52w_mean": round(prior_year, 1),
        "peak": peak,
        "spikes": spikes,
        "seasonality": {
            "strength": round(seasonality_strength, 2),
            "peak_month": peak_month,
            "low_month": low_month,
            "monthly_index": seasonal_index,
        },
    }


def _pairwise_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Share of voice and head-to-head stats across terms in the same chart."""
    if df.empty:
        return {"empty": True}
    totals = df.sum()
    sov = (totals / totals.sum() * 100).round(1).to_dict() if totals.sum() > 0 else {}
    recent = df.iloc[-52:].sum() if len(df) >= 52 else df.sum()
    sov_recent = (recent / recent.sum() * 100).round(1).to_dict() if recent.sum() > 0 else {}
    corr = df.corr().round(2).to_dict() if df.shape[1] > 1 else {}
    return {
        "empty": False,
        "share_of_voice_all_time_pct": sov,
        "share_of_voice_last_52w_pct": sov_recent,
        "correlation": corr,
    }


def _related_summary(rq: dict, rt: dict, top_n: int = 10) -> dict[str, Any]:
    def _head(rows, n=top_n):
        return [
            {k: v for k, v in r.items() if k in ("query", "topic_title", "topic_type", "value")}
            for r in (rows or [])[:n]
        ]

    return {
        "term": rq.get("term"),
        "queries_top": _head(rq.get("top")),
        "queries_rising": _head(rq.get("rising")),
        "topics_top": _head(rt.get("top")),
        "topics_rising": _head(rt.get("rising")),
    }


def compute_stats(raw_dir: Path, out_dir: Path, brief: dict) -> dict:
    """Walk the raw/ directory, produce one stats pack per bucket group.

    Output structure (written to out_dir/stats/):
      - brand.json        — brand_terms iot + related for brand head
      - competitors.json  — competitor iot + related
      - category.json     — category_terms iot + related
      - adjacent.json     — adjacent_terms iot + related
      - comparison.json   — comparison_pairs
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = raw_dir / "_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}

    def _load(name: str) -> dict:
        p = raw_dir / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def _summarize_iot_file(name: str) -> dict:
        iot = _load(f"iot_{name}")
        df = _iot_to_df(iot)
        if df.empty:
            return {"empty": True, "terms": iot.get("series", {}).keys() and list(iot["series"].keys()) or []}
        per_term = {term: _summarize_series(df[term]) for term in df.columns}
        return {
            "empty": False,
            "terms": list(df.columns),
            "per_term": per_term,
            "pairwise": _pairwise_summary(df),
        }

    import hashlib

    def _related_for(term: str) -> dict:
        safe = hashlib.md5(term.encode("utf-8")).hexdigest()[:10]
        rq = _load(f"rq_{safe}")
        rt = _load(f"rt_{safe}")
        if not rq and not rt:
            return {}
        return _related_summary(rq, rt)

    buckets = brief.get("buckets", {})
    packs: dict[str, dict] = {}

    # Brand
    if "brand_terms" in buckets:
        pack = {"iot": _summarize_iot_file("brand_terms")}
        if buckets["brand_terms"]:
            rel = _related_for(buckets["brand_terms"][0])
            if rel:
                pack["related"] = rel
        packs["brand"] = pack

    # Competitors
    if "competitor_terms" in buckets:
        comps = buckets["competitor_terms"]
        comp_pack: dict = {}
        if isinstance(comps, dict):
            if (raw_dir / "iot_competitors_head.json").exists():
                comp_pack["head_to_head"] = _summarize_iot_file("competitors_head")
            comp_pack["per_competitor"] = {}
            for name, terms in comps.items():
                if (raw_dir / f"iot_competitor_{name}.json").exists():
                    comp_pack["per_competitor"][name] = _summarize_iot_file(f"competitor_{name}")
                rel = _related_for(terms[0]) if terms else {}
                if rel:
                    comp_pack["per_competitor"].setdefault(name, {})["related"] = rel
        elif isinstance(comps, list):
            chunks = [f for f in raw_dir.iterdir() if f.name.startswith("iot_competitors_") and f.suffix == ".json"]
            comp_pack["chunks"] = {
                f.stem.replace("iot_", ""): _summarize_iot_file(f.stem.replace("iot_", "")) for f in chunks
            }
        packs["competitors"] = comp_pack

    # Category
    if "category_terms" in buckets:
        chunks = [f for f in raw_dir.iterdir() if f.name.startswith("iot_category_") and f.suffix == ".json"]
        cat_pack = {f.stem.replace("iot_", ""): _summarize_iot_file(f.stem.replace("iot_", "")) for f in chunks}
        related = {}
        for term in buckets["category_terms"][:3]:
            rel = _related_for(term)
            if rel:
                related[term] = rel
        packs["category"] = {"iot_chunks": cat_pack, "related": related}

    # Adjacent
    if "adjacent_terms" in buckets:
        chunks = [f for f in raw_dir.iterdir() if f.name.startswith("iot_adjacent_") and f.suffix == ".json"]
        adj_pack = {f.stem.replace("iot_", ""): _summarize_iot_file(f.stem.replace("iot_", "")) for f in chunks}
        related = {}
        for term in buckets["adjacent_terms"][:3]:
            rel = _related_for(term)
            if rel:
                related[term] = rel
        packs["adjacent"] = {"iot_chunks": adj_pack, "related": related}

    # Comparisons
    if buckets.get("comparison_pairs"):
        pairs = [f for f in raw_dir.iterdir() if f.name.startswith("iot_compare_") and f.suffix == ".json"]
        packs["comparison"] = {f.stem.replace("iot_", ""): _summarize_iot_file(f.stem.replace("iot_", "")) for f in pairs}

    for name, pack in packs.items():
        (out_dir / f"{name}.json").write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")

    return packs
