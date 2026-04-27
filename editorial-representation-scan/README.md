# Editorial Representation Scan

A Claude Code skill for mapping how a topic is framed, discussed, and constructed in **Israeli news media and cultural commentary**. The output is a 40–60 slide branded deck with every claim cited to a specific article.

This is not consumer voice analysis, social listening, or search demand — it analyzes how Israeli journalists, editors, and commentators *represent* a topic.

---

## What it produces

A SumItUp-branded PowerPoint deck (40–60 slides + indexed appendix) covering:

- Top frames with outlet coverage and ideological splits
- Hebrew vocabulary clusters in their rhetorical context
- Temporal arc of the discourse
- Ideological battlegrounds (side-by-side quote comparisons)
- Cast of named experts and standout articles
- Absences (what's *not* said) with evidence
- Client-specific positioning translation

Total wall-clock: 6–9 hours. User active time: ~50 min (intake + 2 checkpoints + deck review).

---

## Architecture

Main orchestrator + 10 specialized sub-agents dispatched via Claude Code's Task tool, plus a deterministic Python deck renderer:

| # | Agent | Stage | Model |
|---|---|---|---|
| 1 | Category Mapper | 2 | Sonnet |
| 2 | Collector (×2–3 parallel) | 4 | Haiku |
| 3 | Pre-digest | 4.5 | Haiku |
| 4 | Categorical Extractor | 5a | Sonnet |
| 5 | Textual Extractor | 5b | Sonnet |
| 6 | Interpretive Synthesizer | 5c | Sonnet |
| 7 | Verifier | 5.5 | Sonnet |
| 8 | Quote Curator | 5.7 | Sonnet |
| 9 | Frame Deep-Dive Writer | 5.8 | Sonnet |
| 10 | Client Translator (conditional) | 5.9 | Sonnet |
| — | Deck Architect + Python renderer | 6 | Sonnet + Python |

Haiku is reserved for mechanical filtering and template summarization. Hebrew nuance, cross-corpus synthesis, and strategic reasoning stay on Sonnet.

---

## Pipeline (six stages)

| Stage | What happens | Wall-clock | User attention |
|---|---|---|---|
| 1. Brief intake | Conversational — topic, client, time window, depth | 5 min | 5 min |
| 2. Category mapping | Sonnet agent maps the discourse landscape | 20 min | — |
| 3. Plan generation | 18–25 Hebrew queries across 5 angles + adversarial | 10 min | 10 min ✓ |
| 4. Collection | 2–3 parallel Haiku collectors, snippet-first filtering | 1.5–3 hr | — |
| 4.5. Pre-digest | One Haiku pass produces a rich JSONL digest | 40 min | — |
| 5. Analysis | Categorical + textual extraction → narrative synthesis | 90 min | — |
| 5.5. Verification | Spot-check 8 articles, 3 load-bearing claims each | 15 min | — |
| 5.7–5.8. Curation + deep-dives | Quote Curator + Frame Deep-Dive Writer (parallel) | 45 min | — |
| 5.9. Client translation | Strategic positioning notes (conditional) | 15 min | — |
| Checkpoint | Approve analytical summary | 5 min | 10 min ✓ |
| 6a. Deck Architect | Writes `deck_plan.yaml` | 25 min | — |
| 6b. Render | Deterministic Python → `deck.pptx` | 2 min | — |
| Deck review | User feedback | — | 20 min |

Two mandatory user checkpoints (✓): after Stage 3 (approve collection plan) and after Stage 5 (approve analytical summary before deck generation).

---

## How to run

From Claude Code, `cd` into this folder and start a conversation:

- *"Let's run an editorial scan"*
- *"Start a new scan for [client] on [topic]"*
- *"Resume the active scan"*

Claude Code reads `CLAUDE.md` and begins Stage 1 intake. Answer the intake questions, confirm the brief, and the run kicks off. State is persisted in `runs/<run_id>/progress.json` after every stage — interrupted runs resume from the last checkpoint.

---

## Hard rules (a few highlights)

- **Hebrew-first searches**, English synthesis. Hebrew quotes preserved with English gloss.
- **Every deck claim cites a specific article** in the appendix.
- **Never claim consumer voice.** Phrases are "Israeli media represents X as…" not "Israelis think X."
- **Snippet-first collection** — filter by URL pattern + snippet before fetching, max 3 fetches per (query × source).
- **Saturation-aggressive stopping** — stop a query when 2 consecutive batches add <2 new articles.
- **Mechanical aggregation only** for `frames.csv` / `temporal.csv` / `ideological_split.csv` — `scripts/aggregate_classifications.py` does it deterministically. No LLM aggregation.
- **Deck planning vs. rendering separation** — the Deck Architect agent writes `deck_plan.yaml`, then `scripts/render_deck.py` builds the deck from it. The LLM never writes python-pptx code directly.

Full ruleset: see `CLAUDE.md`.

---

## Folder structure

```
editorial-representation-scan/
├── CLAUDE.md                  # Orchestration logic — Claude Code reads this
├── README.md                  # This file
├── tier1_sources.yaml         # Fixed Israeli news source list
├── agents/                    # 11 sub-agent prompts (one per role)
├── docs/                      # Calibration protocol + slide template reference
├── scripts/                   # 3 Python tools (aggregate, render, helpers)
└── runs/                      # Auto-created on first run; one folder per scan
```

A run folder contains: `brief.yaml`, `category_map.md`, `plan.yaml`, `articles/`, `articles_digest.jsonl`, `article_classifications.csv` + 3 aggregated CSVs, vocabulary/experts CSVs, 5 narrative `.md` files, `verification.md`, quote-curator outputs, `frame_deep_dives/`, `deck_plan.yaml`, `deck.pptx`, `progress.json`.

---

## Dependencies

- **Claude Code** with Task, web_search, web_fetch tools
- **Skills:** `sumitup-powerpoint` (brand compliance) — required for Stage 6
- **Python:** `python-pptx`, `pyyaml`, `pandas`, `lxml`
- `web_fetch` rate limit: ~100 uncached/hour. Parallel collectors share this budget — orchestrator caps at 3.

---

## Run cadence

- **One-shot** for new client onboarding in unfamiliar topic territory
- **Quarterly refresh** for retainer clients (compare deltas, surface newly-emerged frames)
- **One-time `quick_scan` (50 articles)** for pitch preparation
- **`deep_dive` (80 articles)** for strategic positioning work

---

## Why Claude Code (not Cowork)

- Stages 2, 4, 5 are ~80% programmatic — search, fetch, dedup, cluster, write CSVs
- Stage 4 needs parallel sub-agents with scoped context windows; Cowork collapses them into one bloated context
- Rate-limit handling and state persistence need real batch logic
- File handling (articles/, CSVs, state files) is native here
- Reuses existing infrastructure: Skills library, sub-agent patterns, sumitup-powerpoint skill

---

## Version

Current: **v2.1** (depth expansion). Pre-digest schema enriched with 3 quotes per article, rhetorical stance, and audience signal. Two new sub-agents (Quote Curator, Frame Deep-Dive Writer) feed a deterministic deck renderer. Deck grew from ~15 slides (v1) to 40–60 slides at ~55% of v1's cost.

See `CLAUDE.md` for full version history and migration notes.
