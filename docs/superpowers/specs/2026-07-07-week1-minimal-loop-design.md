# Week 1 — 最小可跑通 Loop 设计 Spec

> 把 `docs/PLAN.md` 第一周的目标（handroll + deepagent 两路跑通同一任务）变成一份可执行设计。
>
> 这是 Loop Engineering Lab 教学项目的第一阶段。目标不是做出最好的 Code Agent，而是通过双路对比深度理解 agent loop 各组件。

---

## 1. 目标与非目标

### 1.1 Week 1 目标

- **handroll 路与 deepagent 路** 都能独立完成 `task_01_simple_script`（在 `sandbox/` 下创建并运行 `hello.py`，输出 `hello world`）。
- 两路产出 **格式一致** 的 `RunLog` JSON，落在 `outputs/runs/`。
- 一个 CLI 入口能并排展示两路摘要。
- 每个核心文件顶部有 docstring，记录"和 DeepAgent 的对比"。

### 1.2 不在 Week 1 范围内

| 项目 | 推迟到 |
|---|---|
| CoT / Plan-and-Execute planner | Week 3 |
| Observation raw vs structured A/B | Week 2 |
| Memory / context 压缩 | Phase 2 |
| 多任务 benchmark（task_02 ~ task_05） | Week 2 |
| 实验矩阵 / 批量跑 | Week 3 |
| `framework_diff.md` / `phase1_retro.md` | Week 4 |
| `BaseAgent` 抽象沉淀 | Week 4 |

---

## 2. 关键决策（已确认）

| 决策点 | 选择 | 理由 |
|---|---|---|
| 范围 | Week 1 最小可跑通 | 优先看到完整对比，再迭代 |
| 现有代码 | 重写（保留作参考） | 教学目的，重写过程本身就是学习 |
| LLM provider | OpenAI 兼容 API，两路同一个模型 | 支持自部署 / 第三方供应商；保证对比公平 |
| DeepAgent 主体 | LangChain `deepagents` 库（默认配置） | 用户指定 |
| 沙箱策略 | 工作目录限制（`sandbox/` 前缀） | 简单、零依赖，足以防误操作 |
| Week 1 任务 | `task_01_simple_script` | PLAN.md 已定义；简单可验证 |
| 架构 | Mirror PLAN.md 结构 | 结构本身是教学点；后续无须重构 |
| `deepagents` 工具 | 用我们自己的 3 个工具（`bash_exec` / `file_read` / `file_write`） | 公平对比 |
| `write_todos` | 默认启用，作为 tool_call 记录 | 让不对称显式化 |
| Tool 返回类型 | `dict`（非 dataclass） | 便于序列化进 RunLog |
| 错误处理 | 工具永不抛异常，返回 `{"ok": False, ...}` 错误 payload | Loop 无须 try/except 嵌套 |

---

## 3. 架构概览

