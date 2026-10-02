# 交付 Manifest 与读回证据

`manifest.json` 必须通过 `readback_path` 指向独立的飞书读回 JSON。本地正文和飞书读回是两类证据，不得互相替代。

个人规划必须声明交付模式。默认使用紧凑完整的标准学生版 `standard`；只有用户明确要求深度完整版时使用 `full`，明确要求摘要时使用 `concise`：

```json
{
  "visual_manifest_path": "qa/visual-manifest.json",
  "expected": {
    "career_plan_delivery_mode": "standard",
    "require_source_fidelity": true
  },
  "career_plan": {
    "delivery_mode": "standard",
    "required_route_keys": ["primary_route", "secondary_route"],
    "expected_project_count": 2,
    "requires_agent_company_split": true,
    "rendered_pdf_path": "qa/career-plan.pdf",
    "rendered_pages_dir": "qa/rendered-personal",
    "source_fidelity": {
      "authoritative_artifact_path": "output/student-career-plan.pdf",
      "authoritative_artifact_sha256": "64-character-lowercase-hex",
      "authoritative_text_path": "qa/authoritative-plan.txt",
      "protected_marker_groups": [
        {"label": "headings", "markers": ["方向优先级", "投递与面试策略"]},
        {"label": "sources", "markers": ["[S1]", "https://example.com/source"]},
        {"label": "decision chain", "markers": ["项目证据 → 简历版本 → 正式投递 → 面试反馈"]}
      ],
      "required_visual_ids": ["career-route-map", "evidence-chain", "timeline"]
    }
  }
}
```

只要写入前已有完整 PDF、Word、Markdown 或已确认飞书稿，就必须设置 `require_source_fidelity: true` 并填写 `source_fidelity`。`authoritative_artifact_sha256` 锁定母版文件，`authoritative_text_path` 保存可检索的完整文字快照；`protected_marker_groups` 至少覆盖章节、关键数字/结论、公司名、引用/URL和行动链条。若用户明确要另做摘要，摘要必须作为独立产物，不把该门关闭后覆盖完整版。

`visual_manifest_path` 指向符合 `visual-document-delivery` 合同的独立 JSON。白皮书与完整个人规划的复杂关系、必需图、媒体读回和最终渲染逐页检查统一记录在该文件中。`scripts/validate_delivery.py` 会调用共享视觉校验；它是现有职业规划校验的附加门，不替代正文、父子关系、附件、PDF 指纹或逐页图片校验。

`whitepaper` 为可选对象。用户只要求个人职业规划时，manifest、`expected`、`career_plan` 和飞书读回都可以不声明白皮书或 `whitepaper_url`；校验器不会因此报错。只要 manifest 声明了 `whitepaper`，白皮书正文、链接、父级、来源和读回字段即全部必检，个人规划中的延伸阅读链接也必须一致。

`standard` 使用 1—3 条 `required_route_keys`；键名自定义，但必须与读回证据的 `route_coverage` 一致。`full` 保留原有深度验收，通常至少两条路线；只有用户明确要求精简版时才使用 `concise`。若规划包含 AI Agent 方向并需要公司池，设置 `requires_agent_company_split: true`，校验器会要求大厂和中小/垂直公司两组真实名称。

## 标准版读回字段

`standard` 在 `career_plan.standard_plan_checks` 中记录真实正文证据，不用字符数和页数冒充完整度：

```json
{
  "direction_count_observed": 2,
  "salary_reference_date": "2026-09-29",
  "route_coverage": {
    "primary_route": {
      "label": "Agent 应用开发",
      "daily_work_markers": ["检索与工具调用"],
      "fit_markers": ["Zygote"],
      "role_markers": ["Agent 应用工程师"],
      "salary_markers": ["约 25—42 万/年"],
      "company_markers": ["智谱", "携程"]
    },
    "secondary_route": {
      "label": "Agent 评测／应用算法",
      "daily_work_markers": ["Bad Case 归因"],
      "fit_markers": ["LLM Teaming"],
      "role_markers": ["Agent 评测工程师"],
      "salary_markers": ["约 30—55 万/年"],
      "company_markers": ["字节跳动", "华为"]
    }
  },
  "company_pool": {
    "current_samples_separated_from_research_pool": true
  },
  "agent_company_split": {
    "bigtech_markers": ["字节跳动", "华为"],
    "sme_markers": ["智谱", "MiniMax"],
    "role_tier_boundary_present": true
  }
}
```

