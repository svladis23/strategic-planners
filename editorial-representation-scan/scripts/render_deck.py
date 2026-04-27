"""
Deterministic deck renderer. Reads deck_plan.yaml + calls deck_helpers.py → deck.pptx.

Called at Stage 6b after the Deck Architect writes deck_plan.yaml.

Usage:
    python scripts/render_deck.py <run_folder>

Example:
    python scripts/render_deck.py runs/open_university_higher_ed_value_2026-04-21

Exit codes:
    0 — deck.pptx written successfully
    1 — missing or invalid deck_plan.yaml
    2 — template error (unknown template name, missing required params)
    3 — python-pptx save error
"""
import sys
from pathlib import Path
from collections import Counter

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Import deck_helpers from sibling
sys.path.insert(0, str(Path(__file__).parent))
from deck_helpers import new_presentation, dispatch_slide, TEMPLATES  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("Usage: python render_deck.py <run_folder>", file=sys.stderr)
        sys.exit(1)

    run_folder = Path(sys.argv[1])
    if not run_folder.is_dir():
        print(f"ERROR: Run folder not found: {run_folder}", file=sys.stderr)
        sys.exit(1)

    plan_path = run_folder / "deck_plan.yaml"
    if not plan_path.exists():
        print(f"ERROR: deck_plan.yaml not found at {plan_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(plan_path, encoding="utf-8") as f:
            plan = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"ERROR: deck_plan.yaml is invalid YAML: {e}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(plan, dict) or "slides" not in plan:
        print("ERROR: deck_plan.yaml must be a dict with a 'slides' list.", file=sys.stderr)
        sys.exit(1)

    slides = plan["slides"]
    if not isinstance(slides, list) or not slides:
        print("ERROR: 'slides' must be a non-empty list.", file=sys.stderr)
        sys.exit(1)

    # Validate all template names BEFORE rendering
    unknown = [s.get("template") for s in slides if s.get("template") not in TEMPLATES]
    if unknown:
        print(f"ERROR: unknown templates: {sorted(set(unknown))}", file=sys.stderr)
        print(f"Available: {sorted(TEMPLATES.keys())}", file=sys.stderr)
        sys.exit(2)

    # Render
    prs = new_presentation()
    page_num = 0
    template_counts = Counter()

    for i, slide_entry in enumerate(slides):
        try:
            page_num = dispatch_slide(prs, page_num, slide_entry)
            template_counts[slide_entry["template"]] += 1
        except Exception as e:
            print(f"ERROR rendering slide {i+1} (template={slide_entry.get('template')!r}): {e}",
                  file=sys.stderr)
            sys.exit(2)

    # Save
    out_path = run_folder / "deck.pptx"
    try:
        prs.save(str(out_path))
    except Exception as e:
        print(f"ERROR saving {out_path}: {e}", file=sys.stderr)
        sys.exit(3)

    # Report
    meta = plan.get("meta", {})
    print(f"Deck rendered: {out_path}")
    print(f"Total slides: {len(prs.slides)}")
    print(f"Client: {meta.get('client', '—')}")
    print(f"Topic: {meta.get('deck_title', '—')}")
    print()
    print("Template distribution:")
    for template, count in template_counts.most_common():
        print(f"  {template}: {count}")

    # Quality check
    hints = []
    if len(prs.slides) < 35:
        hints.append(f"[warn] Deck has {len(prs.slides)} slides - below the v2.1 target of 40-60 for deep_dive.")
    if template_counts.get("frame_argument", 0) < 4:
        hints.append("[warn] Fewer than 4 frame_argument slides - frame deep-dives look thin.")
    if template_counts.get("battleground", 0) == 0:
        hints.append("[warn] Zero battleground slides - divergent frames not surfaced.")
    if template_counts.get("vocabulary_cluster", 0) < 4:
        hints.append("[warn] Fewer than 4 vocabulary_cluster slides - vocabulary atlas is thin.")

    if hints:
        print()
        print("Quality hints:")
        for h in hints:
            print(" ", h)
    else:
        print()
        print("[ok] Quality hints: none. Deck structure looks healthy.")


if __name__ == "__main__":
    main()
