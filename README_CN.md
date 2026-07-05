# Re-search：面向研究与实现工作的 Codex Skill Pack

[![Verify](https://github.com/Pineapplee01/Re-search/actions/workflows/verify.yml/badge.svg)](https://github.com/Pineapplee01/Re-search/actions/workflows/verify.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

[English README](README.md) | [贡献说明](CONTRIBUTING_CN.md) | [Agent 指南](AGENT_GUIDE.md) | [发布清单](RELEASE_CHECKLIST.md)

公开仓库地址：[`Pineapplee01/Re-search`](https://github.com/Pineapplee01/Re-search)

Re-search 是一个面向 Codex 的 skill pack 与 research/implementation methodology 仓库。
它主要服务两类重复任务：

- 研究问题与文献分析
- 基于强外部方案的 skill / workflow 设计与优化

这个仓库当前坚持 `skill-pack first`。
公开边界是 `skills/` 下的各个 skill 目录，而不是一个 repo-level Python package，也不是一个庞大的自动化框架。

## 方法论优先

Re-search 在解决问题前，先遵循一条固定纪律：

1. define problem boundary
2. inspect strong existing solutions
3. judge migration path
4. mark boundary risks
5. learn before implementing

这条方法论同时适用于 research 任务和 skill-development 任务。
目标是减少边界漂移、能力夸大和高噪声的即兴执行。

## 默认使用路径

仓库的默认使用路径为：

1. `Re-search`
2. `literature-gap-workflow`
3. `research-map`
4. `research-hunt`
5. `research-compare`
6. `research-report`

其中 `Re-search` 是 preflight 入口。
它负责识别任务类型、显式化边界、记录可迁移的外部模式，并产出可验证的 handoff artifact。

## 当前 Skills

| Skill | 类型 | 作用 |
| --- | --- | --- |
| `Re-search` | scripted | 前置 meta-skill 与 preflight contract |
| `literature-gap-workflow` | scripted | 分阶段 workflow 入口 |
| `research-map` | prompt-only | 问题映射与 baseline snapshot |
| `research-hunt` | scripted | 论文筛选、校验、beast merge/jury gate |
| `research-compare` | prompt-only | 与 baseline 的差异分析 |
| `research-report` | prompt-only | 固定结构最终汇报 |

## Script-Backed Surfaces

当前确定性脚本面包括：

- `skills/Re-search/scripts/preflight_run.py`
- `skills/literature-gap-workflow/scripts/literature_run.py`
- `skills/research-hunt/scripts/validate_papers_json.py`
- `skills/research-hunt/scripts/beast_hunt.py`

这些脚本负责 artifact 初始化、校验、状态 gate、merge 与 jury 控制。
而 prompt-only 阶段保持轻量，主要消费结构化 artifact，而不是依赖聊天记忆。

## Artifact 模型

Re-search 通过显式 artifact 同步状态，而不是只靠线程记忆。

- preflight artifact 写入 `research-wiki/preflight_runs/<run-id>/`
- literature workflow artifact 写入 `research-wiki/literature_runs/<run-id>/`

关键产物包括：

- `preflight.json`
- `preflight.md`
- `problem-map.md`
- `baseline-snapshot.md`
- `papers.json`
- `difference-matrix.md`
- `report.md`
- `state.json`

## 安装

PowerShell：

```powershell
.\scripts\install.ps1
```

该脚本会把公开 skill 目录链接到 `$env:USERPROFILE\.agents\skills`。

## 验证

PowerShell：

```powershell
.\scripts\verify.ps1
```

该入口会统一运行当前所有 script-backed skill 的测试。

## 仓库结构

```text
skills/
  <skill-name>/
    SKILL.md
    references/
    scripts/
scripts/
  install.ps1
  verify.ps1
tests/
  README.md
```

## 这个仓库不是什么

Re-search 当前不应被表述为：

- 完整自动研究平台
- 通用 Python framework
- 自带 sleep/replay/log harvesting 的系统

本仓库在公开展示效果上会向 ARIS 一类仓库对齐，但能力边界只覆盖当前真实已经实现的部分。

## 备注

- literature workflow 的公开控制字段是 `effort: lite | balanced | max | beast`
- 旧的 `mode` 输入不再兼容
- 只有当多个 scripted skills 持续共享大量运行时逻辑时，才考虑抽 repo-level runtime
