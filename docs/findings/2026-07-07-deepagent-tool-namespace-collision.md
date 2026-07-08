# Deepagent Tool Namespace Collision — Why `bash_exec` Kept "Failing"

**Date:** 2026-07-07
**Task:** `task_01_simple_script` (create `sandbox/hello.py`, run, verify "hello world")
**Trigger:** First live side-by-side run of `python -m cli run --agent both --task task_01_simple_script`

## TL;DR

`create_deep_agent` injects **8 built-in tools** alongside the 3 we passed in, creating **3 overlapping name pairs** (`write_file`/`file_write`, `read_file`/`file_read`, `execute`/`bash_exec`). The model picks the alphabetically-first `write_file`, which uses a different schema (`file_path` vs `path`) and a different CWD convention than our sandboxed `bash_exec`. The resulting CWD mismatch causes 5 bash attempts before the model stumbles onto the right relative path. Handroll has no such issue because it exposes only the 3 shared tools.

## Observation

Run `python -m cli run --agent both --task task_01_simple_script`. Both paths succeed, but their RunLogs look very different:

| agent     | success | turns | in_tokens | out_tokens | duration_s |
|-----------|---------|-------|-----------|------------|------------|
| handroll  | True    | 3     | 2413      | 282        | 9.48       |
| deepagent | True    | 21    | 47202     | 563        | 12.64      |

`loop_turns` is ~7x, `in_tokens` is ~20x. The task is "create hello.py and run it" — there is no reason for 21 turns. The deepagent `tool_calls` trace tells the story:

```json
"tool_calls": [
  {"name": "write_file",  "input": {"file_path": "sandbox/hello.py", "content": "print('hello world')\n"}},
  {"name": "bash_exec",   "input": {"command": "cd /sandbox && python hello.py"}},
  {"name": "bash_exec",   "input": {"command": "python /sandbox/hello.py"}},
  {"name": "bash_exec",   "input": {"command": "pwd && ls"}},
  {"name": "bash_exec",   "input": {"command": "python /e/2026projects/loop-engineer/sandbox/hello.py"}},
  {"name": "bash_exec",   "input": {"command": "python hello.py"}}
]
```

Five `bash_exec` attempts for a one-line file. The handroll trace is clean — one `file_write`, one `bash_exec`, done.

## Evidence: What the Model Actually Sees

Inspecting the ToolNode of the compiled graph (`agent.get_graph().nodes["tools"]`) reveals **12 tools total**: 9 deepagents built-ins + 3 of ours.

### Full Tool Inventory

| # | Tool | Source | Overlap | Purpose (first line of description) | Key args |
|---|------|--------|---------|-------------------------------------|----------|
| 1 | `write_todos` | deepagents | — | Manage a structured task list for the current session | `todos: array` |
| 2 | `ls` | deepagents | soft overlap with `file_read` | Lists all files in a directory | `path: string` (**absolute**) |
| 3 | `read_file` | deepagents | **name-conflicts** with our `file_read` | Reads a file from the filesystem (supports pagination, multimodal) | `file_path`, `offset`, `limit` (**absolute path**) |
| 4 | `write_file` | deepagents | **name-conflicts** with our `file_write` | Writes to a new file in the filesystem | `file_path`, `content` (**absolute path**) |
| 5 | `edit_file` | deepagents | — | Performs exact string replacements in files | `file_path`, `old_string`, `new_string`, `replace_all` |
| 6 | `glob` | deepagents | — | Find files matching a glob pattern | `pattern`, `path` |
| 7 | `grep` | deepagents | — | Search for a text pattern across files (literal, not regex) | `pattern`, `path`, `glob`, `output_mode` |
| 8 | `execute` | deepagents | **functional overlap** with our `bash_exec` | Executes a shell command in an isolated sandbox environment | `command`, `timeout` |
| 9 | `task` | deepagents | — | Launch an ephemeral subagent for complex multi-step tasks | `description`, `subagent_type` |
| 10 | `bash_exec` | **OURS** | — | 在沙箱 shell（限制在 sandbox/ 工作目录）中执行命令 | `command`, `timeout` |
| 11 | `file_read` | **OURS** | — | 读取 sandbox/ 工作目录下的文件内容 | `path`, `encoding` (**relative to sandbox**) |
| 12 | `file_write` | **OURS** | — | 将内容写入 sandbox/ 工作目录下的文件 | `path`, `content`, `encoding` (**relative to sandbox**) |

