# Loop Engineering Lab — 第一阶段开发计划

> 目标：通过手写 agent loop 与 DeepAgent 框架的对比实验，深度理解 loop engineering 各核心组件的实现原理。

---

## 项目背景

### 实验核心问题

**框架帮你做了什么，你自己又要做什么？**

DeepAgent（LangChain + LangGraph）封装了大量 agent loop 的复杂性。本项目通过手动实现同等功能的 loop，逼迫自己直面每一个细节，从而建立对 agent 开发的深度理解。

### 两条并行实现路径

| 路径 | 实现方式 | 目的 |
|------|----------|------|
| `handroll/` | 纯手写 loop，逐个实现组件 | 理解底层机制 |
| `deepagent/` | LangGraph + LangChain | 对比框架抽象的价值 |

### 六个 Loop 核心组件

```
Planner → Tool Use → Executor → Observation → Evaluator → （回到 Planner）
```

| 组件 | 职责 | 关键问题 |
|------|------|----------|
| **Planner** | 任务分解 / 规划策略 | CoT vs ReAct vs Plan-and-Execute 哪种更适合 Code Agent？ |
| **Tool Use** | 工具定义 / LLM 工具选择 | tool description 质量如何影响工具选择准确率？ |
| **Executor** | 执行工具调用 | 工具失败时如何让 LLM 正确理解并恢复？ |
| **Observation** | 格式化执行结果 | raw JSON vs 结构化自然语言，哪种 LLM 更容易理解？ |
| **Evaluator** | 判断 loop 是否终止 | self-critique / 硬上限 / 死循环检测如何组合？ |
| **Memory** | 管理 context 历史（Phase 2） | context 压缩策略如何权衡信息保留与 token 效率？ |

---

## 阶段目标

**第一阶段（本计划）：Code Agent**

选择 Code Agent 作为第一阶段目标，原因：
- 成功判断清晰（代码能跑通 = 成功）
- 工具集固定（bash_exec / file_read / file_write）
- 错误信息可解释（exit code / traceback）

**后续阶段预览：**
- Phase 2 — Research Agent：Memory 模块压力测试
- Phase 3 — Data Analysis Agent：Executor 沙箱与错误恢复

---

## 四周开发计划

### Week 1 — 环境搭建 + 最简 loop 跑通

**目标**：hello world 级别的 agent 能完整跑一轮

#### 任务清单

- [ ] **W1-1** 项目脚手架
  - 按照 `项目结构` 章节建立目录
  - 配置 `pyproject.toml` 和 `.env`
  - 交付物：可以 `pip install -e .` 的项目骨架

- [ ] **W1-2** 工具定义（`shared/tools/`）
  - 实现 `bash_exec`、`file_read`、`file_write`
  - 在 `schemas.py` 中定义 JSON Schema
  - 重点：tool description 写得越清晰，LLM 选错工具的概率越低
  - 交付物：三个工具均可独立调用并返回格式化结果

- [ ] **W1-3** 最简手写 loop（`handroll/loop/loop.py`）
  - Planner → Tool Use → Executor 串联
  - 暂不接入完整 Evaluator，硬编码 max_turns=10
  - 目标：能完成"写一个 Python 脚本并运行"这类简单任务
  - 交付物：`handroll/agent.py` 可成功运行

- [ ] **W1-4** DeepAgent 等价实现（`deepagent/`）
  - 用 LangGraph 实现功能等价的 Code Agent
  - 与 handroll 保持相同的任务输入 / RunLog 输出接口
  - 交付物：`deepagent/agent.py` 可成功运行同一任务

#### 学习重点

> 在实现过程中记录：`loop.py` 里你手动处理的每一个细节，
> 在 LangGraph 里是被哪个组件/哪行代码自动处理的？

---

### Week 2 — Evaluator + Observation 精细化

**目标**：loop 能自主判断任务完成 / 失败，而不依赖 max_turns 兜底

#### 任务清单

- [ ] **W2-1** Evaluator 完整实现（`handroll/evaluator/evaluator.py`）
  - 策略 1：self-critique prompt（LLM 自判断）
  - 策略 2：max_turns 硬上限（已有框架）
  - 策略 3：重复 action 检测（hash 对比）
  - 交付物：三种策略均实现并可独立开关

- [ ] **W2-2** Observation 格式化实验（`handroll/observation/formatter.py`）
  - 实现两种格式：`format_raw` vs `format_structured`
  - 在同一任务上分别测试两种格式，记录 LLM 理解差异
  - 交付物：对比记录文档 + 推荐格式决策