```
loop-engineer/
├── handroll/                    # 手写 loop
│   ├── __init__.py
│   ├── agent.py                 # 入口：组装 task + loop + RunLog
│   ├── loop/
│   │   └── loop.py              # ★ 核心 loop：6 步串联
│   ├── executor/
│   │   └── executor.py          # 工具分发 + 错误捕获
│   ├── evaluator/
│   │   └── evaluator.py         # max_turns + loop_detect + self_critique
│   ├── observation/
│   │   └── formatter.py         # 工具结果格式化
│   ├── planners/                # Week 3 占位（空 __init__.py）
│   └── memory/                  # Phase 2 占位（空 __init__.py）
├── deepagent/
│   ├── __init__.py
│   └── agent.py                 # create_deep_agent 极薄包装
├── shared/
│   ├── tools/
│   │   ├── schemas.py           # 3 个工具 schema + LangChain @tool 派生
│   │   ├── bash_exec.py
│   │   ├── file_read.py
│   │   └── file_write.py
│   ├── utils/
│   │   ├── llm_client.py        # OpenAI 兼容 chat()
│   │   ├── config.py            # 加载 .env
│   │   └── sandbox.py           # 路径限制器
│   └── tracker/
│       └── run_logger.py        # RunLog 数据类
├── tasks/
│   ├── __init__.py
│   ├── task_base.py             # Task dataclass
│   └── benchmark/
│       ├── __init__.py
│       └── task_01_simple_script.py
├── sandbox/                     # 工具实际读写此处（gitignore；保留 .gitkeep）
├── outputs/runs/                # RunLog JSON 输出（gitignore）
├── cli.py                       # 统一入口
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

**核心设计原则：**

1. `shared/` 是地基 —— 两路都站在它上面。工具、LLM 客户端、沙箱、RunLog 全在这里。任何 `shared/` 接口变化都会同时影响两路，强迫你看到"框架帮你做了什么"。
2. `handroll/` 每个 subdir 是一个 loop 组件 —— 这就是教学点。打开 `executor/executor.py` 看到的就是 Executor 组件的全部。
3. `deepagent/` 极薄 —— 只有一个 `agent.py` 调用 `create_deep_agent()`。这种"薄"本身就是教训。
4. `sandbox/` 和 `outputs/` 是物理隔离工作区 —— agent 的所有文件操作被限制在 `sandbox/`，运行日志写到 `outputs/runs/`。
5. `cli.py` 是唯一入口 —— 保证两路用完全相同的 task 输入与 RunLog 输出格式。

---

## 4. `shared/` 详细设计

### 4.1 `shared/tools/`

**`schemas.py`** —— 每个工具一个 dict（含 `name`、`description`、`input_schema`），同时为 deepagent 路派生 LangChain `@tool` 形式。

```python
# 双导出
ALL_TOOLS = [BASH_EXEC_SCHEMA, FILE_READ_SCHEMA, FILE_WRITE_SCHEMA]
ALL_TOOLS_AS_CALLABLES = [bash_exec_lc, file_read_lc, file_write_lc]
```

两个列表共享相同的 `name` / `description` / `input_schema` —— 通过一次编写、二次派生保证一致（`to_langchain_tool(schema, fn)` helper 接收一个 schema dict 和一个 Python 函数，返回一个 LangChain `@tool` 包装的 callable）。这确保 **LLM 在两条路径看到完全相同的工具描述**。

> 双形式的必要性：handroll 直接构造 `chat()` 请求，需要 OpenAI tools API 格式（JSON dict）；deepagents 通过 LangChain 调度，需要 Python callable。共享底层 `run(**kwargs) -> dict` 函数，只是两套适配外壳。

**`bash_exec.py` / `file_read.py` / `file_write.py`** —— 每个文件暴露 `def run(**kwargs) -> dict`。返回结构化 dict（绝不抛异常，错误也是 payload）。

```python
# bash_exec.run 成功返回
{"ok": True, "stdout": "...", "stderr": "...", "exit_code": 0, "duration_s": 1.2}
# 失败返回
{"ok": False, "error_type": "TimeoutExpired", "message": "超时 30s",
 "stdout": "...", "exit_code": -1}
```

工具 schema 示例（保持简洁但够清晰）：

```python
BASH_EXEC_SCHEMA = {
    "name": "bash_exec",
    "description": (
        "在沙箱 shell（限制在 sandbox/ 工作目录）中执行一条 bash 命令，"
        "返回 stdout、stderr 和 exit_code。超时默认 30 秒。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "要执行的 bash 命令"},
            "timeout": {"type": "integer", "description": "超时秒数，默认 30", "default": 30},
        },
        "required": ["command"],
    },
}
```

### 4.2 `shared/utils/sandbox.py`

```python
SANDBOX_DIR = Path(__file__).resolve().parents[2] / "sandbox"

def resolve_in_sandbox(rel_or_abs_path: str) -> Path:
    """把用户提供的路径解析为 sandbox/ 下的绝对路径。
    解析后若超出 sandbox 目录，抛 PermissionError。"""

def reset_sandbox() -> None:
    """清空 sandbox/（保留 .gitkeep）。每次 run 前由 CLI 调用。"""
