# Visual Decision Matrix

## Decide from the relationship, not from a desired image count

| Observable relationship | Use | Do not use |
| --- | --- | --- |
| Multiple steps, branches, loops, or failure recovery | Flowchart or sequence diagram | A paragraph that hides branches |
| Inputs, processing, modules, data, and outputs | Architecture diagram | An undirected concept cloud |
| Roles, departments, or upstream/downstream handoffs | Swimlane or collaboration map | A flat list of role names |
| Time stages, application rhythm, or growth path | Timeline or route map | Repeated month lists |
| Options, roles, evidence, gaps, or priorities | Matrix or compact comparison table | A full article inside table cells |
| Metric change, trend, distribution, or composition | Data chart | Any chart without trustworthy numbers |
| Facts, inference, and unresolved items | Evidence card or layered relationship | Color that makes uncertainty look confirmed |
| One conclusion or simple linear explanation | Short prose, quote, or information card | A diagram added only for decoration |

## Complexity test

A substantial document needs a visual plan. A visual is normally required when at least one condition is true:

- three or more dependent steps, components, actors, stages, or routes;
- a branch, loop, failure, fallback, handoff, or state change;
- the reader must compare multiple options or evidence paths together;
- verified quantitative data is central to the decision.

If none applies, record a specific `no_visual_reason`. “The document is short” is insufficient when it still contains a complex relationship.

## Evidence boundary

Every visual node or series must carry one of these meanings:

- `Confirmed`: supported student/client action, output, or result;
- `Externally verified`: supported public company, market, JD, or research fact;
- `Inferred`: a labelled interpretation or abstraction;
- `Knowledge supplement`: teaching or domain knowledge, not personal experience;
- `Open`: unresolved, planned, or awaiting evidence.

Do not merge these categories through layout or color. A team result cannot become a personal result, a public business flow cannot become an internal product architecture, and a project plan cannot appear as completed work.

## Data-chart gate

Create a chart only when all four fields are available:

1. source or dataset identity;
2. metric definition;
3. time range;
4. unit or denominator.

If any field is missing, use a sourced statement, evidence matrix, or explicitly labelled conceptual diagram instead.
