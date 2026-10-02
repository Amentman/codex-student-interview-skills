# RED baseline: career-plan delivery without the new Skill

Date: 2026-09-02

Three fresh-context agents were asked to design the workflow without reading the new Skill or its design spec. The purpose was to capture observable omissions, not to evaluate writing quality.

## Scenario results

| Required behavior | Cross-industry candidate | Reference belongs to another student | Whitepaper + current product map |
|---|---|---|---|
| Separate reusable industry whitepaper | **Missing.** Proposed a one-page primer inside the personal plan. | **Missing.** Went directly to one personal planning document. | Present. Proposed a reusable whitepaper separate from the personal plan. |
| Reference/current-student fact boundary | Present. | Present and explicit. | Present. |
| Preserve original resume attachment | **Weak.** Mentioned only an attachment index, not preservation as a hard invariant. | Present. | **Missing.** Did not require the original resume attachment to remain on the student page. |
| Read the live product knowledge base | **Weak.** Named the boss knowledge base, but did not define a fresh-read source ledger. | **Missing.** Product support stayed generic. | Present and time-stamped. |
| Map role gaps to product outputs and acceptance | **Weak.** Listed generic deliverables without a role-gap-to-output acceptance table. | **Weak.** Listed product types but not a complete responsibility/acceptance map. | Present. |
| Use the fixed Feishu hierarchy | **Missing.** Deferred the destination and did not lock known parent tokens. | **Missing.** Described a generic target document/database. | **Missing.** Invented generic directory names instead of the confirmed parent hierarchy. |
| Require write-after-readback verification | Present. | Present. | Present. |

## RED findings that the Skill must close

1. A useful industry introduction was rationalized as a short chapter inside the student plan, so it was not reusable across students.
2. Correct fact-boundary guidance did not guarantee original-resume preservation or a durable source manifest.
3. Product mapping drifted toward generic service names unless the workflow required a fresh read of the live product knowledge base and a role gap -> service action -> student output -> acceptance-evidence map.
4. Even strong answers invented or deferred the Feishu location rather than using the confirmed `求职策略与知识库 -> 行业白皮书与岗位科普` and `职业规划` parents.
5. Readback was commonly remembered, but it was not coupled to parent validation, attachment validation, and two-document cross-link validation.

Result: RED confirmed. Every scenario omitted at least one required behavior, and the cross-industry scenario missed four of the seven invariants.

## GREEN comparison after loading the Skill

Three new fresh-context agents read the completed Skill and the references it routed for the same scenarios. They did not edit files or write Feishu.

| Required behavior | Cross-industry candidate | Reference belongs to another student | Whitepaper + current product map |
|---|---|---|---|
| Separate reusable industry whitepaper | Present | Present | Present |
| Reference/current-student fact boundary | Present | Present | Present |
| Preserve original resume attachment | Present | Present | Present |
| Read the live product knowledge base | Present | Present | Present |
| Map role gaps to product outputs and acceptance | Present | Present | Present |
| Use the fixed Feishu hierarchy | Present | Present | Present |
| Require write-after-readback verification | Present | Present | Present |

Observable change: all three responses independently named the two-document order, the original attachment invariant, the live knowledge-base read, the full role-gap-to-service-to-student-output-to-acceptance Map, the fixed Feishu destinations, and the post-write readback/manifest gate. GREEN confirmed for the seven targeted behaviors.