```

`file_read.run` / `file_write.run` 调用 `resolve_in_sandbox()`。`bash_exec.run` 用 `cwd=sandbox/` 启动子进程。

**已知限制（写入 docstring）：** `bash_exec` 无法阻止 LLM 通过 `cd /` 或绝对路径访问沙箱外的文件。Week 1 仅依赖 `cwd` 设置 + 路径前缀检查作为主要防线。更严格的隔离（容器）在 Phase 3 讨论。

### 4.3 `shared/utils/config.py`

```python
@dataclass
class LLMConfig:
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str

def load_env() -> LLMConfig:
    """从 .env 读取 LLM_BASE_URL / LLM_API_KEY / LLM_MODEL。"""
```

`.env.example`：

```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

### 4.4 `shared/utils/llm_client.py`

```python
from openai import OpenAI
from shared.utils.config import load_env

def chat(
    messages: list[dict],
    system: str,
    tools: list[dict],
    max_tokens: int = 1024,
) -> tuple[object, int, int]:
    """OpenAI 兼容 chat 接口。返回 (response, input_tokens, output_tokens)。"""
```

handroll 路直接用此客户端；deepagent 路不直接用，而是构建一个配置了相同 `base_url`、`api_key`、`model` 的 `langchain_openai.ChatOpenAI` 实例。两路底层打同一个模型。

### 4.5 `shared/tracker/run_logger.py`

```python
@dataclass
class RunLog:
    task_id: str
    agent_type: str                         # "handroll" | "deepagent"
    planner_strategy: str = "react"         # Week 1 硬编码
    success: bool = False
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    loop_turns: int = 0
    stop_reason: str = ""                   # task_complete | max_turns | loop_detected | error
    duration_s: float = 0.0
    final_answer: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def log_tool_call(self, name, input, result): ...
    def log_event(self, turn, kind, **fields): ...
    def finish(self, success, stop_reason, final_answer): ...
    def save(self, dir="outputs/runs") -> Path:
        """写入 {timestamp}_{agent}_{task}.json"""
```

RunLog JSON 示例：

```json
{
  "task_id": "task_01_simple_script",
  "agent_type": "handroll",
  "planner_strategy": "react",
  "success": true,
  "total_input_tokens": 1820,
  "total_output_tokens": 540,
  "loop_turns": 4,
  "stop_reason": "task_complete",
  "duration_s": 8.23,
  "final_answer": "...",
  "tool_calls": [
    {"name": "file_write", "input": {"path": "hello.py", "content": "..."},
     "ok": true, "duration_s": 0.01},
    {"name": "bash_exec", "input": {"command": "python hello.py"},
     "ok": true, "duration_s": 0.32, "exit_code": 0}
  ],
  "events": [
    {"turn": 1, "kind": "llm_call", "input_tokens": 480, "output_tokens": 110},
    {"turn": 1, "kind": "tool_call", "name": "file_write"},
    {"turn": 2, "kind": "llm_call", "input_tokens": 540, "output_tokens": 130},
    {"turn": 2, "kind": "tool_call", "name": "bash_exec"}
  ],
  "notes": []
}
```

`notes` 字段记录口径差异 / 已知问题，例如：
- handroll: `["self_critique 在 Week 1 实质禁用"]`
- deepagent: `["loop_turns 是 LangGraph 节点更新次数，非严格 LLM 调用次数", "write_todos 调用计入了 tool_calls"]`

---

## 5. `handroll/` 详细设计

### 5.1 `handroll/loop/loop.py` — 核心 6 步 loop

