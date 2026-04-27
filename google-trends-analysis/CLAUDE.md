# Google Trends Analysis Workflow

This project runs brand-and-category Google Trends analyses for SumItUp clients (Israel-focused, Hebrew + English).

## The workflow
User invokes `/trends <brand> <category>`. The skill at `.claude/skills/trends/SKILL.md` orchestrates:

1. **Brief** — main session (Opus 4.7) generates query plan as JSON
2. **Fetch** — `src/runner.py` pulls pytrends data with sqlite cache, rate-limited
3. **Stats** — deterministic pandas computes trend slope, peaks, seasonality, related queries
4. **Charts** — matplotlib PNGs saved to disk
5. **Interpret** — 3 sub-agents in parallel read their stats pack only:
   - `trends-brand-health` (Haiku)
   - `trends-category-dynamics` (Haiku)
   - `trends-audience-insight` (Opus — Hebrew nuance matters)
6. **Synthesize** — `trends-synthesizer` (Opus) reads findings, decides if deepening round needed (max 2)
7. **PPT** — main session invokes `sumitup-powerpoint` skill to build deck

## Key design rules
- **LLMs never see raw time-series data.** Stats layer digests first. This is the main token optimization.
- **Sub-agents are siloed** — each reads only its own stats pack + chart paths, not other agents' output.
- **sqlite cache** at `cache.db` — deepening loop reuses overlapping queries for free.
- **Serial pytrends requests** with 15-25s delays; no parallelism against Google.
- **Geo = Israel only.** No geographic sub-agent. User only works in the Israeli market.
- **Interactive brief, step-by-step.** Walk through all 7 brief sections (question/hypotheses → brand → competitors → category → adjacent → comparisons → final confirm), get approval each. Never bulk-propose. Only bypass if Vlad explicitly says "one run / no permissions".
- **Every claim in the PPT gets a plot.** Text-only slides allowed only for cover, section dividers, exec summary, caveats, closing. Bar/line/big-stat per claim. `charts.py` auto-generates sov_bar, yoy_bar, rising_queries, top_queries for this.

## Python environment
Always use: `C:\Users\vlad\.claude\venv\Scripts\python.exe`
Never anaconda.

## Run outputs
Each run creates `data/{brand_slug}_{timestamp}/` containing:
- `brief.json` — query plan
- `raw/*.parquet` — cached pytrends pulls
- `stats/*.json` — digested metrics per bucket
- `charts/*.png` — visualizations
- `findings/*.md` — sub-agent outputs
- `synthesis.md` — final narrative
- `deck.pptx` — final output

## Buckets (query groups)
- `brand_terms` — brand name + variants (he/en)
- `competitor_terms` — grouped by competitor
- `category_terms` — generic category queries
- `adjacent_terms` — emotional/behavioral language around the category
- `comparison_pairs` — head-to-head ("menora vs migdal")
