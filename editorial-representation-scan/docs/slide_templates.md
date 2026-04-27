# Slide Templates — visual reference for the Deck Architect

Every template below is a function in `scripts/deck_helpers.py`. The Deck Architect references them by name in `deck_plan.yaml`. The renderer (`scripts/render_deck.py`) dispatches to the matching Python function.

All templates are SumItUp brand-compliant by construction: navy/cream backgrounds, Heebo font (specified in XML — must be installed on the rendering machine for visual fidelity), RTL handling for Hebrew, footer on every content slide.

---

## Cover & dividers (no footer, no page number)

### `cover`
The first slide. Navy bg. Large deck title + subtitle + client tag + meta line + date.

Params:
```yaml
template: cover
params:
  title: "Higher Education"                      # primary title, white bold 64pt
  subtitle: "in the AI Era"                      # secondary line, white 28pt
  client_tag: "Prepared for: The Open University" # teal bold 14pt
  meta_line: "86 articles · 13 outlets · 2021-2026"
  run_date: "April 2026"
```

### `section_divider`
Navy-bg transition slide between deck sections.

```yaml
template: section_divider
params:
  title: "Frame Deep-Dives"                       # white bold 44pt, center
  subtitle: "How Israeli media argues about..."   # optional, teal italic 18pt
```

### `closing`
"Thank you" slide. Navy.

```yaml
template: closing
params:
  title: "Thank you."
  subtitle: "Editorial Representation Scan — ..."
  client_line: "Prepared for ... — April 2026"
```

### `appendix_cover`
Transition to appendix. Navy.

```yaml
template: appendix_cover
params:
  title: "Appendix"
  subtitle: "Article index by frame — 86 articles · 13 outlets · 2021-2026"
```

---

## Content templates (cream bg, footer + page number)

### `executive_summary`
Top 8 frames grid. Each row: number + name + convergence tag + 1-line description.

```yaml
template: executive_summary
params:
  subtitle: "Eight frames shape how Israeli media argues about higher education's value"
  frames:
    - num: 1
      name: "Degree-as-ROI calculation"
      tag: "CONVERGENT"                    # CONVERGENT | DIVERGENT | RISING | COUNTER | STABLE | DECLINING
      description: "All outlets cite the same data; disagree on what to do about it."
    # ... up to 8
  source_line: "Source: Categorical Extractor / Interpretive Synthesizer"
```

### `outlet_landscape`
Positioning map of outlets scanned. 3–5 columns of ideological-position blocks.

```yaml
template: outlet_landscape
params:
  title: "Which outlets carry what"
  subtitle: "13 outlets across 5 ideological positions"
  outlet_blocks:
    - position: "left-liberal"
      color: "navy"                        # navy | purple | teal | gold
      outlets: ["Haaretz", "TheMarker"]
      signature_framing: "Leads the formation defense; carries humanities-crisis as civilizational loss."
    # ... 3-5 blocks
```

### `frame_argument`  (one per top frame)
The lead slide in each frame's 3-slide deep-dive. Two Hebrew quotes side-by-side + outlet presence + implication.

```yaml
template: frame_argument
params:
  frame_number: 1
  frame_name: "Degree-as-ROI calculation"
  tag: "CONVERGENT"
  one_line_summary: "The topic's lingua franca — everyone cites the same numbers..."
  main_quote:
    hebrew: "..."
    gloss: "..."
    source: "Bizportal · consumer-finance framing"
    speaker: "author"                       # or named expert
  supporting_quote:
    hebrew: "..."
    gloss: "..."
    source: "..."
    speaker: "..."
  outlet_presence:
    lead: ["Bizportal", "Calcalist", "Davar"]
    secondary: ["Ynet", "Mako", "Walla"]
  implication: "Safe ground for comms. Frame as 'the ROI that survived AI'."
  sources: ["https://...", "https://...", "https://..."]
```

### `frame_language`  (one per top frame, after frame_argument)
Hebrew vocabulary carrying THIS frame. Up to 10 phrases in 2-column grid, each with in-situ example.

```yaml
template: frame_language
params:
  frame_number: 1
  frame_name: "Degree-as-ROI calculation"
  phrases:
    - hebrew: "בועת ההשכלה"
      gloss: "education bubble"
      valence: "negative"
      in_situ: "עשרות אלפי בוגרים תקועים בבועת ההשכלה"
      in_situ_outlet: "Calcalist"
    # ... 6-10 phrases
  note: "The vocabulary of this frame weaponizes financial metaphors..."
```

### `frame_positions`  (one per top frame, after frame_language)
How 2-3 ideological positions construct this frame. Quote from each side + absences note.

