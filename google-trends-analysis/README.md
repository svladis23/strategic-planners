# Google Trends Analysis

A Claude Code skill that runs a brand-and-category Google Trends analysis for a client (Israel-focused, Hebrew + English). The output is a SumItUp-branded PowerPoint deck where every claim is backed by a chart.

Built around a hard token-economics rule: **LLMs never see raw time-series data.** A pandas stats layer digests pytrends pulls into compact JSON packs; sub-agents read only their own pack.

---

## What it produces

For each `/trends <brand> <category>` invocation:

- An interactive query brief (7 sections, approved by the user one at a time)
- pytrends pulls cached in sqlite (free reuse on deepening rounds)
- A stats layer (`stats/*.json`) — trend slope, peaks, seasonality, share-of-voice, rising queries, top queries
- matplotlib chart PNGs — `sov_bar`, `yoy_bar`, `rising_queries_*`, `top_queries_*`, brand trajectory, seasonality
- 3 parallel sub-agent findings (brand health, category dynamics, audience insight) — each siloed to its own stats pack
- A synthesizer pass that decides whether to deepen (max 2 rounds total)
- Final PPT deck via the `sumitup-powerpoint` skill — every claim slide carries a chart

---

## Architecture

Main orchestrator + 4 specialized sub-agents + deterministic Python pipeline:

| Component | Role | Model |
|---|---|---|
| `trends-brand-health` | Brand-level trajectory, SoV, seasonality | Haiku |
| `trends-category-dynamics` | Category trajectory, rising queries, sub-segments | Haiku |
| `trends-audience-insight` | Hebrew-language nuance, intent + emotion signals | Opus |
| `trends-synthesizer` | Decides deepening + writes final synthesis | Opus |
| `src/runner.py` | CLI entry: `init`, `fetch`, `stats`, `charts` | Python |
| `src/fetcher.py` | pytrends pulls, sqlite cache, polite rate-limiting | Python |
| `src/stats.py` | pandas digest into stats packs | Python |
| `src/charts.py` | matplotlib PNG generation | Python |
| `src/build_deck.py` | PPT assembly (via sumitup-powerpoint skill) | Python |

---

## Pipeline (eight steps)

| Step | What happens | Model | Time |
|---|---|---|---|
| 1. Interactive brief | 7 sections approved one-by-one (research Q + hypotheses, brand, competitors, category, adjacent, comparison pairs, final) | Opus | 10–20 min |
| 2. Fetch | pytrends pulls with 15–25s delays, sqlite cache | Python | 5–15 min |
| 3. Stats + charts | pandas digest + matplotlib PNGs | Python | <10 sec |
| 4. Sub-agents | 3 parallel agents read their own stats pack | Haiku + Opus | 5 min |
| 5. Synth round 1 | Decide: deepen or finalize | Opus | 2 min |
| 5b. Deepen (optional) | Re-fetch with extra buckets, re-run stats + sub-agents | mixed | 10 min |
| 6. Final synthesis | Write `synthesis.md` | Opus | 3 min |
| 7. Build deck | sumitup-powerpoint skill produces PPTX | Python | 1 min |
| 8. Report | Path + headline finding | — | — |

---

## Folder structure

```
google-trends-analysis/
├── README.md                              # This file
├── CLAUDE.md                              # Orchestration logic — Claude Code reads this
├── requirements.txt                       # pytrends, pandas, matplotlib, python-bidi, jsonschema
├── .claude/
│   ├── agents/
│   │   ├── trends-audience-insight.md
│   │   ├── trends-brand-health.md
│   │   ├── trends-category-dynamics.md
│   │   └── trends-synthesizer.md
│   └── skills/trends/
│       └── SKILL.md                       # Slash-command spec for /trends
└── src/
    ├── __init__.py
    ├── runner.py                          # CLI entry point
    ├── fetcher.py                         # pytrends + sqlite cache
    ├── stats.py                           # pandas digest
    ├── charts.py                          # matplotlib PNGs
    └── build_deck.py                      # PPT assembly helper
```

A run produces `data/<brand_slug>_<timestamp>/` containing `brief.json`, `raw/*.parquet`, `stats/*.json`, `charts/*.png`, `findings/*.md`, `synthesis.md`, `deck.pptx`. The `data/` folder is gitignored — analysis outputs stay local.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Python 3.10+ recommended. `pytrends` uses **no API key** — it scrapes Google Trends' public endpoints. No credentials anywhere in this skill.

### 2. Adjust paths

`CLAUDE.md` and `SKILL.md` reference an absolute Python path (`C:\Users\vlad\.claude\venv\Scripts\python.exe`). Replace with your environment's Python — e.g. `python` if it's on PATH, or your venv's path.

### 3. Run folder

`data/<brand>_<timestamp>/` is auto-created on `runner.py init`. The sqlite cache (`cache.db`) is created in the project root on first fetch.

---

## How to invoke

From Claude Code, `cd` into this folder. The skill activates on the slash command:

```
/trends <brand> <category>
```

Example: `/trends Menora pension`

If the user provides no args, the orchestrator asks for brand + category before proceeding.

To skip the interactive brief (one-shot mode): say *"run in one go / no permissions / decide alone"* — the orchestrator still does all 7 brief sections internally and shows the consolidated brief as a final summary, but doesn't pause for approval.

---

## Hard rules (the load-bearing ones)

- **LLMs never see raw time-series data.** Stats layer digests first. Sub-agents and the main session only ever read JSON packs and chart paths — never `raw/*.parquet`.
- **Sub-agents are siloed** — each reads only its own stats pack, not other agents' output. Synthesizer reads the three findings files.
- **Serial pytrends requests with 15–25s delays.** No parallelism against Google. The cache makes deepening rounds free for overlapping queries.
- **Geo = Israel only** (`hl=he-IL`, `tz=120`). No geographic sub-agent. Hebrew nuance matters in the audience-insight agent.
- **Interactive brief, step-by-step.** Walk through all 7 brief sections one at a time. Never bulk-propose.
- **Every claim slide carries a chart.** Text-only slides allowed only for cover, section dividers, executive summary, data caveats, closing. If a claim isn't worth charting, cut it.
- **Max 5 terms per pytrends request** (hard API limit).
- **Max 2 deepening rounds total.** Cap is enforced in the synthesizer.

---

## Why this skill exists

Google Trends is the cheapest way to read demand-side signal in Israel — no panel cost, no survey. But the raw time series is dense and noisy, and LLMs handle it poorly. This skill makes it work by:

1. Spending real attention on the brief (the bet that costs the most token budget)
2. Letting Python do the math (slope, peaks, seasonality, SoV) — not the LLM
3. Siloing sub-agents on small JSON packs to avoid context bloat
4. Forcing every deck claim to be chartable — no hand-wavy synthesis
