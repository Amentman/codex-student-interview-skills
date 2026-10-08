import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VALIDATOR = SKILL_DIR / "scripts" / "validate_delivery.py"
NAME = "测试同学"


def tier_sections():
    rows = []
    for score, label, role in (
        ("90%", "主投", "业务运营"),
        ("80%", "稳妥拓展", "数据运营"),
        ("70%", "进阶尝试", "商业分析"),
    ):
        rows.append(f"""### {score}｜{label}｜{role}
**岗位日常：** 把岗位的核心工作拆成数据口径、分析动作、协作和复盘。
**匹配证据：** 项目 A 的数据分析和问题拆解可以直接或迁移使用。
**差距：** 行业协作范围和最终采用情况仍需补证。
**档位原因：** 依据直接证据和缺口综合判断，并非精确算法评分。
**投递建议：** 按该档位投递，同时准备项目证据和边界说明。
""")
    return "\n".join(rows)


def teacher_card(index, title):
    return f"""#### 题目{index}｜{title}
**考察目标：** 判断候选人能否围绕真实项目说明问题、个人动作、产物和事实边界。
**表达类型：** 迁移表达
**合格回答要素：** 先给结论，再交代场景、本人动作、结果或产物、复盘和岗位关联。
**候选人可用素材：** S01｜项目 A；本人完成数据清洗、方案比较和分析报告，业务采用范围仍待核实。
**岗位场景补充：** K01｜业务运营通常要先统一口径，再比较方案，并为关键结果保留人工复核。
**参考回答方向：** 老师重点听候选人是否能把项目 A 从业务问题讲到个人动作，并明确哪些结果能认领、哪些仍需补证，而不是只复述岗位术语。
**继续追问：** 第一层追具体输入、动作和产物；第二层追 Bad Case、方案取舍、结果归因和职责边界。
**常见问题：** 容易把团队背景说成个人成绩，或只有方法名，没有真实过程。
**反馈建议：** 指出缺失的事实层，并要求下次用“结论—场景—动作—结果—复盘”重录一遍。

"""


def student_card(index, title):
    return f"""#### 题目{index}｜{title}
**考察点：** 证明自己能用真实经历说明判断、个人动作、产物和边界。
**表达类型：** 迁移表达
**你的答题主线：** 先回答题目结论，再用项目 A 说明场景、动作、结果，最后回扣目标岗位。
**事实或场景依据：** S01｜项目 A 的数据清洗和方案比较；K01｜业务运营的口径、验证与人工复核方法。
**参考表达：** 对“{title}”这道题，我没有直接做过完整闭环，但在项目 A 中做过口径核对和方案比较。放到这个岗位，我会先确认目标和指标，再小范围验证，最后保留人工复核。
**我的版本：**
**答题提示：** 先把请补项写实，再录音 2 遍；第二遍不得照读，并检查是否出现具体动作、产物和边界。

"""


CATEGORIES = [
    ("第一部分｜基础行为面", [
        "请做一分钟自我介绍", "为什么选择目标岗位", "为什么选择这家公司", "你的核心优势是什么",
        "你的短板是什么", "未来三年的职业规划", "如何证明稳定性", "你想反问什么",
    ]),
    ("第二部分｜宝洁八大问", [
        "讲一次设定高目标并完成", "讲一次主动推动团队", "讲一次收集信息解决问题", "讲一次用事实说服他人",
        "讲一次团队合作", "讲一次创新改善", "讲一次判断优先级", "讲一次快速学习并应用",
    ]),
    ("第三部分｜实习与项目深挖", [
        "用大白话讲清项目 A", "项目 A 中你个人做了什么", "项目 A 的结果如何验证", "讲一个项目 A 的 Bad Case",
    ]),
    ("第四部分｜岗位专业题", [
        "如何拆解一个模糊业务问题", "如何设计指标与归因", "AI 可以替代哪些环节", "信息不足时如何做判断",
    ]),
]


def shared_questions(card_builder):
    blocks = []
    index = 1
    for category, titles in CATEGORIES:
        blocks.append(f"### {category}\n\n")
        for title in titles:
            blocks.append(card_builder(index, title))
            index += 1
    return "".join(blocks)