校验器会在正文中查找这些 marker，并验证项目标题位于简历版本和正式投递之前。`expected_project_count` 由用户范围和学生类型决定；应届生通常为 1—2，社招可以为 0，但仍需用既有项目/经历形成岗位证据。

## 原始简历指纹

`career_plan.original_resume` 至少包含：

```json
{
  "path": "/absolute/path/student-resume.pdf",
  "filename": "student-resume.pdf",
  "size_bytes": 123456,
  "sha256": "64-character-lowercase-hex"
}
```

校验器会重新读取本地文件，校验存在性、文件名、字节数和 SHA-256。仅写入一个看似简历的路径不会通过。

## 飞书读回 JSON

下面保留的是 `full` 且同时交付白皮书时的完整示例。`standard` 只保留实际交付对象，并用上文的 `standard_plan_checks` 替换 `full_plan_checks`；未交付白皮书时删除 `whitepaper` 和 `whitepaper_url`，不要制造占位对象。

```json
{
  "method": "lark-cli",
  "read_at": "2026-09-04T17:30:00+08:00",
  "whitepaper": {
    "url": "https://example.invalid/wiki/token",
    "title": "赛道｜行业与岗位白皮书（2026版）",
    "parent_node_token": "parent-token",
    "observed_parent_node_token": "parent-token",
    "observed_parent_title": "行业白皮书与岗位科普",
    "parent_relation_source": "sidebar-tree",
    "observed_node_level": 4,
    "observed_node_pos": "4,2,4,3",
    "observed_parent_level": 3,
    "observed_parent_node_pos": "4,2,4",
    "direct_parent_verified": true,
    "duplicate_page_count": 1,
    "unexpected_blank_sibling_count": 0,
    "source_first_marker_present": true,
    "source_last_marker_present": true,
    "source_count_observed": 20,
    "required_sections_present": 10,
    "required_sections_total": 10
  },
  "career_plan": {
    "url": "https://example.invalid/wiki/token",
    "title": "姓名｜主攻方向职业规划",
    "parent_node_token": "parent-token",
    "observed_parent_node_token": "parent-token",
    "observed_parent_title": "职业规划",
    "parent_relation_source": "sidebar-tree",
    "observed_node_level": 3,
    "observed_node_pos": "4,8,1",
    "observed_parent_level": 2,
    "observed_parent_node_pos": "4,8",
    "direct_parent_verified": true,
    "duplicate_page_count": 1,
    "unexpected_blank_sibling_count": 0,
    "whitepaper_url": "https://example.invalid/wiki/whitepaper-token",
    "required_sections_present": 10,
    "required_sections_total": 10,
    "original_resume_attachment_count": 1,
    "full_plan_checks": {
      "main_section_count": 15,
      "jd_count_observed": 8,
      "project_count_observed": 2,
      "resume_version_count_observed": 3,
      "internship_stage_count_observed": 3,
      "has_90_day_plan": true,
      "has_graduation_timeline": true,
      "route_coverage": {
        "primary_route": {
          "label": "技术型 AI 产品",
          "jd_count_observed": 4,
          "project_count_observed": 1,
          "resume_version_count_observed": 1,
          "adjustment_conditions_present": true,
          "jd_markers": ["公司｜岗位 A", "公司｜岗位 B"],
          "project_markers": ["项目一：场景化项目"],
          "resume_markers": ["V1 产品版"],
          "adjustment_markers": ["转为产品单主线"]
        },
        "technical_route": {
          "label": "Agent 应用开发",
          "jd_count_observed": 4,
          "project_count_observed": 1,
          "resume_version_count_observed": 1,
          "adjustment_conditions_present": true,
          "jd_markers": ["公司｜岗位 C", "公司｜岗位 D"],
          "project_markers": ["项目二：Agent 项目"],
          "resume_markers": ["V2 Agent 版"],
          "adjustment_markers": ["转为 Agent 单主线"]
        }
      }
    },
    "rendered_pdf_pages": 15,
    "rendered_pdf_sha256": "64-character-lowercase-hex",
    "rendered_page_image_count": 15,
    "visual_qa_pass": true,
    "visual_qa_pages": [
      {"page": 1, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 2, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 3, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 4, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 5, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 6, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 7, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 8, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 9, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 10, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 11, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 12, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 13, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 14, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []},
      {"page": 15, "status": "passed", "image_sha256": "64-character-lowercase-hex", "checked_items": ["clipping", "readability", "layout"], "issues": []}
    ],
    "markdown_sha256": "64-character-lowercase-hex",
    "source_fidelity_checks": {
      "visual_media_blocks": [
        {"visual_id": "career-route-map", "token": "feishu-image-token-1"},
        {"visual_id": "evidence-chain", "token": "feishu-image-token-2"},
        {"visual_id": "timeline", "token": "feishu-image-token-3"}
      ]
    },
    "attachment": {
      "block_type": "file",
      "filename": "student-resume.pdf",
      "position": "first_page",
      "preview_opened": true
    }
  }
}
```

