# Loop Engineering Lab

> 通过手写 agent loop 与 deepagents 框架的对比实验，深度理解 loop engineering 各核心组件的实现原理。

## 快速开始

```bash
pip install -e ".[dev]"
cp .env.example .env   # 编辑 .env 填入 LLM 配置

# 跑两路对比
python -m cli run --agent both --task task_01_simple_script
```

## 核心文件阅读顺序

1. `shared/tools/schemas.py` — 工具定义
2. `handroll/loop/loop.py` — ★ 核心 loop 实现
3. `handroll/executor/executor.py` — 工具分发
4. `handroll/evaluator/evaluator.py` — 终止判断
5. `handroll/observation/formatter.py` — 结果格式化
6. `deepagent/agent.py` — 框架等价实现（极薄）

详细设计见 `docs/superpowers/specs/2026-07-07-week1-minimal-loop-design.md`。
