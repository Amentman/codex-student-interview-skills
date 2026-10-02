# 环境基线

本仓库在以下本机环境完成打包与自动测试（2026-10-02，Asia/Shanghai）：

| 组件 | 验收版本 |
| --- | --- |
| Codex CLI | `0.155.0-alpha.9.2` |
| Python | `3.14.7` |
| Node.js | `22.23.2` |
| lark-cli | `1.0.72` |
| 操作系统 | macOS |

版本不是硬编码下限，但工具参数、飞书返回结构、插件清单和渲染结果可能随版本变化。迁移到其他环境时先运行仓库测试，再用脱敏样例完成一次不写入/测试空间演练。

## 必需能力

- Codex 能发现 `skills/` 中的 Skill，并支持 `.codex-plugin/plugin.json` 或根目录可移植 `plugin.json`。
- Python 只使用标准库运行仓库内校验器；Codex 自带的 Skill/插件验证脚本需要 PyYAML。本仓库验收命令使用 `uv run --with pyyaml python <validator> ...` 临时提供依赖，不要求污染系统 Python。
- 飞书交付需要已登录的 `lark-cli`、目标文档权限和当前版本的 Wiki/Docs/Drive 使用指南。
- Word、PDF和页面渲染能力由安装环境提供，本仓库不复制 OpenAI 自带系统 Skill。

## 路径与命令约定

- Skill 文档中的 `scripts/...` 都相对该 Skill 自己的目录解析；从仓库根目录执行时应使用 `python3 skills/<skill-name>/scripts/<script>.py ...`，不要依赖当前工作目录碰巧位于 Skill 内。
- `student-mock-interview-delivery/scripts/locate_student.py` 保留了制作者在 macOS 上的默认搜索目录，方便原环境继续使用。迁移到其他机器时必须显式传 `--root <交付根目录>`；可多次传入 `--root`，但不能用默认目录猜测学生身份。
- `prompts/` 是审计快照而不是直接覆盖模板，其中出现的本机绝对路径不具备可移植性。其他使用者应以根目录 `AGENTS.md` 为入口，并对用户级规则做人工合并。

## 提示词容量

原始全局提示词为 12,215 字节，项目提示词为 16,334 字节，合计 28,549 字节，低于 Codex 默认 32 KiB 项目指令合并上限，但如果目标项目还有更深层 `AGENTS.md`，仍可能触发截断。使用 `codex --ask-for-approval never "Summarize the current instructions."` 核对实际加载结果。