- [ ] **W2-3** 错误回注机制（`handroll/executor/executor.py`）
  - 工具执行失败时的 error message 设计
  - 验证：错误信息能引导 LLM 选择正确的重试策略
  - 交付物：至少覆盖三类错误（超时 / 参数错误 / 未知工具）

- [ ] **W2-4** 基准任务集（`tasks/benchmark/`）
  - 5 个固定测试用例（已在代码中定义）
  - 为每个用例手写验收函数（`success_criterion`）
  - 交付物：5 个用例均可通过 handroll + react 策略完成

#### 实验记录模板

每次运行记录以下字段（自动写入 `outputs/runs/`）：

```json
{
  "task_id": "task_01_simple_script",
  "agent_type": "handroll",
  "planner_strategy": "react",
  "success": true,
  "total_tokens": 3200,
  "loop_turns": 4,
  "stop_reason": "task_complete",
  "duration_s": 12.3
}
```

---

### Week 3 — Planner 策略对比实验

**目标**：用数据量化三种规划策略在 Code Agent 场景下的效果差异

#### 任务清单

- [ ] **W3-1** 三种 Planner 策略实现（`handroll/planners/`）
  - `cot.py`：一次性输出完整思维链和计划
  - `react.py`：每步 Thought → Action 循环
  - `plan_and_execute.py`：先生成子任务列表再逐一执行
  - 交付物：三个 planner 均可作为 `handroll/agent.py` 的策略参数传入

- [ ] **W3-2** 实验追踪系统（`shared/tracker/`）
  - `run_logger.py` 完整实现
  - `shared/evals/metrics.py` 汇总统计函数
  - 交付物：实验结果自动保存到 `outputs/runs/`，支持批量汇总

- [ ] **W3-3** 策略对比实验（`experiments/planner_ablation.py`）
  - 矩阵：3 种 Planner × 5 个任务 × 2 条路（handroll + deepagent）
  - 指标：成功率 / 平均 token / 平均轮次 / 平均耗时
  - 交付物：`outputs/planner_ablation_results.csv`

- [ ] **W3-4** 工具描述质量实验（`experiments/tool_desc_ablation.py`）
  - 对比详细 vs 简略 tool description 对工具选择准确率的影响
  - 交付物：`docs/tool_desc_ablation.md`

#### 预期发现（假设）

> 记录你的预期，实验后对照实际结果，差异往往是最大的学习点。

| 假设 | 验证方式 |
|------|----------|
| ReAct 在工具调用密集的任务上 token 消耗更高，但成功率也更高 | W3-3 实验数据 |
| 详细的 tool description 显著降低工具选错率 | W3-4 实验数据 |
| CoT 在复杂多步任务上容易规划过头导致失败 | task_04 成功率对比 |

---

### Week 4 — 对比分析 + 阶段总结

**目标**：沉淀可复用框架骨架，输出有洞察的阶段复盘

#### 任务清单

- [ ] **W4-1** 全量基准测试（`experiments/experiment_runner.py`）
  - 跑完整的 3 planner × 5 task × 2 agent 矩阵（30 次运行）
  - 生成最终对比报告
  - 交付物：`outputs/final_eval_report.md`

- [ ] **W4-2** 框架拆解分析（`docs/framework_diff.md`）
  - DeepAgent 帮你省掉了哪些问题？
  - 手写时踩了哪些坑？
  - 什么情况下选框架，什么情况下选手写？
  - 交付物：至少 1000 字的分析文档

- [ ] **W4-3** BaseAgent 骨架沉淀（`handroll/base_agent.py`）
  - 提炼通用 `BaseAgent` 抽象类
  - 验收标准：Phase 2 的 Research Agent 只需继承并插入 Memory 模块
  - 交付物：`base_agent.py` + 接口说明注释

- [ ] **W4-4** 阶段复盘（`docs/phase1_retro.md`）
  - 关键发现（有数据支撑）
  - 反直觉结论（和预期假设对比）
  - 对 Phase 2 的设计启示
  - 交付物：结构化复盘文档

---

## 验收指标

| 指标 | 标准 |
|------|------|
| 任务覆盖 | 5 个 benchmark 任务全部跑通（handroll + react）|
| 双路可对比 | handroll 和 deepagent 均产出 RunLog，指标可横向比较 |
| 代码可复用 | `BaseAgent` 可被 Phase 2 直接继承 |
| 文档产出 | `framework_diff.md` + `phase1_retro.md` + `tool_desc_ablation.md` |
| 数据产出 | `planner_ablation_results.csv` 包含完整实验矩阵 |