```python
def run_loop(task: Task, system_prompt: str, run_log: RunLog, max_turns: int = 15) -> RunLog:
    evaluator = Evaluator(max_turns=max_turns)
    messages = [{"role": "user", "content": task.prompt}]

    for turn in range(max_turns):
        run_log.loop_turns = turn + 1

        # ① 调 LLM（Tool Use 隐式发生）
        resp, in_tok, out_tok = chat(messages, system=system_prompt, tools=ALL_TOOLS)
        run_log.total_input_tokens += in_tok
        run_log.total_output_tokens += out_tok
        run_log.log_event(turn + 1, "llm_call", input_tokens=in_tok, output_tokens=out_tok)

        # ② 解析：text blocks + tool_use blocks
        text_parts, tool_use_blocks = parse_response(resp)

        # ③ 无 tool_use → 任务完成
        if not tool_use_blocks:
            run_log.finish(success=True, stop_reason="task_complete",
                           final_answer="\n".join(text_parts))
            return run_log

        # ④ 把 assistant 消息追加到 messages（含 tool_use blocks）
        messages.append({"role": "assistant", "content": resp.content})

        # ⑤ 执行所有工具、格式化观察、作为 user 消息追加
        tool_results = []
        last_action = None
        for block in tool_use_blocks:
            obs = execute_tool(block.name, block.input, run_log)
            formatted = format_observation(block.name, block.input, obs)
            tool_results.append({"type": "tool_result",
                                 "tool_use_id": block.id, "content": formatted})
            last_action = {"name": block.name, "input": block.input}
        messages.append({"role": "user", "content": tool_results})

        # ⑥ Evaluator 判断是否继续
        should_stop, reason = evaluator.should_stop(
            task.prompt, "\n".join(text_parts), turn + 1, last_action)
        if should_stop:
            run_log.finish(success=(reason == "task_complete"),
                           stop_reason=reason,
                           final_answer="\n".join(text_parts))
            return run_log

    run_log.finish(success=False, stop_reason="max_turns", final_answer="")
    return run_log
```

**与原始 `loop.py` 的差异：**
- 接受 `Task`（而非裸字符串），便于追踪 `task_id`
- 返回 `RunLog`（而非裸字符串），日志贯穿全流程
- 在每个 tool_call / llm_call 周围记录细粒度 events

**`parse_response(resp)` helper（loop.py 内联或独立模块）：** 把 OpenAI response 拆成 `(text_parts: list[str], tool_calls: list[dict])`。OpenAI tools API 返回的 `resp.choices[0].message.tool_calls` 是 list of `{id, type, function: {name, arguments}}`；`arguments` 是 JSON 字符串需 `json.loads`。文本部分来自 `resp.choices[0].message.content`。

### 5.2 `handroll/executor/executor.py`

```python
from shared.tools import bash_exec, file_read, file_write

TOOL_REGISTRY = {
    "bash_exec": bash_exec.run,
    "file_read": file_read.run,
    "file_write": file_write.run,
}

def execute_tool(name: str, input: dict, run_log: RunLog) -> dict:
    if name not in TOOL_REGISTRY:
        err = {"ok": False, "error_type": "UnknownTool",
               "message": f"未知工具 {name}"}
        run_log.log_tool_call(name, input, err)
        return err
    try:
        result = TOOL_REGISTRY[name](**input)
        run_log.log_tool_call(name, input, result)
        return result
    except Exception as e:
        # 防御：工具不应抛异常，但万一
        err = {"ok": False, "error_type": type(e).__name__, "message": str(e)}
        run_log.log_tool_call(name, input, err)
        return err
```

### 5.3 `handroll/evaluator/evaluator.py` — 三策略

| 策略 | 检查 | 成本 |
|---|---|---|
| `max_turns` | `current_turn >= max_turns` | 免费 |
| `loop_detect` | 同一 action hash 出现 ≥3 次 | 免费 |
| `self_critique` | 仅当无 tool_use 且我们即将停止时（实际 Week 1 几乎不触发，因为无 tool_use 时已在 ③ 停止） | 1 次额外 LLM 调用 |

**Week 1 简化：** `self_critique` 实际上几乎被禁用。Week 2 会真正探索 LLM 自评。

### 5.4 `handroll/observation/formatter.py`

```python
def format_observation(tool_name: str, tool_input: dict, result: dict,
                       mode: str = "structured") -> str:
    """mode='raw' → json.dumps(result, indent=2, ensure_ascii=False)
       mode='structured' → 每工具自定义模板"""
```

Week 1 默认 `structured`。`raw` 路径存在但 Week 2 才做 A/B。

每工具的 structured 模板：

