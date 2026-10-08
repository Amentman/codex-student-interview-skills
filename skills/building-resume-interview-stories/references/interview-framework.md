# Interview Framework

Use this reference only after the project story and resume claims are stable.

## 1. Build Questions From Claims

Create a claim map:

| Resume claim | Evidence | Likely challenge | Required example |
| --- | --- | --- | --- |
| Defined requirements | Notes, deliverable, user statement | How did you handle ambiguity? | One real requirement change |
| Built a workflow | Code, artifact, user statement | What was the data/process flow? | One end-to-end example |
| Improved quality | Checks, test, review | How did you know it was correct? | One detected issue |
| Produced a result | Metric or artifact | What changed because of your work? | Before/after evidence |

Every important resume bullet should generate at least one question. Do not generate technical trivia unrelated to the claims or target role.

## 2. Business Question Set

Cover:

- What did the project do in plain language?
- Who had the problem and why did it matter?
- What exactly did the candidate own?
- How were ambiguous requirements clarified?
- What alternatives or tradeoffs were considered?
- What was difficult or went wrong?
- How was quality measured or controlled?
- What result was achieved?
- What was not achieved or measured?
- What would the candidate improve?
- What did the experience reveal about career direction?

Answer with:

`Conclusion → context → personal action → result/evidence → boundary`

## 3. Technical Question Set

Only include categories supported by the experience:

- system or workflow architecture;
- inputs, transformations, outputs, and interfaces;
- core algorithm or implementation choice;
- data/model/product validation;
- edge cases and failure modes;
- performance, scale, reliability, and monitoring;
- technology choice and alternatives;
- testing and debugging;
- prototype-to-production improvements.

Answer with:

`Definition/goal → implementation → key risk → validation → tradeoff/limit`

Clearly separate actual implementation from system context and future design ideas.

## 4. Build Reusable Story and Knowledge Anchors

Before drafting answers, create two reusable sets:

- `S01...`: confirmed personal stories with source, context, personal action, artifact/result, boundary, failure/tradeoff, speaking status, and Open items.
- `K01...`: role knowledge with normal workflow, rationale, exceptions/risks, metrics/acceptance, link to the candidate, and expression boundary.

Do not remove useful role knowledge merely because the candidate has not performed the full workflow. Teach it fully, then choose one expression mode per question:

- **Personal experience:** at least one S anchor.
- **Transfer:** at least one S and one K anchor; explicitly state the missing direct experience before explaining the transferable action.
- **Role knowledge:** at least one K anchor; describe how the job normally works, not what the candidate supposedly did.
- **Scenario reasoning:** at least one K anchor and an explicit hypothetical condition.

## 5. Format Each Question

Use this structure:

### Q: [Natural interviewer question]

**Interviewer intent:** What they are testing.
**Expression mode:** Personal experience / transfer / role knowledge / scenario reasoning.
**Answer framework:** 3-5 short anchors.
**Evidence or scenario basis:** S/K anchor identifiers.
**Reference answer:** Natural spoken language. Use the shortest answer that fully makes the point; do not pad every answer to a fixed minimum. Longer answers are reserved for project introductions.
**Truth boundary:** Any detail that must be confirmed or personalized.

Do not produce robotic memorization text. The answer should be speakable and should start with the outcome or conclusion.

## 6. Handle Difficult Questions Honestly

### No numeric result

> We did not run a formal before/after measurement, so I would not claim a percentage. The verifiable result was [artifact/process/coverage/adoption]. If continuing, I would track [metric].

### Team project

> The project was collaborative. I specifically owned/implemented [confirmed part], while [other part] was handled by [team/mentor].

### Knowledge beyond personal implementation

> I did not implement that part directly. My understanding of its role in the overall system is [brief explanation].

### Prototype, not production

> The output reached [prototype/internal validation] rather than full production. Productionization would still require [concrete gaps].

## 7. Full Markdown Package

When requested, use:

1. `公司与岗位背景`
2. `事实清单与待确认项`
3. `最终简历内容`
4. `业务白话：一句话、角色、前后变化、全流程、案例、价值`
5. `技术梳理：架构、数据流、核心逻辑、验证、边界、取舍`
6. `业务面试题`
7. `技术面试题`
8. `面试前必须补齐的真实案例和指标`
9. `公开资料来源与访问日期`

Keep confirmed facts, external research, knowledge supplements, and open items visibly distinct.

## 8. Acceptance Scenarios

The preparation passes only if it handles all of these:

| Scenario | Required behavior |
| --- | --- |
| User is not a domain expert | Teach the workflow before using jargon |
| No metrics supplied | Use a truthful qualitative result and request measurable evidence |
| Ownership is unclear | Use conservative verbs or ask one focused question |
| Technical project, non-technical target role | Preserve technical credibility while leading with business value |
| User asks only for resume | Return concise bullets, not a full question bank |
| User asks for complete package | Include sources, fact boundaries, business and technical preparation |
| User cannot explain their own resume | Pause interview scripting and rebuild understanding first |
| Candidate has not done the full target-role workflow | Teach the K knowledge fully, then use transfer, role-knowledge, or hypothetical wording instead of either omitting it or claiming it as experience |

## 9. Final Consistency Check

- Questions trace to resume claims.
- Answers do not add stronger ownership than the resume.
- Technical answers identify what was implemented versus understood.
- At least one answer covers failure, limitation, or missing measurement.
- No answer depends on an invented example.
- Every answer declares an expression mode and cites the required S/K anchors.
- The candidate can personalize all marked boundaries before memorizing.
