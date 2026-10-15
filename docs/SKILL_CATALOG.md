# 校招交付 Skills 目录

这套目录把学生求职服务拆成可独立发现、可组合调用的 Agent Skills。先按用户请求选择一个主入口；需要资料整理、复杂文档或岗位核验时，再调用对应辅助 Skill。岗位搜索和写回必须保留来源、核验时间、证据等级与待确认项。

| Skill | 主入口 | 适用请求 |
| --- | --- | --- |
| `auditing-candidate-resumes` | 候选人审查 | 从 HR/招聘方视角比较简历、识别时间线与岗位匹配风险 |
| `building-resume-interview-stories` | 证据化表达 | 简历要点、JD 映射、项目解释、STAR 故事与面试题 |
| `campus-job-matching` | 校招选岗主入口 | 找真实在招岗位、匹配简历、生成投递清单与截图包 |
| `campus-recommend` | 岗位推荐写回 | 已有学生画像，按城市/方向推荐岗位并写回多维表 |
| `delivering-student-career-plans` | 职业规划 | 方向地图、公司池、薪资、项目补强、简历分版与时间线 |
| `designing-student-portfolio-products` | 作品集规划 | 基于真实业务设计可落地的作品集前置资料、PRD、Demo 与验收 |
| `recording-processing` | 录音整理 | 会议、课程、咨询或语音备忘的转写整理与获授权知识库分流 |
| `revising-and-delivering-resumes` | 简历修改交付 | 简历诊断、改写、Word/PDF 版本与投递验收 |
| `student-interview-review-delivery` | 真实面试复盘 | 已发生面试的逐题分析、纠正、训练任务与复盘页 |
| `student-job-content` | 求职内容 | 岗位认知、求职文章、学校与企业差距、项目能力和面试判断 |
| `student-mock-interview-delivery` | 通用模拟面试 | 无明确公司/JD 的老师版、学生版和训练工作簿 |
| `student-role-interview-prep` | 专岗面试准备 | 已有公司、岗位、JD 或邀约的定向准备 |
| `visual-document-delivery` | 复杂文档验收 | 含流程、关系、时间线、比较或可信数据的文档图解与渲染验收 |

## 路由顺序

1. 用户只说“找校招岗位、筛岗、投递清单”时进入 campus-job-matching；若明确要求写回学生多维表，可同时参考 campus-recommend。
2. 用户要职业方向和投递节奏时进入 delivering-student-career-plans；不要把真实岗位搜索结果写成静态公司池。
3. 用户要简历改写、排版或投递版文件时进入 revising-and-delivering-resumes；只要解释项目或准备表达，可使用 building-resume-interview-stories。
4. 没有明确公司/JD 的面试训练进入 student-mock-interview-delivery；面试前已有公司/JD 进入 student-role-interview-prep；面试已经发生并有逐字稿进入 student-interview-review-delivery。
5. 录音只做整理时使用 recording-processing；它不能替代真实面试复盘。
6. 作品集需要规划、PRD、UI/UX Demo 或验收标准时进入 designing-student-portfolio-products；规划不等于学生已经完成产品。
7. 任一主入口产出复杂长文、流程图、时间线、角色交接或可信数据图时调用 visual-document-delivery，并按目标格式验收。

## 岗位匹配的硬限制

每个学生每家公司最多保留 3 个岗位。岗位完成评分和排序后，先运行 `skills/campus-job-matching/scripts/enforce_company_cap.py`，再生成 Excel、截图包或写回飞书；回读时按公司计数，超过 3 条即判定未完成。该限制适用于不同城市、不同方向和同公司的多个职位 ID。

## 公开边界

仓库只提供通用流程、可选脚本和脱敏示例，不包含学生简历、逐字稿、私人知识库、飞书节点、访问令牌或固定本机路径。每个使用者需要在当前任务或自己的配置中提供资料位置、外部工具权限和目标交付面。
