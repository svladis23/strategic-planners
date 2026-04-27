"""Matplotlib chart generation. Writes PNGs to disk; agents reference paths.

Hebrew labels require a font that supports the script. On Windows,
'Arial' or 'Segoe UI' typically work. We also reverse Hebrew strings
when matplotlib refuses to render RTL properly (fallback path).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

try:
    from bidi.algorithm import get_display as _bidi
except ImportError:  # fallback: no-op
    def _bidi(s: str) -> str:
        return s

# Prefer a font with Hebrew glyph coverage
plt.rcParams["font.family"] = ["Segoe UI", "Arial", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

_HEBREW_RE = re.compile(r"[\u0590-\u05FF]")


def _rtl(s: str) -> str:
    """Convert logical-order Hebrew string to visual order for matplotlib.
    Leaves pure-ASCII strings untouched."""
    if not isinstance(s, str) or not _HEBREW_RE.search(s):
        return s
    return _bidi(s)


def _iot_to_df(iot: dict) -> pd.DataFrame:
    if iot.get("empty") or not iot.get("dates"):
        return pd.DataFrame()
    idx = pd.to_datetime(iot["dates"])
    return pd.DataFrame(iot["series"], index=idx)


def _line(df: pd.DataFrame, title: str, out_path: Path) -> Path | None:
    if df.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    for col in df.columns:
        ax.plot(df.index, df[col], label=_rtl(col), linewidth=1.6)
    ax.set_title(_rtl(title), fontsize=13)
    ax.set_ylabel("Search interest (0-100)")
    ax.set_xlabel("")
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.25)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _bar(series: dict, title: str, out_path: Path, xlabel: str = "") -> Path | None:
    if not series:
        return None
    labels = [_rtl(str(k)) for k in series.keys()]
    values = list(series.values())
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(labels, values)
    ax.set_title(_rtl(title))
    ax.set_ylabel(xlabel or "Value")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    ax.grid(alpha=0.25, axis="y")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _timeframe_label(tf: str) -> str:
    mapping = {
        "today 5-y": "5y",
        "today 12-m": "12mo",
        "today 3-m": "3mo",
        "today 1-m": "1mo",
        "today 1-y": "1y",
        "all": "all time",
    }
    return mapping.get(tf, tf)


def build_charts(raw_dir: Path, out_dir: Path, brief: dict) -> dict[str, str]:
    """Generate all charts referenced by the skill/PPT.

    Returns a dict mapping chart_name -> path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    made: dict[str, str] = {}
    tf_label = _timeframe_label(brief.get("timeframe", "today 5-y"))

    def _load(name: str) -> dict:
        p = raw_dir / f"{name}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def _save_line(iot_name: str, chart_name: str, title: str):
        # iot_name is the stem WITHOUT the "iot_" prefix
        iot = _load(f"iot_{iot_name}")
        df = _iot_to_df(iot)
        path = out_dir / f"{chart_name}.png"
        if _line(df, title, path):
            made[chart_name] = str(path)

    buckets = brief.get("buckets", {})

    # Brand vs competitors (head-to-head)
    if (raw_dir / "iot_competitors_head.json").exists():
        _save_line("competitors_head", "brand_vs_competitors", f"Brand vs. Competitors — search interest ({tf_label})")

    # Brand alone
    if "brand_terms" in buckets:
        _save_line("brand_terms", "brand_terms", f"Brand terms — search interest ({tf_label})")

    # Per-competitor term bundles
    if isinstance(buckets.get("competitor_terms"), dict):
        for name in buckets["competitor_terms"]:
            fname = f"iot_competitor_{name}"
            if (raw_dir / f"{fname}.json").exists():
                _save_line(f"competitor_{name}", f"competitor_{name}", f"{name} — brand term variants ({tf_label})")

    # Category chunks
    if "category_terms" in buckets:
        for f in raw_dir.glob("iot_category_*.json"):
            stem = f.stem.replace("iot_", "")
            _save_line(stem, f"{stem}", f"Category — {stem}")

    # Adjacent chunks
    if "adjacent_terms" in buckets:
        for f in raw_dir.glob("iot_adjacent_*.json"):
            stem = f.stem.replace("iot_", "")
            _save_line(stem, f"{stem}", f"Adjacent — {stem}")

    # Comparison pairs
    for f in raw_dir.glob("iot_compare_*.json"):
        stem = f.stem.replace("iot_", "")
        iot = _load(f.stem)
        terms = list((iot.get("series") or {}).keys())
        title = f"Comparison — {' vs '.join(terms)}" if terms else f"Comparison — {stem}"
        _save_line(stem, stem, title)

    # Seasonality chart for brand head term
    if "brand_terms" in buckets and buckets["brand_terms"]:
        brand_iot = _load("iot_brand_terms")
        df = _iot_to_df(brand_iot)
        head = buckets["brand_terms"][0]
        if not df.empty and head in df.columns:
            monthly = df[head].groupby(df.index.month).mean()
            _bar(
                monthly.round(1).to_dict(),
                f"Seasonality — {head} (avg by month)",
                out_dir / "brand_seasonality.png",
                xlabel="Avg search interest",
            )
            made["brand_seasonality"] = str(out_dir / "brand_seasonality.png")

    # Share-of-voice bar chart (brand + competitors head-to-head)
    head_iot = _load("iot_competitors_head")
    head_df = _iot_to_df(head_iot)
    if not head_df.empty:
        totals = head_df.sum()
        if totals.sum() > 0:
            sov_all = (totals / totals.sum() * 100).round(1)
            path = out_dir / "sov_bar.png"
            _bar(sov_all.to_dict(), f"Share of voice — all-time ({tf_label})", path, xlabel="% of total search")
            made["sov_bar"] = str(path)
        if len(head_df) >= 52:
            recent = head_df.iloc[-52:].sum()
            if recent.sum() > 0:
                sov_r = (recent / recent.sum() * 100).round(1)
                path = out_dir / "sov_bar_52w.png"
                _bar(sov_r.to_dict(), "Share of voice — last 52 weeks", path, xlabel="% of total search")
                made["sov_bar_52w"] = str(path)

    # YoY % change bar chart across key terms (brand + competitor heads)
    yoy_values: dict[str, float] = {}
    stats_dir = out_dir.parent / "stats"
    try:
        brand_stats = json.loads((stats_dir / "brand.json").read_text(encoding="utf-8")) if (stats_dir / "brand.json").exists() else {}
        comp_stats = json.loads((stats_dir / "competitors.json").read_text(encoding="utf-8")) if (stats_dir / "competitors.json").exists() else {}
        for term, per in (brand_stats.get("iot", {}).get("per_term", {}) or {}).items():
            if not per.get("empty"):
                yoy_values[term] = per.get("yoy_change_pct", 0.0)
        head_pack = comp_stats.get("head_to_head", {}).get("per_term", {})
        for term, per in (head_pack or {}).items():
            if term not in yoy_values and not per.get("empty"):
                yoy_values[term] = per.get("yoy_change_pct", 0.0)
    except Exception:
        pass
    if yoy_values:
        path = out_dir / "yoy_bar.png"
        _bar(yoy_values, "YoY % change — last 52w vs prior 52w", path, xlabel="YoY %")
        made["yoy_bar"] = str(path)

    # Rising & top queries bar charts for 3 key terms (brand head, category[0], adjacent[0])
    key_terms: list[str] = []
    if buckets.get("brand_terms"):
        key_terms.append(buckets["brand_terms"][0])
    if buckets.get("category_terms"):
        key_terms.append(buckets["category_terms"][0])
    if buckets.get("adjacent_terms"):
        key_terms.append(buckets["adjacent_terms"][0])

    import hashlib as _hl

    for term in key_terms:
        safe = _hl.md5(term.encode("utf-8")).hexdigest()[:10]
        rq = _load(f"rq_{safe}")
        if not rq:
            continue
        # Rising
        rising = (rq.get("rising") or [])[:10]
        if rising:
            series = {}
            for row in rising:
                q = row.get("query", "")
                v = row.get("value", 0)
                if q:
                    series[q[:50]] = int(v) if v != "Breakout" else 5000
            if series:
                path = out_dir / f"rising_{safe}.png"
                _bar(series, f"Rising queries — {term}", path, xlabel="% change (capped 5000 for 'Breakout')")
                made[f"rising_{term}"] = str(path)
        # Top
        top = (rq.get("top") or [])[:10]
        if top:
            series = {row.get("query", "")[:50]: int(row.get("value", 0)) for row in top if row.get("query")}
            if series:
                path = out_dir / f"top_{safe}.png"
                _bar(series, f"Top queries — {term}", path, xlabel="Relative search volume (0-100)")
                made[f"top_{term}"] = str(path)

    (out_dir / "_index.json").write_text(json.dumps(made, ensure_ascii=False, indent=2), encoding="utf-8")
    return made
