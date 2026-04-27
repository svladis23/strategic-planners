# Strategic Planners

A collection of Claude Code skills for marketing strategy, marketing science, and editorial intelligence work. Each skill is a self-contained orchestration pattern — main orchestrator + specialized sub-agents + deterministic helpers — designed to run end-to-end inside Claude Code with a small number of human checkpoints.

Maintained by [SumItUp](https://sumitup-il.com), a marketing science consultancy based in Israel.

---

## Skills in this repo

### [`editorial-representation-scan/`](editorial-representation-scan/)

Maps how a topic is framed, discussed, and constructed in Israeli news media and cultural commentary. Output is a 40–60 slide branded deck where every claim cites a specific article. Runs ~6–9 hours of compute, ~50 min of human attention.

Use cases: client onboarding in unfamiliar topic territory, quarterly discourse refreshes, pitch prep, strategic positioning research.

*More skills will be added here as they're built.*

---

## How to use a skill

1. Clone this repo
2. `cd` into the skill folder you want (e.g. `editorial-representation-scan/`)
3. Open a Claude Code session in that folder
4. Read the skill's own `README.md` for invocation patterns and dependencies
5. Claude Code reads the local `CLAUDE.md` and begins the orchestration

Each skill is independent. They share design conventions but no code or state.

---

## Design conventions

The skills here follow a few common patterns:

- **Main orchestrator + sub-agents.** The orchestrator handles state, routing, and user-facing checkpoints. Sub-agents have scoped contexts and single responsibilities. Dispatched via Claude Code's `Task` tool.
- **Model routing.** Haiku for mechanical filtering and template summarization. Sonnet for nuance, synthesis, and strategic reasoning. Calibration protocols in each skill specify what's safe to downgrade.
- **State files over conversation memory.** Every stage writes structured output (YAML, JSONL, CSV, Markdown) to a run folder. Interrupted runs resume from `progress.json`.
- **Mechanical aggregation, not LLM aggregation.** Where pandas can do it, pandas does it. LLMs don't sum CSV rows.
- **Plan vs. render separation.** When a skill produces a complex artifact (a deck, a report), one agent plans the structure (YAML), and a deterministic Python renderer builds the artifact. The LLM never writes formatting code directly.
- **Hard rules per skill.** Each skill's `CLAUDE.md` opens with non-negotiable rules — what the skill won't claim, what evidence is required, where checkpoints sit. These exist to keep runs honest under cost pressure.

---

## License

[MIT](LICENSE). Use freely, attribution appreciated.

---

## Contact

[vlad@sumitup-il.com](mailto:vlad@sumitup-il.com)