```yaml
template: frame_positions
params:
  frame_number: 1
  frame_name: "Degree-as-ROI calculation"
  positions:
    - name: "Left-liberal"
      outlets: "Haaretz, TheMarker"
      framing_valence: "skeptical but pragmatic"
      quote:
        hebrew: "..."
        gloss: "..."
        speaker: "Name (affiliation)"
        outlet_date: "Haaretz · 2024-06"
    # 2-3 positions total
  absences: "Right-populist and religious-Zionist voices excluded by scope."
  convergence_note: "Everyone cites the same data; divergence is interpretive."
```

### `vocabulary_cluster`  (one per cluster, typically 8-10 slides)
All phrases in one thematic cluster. Up to 16 phrases in 2-column grid + a signature quote.

```yaml
template: vocabulary_cluster
params:
  cluster_name: "Skepticism & devaluation"
  cluster_valence: "negative"                # positive | negative | neutral | contested
  cluster_description: "Vocabulary positioning the degree as hollow, expired, or collapsed."
  phrases:
    - hebrew: "בועת ההשכלה"
      gloss: "education bubble"
      valence: "negative"
      outlets: "business;mainstream"
    # ... all cluster phrases (up to 16 shown)
  signature_quote:
    hebrew: "..."
    gloss: "..."
    source: "Calcalist, 2025"
```

### `temporal_phase`  (one per phase, typically 4 slides)
Phase title + date range + 3 article examples with quotes.

```yaml
template: temporal_phase
params:
  phase_num: 1
  phase_title: "Chronic credential-inflation debate"
  date_range: "April 2021 – November 2022"
  phase_description: "Baseline phase. Taub/Ben-David 'excess education' dominant. Humanities treated as managed decline."
  article_examples:
    - title: "Full article title"
      outlet: "Calcalist"
      date: "2022-03-15"
      url: "https://..."
      hebrew_quote: "..."
      english_gloss: "..."
    # 3 examples per phase
  signature_finding: "This phase reveals the degree debate as pre-AI, pre-rupture — classical over-education framing."
```

### `battleground`  (3-5 slides for divergent frames)
Side-by-side comparison of how 2-3 outlets frame the same sub-topic. Full Hebrew quotes per side.

```yaml
template: battleground
params:
  battleground_name: "Humanities crisis: loss or correction"
  context: "The sharpest ideological fault line in the corpus."
  left:
    position: "Left-liberal"
    outlet: "Haaretz"
    speaker: "Dorit Shilah"
    hebrew_quote: "..."
    english_gloss: "..."
    rhetorical_move: "moral appeal to democratic values"
  right:
    position: "Business-pragmatic"
    outlet: "Globes"
    speaker: "Hatzroni"
    hebrew_quote: "..."
    english_gloss: "..."
    rhetorical_move: "aggressive market-logic dismissal"
  third:                                       # optional for partial_divergence
    position: "Humanities-insider"
    outlet: "Globes"
    speaker: "Ataria"
    hebrew_quote: "..."
    english_gloss: "..."
    rhetorical_move: "internal-market lament"
  axis_of_contestation: "Not facts — moral valence. Everyone agrees enrollments collapse; they disagree on whether that's tragedy or correction."
```

### `experts_grid`  (2 slides)
Cast of characters. 3×3 grid per slide = up to 9 experts. Each card: name + credential + institution + article count + representative Hebrew quote.

```yaml
template: experts_grid
params:
  subtitle: "Top institutional voices"
  experts:
    - name: "Taub Center"
      credential: "Hadas Fuchs, Eyal Bar-Haim"
      institution: "Policy think tank"
      article_count: 5
      representational_note: "canonical data source across outlets"
      representative_hebrew_quote: "..."
      representative_gloss: "..."
    # 6-9 per slide
  scope_note: "49 experts identified; top 9 shown on this slide."
```

### `quote_vs_avoid`  (1 slide — client-specific)
Left column: voices to quote (teal). Right column: voices to avoid (purple). Up to 6 entries per side.

```yaml
template: quote_vs_avoid
params:
  subtitle: "Voices to quote / align with vs. voices to avoid — for The Open University"
  quote_side:
    label: "QUOTE · ALIGN WITH"
    entries:
      - name: "Taub Center"
        reason: "cross-outlet data authority"
      # 3-6 entries
  avoid_side:
    label: "AVOID"
    entries:
      - name: "Prof. Dan Ben-David (Shoresh)"
        reason: "his 'אינפלציית התארים' weaponizes against the client's category"
      # 3-6 entries
```

### `absence_detail`  (4-6 slides, one per absence category)
Deep-dive on ONE absence. Confidence + what's missing + why expected + evidence + strategic implication.

```yaml
template: absence_detail
params:
  absence_category: "Missing voices"
  absence_name: "Students themselves"
  what_is_missing: "First-person student voice — near-zero in corpus."
  why_expected: "Topic directly addresses students' decisions..."
  evidence: "Coverage is ABOUT students, not BY them. Only <N> articles quote a student directly."
  confidence: "HIGH"                          # HIGH | MEDIUM | LOW
  strategic_implication: "The client can occupy this space with student-voice-first content."
```