### Three Conflict Pairs

The collisions that actually confuse the model:

| Built-in (deepagents) | Ours | Schema mismatch | Behavioral mismatch |
|-----------------------|------|-----------------|---------------------|
| `write_file(file_path=...)` | `file_write(path=...)` | arg name `file_path` vs `path` | built-in uses **absolute** paths from project root; ours uses **relative-to-sandbox** paths |
| `read_file(file_path=...)` | `file_read(path=...)` | arg name `file_path` vs `path` | same as above; built-in also has `offset`/`limit` pagination we don't |
| `execute(command=...)` | `bash_exec(command=...)` | same arg name `command` | built-in runs "in an isolated sandbox environment" (deepagents-managed); ours sets `cwd=SANDBOX_DIR` explicitly |

### Built-in Tool Descriptions (Full Reference)

The descriptions below are verbatim from the deepagents ToolNode (captured via `agent.get_graph().nodes["tools"].data.tools_by_name[name].description`). They are useful for understanding what the model sees when reasoning about which tool to pick.

**`write_todos`** — Task-list manager. Triggers when the model thinks the task needs 3+ steps. Injects a planning phase that adds turns/tokens. (For `task_01_simple_script` this is pure overhead.)

**`ls`** — Directory listing. Args: `path` (**"Must be absolute, not relative"**). The deepagents filesystem model is rooted at the project root, NOT at our sandbox.

**`read_file`** — File reader with pagination + multimodal (images/PDFs). Args: `file_path` (**"Must be absolute"**), `offset` (0-indexed line), `limit`. Returns content in `cat -n` format.

**`write_file`** — File creator. Args: `file_path` (**"Must be absolute"**), `content`. Documentation explicitly says "Prefer to edit existing files (with the edit_file tool) over creating new ones when possible."

**`edit_file`** — String replacement editor. Requires reading the file first. Args: `file_path`, `old_string`, `new_string`, `replace_all`.

**`glob`** — Pattern match. Args: `pattern` (e.g. `**/*.py`), `path` (base dir).

**`grep`** — Literal text search (NOT regex). Args: `pattern`, `path`, `glob`, `output_mode` (`files_with_matches` | `content` | `count`).

**`execute`** — Shell executor. Args: `command`, `timeout`. Documentation specifically says "avoid using search commands like find and grep. Instead use the grep, glob tools" and "avoid read tools like cat, head, tail, and use read_file". This is a Claude-Code-style opinionated workflow.

**`task`** — Subagent spawner. Args: `description`, `subagent_type` (`general-purpose` by default). Each spawn is stateless.

### Summary of the Built-in Behavior Model

All deepagents built-in filesystem tools (`ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`) **require absolute paths rooted at the project directory**. This is the opposite convention from our shared tools, which **require paths relative to `sandbox/`**. When the model mixes the two (which it will, because they look similar), the CWD assumptions collide and produce the kind of multi-attempt recovery seen in the RunLog.

The deepagents library documents this in `create_deep_agent`'s docstring:

> By default, this agent has access to the following tools:
> - `write_todos`: manage a todo list
> - `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`: file operations
> - `execute`: run shell commands
> - `task`: call subagents

There is **no `disable_default_tools` flag** in the `create_deep_agent` signature. The built-ins are always added.

## Root Cause #1 — Tool Namespace Pollution

The model sees alphabetically sorted tools. For the write step:

```
...
write_file   (deepagents)   ← appears first
file_write   (ours)
...
```

Both descriptions are plausible ("Writes to a new file in the filesystem" vs "将内容写入 sandbox/ 工作目录下的文件"). The model picks `write_file` — the built-in, not ours.

**Consequence:** The file write goes through deepagents' code path, not our `shared/tools/file_write.py`. This means:
- Our `resolve_in_sandbox` path guard is **bypassed**
- Our errors-as-payload dict shape is not produced
- The model learns the wrong schema (`file_path=...` instead of `path=...`)

The file did get written to the right location, but only by accident: deepagents' `write_file` runs from the real project root, so relative `sandbox/hello.py` resolves to the same path our sandbox guard would have enforced.

## Root Cause #2 — CWD Context Mismatch

Our `bash_exec` runs with `cwd=SANDBOX_DIR`. The model does not know this. Its mental model of "where am I" comes from the `write_file` call that preceded it — and `write_file` ran from the project root.

