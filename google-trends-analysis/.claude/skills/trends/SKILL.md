---
name: trends
description: Run a full Google Trends brand-and-category analysis. Builds a query brief, fetches data via pytrends (Israel geo, Hebrew + English), computes stats, runs 3 parallel sub-agents, synthesizes, optionally deepens, and builds a PPT deck.
---

# Trends Analysis Workflow

Usage invoked by the user: `/trends <brand> <category>` (e.g. `/trends Menora pension`).
If the user provides no args, ask for brand + category before proceeding.

## Step-by-step orchestration

### Step 1 — Interactive brief building (NO subagent, main session works with user)

**The brief is the single most important step.** Each term is a bet that costs time and pytrends rate-limit budget. A weak adjacent-terms bucket limits the "why" analysis; a wrong competitor set wastes 30+ min of fetching. Walk the user through each section one at a time, get explicit approval, move to next.

**Do NOT bulk-propose the whole brief and ask for one approval.** Break it into the 7 sections below. For each, propose 3–8 candidates with reasoning, then ask: "Approve this? Add, remove, or replace?"

Only after ALL sections are approved, write the final JSON to `data/brief_pending.json`.

#### Section 1 — Research question + hypotheses
State the client's actual question and 2–3 testable hypotheses that the data should confirm or refute. Example: "Hypothesis: the credential→job logic is eroding. Testable via: trend in 'תואר שווה', rising queries for alternatives, SoV shift to online/bootcamp terms." Get the user's approval on what you're actually testing before proposing any terms.

#### Section 2 — Brand terms
Propose 2–5 variants (Hebrew + English if relevant). Note which is the primary "head" term. Flag ambiguous brand names.

#### Section 3 — Competitors
Propose 3–5 competitors with ONE-line justification per competitor (why them, what they represent in the landscape — premium alternative? direct substitute? aspirational anchor?). Include 1–3 term variants per competitor.

#### Section 4 — Category terms
Propose 4–6 generic category queries. Each should tie to a hypothesis from Section 1.

#### Section 5 — Adjacent terms (spend time here)
This is the richest source of insight. Propose 6–10 emotional/behavioral/alternative-path queries. For each, name the hypothesis it tests. Examples of categories to cover:
- "how to" queries (איך, כמה עולה, מתי)
- emotional queries (שווה? חשוב? טוב?)
- life-stage cues (גיל, פרישה, הסבה)
- alternative paths (bootcamp, online, career retraining)
- cost/ROI frames (כמה עולה, נקודת זיכוי, מחיר)

#### Section 6 — Comparison pairs
Propose 2–4 head-to-head pairs that would produce clear stories. Each pair = 1 chart; pick pairs where the answer isn't obvious.

#### Section 7 — Final confirmation
Show the consolidated JSON. Confirm geo (IL default), hl (he-IL default), timeframe (today 5-y default), languages. Get final GO.

**Rules:**
- Max 5 terms per list (pytrends hard limit per request)
- Prefer `competitor_terms` as a dict (name → term list)
- When in doubt, ask rather than guess
- If the user says "run in one run / no permissions / decide alone", skip the interactive dance BUT still do all 7 sections internally and show the brief as a final summary for informational transparency

### Step 2 — Initialize run + fetch

```bash
python src/runner.py init --brief data/brief_pending.json
```

This prints the run directory. Capture it — you'll need it for every subsequent step. (You can also pass `--out data/explicit_name`.)

Then fetch (this is the slow step — 5-15 minutes depending on brief size):

```bash
python src/runner.py fetch --run <RUN_DIR>
```

Run in background via Bash `run_in_background: true`. Tell the user it'll take several minutes and you'll resume when it finishes.

### Step 3 — Stats + charts (fast, <10 seconds)

```bash
python src/runner.py stats --run <RUN_DIR>
python src/runner.py charts --run <RUN_DIR>
```

### Step 4 — Spawn 3 sub-agents in parallel

Use the Agent tool with these subagent_types, **all in one message** for parallel execution:
- `trends-brand-health`
- `trends-category-dynamics`
- `trends-audience-insight`

