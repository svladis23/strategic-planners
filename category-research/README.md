# Category Research

A Claude Code skill for deep competitive analysis when onboarding a new client brand into an unfamiliar category. Input is a brand name + category. Output is a SumItUp-branded English PowerPoint deck covering the client and its competitors, with research briefs and a clickable sources appendix.

Hebrew sources for Israeli market depth, English sources for global context — deck is in English.

---

## What it produces

For each client onboarding run:
- One company brief per competitor (Sonnet research subagents) — financials, positioning, recent activity, KPIs JSON
- Marketing-intelligence brief per competitor — ad spend, agency, campaign inventory, media mix, share of voice
- YouTube creative scan per competitor — top videos by views over the last 2 years, with transcripts (requires YouTube API setup, see below)
- Deck outline written by a `deck-architect` subagent (Opus) covering perceptual maps, message-pillars matrix, distinctiveness audit, positioning gap, and a hyperlinked sources appendix
- Rendered PPTX via the `sumitup-powerpoint` skill, with matplotlib chart PNGs framed in SumItUp brand teal

---

## Architecture

Main orchestrator + 5 specialized sub-agents:

| Agent | Role | Model |
|---|---|---|
| `company-researcher` | Per-company brief + KPIs JSON | Sonnet |
| `competitor-finder` | Sized competitor list (3–10) | Haiku |
| `marketing-researcher` | Marketing-intelligence pass | Sonnet |
| `youtube-scanner` | Creative pull from YouTube | Sonnet |
| `deck-architect` | Outline + chart specs | Opus |

Phase 3 fans all per-competitor agents out in a single parallel batch — for N competitors, that's 3N + 2 agents in one message.

---

## Pipeline (five phases)

| Phase | What happens | Approval gate |
|---|---|---|
| 0. Setup | Confirm brand + category, create run folder | — |
| 1. Client research | One `company-researcher` for the client | — |
| 2. Competitor identification | `competitor-finder` returns sized list | ✓ Gate |
| 3. Per-competitor research | Parallel: company + marketing + youtube per competitor | — |
| 4. Synthesis + outline | `deck-architect` writes outline + chart specs | ✓ Gate |
| 5. Render | matplotlib charts → PPTX via sumitup-powerpoint skill | — |

In **default mode**, the orchestrator pauses at gates and waits for explicit approval. In **one-go mode** ("run in one go", "trust your instinct"), gates become non-blocking checkpoints — the orchestrator posts inline status updates and continues.

---

## Folder structure

```
category-research/
├── README.md                                   # This file
└── .claude/
    ├── agents/
    │   ├── company-researcher.md
    │   ├── competitor-finder.md
    │   ├── deck-architect.md
    │   ├── marketing-researcher.md
    │   └── youtube-scanner.md
    └── skills/
        └── competitive-analysis/
            ├── SKILL.md                        # Workflow definition
            ├── brief-schema.md                 # Standard brief structure
            └── sources.md                      # Source-priority guidance
```

When Claude Code starts in this folder, it discovers the `.claude/` skill and agents automatically. The skill lives under `.claude/skills/competitive-analysis/` and is invoked when the user asks for a "competitive analysis", "competitor research", or "research [brand] in [category]" — see SKILL.md for the full trigger list.

---

## Setup

### 1. Adjust paths

`SKILL.md` references an absolute project root (`C:\Users\vlad\OneDrive\Desktop\claude\Competitive analysis`). When you clone this repo, replace that path with your own working directory — typically `<repo>/category-research/`.

### 2. Run folders

Create a run folder per client onboarding:

```
runs/<brand-slug>/<YYYY-MM-DD>/
├── briefs/
├── marketing/
├── youtube/
└── deck/
```

These are gitignored — client research stays local.

### 3. YouTube API (optional, for the `youtube-scanner` agent)

The `youtube-scanner` agent in `.claude/agents/youtube-scanner.md` references a helper script (`scripts/youtube_scan.py`) that pulls top videos via the YouTube Data API v3 and fetches transcripts via `youtube-transcript-api`. **The script itself is not included in this repo** — to enable this phase you need to either:

**Option A — Write your own helper script.**

Required functionality:
- Resolve a brand name to a YouTube channel ID via `youtube.search.list`
- Fetch top N videos by view count in a configurable time window via `youtube.search.list` + `youtube.videos.list`
- Fetch transcripts (Hebrew, then English) via `youtube-transcript-api`
- Emit a single JSON blob the `youtube-scanner` agent can read

Recommended dependencies:
```
google-api-python-client
youtube-transcript-api
python-dotenv
```

**Option B — Stub it out.**

If you don't need YouTube creative analysis, edit SKILL.md to drop Phase 3's `youtube-scanner` agent and remove the corresponding agent file.

### 4. YouTube API credentials

If you implement Option A:

1. Create a project at https://console.cloud.google.com
2. Enable the **YouTube Data API v3**
3. Create an API key (APIs & Services → Credentials → Create credentials → API key)
4. Restrict the key to YouTube Data API only
5. Save it to `.claude/skills/competitive-analysis/.env`:
   ```
   YOUTUBE_API_KEY=YOUR_KEY_HERE
   ```
6. The `.env` file is gitignored — never commit your key

YouTube Data API quota: 10,000 units/day on the free tier. Each scan uses ~102 units (1 search × 100 + 1 videos.list + 1 channels.list), so you can run ~98 brand scans per day before hitting the quota.

### 5. Other dependencies

- **`sumitup-powerpoint` skill** — required for Phase 5 rendering. Provides brand-compliant slide templates.
- **matplotlib** — for chart PNGs (Phase 5).
- **LibreOffice (optional)** — for PPTX → PDF visual QA. The skill flags missing LibreOffice rather than skipping silently.

---

## How to invoke

From Claude Code, `cd` into this folder and start a conversation. The skill activates on phrases like:

- *"Run a competitive analysis for [brand] in [category]"*
- *"Competitor research for [client]"*
- *"New client briefing: [brand]"*

For an end-to-end run without manual approval gates, add *"run in one go"* or *"trust your instinct"*.

---

## Hard rules (highlights)

- Every claim in a brief carries a **date and source URL**
- Every competitor brief includes an **"Implication for client"** section (sharp, not generic)
- Every company brief emits a **`kpis.json`** alongside the prose, so the deck renders real charts
- **Marketing intelligence is a first-class phase**, not an afterthought
- The orchestrator never reads raw `WebFetch` output — subagents return compact summaries; full briefs live on disk
- If asked to re-render with a different angle, **re-run only Phases 4 + 5** using existing briefs

Full ruleset: see SKILL.md.
