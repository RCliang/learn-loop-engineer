# Loop Engineering Lab

> 通过手写 agent loop 与 DeepAgent 框架的对比实验，深度理解 loop engineering 各核心组件的实现原理。

## 这个项目是什么

一个**教程性质的实验项目**。目标不是做出最好的 Code Agent，而是搞清楚：

- Agent loop 的每个组件（Planner / Tool Use / Executor / Evaluator / Observation）**分别做了什么**
- DeepAgent（LangGraph）**帮你自动处理了哪些问题**
- 不同**规划策略**（CoT / ReAct / Plan-and-Execute）在实际任务中的**效果差异**

## 项目结构

```
handroll/    ← 手写 loop（核心学习对象）
deepagent/   ← LangGraph 等价实现（对比基准）
shared/      ← 工具、追踪、评估（两边共用）
tasks/       ← 5 个 benchmark 任务
experiments/ ← 对比实验脚本
docs/        ← 分析文档
```

详细结构和四周开发计划见 → **[PLAN.md](./PLAN.md)**

## 快速开始

```bash
pip install -e ".[dev]"
cp .env.example .env   # 填入 ANTHROPIC_API_KEY

# 跑第一个 agent（手写 loop + ReAct）
python -m handroll.agent
```

## 核心文件阅读顺序

1. `shared/tools/schemas.py` — 工具定义
2. `handroll/loop/loop.py` — ★ 核心 loop 实现
3. `handroll/evaluator/evaluator.py` — 终止判断
4. `handroll/observation/formatter.py` — 结果格式化
5. `handroll/planners/react.py` — ReAct 策略