---

## 评估维度说明

### 成功率（task completion rate）
- 定义：`success_criterion(final_answer) == True` 的比例
- 收集：每次运行后自动写入 `RunLog.success`

### Token 消耗（total tokens）
- 定义：`input_tokens + output_tokens` 的总和
- 意义：token 效率是框架和策略选择的重要成本维度

### Loop 轮次（loop turns）
- 定义：从任务开始到终止的 LLM 调用次数
- 意义：轮次越少 = 规划越准确，不代表任务越简单

### 错误恢复能力（robustness）
- 定义：task_05（超时任务）的成功率
- 意义：衡量 Observation 设计 + Evaluator 对错误的处理质量

---

## 项目结构

```
loop-engineering-lab/
│
├── handroll/                    # 手写 loop 实现
│   ├── agent.py                 # Code Agent 入口
│   ├── base_agent.py            # 可复用基类（Week 4 沉淀）
│   ├── loop/
│   │   └── loop.py              # ★ 核心 loop 实现
│   ├── planners/
│   │   ├── cot.py               # CoT 策略
│   │   ├── react.py             # ReAct 策略
│   │   └── plan_and_execute.py  # Plan-and-Execute 策略
│   ├── executor/
│   │   └── executor.py          # 工具执行 + 错误处理
│   ├── evaluator/
│   │   └── evaluator.py         # 终止判断（self-critique / max_turns / loop_detect）
│   ├── observation/
│   │   └── formatter.py         # 工具结果格式化
│   └── memory/
│       └── context_manager.py   # Context 压缩（Phase 2 补充）
│
├── deepagent/                   # DeepAgent / LangGraph 实现（Week 1 TODO）
│   ├── agent.py                 # Code Agent 入口（与 handroll 接口一致）
│   ├── graph.py                 # LangGraph StateGraph 定义
│   └── nodes.py                 # 各节点实现
│
├── shared/                      # handroll 和 deepagent 共用
│   ├── tools/
│   │   ├── schemas.py           # ★ 工具 JSON Schema 定义
│   │   ├── bash_exec.py
│   │   ├── file_read.py
│   │   └── file_write.py
│   ├── evals/
│   │   └── metrics.py           # 汇总统计函数
│   ├── tracker/
│   │   └── run_logger.py        # RunLog 数据结构 + 保存
│   └── utils/
│       └── llm_client.py        # Anthropic API 封装
│
├── tasks/                       # 测试任务定义
│   ├── task_base.py             # Task 数据类
│   └── benchmark/
│       ├── task_01_simple_script.py
│       ├── task_02_bug_fix.py
│       ├── task_03_dependency_install.py
│       ├── task_04_multi_file.py
│       └── task_05_timeout.py
│
├── experiments/                 # 实验脚本
│   ├── experiment_runner.py     # 批量运行实验
│   ├── planner_ablation.py      # Planner 策略对比
│   ├── tool_desc_ablation.py    # 工具描述质量实验
│   └── observation_format_ablation.py  # Observation 格式实验
│
├── docs/                        # 分析文档
│   ├── framework_diff.md        # 框架对比分析（Week 4）
│   └── phase1_retro.md          # 阶段复盘（Week 4）
│
├── outputs/                     # 实验输出（gitignore）
│   └── runs/                    # 每次运行的 RunLog JSON
│
├── pyproject.toml
├── .env.example
├── README.md
└── PLAN.md                      # 本文件
```

---

## 快速开始

```bash
# 1. 安装依赖
pip install -e ".[dev]"

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY

# 3. 运行第一个测试（手写 loop + ReAct）
python -m handroll.agent

# 4. 批量跑实验
python -m experiments.experiment_runner --tasks all --planners react --agents handroll

# 5. 查看结果
cat outputs/runs/summary.json
```

---

## 学习笔记模板

每次实现一个组件后，在对应文件顶部的 docstring 补充：

```
【踩坑记录】
- 问题：...
- 原因：...
- 解决：...

【和 DeepAgent 的对比】
- DeepAgent 用 ___ 自动处理了这个问题
- 手写时需要注意 ___

【关键认知】
- ...
```

---

*Phase 1 完成后，进入 Phase 2 — Research Agent（Memory 模块压力测试）*
