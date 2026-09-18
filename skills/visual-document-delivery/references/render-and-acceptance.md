# Render and Acceptance

## Completion sequence

1. Render or export the actual target format.
2. Read back title hierarchy, visual count, visual position, caption, source, fact boundary, and media identifiers.
3. Inspect every rendered page or equivalent full surface at normal desktop zoom.
4. Fix clipping, overlap, tiny labels, broken legends, table overflow, bad page breaks, or visual/text separation.
5. Render again and repeat the full inspection.
6. Record the final result in `visual_contract` and run the shared validator.

## Format-specific checks

### Feishu

- Prefer native tables, callouts, images, and whiteboards that render reliably.
- Use `lark-cli` for structural readback when available.
- Verify non-empty media tokens or `src`, block order, title, caption, and parent section.
- Export to PDF or use an equivalent student-facing render for every-page inspection.

### Word and PDF

- Use the document/PDF workflow appropriate to the file type.
- Render the document to page images and inspect every page.
- Check page breaks, figure anchoring, table width, margins, font size, and captions.

### Markdown and HTML

- Keep diagram source or chart data traceable.
- Validate the rendered output, not only Markdown text or Mermaid syntax.
- If the target renderer does not support the diagram, export a readable image or use a native relationship table.

## Required manifest shape

```json
{
  "skill": "domain-skill-name",
  "visual_contract": {
    "substantial": true,
    "complexity_signals": ["multi_step_flow"],
    "required_visual_ids": ["business-flow"],
    "visual_plan": [
      {
        "id": "business-flow",
        "type": "flowchart",
        "reason": "Explains a branched workflow.",
        "section": "Business flow",
        "fact_boundary": "Inferred",
        "caption": "Public abstraction, not internal architecture.",
        "source_note": "Official public pages and supplied JD."
      }
    ],
    "readback": {
      "media_blocks": [
        {"visual_id": "business-flow", "token": "non-empty-token"}
      ]
    },
    "render_qa": {
      "page_count": 3,
      "checked_pages": [1, 2, 3],
      "checked_items": ["clipping", "readability", "layout", "caption"],
      "issues": []
    }
  }
}
```

For a simple artifact without visuals, set `substantial` to `false`, keep `visual_plan` empty, and provide a concrete `no_visual_reason`.

## Failure conditions

Delivery remains incomplete when any required visual is missing, a token is empty, a caption/source/fact boundary is absent, page review is partial, or render issues remain unresolved. CLI success, HTTP 200, revision changes, syntax validation, or a static source screenshot do not override these failures.