def full_teacher():
    return f"""# {NAME}｜模拟面试指导者版

> 原始简历：[测试同学简历.pdf](测试同学简历.pdf)

## 老师快速上手
目标是帮助不熟悉岗位的老师在一场面试中看懂候选人的业务主线、真实动作、证据边界和表达短板。

## 候选人业务主线
项目 A 证明数据分析、问题拆解和证据意识；最关键风险是业务采用范围和跨团队协作细节未确认。

## 三档匹配 JD
{tier_sections()}

## JD逐条证据矩阵
| JD 要求 | 证据等级 | 候选人证据 | 缺口 | 验证题 |
| --- | --- | --- | --- | --- |
| 数据分析 | 直接证据 | 项目 A | 业务采用范围待确认 | 题目17 |
| 跨团队协作 | 可迁移证据 | 课程协作 | 企业协作不足 | 题目10 |
| Agent 搭建 | 缺口 | 无直接经历 | 需补作品 | 题目23 |

## 面试准备度与建议模式
建议结构化训练；先验证项目 A 的事实和口述闭环，再做岗位专业题。

## 口述能力四级评分
当前按 1–2 级之间预判，须在现场根据能否讲清动作、产物和 Bad Case 复核。

## 实习履历大白话拆解
### 项目 A｜到底做了什么
业务方拿到的数据口径不稳定，候选人负责核对字段、清洗数据、比较方案并输出报告。能确认的是分析过程和报告；最终采用范围仍是 Open。老师应继续追输入、本人动作、报告名称、异常处理和采用证据。

## 项目地图与必做产物
项目 A：业务问题 → 原始数据 → 口径核对 → 清洗与方案比较 → 分析报告 → 复盘；学生需补报告名称和采用证据。

## 数值反推
所有结果先核对定义、基线、统计窗口、对照方式和可归因范围；本示例没有可确认的数值成果。

## 职责边界
Confirmed：数据核对、分析和报告。Open：业务采用范围、跨团队推动深度。

## 事实账本
- Confirmed：项目 A 的数据清洗、方案比较和分析报告。
- Externally verified：目标 JD 要求数据分析与协作。
- Inferred：分析能力可能迁移至业务运营。
- Knowledge supplement：指标体系和 Agent 人工兜底属于岗位知识。
- Open：采用范围、协作方、真实业务结果。

## 故事证据与岗位补充
### S01｜项目 A：数据口径与方案比较
**来源：** 简历与项目报告
**场景／目标：** 业务方需要从口径不稳定的数据中获得可复核结论。
**本人动作：** 核对字段、清洗数据、比较两种方案并输出分析报告。
**产物／结果：** 已确认分析报告；最终采用范围仍为 Open。
**职责边界：** 可认领分析过程，不认领未证实的团队采用和业务结果。
**失败／取舍：** 字段定义变化导致跨周期不可比，因此优先统一口径。
**学生原话／口述状态：** 已有事实材料，仍需改成自然口述并补报告名称。
**Open：** 协作方、报告名称和最终采用证据。

### K01｜业务运营如何把分析变成可执行动作
**岗位通常怎么做：** 先统一目标和指标口径，再比较方案、小范围验证并复盘。
**为什么这样做：** 避免口径不同造成伪结论，也避免一次性放大未经验证的方案。
**常见例外／风险：** 数据量太小、外部环境变化或协作链路过长都会干扰归因。
**指标／验收：** 同时看结果指标、过程指标和护栏指标，并说明统计窗口。
**与学生经历的连接：** S01 已做过口径核对和方案比较，可迁移到运营验证。
**表达边界：** 这是岗位方法，不得说成自己已经完整负责过业务运营闭环。

## 个性化锚点清单
- E01｜Confirmed｜简历｜项目 A：清洗数据、比较方案并交付分析报告
- J01｜Externally verified｜目标 JD｜要求数据分析和跨团队协作
- O01｜Open｜待确认｜项目 A 的采用范围和最终业务结果

## 核心经历深挖覆盖
### P01｜项目 A
- 业务问题：业务方无法稳定获得可复核结论
- 输入：原始数据和需求说明
- 个人动作：核对口径、清洗数据、比较方案、输出报告
- 产物：分析报告和复盘记录
- 数字：没有可靠数值成果
- Bad Case：字段定义变化导致跨周期不可比
- 职责边界：本人完成分析，采用范围待确认
- 对应题目：题目17、题目18、题目19、题目20

## 业务运营追问路线
### 业务流程图
问题定义 → 数据口径 → 分析判断 → 运营动作 → 结果验证 → 复盘沉淀。
### 指标与归因
区分结果指标、过程指标和护栏指标，先排口径、流量结构和外部变化，再判断动作贡献。

## 数值成果来源索引
本示例没有候选人数值成果。

## 核心项目架构／图解
看什么：先看业务输入如何经过学生的分析动作变成可复核的产物。

```mermaid
flowchart LR
    A[业务输入] --> B[口径核对] --> C[分析与方案比较] --> D[产物与校验]
```

本人负责数据核对和分析；团队采用范围是 Open；对应题目17—20。

## 模拟面试流程
5 分钟定位与动机，15 分钟行为与宝洁八大问，20 分钟项目深挖，10 分钟岗位题，10 分钟反馈与作业。

## 模拟面试问题与带教指引
{shared_questions(teacher_card)}

## 课后反馈模板
先写一句总判断，再分别记录“已经能讲清的证据”“需要补的事实”“结构或表达问题”“下一轮必须完成的录音／产物”。反馈必须落到可执行动作，不能只写多练习。
"""


