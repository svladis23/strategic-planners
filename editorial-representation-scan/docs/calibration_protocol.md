# Calibration Protocol — verifying a model downgrade before committing

## When to use this

Before downgrading ANY sub-agent in the pipeline from Sonnet (or the parent model) to Haiku, run this protocol. The goal is empirical evidence that the cheaper model produces structurally-equivalent output, not a hunch.

In v2, Haiku is used only for:
- `agents/collector.md` (Collectors — URL filtering + snippet assessment)
- `agents/pre_digest.md` (Pre-digest — template summarization)

These two were downgraded because their work is mechanical. All other agents stay on Sonnet because they do judgment work (Hebrew nuance, cross-corpus synthesis, strategic positioning).

**If you want to try Haiku on a third agent, run this protocol first.**

---

## The test

### Step 1: Pick one real input

Use an in-progress or completed run. Pick the input the target agent would see — for Collectors, that's a single (source × query set); for Pre-digest, that's a random 10-article subset.

### Step 2: Run the same prompt on BOTH models

Dispatch the agent twice with identical prompts:
- Once with `model: "sonnet"` (or current production model)
- Once with `model: "haiku"`

Store both outputs.

### Step 3: Structured comparison

Don't eyeball the output. Use these specific comparison rules per agent type:

#### For a Collector run
Compare the two `collector_state_X.json` files (or the rows appended to `articles_index.csv`):
- Did both models pick the same URLs? (Expected: ≥80% overlap)
- Did both reject the same URL-pattern garbage? (Expected: 100% overlap on URL-pattern rejects)
- Did Haiku include any sponsored / tag-page / listicle URLs that Sonnet rejected? (Expected: no)
- Did Haiku fetch more URLs than Sonnet per (query × source)? (Expected: same or fewer)

**Ship criterion:** ≥80% URL-picking overlap AND zero bad URLs in Haiku's output. Below that → keep on Sonnet.

#### For a Pre-digest run
Compare the two `articles_digest.jsonl` files on 10 articles:
- Do the `candidate_frames_mentioned` arrays match? (Expected: same top-2 frames per article, additional frames may differ)
- Do the `key_hebrew_phrases_first_pass` arrays overlap? (Expected: ≥60% phrase overlap)
- Do the `summary_3_sentences` convey the same stance (celebratory / skeptical / analytical)? (Expected: yes — don't require same sentences, require same stance tag if you force-tag them)
- Are the `experts_named` arrays the same? (Expected: ≥80% overlap)

**Ship criterion:** top-2 frames match per article AND expert extraction matches AND stance tag matches. Hebrew phrase overlap ≥60% is acceptable — perfect overlap is not needed.

#### For a generic extraction/classification task
- List the concrete decisions the agent made (URLs picked, frames assigned, phrases extracted).
- Compare item-by-item.
- Tolerance: Haiku can be slightly more generous (more items) but must not miss anything Sonnet caught, and must not introduce errors Sonnet didn't.

### Step 4: Decide

If Haiku passes the ship criterion → commit the downgrade. Update the relevant `agents/*.md` with `**Model:** Haiku`.

If Haiku fails → revert, document why in `docs/calibration_notes.md` (which you create on first failure), keep Sonnet.

### Step 5: Re-calibrate when the model family updates

New Haiku versions come out. A task that Haiku-3.5 couldn't do, Haiku-4.5 might. Re-run this protocol any time Anthropic releases a new Haiku tier AND at the start of any new topic area (e.g., if the pipeline is used for non-Israel topics, re-calibrate Hebrew-specific expectations).

---

## Why this exists

Model choice is often decided by hunch: "feels like it needs a smarter model." Hunches are expensive — if Haiku works for a task and you use Sonnet, you overspend 3×. If Sonnet is needed and you use Haiku, quality drops silently.

A 10-minute A/B test per task type eliminates the guesswork. Calibration is a one-time cost that pays back every run.

---

## Things NOT to calibrate (keep on Sonnet regardless)

These tasks require Hebrew nuance, cross-corpus synthesis, or strategic reasoning. Don't even try:

- **Category Mapper** — deciding what frames plausibly exist requires interpretive reasoning.
- **Categorical Extractor** — frame assignment involves Hebrew editorial stance, which Haiku tends to flatten.
- **Textual Extractor** — phrase valence (`תואר ריק` vs `תואר מיותר` vs `תואר מיושן`) requires nuance.
- **Interpretive Synthesizer** — cross-corpus narrative synthesis.
- **Verifier** — a cheap second read is less valuable than a smart second read.
- **Client Translator** — strategic positioning is judgment work.

The "safe to downgrade" list is only mechanical filtering and template summarization. Keep it short.
