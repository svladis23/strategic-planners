"""
Aggregate article_classifications.csv into frames.csv, temporal.csv, ideological_split.csv.

Pure pandas. No LLM. Invoked by the orchestrator after Stage 5a (Categorical Extractor)
completes. This replaces ~1M tokens of LLM aggregation work in v1 with deterministic Python.

Usage:
    python scripts/aggregate_classifications.py <run_folder>

Example:
    python scripts/aggregate_classifications.py runs/open_university_higher_ed_value_2026-04-21
"""
import sys
import csv
from pathlib import Path
from collections import defaultdict, Counter

# Try to import pandas; fallback to stdlib csv if not available (rare).
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def split_multi(cell: str) -> list:
    """Split a semicolon-separated cell into a list, trimming whitespace. Empty → []."""
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []
    cell = str(cell).strip()
    if not cell or cell == "nan":
        return []
    return [s.strip() for s in cell.split(";") if s.strip()]


def load_classifications(path: Path):
    """Load article_classifications.csv as list of dicts."""
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def build_frames_csv(rows, out_path: Path):
    """Per frame: which outlets cover it at lead / secondary / passing prominence.

    Schema:
        frame,outlets_covering,prominence_per_outlet,example_article_urls
    """
    # frame -> outlet -> highest_prominence ("lead" > "secondary" > "passing")
    PROMINENCE_ORDER = {"lead": 0, "secondary": 1, "passing": 2}
    REVERSE_ORDER = {v: k for k, v in PROMINENCE_ORDER.items()}

    frame_outlet_prom = defaultdict(lambda: defaultdict(lambda: 99))  # 99 = absent
    frame_examples = defaultdict(lambda: defaultdict(list))  # frame -> outlet -> [urls at LEAD]

    for row in rows:
        outlet = row.get("outlet", "").strip()
        url = row.get("url", "").strip()
        for frame in split_multi(row.get("frames_lead", "")):
            if PROMINENCE_ORDER["lead"] < frame_outlet_prom[frame][outlet]:
                frame_outlet_prom[frame][outlet] = PROMINENCE_ORDER["lead"]
            if len(frame_examples[frame][outlet]) < 2:
                frame_examples[frame][outlet].append(url)
        for frame in split_multi(row.get("frames_secondary", "")):
            if PROMINENCE_ORDER["secondary"] < frame_outlet_prom[frame][outlet]:
                frame_outlet_prom[frame][outlet] = PROMINENCE_ORDER["secondary"]
            if len(frame_examples[frame][outlet]) < 2:
                frame_examples[frame][outlet].append(url)
        for frame in split_multi(row.get("frames_passing", "")):
            if PROMINENCE_ORDER["passing"] < frame_outlet_prom[frame][outlet]:
                frame_outlet_prom[frame][outlet] = PROMINENCE_ORDER["passing"]

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["frame", "outlets_covering", "prominence_per_outlet", "example_article_urls"])
        for frame in sorted(frame_outlet_prom.keys()):
            outlets = sorted(frame_outlet_prom[frame].keys())
            outlets_str = ";".join(outlets)
            prom_str = ";".join(REVERSE_ORDER[frame_outlet_prom[frame][o]] for o in outlets)
            # Collect up to 5 example URLs across the outlets
            examples = []
            for o in outlets:
                examples.extend(frame_examples[frame][o][:2])
                if len(examples) >= 5:
                    break
            examples_str = "|".join(examples[:5])
            w.writerow([frame, outlets_str, prom_str, examples_str])


def build_temporal_csv(rows, out_path: Path):
    """Per (frame, year): article count + example URLs + weak-sample flag.

    Schema:
        frame,year_or_quarter,article_count,weak_sample,example_urls
    """
    fy_articles = defaultdict(list)  # (frame, year) -> [url, ...]

    for row in rows:
        year = row.get("year", "").strip()
        url = row.get("url", "").strip()
        frames_here = (split_multi(row.get("frames_lead", ""))
                       + split_multi(row.get("frames_secondary", "")))
        for frame in set(frames_here):
            fy_articles[(frame, year)].append(url)

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["frame", "year_or_quarter", "article_count", "weak_sample", "example_urls"])
        for (frame, year) in sorted(fy_articles.keys()):
            urls = fy_articles[(frame, year)]
            count = len(urls)
            weak = "true" if count < 5 else "false"
            w.writerow([frame, year, count, weak, "|".join(urls[:3])])


def build_ideological_split_csv(rows, out_path: Path):
    """Per frame: which ideological positions frame it, with the valence they use.

    Schema:
        frame,ideological_position,article_count,framing_valences,example_urls
    """
    # (frame, position) -> {'count': int, 'valences': [valence, ...], 'urls': [...]}
    fp_data = defaultdict(lambda: {"count": 0, "valences": [], "urls": []})

    for row in rows:
        pos = row.get("ideological_position", "").strip()
        url = row.get("url", "").strip()
        valence = row.get("ideological_framing_valence", "").strip()
        lead_frames = split_multi(row.get("frames_lead", ""))
        for frame in lead_frames:
            key = (frame, pos)
            fp_data[key]["count"] += 1
            if valence and valence not in fp_data[key]["valences"]:
                fp_data[key]["valences"].append(valence)
            if len(fp_data[key]["urls"]) < 3:
                fp_data[key]["urls"].append(url)

    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["frame", "ideological_position", "article_count", "framing_valences", "example_urls"])
        for (frame, pos) in sorted(fp_data.keys()):
            d = fp_data[(frame, pos)]
            w.writerow([frame, pos, d["count"], "; ".join(d["valences"]), "|".join(d["urls"])])


def main():
    if len(sys.argv) != 2:
        print("Usage: python aggregate_classifications.py <run_folder>")
        sys.exit(1)

    run_folder = Path(sys.argv[1])
    assert run_folder.is_dir(), f"Run folder not found: {run_folder}"

    in_path = run_folder / "article_classifications.csv"
    assert in_path.exists(), f"article_classifications.csv not found at {in_path}"

    rows = load_classifications(in_path)
    print(f"Loaded {len(rows)} article classifications.")

    frames_out = run_folder / "frames.csv"
    temporal_out = run_folder / "temporal.csv"
    ideo_out = run_folder / "ideological_split.csv"

    build_frames_csv(rows, frames_out)
    print(f"Wrote {frames_out.name}")

    build_temporal_csv(rows, temporal_out)
    print(f"Wrote {temporal_out.name}")

    build_ideological_split_csv(rows, ideo_out)
    print(f"Wrote {ideo_out.name}")

    print("Aggregation complete.")


if __name__ == "__main__":
    main()