| 工具 | 模板 |
|---|---|
| `bash_exec`（成功） | `退出代码 {exit_code}\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}` |
| `bash_exec`（失败） | `[错误] 命令执行失败：{message}（类型：{error_type}）` |
| `file_read`（成功） | `已读取 {path}（{n} 行）：\n\n{content}` |
| `file_read`（失败） | `[错误] 读取失败：{message}（类型：{error_type}）` |
| `file_write`（成功） | `已写入 {n} 字节到 {path}` |
| `file_write`（失败） | `[错误] 写入失败：{message}（类型：{error_type}）` |

### 5.5 `handroll/agent.py`

```python
REACT_SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略（ReAct）：
1. 思考任务下一步该做什么
2. 如有必要，调用一个或多个工具
3. 观察工具结果
4. 重复直至任务完成，然后给出最终答案

所有文件操作被限制在当前工作目录（sandbox/）。"""

def run(task: Task) -> RunLog:
    run_log = RunLog(task_id=task.id, agent_type="handroll", planner_strategy="react")
    start = time.time()
    run_log = run_loop(task, REACT_SYSTEM_PROMPT, run_log, max_turns=15)
    run_log.duration_s = time.time() - start
    run_log.save()
    return run_log
```

---

## 6. `deepagent/` 详细设计

### 6.1 `deepagent/agent.py`

```python
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

from shared.tools.schemas import ALL_TOOLS_AS_CALLABLES
from shared.utils.config import load_env
from shared.tracker.run_logger import RunLog
from tasks.task_base import Task

DEEP_AGENT_SYSTEM_PROMPT = """你是一个 Code Agent。...（与 handroll 一致的内容）"""

def build_agent():
    cfg = load_env()
    model = ChatOpenAI(
        model=cfg.LLM_MODEL,
        api_key=cfg.LLM_API_KEY,
        base_url=cfg.LLM_BASE_URL,
        temperature=0,
    )
    return create_deep_agent(
        model=model,
        tools=ALL_TOOLS_AS_CALLABLES,
        system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
    )

def run(task: Task) -> RunLog:
    run_log = RunLog(task_id=task.id, agent_type="deepagent", planner_strategy="react")
    run_log.notes.append("loop_turns 是 LangGraph 节点更新次数，非严格 LLM 调用次数")
    run_log.notes.append("write_todos 调用计入了 tool_calls")
    agent = build_agent()
    start = time.time()

    tool_calls = []
    turn_count = 0
    final_text = ""
    in_tok_total = 0
    out_tok_total = 0

    for event in agent.stream(
        {"messages": [{"role": "user", "content": task.prompt}]},
        stream_mode="updates",
    ):
        turn_count += 1
        # 从 event 中提取 AIMessage、tool_calls、usage 等
        in_tok_total, out_tok_total, tool_calls, final_text = _ingest_event(
            event, run_log, in_tok_total, out_tok_total, tool_calls, final_text)

    run_log.loop_turns = turn_count
    run_log.total_input_tokens = in_tok_total
    run_log.total_output_tokens = out_tok_total
    run_log.duration_s = time.time() - start
    if in_tok_total == 0:
        run_log.notes.append("token_usage_unavailable（模型未返回 usage）")
    run_log.finish(success=task.success_criterion(final_text),
                   stop_reason="task_complete",
                   final_answer=final_text)
    run_log.save()
    return run_log
```

### 6.2 事件 ingest 细则

`_ingest_event(event, run_log, in_tok_total, out_tok_total, tool_calls, final_text)` 是一个**纯函数**，从 LangGraph 的 stream 事件中提取信息并返回更新后的累加值。

**输入**：一个 `stream_mode="updates"` 事件。该事件结构为 `{node_name: {"messages": [AIMessage | ToolMessage, ...]}}` 字典。

**提取逻辑**：