def full_student():
    return f"""# {NAME}｜学生面试准备版

## 如何使用这份材料
先看定位和经历地图，再完成 24 道问题。参考表达只是起步稿：补齐请补项，改成自己的说话方式，完成两遍录音后再脱稿。

## 核心定位
项目 A 证明了数据分析、问题拆解和证据意识；面试中要避免把团队结果或未确认的采用范围说成个人成绩。

## 三档匹配 JD
{tier_sections()}

## 项目地图
项目 A：业务问题 → 原始数据 → 口径核对 → 清洗和方案比较 → 分析报告 → 复盘。需要补齐报告名称、协作方和采用范围。

## 术语大白话卡
- 指标口径：同一个数字究竟怎么算，分子、分母、时间窗口和过滤条件是什么。
- 归因：结果变化是否真的由某个动作造成，而不是流量结构或外部环境变化。
- Agent：能调用工具完成一段流程的 AI 系统，关键任务仍需权限、校验和人工兜底。

## 指标口径扫盲
### 指标1｜转化率
**大白话：** 看到或进入某个环节的人里，最后有多少真正完成了目标动作。
**怎么算／怎么看：** 完成人数 ÷ 进入人数，并同时说清时间窗口。
**为什么重要：** 它用来判断业务动作是否真的推动了下一步。
**容易误判：** 分子、分母、流量人群或时间窗口变了，就不能直接比。
**候选人边界：** 可说自己如何核对口径，不认领尚未证实的业务结果。
### 指标2｜处理时效
**大白话：** 从收到输入到交付结果用了多久。
**怎么算／怎么看：** 交付时间减去开始时间，需统一起止节点。
**为什么重要：** 它能判断流程是否变快，但不能单独代表质量变好。
**容易误判：** 只看平均值可能掩盖极慢的异常样本。
**候选人边界：** 只说简历和原始产物能支持的节点。
### 指标3｜满意度
**大白话：** 使用结果的人觉得好不好用。
**怎么算／怎么看：** 先定义量表、样本和收集方式，再计算平均分或满意占比。
**为什么重要：** 它是结果是否可用的一类证据。
**容易误判：** 样本太少或只问熟人，分数会失真。
**候选人边界：** 没有调研记录时必须标记 Open。

## 岗位与行业知识
业务运营不是只交一张表，而是把模糊问题拆成指标，找到原因，提出动作，再用数据验证。AI 适合重复取数、整理和初步分析，人仍负责口径、异常、风险和最终业务判断。

## 故事证据与岗位补充
### S01｜项目 A：数据口径与方案比较
**来源：** 简历与项目报告
**场景／目标：** 业务方需要从口径不稳定的数据中获得可复核结论。
**本人动作：** 核对字段、清洗数据、比较两种方案并输出分析报告。
**产物／结果：** 已确认分析报告；最终采用范围仍为 Open。
**职责边界：** 可认领分析过程，不认领未证实的团队采用和业务结果。
**失败／取舍：** 字段定义变化导致跨周期不可比，因此优先统一口径。
**学生原话／口述状态：** 已有事实材料，仍需改成自然口述并补报告名称。
**Open：** 协作方、报告名称和最终采用证据。

### K01｜业务运营如何把分析变成可执行动作
**岗位通常怎么做：** 先统一目标和指标口径，再比较方案、小范围验证并复盘。
**为什么这样做：** 避免口径不同造成伪结论，也避免一次性放大未经验证的方案。
**常见例外／风险：** 数据量太小、外部环境变化或协作链路过长都会干扰归因。
**指标／验收：** 同时看结果指标、过程指标和护栏指标，并说明统计窗口。
**与学生经历的连接：** S01 已做过口径核对和方案比较，可迁移到运营验证。
**表达边界：** 这是岗位方法，不得说成自己已经完整负责过业务运营闭环。

## 核心项目架构／图解
看什么：先看项目的输入、本人动作、输出和校验如何连起来。

```mermaid
flowchart LR
    A[业务输入] --> B[口径核对] --> C[分析与方案比较] --> D[产物与校验]
```

本人负责数据核对和分析；团队采用范围是 Open；对应题目17—20。

## 面试问题与个人逐字稿
{shared_questions(student_card)}

## 面试前任务
| 优先级 | 任务 | 交付物 | 验收标准 |
| --- | --- | --- | --- |
| P0 | 补项目 A 的事实 | 一页证据卡 | 输入、动作、产物、Bad Case、边界都有真实证据 |
| P0 | 完成 24 道逐字稿 | 文档加录音 | 无空白请补项；核心题可在 2 分钟内脱稿讲清 |
"""


