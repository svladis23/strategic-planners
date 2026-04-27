# Company brief schema

Every `company-researcher` brief must follow this structure. Sections with no findings say "No notable activity in last 12 months" — do not pad.

## 1. Company snapshot
- Legal entity, ownership, parent company
- HQ, markets active in (emphasize Israel)
- Approximate size: revenue, employees, market cap if public
- Core business in one sentence

## 2. Business & financial news (last 12 months)
- Earnings, funding rounds, M&A, leadership changes, restructuring, layoffs
- Each item: 1-2 sentences, date, source URL

## 3. Marketing activity
- Major campaigns (creative hook, channel mix if known)
- Brand positioning shifts, rebrands, sponsorships
- Agency relationships if publicly known
- Each item: date, source URL

Note: deeper marketing intelligence (ad spend estimates, full campaign inventory, share of voice, media mix) is produced by the separate `marketing-researcher` agent and lives in `marketing/<company>.md`. Section 3 here is a summary only.

## 4. Product & innovation
- New products, features, services launched
- R&D or tech investments
- Each item: date, source URL

## 5. Strategic signals
- Category shifts, geographic expansion, partnerships
- Public strategic statements from leadership
- Regulatory issues, lawsuits, controversies

## 6. Israel-specific context
- Local market share where known, local competitors it names
- Local campaigns, local hires, local distribution
- If foreign brand: how it operates in Israel (importer, franchise, direct)

## 7. What an outsider needs to know
- 3-5 bullets: the non-obvious things Vlad would want to know walking into a meeting about this brand

## 8. Implication for the client (competitors only — skip for the client's own brief)
- 2-3 bullets answering explicitly: *how does this company threaten or enable <client>?*
- Be concrete: which product line, which geography, which customer segment, which channel
- If they don't meaningfully affect the client, say so — don't pad
- This section feeds directly into the deck-architect synthesis, so the sharper it is, the better the deck

## Rules
- Word budget: 800-1,200 total. Hard cap 1,500.
- Every factual claim has inline `(YYYY-MM-DD, source-url)`.
- Separate facts from interpretation. Interpretation lives in sections 7 and 8 and is labeled as such.
- Flag uncertainty explicitly ("dated 2024-11; may be stale") rather than restating stale facts with confidence.

---

# KPI extraction — `<company>.kpis.json`

Alongside the prose brief, every company-researcher must write a structured KPI file so the deck can render real charts.

## Schema

```json
{
  "company": "<Display name>",
  "period": "FY2025",
  "currency": "ILS",
  "financials": {
    "revenue":      {"value": null, "unit": "ILS billion", "yoy_pct": null, "source": null, "date": null},
    "net_profit":   {"value": null, "unit": "ILS billion", "yoy_pct": null, "source": null, "date": null},
    "roe_pct":      {"value": null, "source": null, "date": null},
    "aum":          {"value": null, "unit": "ILS billion", "source": null, "date": null},
    "market_cap":   {"value": null, "unit": "ILS billion", "source": null, "date": null},
    "employees":    {"value": null, "source": null, "date": null}
  },
  "category_kpis": {
    "<metric_key>": {"value": null, "unit": "", "period": "", "source": null, "date": null}
  },
  "marketing_kpis": {
    "ad_spend":     {"value": null, "unit": "ILS million", "period": "", "source": null, "date": null},
    "agency_of_record": null,
    "notable_campaigns": []
  },
  "notes": []
}
```

## Rules

- Use `null` for anything not found. Do not guess — the deck-architect treats null as "omit from chart".
- `category_kpis` is flexible. For insurance include `net_pension_flows`, `policy_count`, `claims_ratio` if available. For retail: `same_store_sales_pct`, `ecommerce_share_pct`, `store_count`. Pick keys that matter for the category.
- Every non-null value must have a `source` URL and `date` (YYYY-MM-DD).
- JSON must parse cleanly. No trailing commas, no comments.
