# 参与 Re-search

欢迎为 Re-search 贡献内容。

这个仓库是一个 `skill-pack first` 的 skills 与方法论集合，而不是 repo-level Python framework。
除非有单独的重构决策，否则所有修改都应保持这一边界。

## 仓库契约

每个公开 skill 位于：

```text
skills/<skill-name>/
```

一个 skill 目录中只应包含：

- `SKILL.md`
- 可选 `references/`
- 可选 `scripts/`

不要把运行产物、缓存或生成式 artifact 写回 skill 目录。

## Skill 形态

Re-search 当前使用两类 execution shape：

- `prompt-only`
- `scripted`

`prompt-only` 负责协议与 artifact 约定。
`scripted` 负责 deterministic validator、gate 或 executor。

## 测试策略

script-backed 行为采用 colocated tests：

- `skills/*/scripts/test_*.py`

仓库级统一验证入口：

```powershell
.\scripts\verify.ps1
```

如果修改了 script-backed surface，应先运行相关局部测试，再运行 `scripts/verify.ps1`。

## 修改原则

- 保持仓库 `skill-pack first`
- 优先做小而可逆的变更
- 优先复用现有模式，再考虑新抽象
- 不要在没有单独重构决策时引入 repo-level shared runtime
- 保持 `SKILL.md` 精简，把细节协议移入 `references/`
- 把 deterministic logic 放进 `scripts/`

## 文档一致性要求

对外发布相关改动应保持这些文档一致：

- `README.md`
- `README_CN.md`
- `CONTRIBUTING.md`
- `CONTRIBUTING_CN.md`
- `AGENT_GUIDE.md`

不要在文档里声明仓库并未真实实现的能力。