`method` 可为 `lark-cli` 或 `browser`。使用浏览器时，保留可追溯的录屏或截图，并从最终 URL 重新打开页面读回；不得用编辑中间状态作为证据。

`parent_node_token` 是交付声明；`observed_parent_node_token` 才是从飞书当前状态读取的独立证据。`parent_relation_source` 只接受 `wiki-node-get` 或 `sidebar-tree`。使用 `sidebar-tree` 时必须填写子页/父页的层级和位置；子页应比父页深一层，且位置数组只多一个末级索引。缺字段、观察到其他父 token，或树位置不能证明直接父子关系时，校验必须失败。

`attachment.position` 只有在附件位于首页的“个人简历”或等价学生可读位置、且早于第一个编号章节时才写 `first_page`。原始简历对应的文件块必须恰好一个；附件在文末、重复附件、只有文件名或未打开预览时必须失败。

所有交付模式的 `markdown_sha256` 都必须绑定本轮飞书全文快照；标准版也不能使用未绑定的手写摘要充当 `text_path`。完整模式下，`full_plan_checks` 不是作者自评：数量必须来自飞书全文读回，并与 `text_path` 的真实标题、JD 表格链接、项目、简历版本和实习阶段计数一致。每条路线用 `label` 和四类互不重复的 `markers` 绑定正文证据；`jd_official_domains` 只填已经核验的企业官方招聘域名。`rendered_pdf_sha256` 必须由导出的 PDF 重算；逐页 PNG 使用 90 DPI 从该 PDF 渲染，尺寸不低于 600×800，并通过 SHA-256 与重新渲染结果逐页一致。`visual_qa_pages` 逐页记录图片指纹、`clipping/readability/layout` 检查项和问题列表，之后 `visual_qa_pass` 才能为 `true`。

`source_fidelity_checks.visual_media_blocks` 必须来自飞书当前页面的媒体块读回。只有 `visual_id` 和非空 token 同时存在，才视为对应图示已真正写入飞书；本地 PDF 中存在该图不算通过。

共享视觉合同中的 `render_qa` 与上述 PDF 证据必须指向同一最终版本。共享合同负责验证必需图、图注、事实边界、媒体 token 和页覆盖；本 Skill 校验器继续负责 PDF／PNG 指纹、页面尺寸、全文结构和飞书读回，两者都通过才算完成。

`unexpected_blank_sibling_count` 必须是 `0`。本次写入产生的“未命名文档”、空白导入页或其他意外同级页都必须显式清理或报告为阻塞，不能在交付验收时忽略。