| 事件中的字段 | 提取后做什么 |
|---|---|
| `AIMessage.tool_calls` (list of `{name, args, id}`) | 对每个调用 `run_log.log_tool_call(name, args, ...)` 并追加到本地 `tool_calls` 列表 |
| `AIMessage.usage_metadata.input_tokens` | 累加到 `in_tok_total` |
| `AIMessage.usage_metadata.output_tokens` | 累加到 `out_tok_total` |
| `AIMessage.content` (非空字符串) | 覆盖 `final_text`（最后一次 AIMessage 的文本作为最终答案） |
| `ToolMessage.content` | 可选地 `run_log.log_event(...)`，Week 1 仅记录不解析 |

**返回**：`(in_tok_total, out_tok_total, tool_calls, final_text)` —— 由调用方累加。

**实施时验证项**（具体字段名因 langchain 版本而异）：
- `usage_metadata` 在 langchain-core ≥ 0.2 的 AIMessage 上存在
- `tool_calls` 在 langchain-core ≥ 0.2 的 AIMessage 上存在
- 若 `usage_metadata` 缺失（部分自部署 server 不返回），累加为 0 + 后续在 `notes` 标注 `token_usage_unavailable`

---

## 7. `tasks/` + CLI

### 7.1 `tasks/task_base.py`

```python
@dataclass
class Task:
    id: str
    prompt: str
    success_criterion: Callable[[str], bool]
    sandbox_seed: list[tuple[str, str]] = field(default_factory=list)
```

### 7.2 `tasks/benchmark/task_01_simple_script.py`

```python
import sys, subprocess
from pathlib import Path
from tasks.task_base import Task
from shared.utils.sandbox import SANDBOX_DIR

def success(final_answer: str) -> bool:
    """(a) sandbox/hello.py 存在；
       (b) 运行该文件 stdout 含 'hello world'。"""
    hello_py = SANDBOX_DIR / "hello.py"
    if not hello_py.exists():
        return False
    result = subprocess.run([sys.executable, str(hello_py)],
                            capture_output=True, timeout=5)
    return b"hello world" in result.stdout.lower()

TASK = Task(
    id="task_01_simple_script",
    prompt=(
        "请在当前工作目录下创建一个名为 hello.py 的 Python 文件，"
        "内容为：打印字符串 'hello world'。"
        "创建完成后，运行该文件验证输出正确。"
    ),
    success_criterion=success,
)
```

**注意：** `success_criterion` 直接操作磁盘，**不**经 sandbox 限制 —— 它是评估代码而非 agent 代码。docstring 中标注。

### 7.3 任务发现

Week 1 用硬编码注册表（单任务）：

```python
# tasks/__init__.py
from tasks.benchmark.task_01_simple_script import TASK as TASK_01
TASKS = {"task_01_simple_script": TASK_01}
```

Week 2 再考虑自动发现 `task_*.py`。

### 7.4 `cli.py`

```python
# 用法：
#   python -m cli run --agent handroll --task task_01_simple_script
#   python -m cli run --agent deepagent --task task_01_simple_script
#   python -m cli run --agent both    --task task_01_simple_script
#   python -m cli tasks
```

流程：
1. 解析参数
2. 查 `TASKS` 注册表拿到 `Task` 对象
3. `reset_sandbox()`
4. 按 `--agent` 分发到 `handroll.agent.run(task)` 或 `deepagent.agent.run(task)`
5. 收集 RunLog，输出到 `outputs/runs/`
6. 打印摘要表（用 `rich.table`）：

```
┌──────────┬─────────┬───────┬────────────┬─────────────┬──────────┐
│ agent    │ success │ turns │ in_tokens  │ out_tokens  │ duration │
├──────────┼─────────┼───────┼────────────┼─────────────┼──────────┤
│ handroll │ True    │ 4     │ 1820       │ 540         │ 8.2s     │
│ deepagent│ True    │ 6     │ 2410       │ 720         │ 11.4s    │
└──────────┴─────────┴───────┴────────────┴─────────────┴──────────┘
```

---

## 8. 对比口径差异（重要）

这是 Week 1 最大的教学点之一。在 `framework_diff.md`（Week 4）和 RunLog `notes` 中明确记录。

