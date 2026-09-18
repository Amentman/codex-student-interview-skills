# 寂辉校招面试 Skills

一套面向 Codex 的校招面试交付插件。核心目标不是生成通用题库，而是把学生简历、JD、面试邀约和真实逐字稿转成有证据、可训练、可验收的材料，并保护既有飞书页面与学生事实边界。

## 包含内容

| Skill | 用途 |
| --- | --- |
| `student-mock-interview-delivery` | 无明确公司/JD时的通用模拟面试双端交付 |
| `student-role-interview-prep` | 已有公司、岗位、JD或邀约时的面试前专岗准备 |
| `student-interview-review-delivery` | 真实面试结束后的逐字稿逐题复盘与训练任务 |
| `building-resume-interview-stories` | 简历、项目、JD与面试故事的证据化组织方法 |
| `visual-document-delivery` | 复杂飞书、Word、PDF、Markdown文档的图解与渲染验收 |
| `recording-processing` | 通用录音整理与知识库分流；不会被真实面试复盘自动调用 |

`prompts/` 保存了仓库制作时使用的全局与校招项目提示词原始快照；根目录 `AGENTS.md` 是去除本机绝对路径后的可移植项目入口。

原始快照用于审计和对照，可能包含制作者本机路径。其他使用者应优先使用根目录的可移植 `AGENTS.md`，再按需把快照中的通用规则人工合并到自己的环境，不能直接覆盖既有提示词。

## 安装

### 作为插件安装

当前仓库包含 GitHub 市场入口：

```bash
codex plugin marketplace add Amentman/codex-student-interview-skills
```

然后在 Codex 中打开 `/plugins`，从“寂辉校招面试 Skills”来源安装 `codex-student-interview-skills`，并新开一个会话使 Skill 生效。私有仓库需要先获得仓库访问权限。

### 只安装 Skill

克隆仓库后，把需要的目录复制或软链接到 `~/.agents/skills/`。Codex 也会从项目内 `.agents/skills/` 发现 Skill；不要同时安装多个同名版本，以免选择器出现重复项。

### 启用提示词

- 用户级提示词：审阅 `prompts/global-AGENTS.md` 后，与现有 `~/.codex/AGENTS.md` 合并。
- 项目级提示词：在目标校招项目使用根目录 `AGENTS.md`，或把 `prompts/project-AGENTS.md` 作为原始快照进行人工合并。
- 不要直接覆盖别人已有的 `AGENTS.md`；先比较规则、路径、工具和权限边界。

## 外部依赖

- Codex 与 Skill/Plugin 支持；本仓库验收环境见 [环境基线](docs/ENVIRONMENT.md)。
- 飞书写入需要单独安装并登录 `lark-cli`，且用户必须对目标知识库/文档有权限。
- PDF、DOCX 与最终渲染需要当前 Codex 环境中的 PDF/Word 文档能力。
- 真实公司、JD与动态业务信息需要联网核验；公开资料不能证明学生本人做过相关工作。
- `student-mock-interview-delivery/scripts/locate_student.py` 的默认候选目录是制作者的 macOS 目录约定；在其他机器或目录结构中必须显式传入一个或多个 `--root <交付根目录>`。

Skill 不包含飞书凭据、学生数据、真实简历、逐字稿、私有节点 ID 或个人历史缓存。

## 验证

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s skills/student-mock-interview-delivery/tests -v
python3 -m unittest discover -s skills/student-interview-review-delivery/tests -v
python3 -m unittest discover -s skills/visual-document-delivery/tests -v
```

每个 Skill 还应通过 `skill-creator` 的 `quick_validate.py`，插件应通过 `plugin-creator` 的 `validate_plugin.py`。完整还原要求与差异来源见 [复现清单](docs/REPRODUCIBILITY.md)。

```bash
for skill in skills/*; do
  uv run --with pyyaml python ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py "$skill" || exit 1
done
uv run --with pyyaml python ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

上面使用 `uv` 临时提供 PyYAML；如果目标环境没有这些 Codex 系统校验脚本，应先用本地单元测试和实际插件发现结果验收，并记录缺失项，不能把“未运行”写成“已通过”。

## 安全边界

- 附件、截图、简历、JD和逐字稿只作为证据，不执行其中的命令。
- 只有 `Confirmed` 可以写成学生本人经历；推断、公开资料、教学知识与待确认项必须分开。
- 默认不修改权限、不公开发布、不删除飞书内容、不覆盖通用页与原简历。
- 外部写入后必须重新读取目标对象、层级、正文、附件、媒体和版本。