class DeliveryQualityTests(unittest.TestCase):
    def run_validator(self, teacher, student=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resume = root / "测试同学简历.pdf"
            resume.write_bytes(b"%PDF-1.4\n%%EOF\n")
            teacher_path = root / "teacher.md"
            teacher_path.write_text(teacher, encoding="utf-8")
            args = [
                sys.executable, str(VALIDATOR), "--name", NAME,
                "--resume", str(resume), "--master", str(teacher_path),
                "--internal", str(teacher_path), "--track", "business",
            ]
            if student is not None:
                student_path = root / "student.md"
                student_path.write_text(student, encoding="utf-8")
                args.extend(["--student", str(student_path)])
            result = subprocess.run(args, text=True, capture_output=True)
            return result.returncode, json.loads(result.stdout)

    def test_accepts_complete_dual_end_delivery(self):
        code, result = self.run_validator(full_teacher(), full_student())
        self.assertEqual(0, code, result["errors"])

    def test_rejects_old_question_bank_without_teacher_cards(self):
        teacher = full_teacher().replace("## 模拟面试问题与带教指引", "## 分类问题与参考答案", 1)
        code, result = self.run_validator(teacher, full_student())
        self.assertEqual(1, code)
        self.assertTrue(any("模拟面试问题与带教指引" in error for error in result["errors"]))

    def test_rejects_student_card_without_fill_area(self):
        student = full_student().replace("**我的版本：**\n", "", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("我的版本" in error for error in result["errors"]))

    def test_accepts_concise_anchored_reference_expression(self):
        code, result = self.run_validator(full_teacher(), full_student())
        self.assertEqual(0, code, result["errors"])

    def test_rejects_student_card_without_expression_type(self):
        student = full_student().replace("**表达类型：** 迁移表达\n", "", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("表达类型" in error for error in result["errors"]))

    def test_rejects_invalid_expression_type(self):
        student = full_student().replace("**表达类型：** 迁移表达", "**表达类型：** 自由发挥", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("表达类型无效" in error for error in result["errors"]))

    def test_rejects_personal_experience_without_story_anchor(self):
        student = full_student().replace("**表达类型：** 迁移表达", "**表达类型：** 亲历表达", 1)
        student = student.replace(
            "**事实或场景依据：** S01｜项目 A 的数据清洗和方案比较；K01｜业务运营的口径、验证与人工复核方法。",
            "**事实或场景依据：** K01｜业务运营的口径、验证与人工复核方法。",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("亲历表达" in error and "S 锚点" in error for error in result["errors"]))

    def test_rejects_transfer_expression_without_knowledge_anchor(self):
        student = full_student().replace(
            "**事实或场景依据：** S01｜项目 A 的数据清洗和方案比较；K01｜业务运营的口径、验证与人工复核方法。",
            "**事实或场景依据：** S01｜项目 A 的数据清洗和方案比较。",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("迁移表达" in error and "K 锚点" in error for error in result["errors"]))

    def test_rejects_teacher_student_expression_type_mismatch(self):
        student = full_student().replace("**表达类型：** 迁移表达", "**表达类型：** 岗位知识", 1)
        student = student.replace(
            "**事实或场景依据：** S01｜项目 A 的数据清洗和方案比较；K01｜业务运营的口径、验证与人工复核方法。",
            "**事实或场景依据：** K01｜业务运营的口径、验证与人工复核方法。",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("表达类型不一致" in error for error in result["errors"]))

    def test_accepts_role_knowledge_with_knowledge_anchor_only(self):
        teacher = full_teacher().replace("**表达类型：** 迁移表达", "**表达类型：** 岗位知识", 1)
        student = full_student().replace("**表达类型：** 迁移表达", "**表达类型：** 岗位知识", 1)
        student = student.replace(
            "**事实或场景依据：** S01｜项目 A 的数据清洗和方案比较；K01｜业务运营的口径、验证与人工复核方法。",
            "**事实或场景依据：** K01｜业务运营的口径、验证与人工复核方法。",
            1,
        )
        old = student_card(1, CATEGORIES[0][1][0]).split("**参考表达：** ")[1].split("\n**我的版本")[0]
        student = student.replace(
            old,
            "业务运营通常先统一目标和指标口径，再小范围验证方案，最后结合结果指标、过程指标和护栏指标复盘。",
            1,
        )
        code, result = self.run_validator(teacher, student)
        self.assertEqual(0, code, result["errors"])

    def test_rejects_scenario_reasoning_without_hypothesis(self):
        teacher = full_teacher().replace("**表达类型：** 迁移表达", "**表达类型：** 场景推演", 1)
        student = full_student().replace("**表达类型：** 迁移表达", "**表达类型：** 场景推演", 1)
        student = student.replace(
            "**事实或场景依据：** S01｜项目 A 的数据清洗和方案比较；K01｜业务运营的口径、验证与人工复核方法。",
            "**事实或场景依据：** K01｜业务运营的口径、验证与人工复核方法。",
            1,
        )
        old = student_card(1, CATEGORIES[0][1][0]).split("**参考表达：** ")[1].split("\n**我的版本")[0]
        student = student.replace(
            old,
            "先统一目标和指标口径，再小范围验证方案，最后结合结果指标、过程指标和护栏指标复盘。",
            1,
        )
        code, result = self.run_validator(teacher, student)
        self.assertEqual(1, code)
        self.assertTrue(any("场景推演必须明确假设条件" in error for error in result["errors"]))

    def test_rejects_teacher_student_question_mismatch(self):
        student = full_student().replace("题目24｜信息不足时如何做判断", "题目24｜临时换成另一道题", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("题目标题或顺序不一致" in error for error in result["errors"]))

    def test_rejects_missing_pg_eight_coverage(self):
        student = full_student().replace("### 第二部分｜宝洁八大问", "### 第二部分｜通用行为题", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("宝洁八大问" in error for error in result["errors"]))

    def test_rejects_teacher_fields_leaking_to_student(self):
        student = full_student().replace(
            "**答题提示：** 先把请补项写实",
            "**继续追问：** 第一层追动作。  \n**答题提示：** 先把请补项写实",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("内部禁用标记" in error for error in result["errors"]))

    def test_rejects_project_architecture_after_interview_questions(self):
        visual = """## 核心项目架构｜先看图，再练题

```mermaid
flowchart LR
    A[业务输入] --> B[项目动作] --> C[结果校验]
```

"""
        student = full_student().replace("## 面试前任务", visual + "## 面试前任务", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("项目图解必须位于面试问题之前" in error for error in result["errors"]))

    def test_rejects_missing_merged_jd_section(self):
        student = full_student().replace("三档匹配 JD", "岗位匹配简表", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("三档匹配 JD" in error for error in result["errors"]))

    def test_rejects_merged_jd_card_without_job_daily(self):
        student = full_student().replace(
            "**岗位日常：** 把岗位的核心工作拆成数据口径、分析动作、协作和复盘。\n",
            "",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("90%" in error and "岗位日常" in error for error in result["errors"]))

    def test_rejects_legacy_split_tier_and_job_card_sections(self):
        student = full_student().replace(
            "## 项目地图",
            "## 主要岗位／JD卡\n### 岗位卡1｜业务运营\n重复岗位说明。\n\n## 项目地图",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("不得拆分" in error for error in result["errors"]))

    def test_rejects_teacher_student_tier_role_mismatch(self):
        student = full_student().replace(
            "90%｜主投｜业务运营",
            "90%｜主投｜产品运营",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("三档匹配 JD 的岗位或顺序不一致" in error for error in result["errors"]))

    def test_rejects_metric_primer_card_without_plain_language_field(self):
        student = full_student().replace(
            "**大白话：** 看到或进入某个环节的人里，最后有多少真正完成了目标动作。\n",
            "",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(any("指标1" in error and "大白话" in error for error in result["errors"]))

    def test_rejects_metric_mentioned_elsewhere_without_matching_primer_card(self):
        student = full_student().replace(
            "把岗位的核心工作拆成数据口径、分析动作、协作和复盘。",
            "把岗位的核心工作拆成数据口径、分析动作、协作和复盘，并持续关注退款率。",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(
            any("退款率" in error and "指标口径扫盲缺少对应卡" in error for error in result["errors"])
        )

    def test_rejects_custom_metric_marker_without_matching_primer_card(self):
        student = full_student().replace(
            "把岗位的核心工作拆成数据口径、分析动作、协作和复盘。",
            "把岗位的核心工作拆成数据口径、分析动作、协作和复盘，并关注【指标：首响健康度】。",
            1,
        )
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(1, code)
        self.assertTrue(
            any("首响健康度" in error and "指标口径扫盲缺少对应卡" in error for error in result["errors"])
        )

    def test_accepts_metric_mentioned_elsewhere_with_matching_primer_card(self):
        student = full_student().replace(
            "把岗位的核心工作拆成数据口径、分析动作、协作和复盘。",
            "把岗位的核心工作拆成数据口径、分析动作、协作和复盘，并持续关注退款率。",
            1,
        )
        refund_card = """### 指标4｜退款率
**大白话：** 已成交订单里，后来发生退款的订单占多少。
**怎么算／怎么看：** 退款订单数除以成交订单数，并统一订单归属周期。
**为什么重要：** 它能帮助判断成交质量和商品、履约或预期管理问题。
**容易误判：** 退款有延迟，只看当天成交会低估真实退款情况。
**候选人边界：** 没有订单明细和归因证据时，只说明口径与排查思路。

"""
        student = student.replace("## 岗位与行业知识", refund_card + "## 岗位与行业知识", 1)
        code, result = self.run_validator(full_teacher(), student)
        self.assertEqual(0, code, result["errors"])

    def test_rejects_project_architecture_after_teacher_interview_flow(self):
        visual = """## 补充项目图解

```mermaid
flowchart LR
    A[补充输入] --> B[补充校验]
```

"""
        teacher = full_teacher().replace(
            "## 模拟面试问题与带教指引",
            visual + "## 模拟面试问题与带教指引",
            1,
        )
        code, result = self.run_validator(teacher, full_student())
        self.assertEqual(1, code)
        self.assertTrue(any("模拟面试流程之前" in error for error in result["errors"]))

    def test_rejects_unresolved_visual_placeholder(self):
        teacher = full_teacher().replace(
            "看什么：先看业务输入",
            "[待插入图片]\n\n看什么：先看业务输入",
            1,
        )
        code, result = self.run_validator(teacher, full_student())
        self.assertEqual(1, code)
        self.assertTrue(any("未解决的图片占位" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