Each agent prompt must include:
- The exact paths to its relevant stats pack(s)
- The exact output path where it should write findings (`data/{run}/findings/{name}.md`)
- Brand and category names

Make sure `data/{run}/findings/` exists before spawning.

### Step 5 — Synthesizer, round 1 (deepening decision)

Invoke `trends-synthesizer` in Mode A. Give it the three findings paths and `data/{run}/deepening_brief.json` as output.

If `deepen: true`:
- Merge the deepening buckets into a new brief at `data/{run}/brief_round2.json` (preserve original geo/timeframe)
- Re-run fetch + stats + charts with this brief, reusing the same run dir (cache will serve overlapping queries)
- Re-run the 3 sub-agents with updated findings paths (append `_r2` suffix or overwrite)
- Proceed to Step 6 — do NOT deepen again (cap at 2 rounds total)

If `deepen: false`: proceed to Step 6.

### Step 6 — Final synthesis

Invoke `trends-synthesizer` in Mode B. Output: `data/{run}/synthesis.md`.

### Step 7 — Build the PPT

Invoke the `sumitup-powerpoint` skill (SumItUp brand-compliant PowerPoint). Hand it:
- `data/{run}/synthesis.md` as the narrative spine
- `data/{run}/charts/` directory for visuals
- `data/{run}/findings/` for supporting detail

**🚨 Every claim slide must be backed by a plot. No text-only claims.**
- A slide that asserts "TAU owns 75.5% SoV" must include the SoV bar chart, not just the number in text
- A slide claiming "attention is moving to program mechanics" must include a rising-queries bar chart
- A slide citing a YoY % must include either a line chart or a big-stat callout
- Text-only slides are allowed ONLY for: cover, section dividers, executive summary (table-of-contents preview), data caveats, closing
- If a claim is worth making, it's worth charting. If there's no chart for it, either generate one in the charts step or cut the claim.

**Required supplementary charts** (the charts step should generate these automatically; if missing, generate on-demand before building the deck):
- `sov_bar.png` — share-of-voice bar chart across brand + competitors (all-time and last 52w, grouped)
- `rising_queries_{term}.png` — top-10 rising queries bar chart for each of the 3 key terms, sorted by % change
- `top_queries_{term}.png` — top-10 queries (by volume) bar chart for each of the 3 key terms
- `yoy_bar.png` — YoY % change bar chart across brand + competitor head terms

Slide outline (every slide has a chart/visual):
1. Title
2. Executive summary (text-only allowed)
3. The question (text + hypotheses)
4. Brand position → brand_vs_competitors chart
5. SoV breakdown → sov_bar chart
6. YoY comparison → yoy_bar chart or big-stat callout
7. Brand trajectory → brand_terms chart
8. Seasonality → brand_seasonality chart (if strength > 0.3)
9. Category dynamics → rising_queries for top category term
10. Emerging sub-segments → rising_queries for 2nd/3rd category term
11. Alternative paths → adjacent chart
12. Key comparison → compare_X chart (the sharpest story)
13. Audience intent signal → top_queries bar + hero Hebrew quote
14. Audience emotion → rising_queries for adjacent terms
15-N. One strategic implication per slide, each paired with the chart/stat that supports it
N+1. Data caveats (text allowed)
N+2. Closing

Save to `data/{run}/deck.pptx`.

### Step 8 — Report to user

Tell the user:
- Path to the deck
- Path to the synthesis markdown
- Brief summary of the headline finding
- Any data gaps worth flagging

## Token-saving rules (non-negotiable)

- NEVER read files from `data/{run}/raw/` into your context. That's raw time-series data; sub-agents must never see it either.
- Sub-agents get ONLY their own stats pack file path. Do not paste file contents into their prompts.
- The synthesizer gets ONLY the three findings files. Do not paste them.
- You (the main session) only need to read `synthesis.md` yourself — never the raw packs, never the charts index in full.

## Error handling

- If `fetch` fails mid-run, the sqlite cache has partial data. Re-run `fetch` and it'll pick up where it left off.
- If a stats pack shows `"empty": true` for a key bucket, tell the user the term got no volume — don't fake analysis.
- If pytrends hits persistent 429s, stop and tell the user to wait 30+ minutes before retrying.