So the model reasons: *"I wrote `sandbox/hello.py` from the project root. To run it, I need to `cd sandbox` or use the path `sandbox/hello.py`."*

Reality: bash is already inside `sandbox/`. Every absolute or `sandbox/`-prefixed path the model tries either doesn't exist or resolves wrong:

| Attempt | Command | Why it fails |
|---------|---------|--------------|
| 1 | `cd /sandbox && python hello.py` | `/sandbox` is not a real absolute dir — `sandbox/` is relative to project root |
| 2 | `python /sandbox/hello.py` | Same — no such file |
| 3 | `pwd && ls` | **Debugging probe** — model discovers CWD is `sandbox/`, file is right here |
| 4 | `python /e/2026projects/loop-engineer/sandbox/hello.py` | Absolute path resolved from sandbox CWD; Python can find it but it's ugly |
| 5 | `python hello.py` | Finally correct — relative path from sandbox CWD |

Three of the five calls produce errors the model has to read and recover from. That recovery is what inflates `in_tokens` to 47k — the model is reading verbose bash error messages and re-reasoning about paths every turn.

## Why Handroll Has No Such Issue

The handroll path exposes exactly 3 tools, all ours:

```
bash_exec, file_read, file_write
```

No naming ambiguity. The model calls `file_write(path="hello.py", ...)` — relative path, which is what our sandbox expects. Then `bash_exec(command="python hello.py")` — also relative, works on the first try because CWD is already the sandbox.

The system prompt is identical between paths. The difference is purely tool surface area.

## Implication: `exit_code` Is Null in All Recorded Calls

Our RunLog records `exit_code: null` for every deepagent tool call, even the ones that obviously errored (`cd /sandbox && python hello.py`). This is because `deepagent/agent.py:_ingest_event` only consumes `AIMessage.tool_calls` — the *request*. The actual `ToolMessage` results (containing stdout/stderr/exit_code) flow through a different LangGraph event that we currently ignore:

```python
elif msg_type == "tool":
    # ToolMessage: 工具结果。若 log_tool_call 时 ok=True 是估计值，这里可校正
    pass
```

So the comparison RunLog can tell you *what the model tried* but not *what actually happened*. To see the bash errors that drove the 47k token spike, you'd need to capture `ToolMessage.content` and correct the `ok` / `exit_code` fields after the fact.

## Week 2 Options

From cheapest to most thorough:

### Option A — Augment the system prompt

Tell the model its bash CWD is `sandbox/`, and to prefer the shared tools over the built-ins:

```
注意：bash_exec 的当前工作目录就是 sandbox/，文件就在当前目录下，直接用相对路径。
优先使用 file_write / file_read / bash_exec，不要使用 write_file / read_file。
```

Cost: 2 lines in `DEEP_AGENT_SYSTEM_PROMPT`. Likely halves the bash attempts.

### Option B — Record ToolMessage results

In `deepagent/agent.py:_ingest_event`, handle the `elif msg_type == "tool"` branch: parse `msg.content` for exit codes / error indicators, and update the corresponding `run_log.tool_calls` entry. This won't change behavior but will make the RunLog a faithful record for comparison.

### Option C — Filter the built-in tools

`create_deep_agent` doesn't accept a `disable_default_tools` flag, but the compiled graph's ToolNode can be replaced post-construction:

```python
agent = create_deep_agent(model=model, tools=ALL_TOOLS_AS_CALLABLES, system_prompt=...)
# Replace the ToolNode to drop overlapping built-ins
keep = {"bash_exec", "file_read", "file_write", "write_todos", "task"}
agent.tools = {n: t for n, t in agent.tools.items() if n in keep}
```

This is fragile — it reaches into deepagents' internal structure and may break on version upgrades. But it's the only way to get a truly clean tool surface for fair comparison.

## Teaching Takeaway

This is the concrete cost of framework abstraction made visible:

- **handroll** = 3 tools, 30 lines of orchestration, model succeeds first try.
- **deepagent** = 11 tools (3 ours + 8 framework-injected), 100 lines of wrapper, model takes 5 tries.

The framework gives you `write_todos`/planning/subagents for free — but it also gives the model 3 overlapping name pairs to disambiguate, and it doesn't tell you when its tools conflict with yours. For Week 1's purpose (see this tradeoff with your own eyes), the current behavior is the lesson.
