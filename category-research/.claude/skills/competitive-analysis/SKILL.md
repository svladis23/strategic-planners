---
name: competitive-analysis
description: Deep competitive analysis for a new client brand. Use when Vlad asks for "competitive analysis", "competitor research", "new client briefing", or "research [brand] in [category]" — always for a new client brand + category combination in Israel. Orchestrates research subagents across the client and its competitors, then renders a SumItUp-branded English PPTX.
---

# Competitive analysis workflow

Run this when Vlad onboards a client from an unfamiliar category. Input: brand name + category. Output: a SumItUp-branded English PPTX covering the client and its competitors, with a clickable sources appendix.

All research runs bilingual (Hebrew for Israeli sources, English for global) but the deck is English.

The project root is `C:\Users\vlad\OneDrive\Desktop\claude\Competitive analysis`. Everything lives here.

## Phases

Run in order. Approval gates behave differently depending on mode (see below).

### Modes

- **Default mode**: pause at each approval gate and wait for explicit approval.
- **One-go mode**: when Vlad says "run in one go", "don't stop", "trust your instinct" or similar — gates become **non-blocking checkpoints**. Post the competitor list and deck outline inline as status updates so Vlad can interject, but continue immediately. Never run silently.

### Phase 0 — Setup

Ask Vlad to confirm the brand name and category if ambiguous. In one-go mode, also confirm: scope of coverage (all product lines or a specific one), appetite for digital challengers, and deck angle (internal briefing vs. client pitch). Then create:

```
C:\Users\vlad\OneDrive\Desktop\claude\Competitive analysis\runs\<brand-slug>\<YYYY-MM-DD>\
├── briefs\
├── marketing\
├── youtube\
└── deck\
```

### Phase 1 — Client research

Spawn one `company-researcher` subagent (Sonnet).
- Pass: company name, category, region=Israel, timeframe=last 12 months, output path = `runs/<brand>/<date>/briefs/<client>.md`, KPI output path = `runs/<brand>/<date>/briefs/<client>.kpis.json`, client_context = "self" (this IS the client).
- Wait for it to return a short summary.

Sanity check: if the brief came back thin (many "No notable activity" sections), confirm with Vlad that the brand name/spelling is right before spending Phase 3 tokens.

### Phase 2 — Competitor identification (CHECKPOINT)

Spawn one `competitor-finder` subagent (Haiku).
- Pass: client name, category, path to client brief.
- It returns a sized list — 3 for concentrated categories, up to 10 for fragmented ones.

Show the list to Vlad. In default mode, wait for approval. In one-go mode, post it as an inline status update and continue.

### Phase 3 — Competitor research + marketing intelligence + YouTube scan (parallel)

Spawn **three agents per competitor** in a single parallel batch:

1. `company-researcher` (Sonnet) — same schema as Phase 1, writes `briefs/<competitor>.md` + `briefs/<competitor>.kpis.json`. Receives `client_context = "<client name>"` so the "Implication for client" section can be sharp.
2. `marketing-researcher` (Sonnet) — focused marketing-intelligence pass, writes `marketing/<competitor>.md`. Covers ad spend, agency relationships, campaign inventory, media mix, share of voice, and brand positioning signals.
3. `youtube-scanner` (Sonnet) — pulls top 5 videos from the last 2 years via YouTube Data API, fetches transcripts, writes `youtube/<competitor>.md` + `youtube/<competitor>.videos.json`. Creative-intelligence read of what the brand actually runs on YouTube.

Also run one `marketing-researcher` AND one `youtube-scanner` for the client itself so the deck has symmetric marketing + creative depth.

**Parallelism:** all of Phase 3 agents (company + marketing + youtube for each competitor, plus marketing + youtube for the client) go in a single message with multiple Agent tool calls — no sequential waits. For N competitors, that's 3N + 2 agents in one batch.

**YouTube API key:** already stored at `.claude/skills/competitive-analysis/.env` (`YOUTUBE_API_KEY=...`). The helper script `scripts/youtube_scan.py` loads it automatically — you don't pass it through the agent interface.

### Phase 4 — Synthesis + outline (CHECKPOINT)

Spawn one `deck-architect` subagent (Opus 4.7).
- Pass: paths to all briefs, all kpis.json files, all marketing briefs, all youtube briefs, deck output folder.
- It writes `deck/outline.md` — structure and length decided from the content, no fixed template.
- It also writes `deck/chart-specs.json` — a list of matplotlib chart specs to render (bar charts, scatter, tables, perceptual maps) from the KPI and positioning data.
- The outline must include a **Brand-Positioning block** (3–4 slides: perceptual map, message-pillars matrix, distinctiveness audit, client positioning-gap) synthesized qualitatively from the marketing briefs. These slides must carry a "(qualitative synthesis)" marker where claims would need brand-tracking data to fully defend.
- The outline must end with a **Sources Appendix** section specifying 2-4 appendix slides grouping every cited URL by company, with URLs rendered as clickable hyperlinks.

Show the outline to Vlad. Default mode: wait. One-go mode: post inline and continue.

### Phase 5 — Render

1. Execute the chart specs with matplotlib — save PNGs to `deck/charts/`.
2. Invoke `anthropic-skills:sumitup-powerpoint` with the approved outline. Save the PPTX to `deck/<brand>-competitive-analysis.pptx`. Chart PNGs get placed on the slides that reference them, wrapped in a teal hand-drawn frame. Sources-appendix URLs are inserted as clickable hyperlinks (python-pptx `run.hyperlink.address`).
3. **Visual QA**: convert the PPTX to PDF via LibreOffice headless mode:
   ```
   soffice --headless --convert-to pdf --outdir deck/ deck/<brand>-competitive-analysis.pptx
   ```
   If LibreOffice is available, skim the PDF for overflow, stretched charts, misaligned text. Fix and re-render as needed. If LibreOffice is not available in the environment, flag this explicitly to Vlad in the final summary rather than silently skipping.

## Rules

- Every research subagent works off `.claude/skills/competitive-analysis/sources.md` and `brief-schema.md` (paths relative to the project root) — do not re-specify the schema inline when spawning.
- Every claim in a brief carries a date and source URL. The deck-architect cites sources on every factual slide AND compiles the appendix.
- Every competitor brief includes a dedicated "Implication for client" section so synthesis doesn't have to invent it.
- Every company brief emits a `kpis.json` alongside the prose brief so the deck can render real charts, not text tables.
- Marketing intelligence is a first-class phase, not an afterthought — SumItUp's value is marketing science; marketing detail must be at parity with financial detail.
- Never pad. If there is nothing to report, say so.
- Main orchestrator never reads raw WebFetch output. Subagents return compact summaries; briefs live on disk.
- If Vlad asks for a re-render with a different angle, re-run only Phase 4 + 5 using the existing briefs on disk — do not re-search.
