"""CLI orchestrator. The /trends skill calls this.

Usage:
    python src/runner.py init --brief path/to/brief.json --out data/run_xyz
    python src/runner.py fetch --run data/run_xyz
    python src/runner.py stats --run data/run_xyz
    python src/runner.py charts --run data/run_xyz
    python src/runner.py all --brief path/to/brief.json --out data/run_xyz
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

# Force UTF-8 stdout so Hebrew prints don't crash on Windows cp1252 consoles
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

# Silence pandas FutureWarnings from pytrends — they drown real output
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="pytrends.*")
warnings.filterwarnings("ignore", category=FutureWarning, message=".*Downcasting.*")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.fetcher import fetch_brief
from src.stats import compute_stats
from src.charts import build_charts


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9\u0590-\u05FF_\- ]+", "", s).strip().replace(" ", "_").lower()
    return s or "run"


def _load_brief(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cmd_init(args) -> None:
    brief = _load_brief(Path(args.brief))
    brand = _slugify(brief.get("brand", "brand"))
    ts = time.strftime("%Y%m%d_%H%M%S")
    out = Path(args.out) if args.out else Path("data") / f"{brand}_{ts}"
    out.mkdir(parents=True, exist_ok=True)
    (out / "brief.json").write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(out))


def cmd_fetch(args) -> None:
    run = Path(args.run)
    brief = _load_brief(run / "brief.json")
    print(f"[fetch] run={run} geo={brief.get('geo', 'IL')} timeframe={brief.get('timeframe', 'today 5-y')}")
    manifest = fetch_brief(brief, run)
    n_iot = len(manifest.get("iot", {}))
    n_rel = len(manifest.get("related", {}))
    print(f"[fetch] wrote {n_iot} iot files, {n_rel} related sets")


def cmd_stats(args) -> None:
    run = Path(args.run)
    brief = _load_brief(run / "brief.json")
    packs = compute_stats(run / "raw", run / "stats", brief)
    print(f"[stats] wrote {len(packs)} packs: {list(packs.keys())}")


def cmd_charts(args) -> None:
    run = Path(args.run)
    brief = _load_brief(run / "brief.json")
    made = build_charts(run / "raw", run / "charts", brief)
    print(f"[charts] wrote {len(made)} charts")
    for name, path in made.items():
        print(f"  {name}: {path}")


def cmd_all(args) -> None:
    cmd_init(args)
    # Re-derive run dir from what cmd_init printed; simpler to re-compute
    brief = _load_brief(Path(args.brief))
    brand = _slugify(brief.get("brand", "brand"))
    # cmd_init used timestamp; for 'all' we need to know the exact dir.
    # Simpler: take args.out if provided, otherwise scan for newest matching dir.
    if args.out:
        run_dir = Path(args.out)
    else:
        data_dir = Path("data")
        candidates = sorted(data_dir.glob(f"{brand}_*"), key=lambda p: p.stat().st_mtime, reverse=True)
        run_dir = candidates[0] if candidates else None
        if run_dir is None:
            raise SystemExit("could not resolve run dir")

    class _A:
        pass

    a = _A()
    a.run = str(run_dir)
    cmd_fetch(a)
    cmd_stats(a)
    cmd_charts(a)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--brief", required=True)
    p_init.add_argument("--out", default=None)
    p_init.set_defaults(func=cmd_init)

    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("--run", required=True)
    p_fetch.set_defaults(func=cmd_fetch)

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("--run", required=True)
    p_stats.set_defaults(func=cmd_stats)

    p_charts = sub.add_parser("charts")
    p_charts.add_argument("--run", required=True)
    p_charts.set_defaults(func=cmd_charts)

    p_all = sub.add_parser("all")
    p_all.add_argument("--brief", required=True)
    p_all.add_argument("--out", default=None)
    p_all.set_defaults(func=cmd_all)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