---

## Client positioning (conditional — only if client != internal test)

### `client_white_space`
3 unclaimed positioning territories with first-move concrete suggestion.

```yaml
template: client_white_space
params:
  title: "White space for The Open University"
  subtitle: "Three territories visible in the corpus without an institutional champion"
  territories:
    - num: 1
      name: "The AI-raises-degree-value counter-frame for ADULTS"
      description: "The counter-frame exists but is voiced entirely by elite research-university presidents defending 22-year-olds..."
      first_move: "Ynet/Mako op-ed pairing BoI's AI-exposure figure with Open U's adult demographic."
    # 2-3 territories
```

### `client_plays`
Top 5 positioning plays. Each: frame + stance + vocabulary + voice + play.

```yaml
template: client_plays
params:
  title: "Top five positioning plays"
  plays:
    - frame: "Mid-career returner / lifelong learning"
      stance: "helps"
      vocabulary: ["למידה לאורך החיים", "קריירה שנייה"]
      voice: "Prof. Boaz Ganor (Reichman) — uses lifelong-learning framing positively"
      play: "Claim 'למידה לאורך החיים' as proprietary category before TAU's Mendel program does."
    # 5 plays
```

### `client_avoids`
3-5 specific warnings, each tied to scan evidence.

```yaml
template: client_avoids
params:
  title: "What to avoid"
  avoids:
    - name: "Never quote Dan Ben-David"
      reason: "His 'אינפלציית התארים' is the single most-repeated weapon against part-time degrees."
      evidence_anchor: "vocabulary.csv cluster: Data-as-authority"
    # 3-5 avoids
```

### `client_taglines`
3 Hebrew taglines worth testing. Each large + gloss + why-it-fits.

```yaml
template: client_taglines
params:
  title: "Three Hebrew taglines worth testing"
  taglines:
    - hebrew: "למידה לאורך החיים"
      gloss: "lifelong learning"
      why_it_fits: "Validated across mainstream + left + longform outlets. Open U's structural home."
    # 3 taglines
```

---

## Methodology

### `methodology`
2-column slide: left = what we did (process bullets), right = Verifier-contested claims + resolutions. Bottom: what this scan is NOT.

```yaml
template: methodology
params:
  subtitle: "What this scan is, what it isn't, and what the Verifier corrected"
  what_we_did:
    - "86 articles from 13 Israeli outlets, 2021-2026"
    - "25 Hebrew queries across 5 angles..."
    # 4-6 process bullets
  verifier_contests:
    - claim: "Zero non-instrumental defenses of academia"
      resolution: "DOWNGRADED to 'exists but fragmented' — 3 articles do make this defense."
    # 2-5 contests
  scope_limits:
    - "Not consumer voice. Not search-demand. Not validated qualitative research."
    - "Scope: secular Jewish-Israeli editorial discourse only."
```

---

## Appendix

### `article_index_page`
One page of the article index, filtered by frame. Paginate across multiple pages by repeating this template with different frames.

```yaml
template: article_index_page
params:
  frame: "Degree-as-ROI calculation"
  article_count_on_this_frame: 25
  articles:
    - outlet: "Bizportal"
      date: "2025-07-14"
      url: "https://..."
      title_excerpt: "כמה באמת שווה התואר שלכם?"
      primary_or_secondary: "primary"              # primary | secondary
    # up to 18 per page
```

---

## When to use what — planner quick-reference

| Content intent | Template |
|---|---|
| Open the deck | `cover` |
| Mark a major section break | `section_divider` |
| Summarize the whole argument | `executive_summary` |
| Set the outlet landscape once | `outlet_landscape` |
| Open a frame deep-dive | `frame_argument` |
| Expand a frame's Hebrew vocabulary | `frame_language` |
| Show how positions diverge on a frame | `frame_positions` |
| Show all phrases in a vocabulary cluster | `vocabulary_cluster` |
| Show how a phase of time felt | `temporal_phase` |
| Stage a head-to-head ideological fight | `battleground` |
| List the experts with their voices | `experts_grid` |
| Give the client a quote/avoid decision list | `quote_vs_avoid` |
| Deep-dive on ONE absence | `absence_detail` |
| Give the client white-space options | `client_white_space` |
| Give the client 5 plays | `client_plays` |
| Warn the client away from things | `client_avoids` |
| Propose 3 Hebrew taglines | `client_taglines` |
| Close with methodology & limits | `methodology` |
| Close with "thank you" | `closing` |
| Open the appendix | `appendix_cover` |
| Paginate the article index | `article_index_page` |

If a slide's content doesn't fit any template, don't invent — tell the orchestrator in the return message which content is homeless, and propose whether it belongs in an existing template or needs a new one added to `deck_helpers.py`.
