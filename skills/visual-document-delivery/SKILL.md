---
name: visual-document-delivery
description: Use when creating or substantially revising a durable Feishu, Word, PDF, Markdown, or HTML document whose content contains multi-step flows, module relationships, role handoffs, state changes, timelines, comparisons, or trustworthy quantitative data.
---

# Visual Document Delivery

## Overview

Turn complex document content into a readable information system. Use diagrams and compact tables only when they make a real relationship easier to understand; visual polish never changes the evidence status of a claim.

## Required references

- Read [visual-decision-matrix.md](references/visual-decision-matrix.md) before choosing a visual or deciding that none is needed.
- Read [layout-and-information-design.md](references/layout-and-information-design.md) when planning a substantial document's hierarchy and reading rhythm.
- Read [render-and-acceptance.md](references/render-and-acceptance.md) before delivery in the target format.

## Delivery contract

1. Identify the reader, decision, target format, and complex relationships.
2. Create a visual plan before drafting. Use `no_visual_reason` when the artifact is simple and no visual improves comprehension.
3. Draft domain content from its authoritative sources. Keep `Confirmed`, `Externally verified`, `Inferred`, `Knowledge supplement`, and `Open` visibly distinct.
4. Place each visual next to the section it explains. Do not collect unrelated figures at the end.
5. Render the actual delivery format, read back its structure and media, inspect every rendered page, fix failures, and render again.
6. Record the result in a `visual_contract` manifest and run:

```bash
python3 <this-skill-directory>/scripts/validate_visual_manifest.py path/to/visual-manifest.json
```

Resolve `scripts/...` from this Skill's directory; do not assume the caller's current working directory.

## When a visual is required

Use the matching visual when the document contains any of these observable signals:

- three or more dependent steps, components, actors, or routes;
- a branch, loop, failure, fallback, handoff, or state transition;
- a time-dependent plan or sequence;
- a comparison whose trade-offs must be read together;
- quantitative change with verified source, definition, period, and units.

Do not force a diagram into a short answer, one resume bullet, a simple script, or a linear explanation that is already clearer in prose.

## Non-negotiable boundaries

- Never invent internal architecture, ownership, metrics, company data, or student experience to complete a figure.
- Label abstractions and inferences inside the figure or caption.
- Use AI-generated imagery only for a requested cover or illustration; it cannot replace a flow, architecture, evidence matrix, or data chart.
- A successful command, valid Mermaid syntax, non-empty token, or HTTP response is not visual acceptance.
- Unresolved clipping, tiny labels, broken legends, missing captions, empty media, or incomplete page review keeps delivery incomplete.

## Quick reference

| Need | Default form |
| --- | --- |
| Steps, branches, fallback | Flowchart or sequence |
| Inputs, modules, outputs | Architecture |
| Roles and handoffs | Swimlane or collaboration map |
| Stages and dates | Timeline or route map |
| Options, evidence, gaps | Matrix or short comparison table |
| Verified quantitative change | Data chart |
| Fact status and uncertainty | Evidence card or layered relationship |

## Common mistakes

- Decorative image with no explanatory job: remove it.
- Long prose copied into boxes: shorten nodes and return detail to the body.
- Tables used as paragraph containers: keep comparison fields in the table and explanation in prose.
- Figure separated from its explanation: move it to the relevant section.
- Renderer cannot display the chosen format: export a readable image or use a compact native table instead.