| 字段 | handroll 口径 | deepagent 口径 |
|---|---|---|
| `loop_turns` | 1 turn = 1 次 `chat()` 调用 | 1 turn = 1 次 LangGraph 节点更新（agent node + tool node 各算一次） |
| `total_*_tokens` | 直接从 API response 累加 | 从 `AIMessage.usage_metadata` 累加；读不到则为 0 |
| `tool_calls` | 来自 `ToolUseBlock` | 来自 `AIMessage.tool_calls`；可能含 `write_todos`（框架内置） |
| `stop_reason` | handroll 自己判断（`task_complete` / `max_turns` / `loop_detected`） | deepagent 不主动给；Week 1 硬编码 `task_complete` + 由 `success_criterion` 决定 `success` |

预期同任务下 deepagent 的 `loop_turns` 约为 handroll 的 **2 倍**；token 消耗相近（取决于 `write_todos` 调用频率）。

---

## 9. 依赖

```toml
[project]
name = "loop-engineer"
requires-python = ">=3.11"
dependencies = [
    "openai>=1.40",
    "langchain>=0.3",
    "langchain-openai>=0.2",
    "langgraph>=0.2",
    "deepagents>=0.0.5",
    "rich>=13",
    "python-dotenv>=1",
]
[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.5"]
```

`anthropic` SDK 不再纳入（用户决定走 OpenAI 兼容）。根目录现有的 `loop.py` / `schemas.py` / `evaluator.py` 保留作为参考，最终按"重写"策略实现新版本；旧的根目录文件在实施过程中删除或归档到 `docs/reference/`。

---

## 10. Week 1 验收清单

- [ ] `pip install -e ".[dev]"` 成功
- [ ] `cp .env.example .env` + 填入 LLM 配置后可运行
- [ ] `python -m cli run --agent handroll --task task_01_simple_script` 成功，`sandbox/hello.py` 存在且可运行
- [ ] `python -m cli run --agent deepagent --task task_01_simple_script` 同上
- [ ] 两次运行都产出 RunLog JSON 到 `outputs/runs/`
- [ ] `python -m cli run --agent both --task task_01_simple_script` 输出并排摘要表
- [ ] 每个核心文件顶部 docstring 包含「和 DeepAgent 的对比」段落：
  - `loop.py`、`executor.py`、`evaluator.py`、`formatter.py`
  - `schemas.py`、`bash_exec.py`、`file_read.py`、`file_write.py`
  - `llm_client.py`、`sandbox.py`、`run_logger.py`
  - `task_01_simple_script.py`

---

## 11. 实施顺序提示（留给 writing-plans）

建议自下而上、由内到外。每完成一层用一个**轻量验证**（不必是完整 CLI run）确认该层独立可用：

1. **地基层**：`pyproject.toml`、`.env.example`、`.gitignore`、目录骨架 + 空 `__init__.py`
   - 验证：`pip install -e ".[dev]"` 成功，`python -c "import shared, handroll, deepagent, tasks"` 无错
2. **shared 层**：`config.py` → `sandbox.py` → `run_logger.py` → `schemas.py` + 3 个工具 → `llm_client.py`
   - 验证：`python -c "from shared.tools import bash_exec; print(bash_exec.run(command='echo hi'))"` 返回 dict
3. **handroll 层**：`executor.py` → `formatter.py` → `evaluator.py` → `loop.py` → `agent.py`
   - 验证：`python -c "from handroll.agent import run"` 不报错（先不实际调用）
4. **tasks 层**：`task_base.py` → `task_01_simple_script.py`
   - 验证：`python -c "from tasks import TASKS; print(TASKS['task_01_simple_script'].id)"`
5. **cli 层**：`cli.py`
   - 验证：`python -m cli tasks` 列出任务；`python -m cli run --agent handroll --task task_01_simple_script` 完整跑通
6. **deepagent 层**（最后）：依赖 shared 都跑通；`agent.py` 单文件
   - 验证：`python -m cli run --agent deepagent --task task_01_simple_script` 完整跑通
7. **最终对比**：`python -m cli run --agent both --task task_01_simple_script` 并排展示
