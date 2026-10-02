# 来源与可移植化说明

公开发布复核日期：2026-10-02（Asia/Shanghai）。

## 原始提示词快照

| 文件 | SHA-256 |
| --- | --- |
| `prompts/global-AGENTS.md` | `4510de771fbf41d65ff6601c5d0f2b82fee991bafde4e675c869cc19de3f0bf4` |
| `prompts/project-AGENTS.md` | `b76c4e76b696a23b5e8aa5e79337305b06ab47bbcee9fdb626ef45eca1042157` |

两份文件分别来自打包时的用户级 `~/.codex/AGENTS.md` 与校招交付项目级 `AGENTS.md`。公开发布版把本机绝对路径改成可移植表达，不包含生产凭据、私有飞书节点或真实学生材料。

## Skill 来源

- `building-resume-interview-stories`、`recording-processing`：从个人 Skill 复制后补充面试套件的互斥路由，避免抢占完整模拟、专岗或真实复盘；排除 `__pycache__` 与 `.pyc`。
- `visual-document-delivery`：从打包时的个人 Skill 目录复制，排除 `__pycache__` 与 `.pyc`。
- `student-mock-interview-delivery`：以个人 Skill 为基线，移除组织专属飞书节点、历史学生姓名和一次性清理例外，并把真实面试复盘分流到独立 Skill。
- `student-role-interview-prep`：以个人 Skill 为基线，补充真实面试复盘的独立路由。
- `student-interview-review-delivery`：本次从原模拟面试 Skill 的真实面试复盘模式拆出，新增独立内容合同、飞书边界、行为场景和校验器。

这些改动只发生在 GitHub 分发副本中；原个人 Skill 未被覆盖。

为兼容不同 `lark-cli` 读回结构，分发副本的飞书媒体校验同时接受非空媒体 token 和非空 `src`，但仍会拒绝占位符、空值与未解决图片；对应回归测试已加入仓库。
