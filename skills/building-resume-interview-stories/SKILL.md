---
name: building-resume-interview-stories
description: Use when a bounded request needs evidence-grounded resume bullets, JD mapping, project explanation, STAR stories, interview questions, interview scripts, company research, or a consolidated Markdown preparation packet; full student mock-interview, role-specific delivery, and real-interview review use their dedicated Skills.
---

# Building Resume Interview Stories

## Core Principle

Build the story from evidence outward: facts first, business meaning second, resume third, interview preparation last. Never make a candidate sound stronger by making their experience less true.

## Route the Request

本 Skill 提供履历证据与表达方法，不抢完整学生交付的主路由：通用模拟面试使用 `student-mock-interview-delivery`，明确公司/JD的面试前准备使用 `student-role-interview-prep`，真实已发生面试的逐字稿复盘使用 `student-interview-review-delivery`。只有用户明确要求简历或故事本身时，才由本 Skill 主导。

| User asks for | Required references | Deliverable |
| --- | --- | --- |
| Understand the project | `references/intake-and-evidence.md`; add `references/visual-story-contract.md` for a durable explanation with complex relationships | Plain-language business model and workflow |
| Resume bullets only | Intake reference + `references/resume-framework.md` | 3-5 concise bullets, including a result |
| Review or optimize a resume | Intake reference + resume reference | JD evidence map, prioritized fixes, rewritten content, and layout QA |
| Interview preparation | Intake + resume + `references/interview-framework.md` | Resume-linked business/technical Q&A |
| Complete package | All references, including `references/visual-story-contract.md` | Sourced Markdown dossier |

Read each selected reference completely before drafting. Do not load unneeded references.

For a complete dossier or a project explanation with three or more dependent stages, actors, components, decisions, or validation paths, **REQUIRED SUB-SKILL:** Use `visual-document-delivery` and create a `visual_contract`. A bullet-only task or simple short answer remains text-only and records a concrete `no_visual_reason`; do not force a visual or render pass into it.

## Mandatory Evidence Gate

Before writing candidate claims, create a compact fact ledger using these labels:

- **Confirmed:** explicitly provided by the user or visible in their source artifact.
- **Externally verified:** public company or industry fact confirmed by a credible source.
- **Inferred:** plausible interpretation that the user has not confirmed.
- **Knowledge supplement:** domain explanation added to help the user understand the work.
- **Open:** missing fact that could materially change ownership, result, or technical depth.

Only **Confirmed** experience can be written as the candidate's action or result. Externally verified facts may describe the company or industry, not the candidate's contribution. Confirm an inference before promoting it into a claim. Never turn a knowledge supplement into personal experience.

If an Open item changes the central story, ask one focused question. If it only affects precision, draft conservatively and list what to verify.

## Workflow

### 1. Normalize the Input

Separate the user's material into company/JD, actual actions, project background, process, result, reflection, tools, collaboration, and metrics. Correct obvious typos without silently changing meaning.

### 2. Turn the JD Into a Screening Rubric

Treat the JD as the question and the resume as the evidence-backed answer. Extract the official target title, responsibilities, capability signals, business context, and explicit constraints. Map each high-priority requirement to the strongest Confirmed evidence and record any gap.

Use one target role per resume version. If no JD is available, confirm the role family or state the screening assumptions instead of silently optimizing for a generic audience.

### 3. Research Only What Is External

When company context is requested, research the legal entity, business, industry position, and current context. Prefer official registries, company pages, regulators, filings, and reputable reporting. Cite sources and label dynamic claims such as headcount, funding, assets, rankings, products, or hiring as time-sensitive.

Do not use web research to invent internal team structure, confidential results, or the candidate's responsibilities.

### 4. Build the Business Model First

Explain in plain language:

1. Who had the problem?
2. What was difficult before?
3. What entered the process?
4. What did the candidate change?
5. What came out?
6. How was quality controlled?
7. What business value resulted?

Lead with a one-sentence definition and one concrete example. Define jargon only after the reader understands the workflow.

For a complex durable explanation, use [visual-story-contract.md](references/visual-story-contract.md) to place an evidence-safe `input → candidate action → output → validation → result/Open` flow beside this section. Personal-action nodes must be Confirmed; team/system context, public facts, inference, teaching content, and Open results remain visibly separate.

### 5. Lock the Story

Check ownership, implementation depth, collaboration route, deployment status, result evidence, and scale. Use conservative verbs until these are confirmed.

Do not proceed to interview scripts when the candidate still cannot explain the resume bullets in plain language. Teach the project first, then draft the resume, then generate questions.

### 6. Draft the Resume

Use implicit STAR rather than visible `S/T/A/R` labels. Start each bullet with a business-facing mini-title when it improves scanning. Default structure:

1. Requirement/problem definition.
2. Solution execution.
3. Quality/risk control.
4. Expansion, reuse, or collaboration.
5. Result, if it is not already explicit.

Keep tools as evidence of execution, not the subject of every bullet. State one outcome even when no numeric metric exists; use scope, workflow change, reusable artifact, adoption, coverage, or decision support instead of fabricated percentages.

### 7. Run the Screening and Layout Pass

Review the resume twice:

1. **Ten-second screen:** Can a recruiter immediately identify the target, education, timeline, strongest relevant experience, and evidence for the main JD requirements?
2. **Delivery QA:** Are hierarchy, field order, density, alignment, emphasis, spelling, pagination, filename, and PDF preview consistent?

Default to one page for early-career candidates only when the meaningful content remains readable. Keep emphasis scarce. Do not default to photos or sensitive identity fields; include them only when the requirement, locale, and user's informed choice support doing so. Treat templates and exact typography values as examples, not universal rules.

### 8. Add the Technical Model

Only add technical depth when the role or user request calls for it. Separate:

- what the candidate actually implemented;
- the end-to-end system context they can explain;
- general domain knowledge and possible future improvements.

Technical depth should cover inputs, transformations, outputs, controls, edge cases, validation, and tradeoffs. Match depth to the candidate's real contribution.

### 9. Generate Interview Preparation

Generate questions from claims that appear in the resume, not from an unrelated knowledge checklist. Cover business understanding, personal contribution, decisions, difficult cases, validation, result, limitations, and reflection. Add technical questions only for technical claims or target roles.

For each question provide:

- interviewer's intent;
- answer framework;
- natural reference answer;
- truth boundary or fact to personalize when needed.

### 10. Package the Output

For a complete Markdown dossier, use this order:

1. Company background and sources.
2. Cleaned JD, evidence map, and remaining gaps.
3. Final resume content and screening/layout notes.
4. Plain-language business explanation and workflow.
5. Technical framework and boundaries.
6. Business interview questions and answers.
7. Technical interview questions and answers.
8. Remaining facts to verify.

Place the JD evidence matrix beside the screening rubric and each project visual beside its plain-language explanation, before the related interview questions. Do not create a separate image appendix or image wall. For rendered dossiers, inspect every final page for placement, captions, source/fact status, normal-zoom readability, clipping, and page breaks.

## Non-Negotiable Guardrails

- Never fabricate metrics, adoption, deployment, model performance, revenue impact, or strategy returns.
- Never upgrade “assisted/participated/tested” into “owned/designed/led” without evidence.
- Never imply direct stakeholder communication when requirements were relayed by a mentor or colleague.
- Never force an AI, product, strategy, or leadership angle merely because it matches the target role.
- Never present a prototype as a production platform.
- Never let a polished answer hide that the user does not understand the underlying project.
- Never return a generic interview encyclopedia when the user asked only for concise resume content.

## Quality Gate

Before delivery, verify:

- Every candidate claim traces to Confirmed evidence.
- Every high-priority JD requirement maps to evidence or a visible gap.
- Company claims have sources and dynamic facts have dates or caveats.
- The business explanation is understandable without domain expertise.
- The resume begins with problem/action/value, not a technology list.
- The target, education, timeline, and strongest evidence survive a ten-second scan.
- At least one result is stated without unsupported precision.
- The final layout has consistent hierarchy, restrained emphasis, no accidental blank page, and no unconfirmed sensitive fields.
- Generic technical knowledge is visibly separated from personal work.
- Interview answers stay within the final resume's claim boundary.
- Open high-impact facts are asked or clearly surfaced.
- Complete dossiers with complex relationships include the correct visual plan, evidence-safe labels, structural readback, and every-page render QA.
- Resume-bullet-only tasks remain concise and do not receive an unnecessary diagram; the ten-second screen and one-page guidance remain unchanged.

If any check fails, revise before presenting the output.
