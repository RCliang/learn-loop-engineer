# virtual_mode=True 修复路径 + 实验基建全面对齐

**日期：** 2026-07-10
**任务：** `task_01_simple_script`（创建 `sandbox/hello.py`，运行，验证输出 "hello world"）
**触发场景：** 在前两篇 finding 的修复链上继续推进——`virtual_mode=True` 修路径、ToolMessage 捕获修 ok 假值、system_prompt 记录修 prompt 可见性、turns 口径统一修指标可比性
**前置文档：**
- [2026-07-09-deepagent-localshell-validate-path.md](./2026-07-09-deepagent-localshell-validate-path.md) —— validate_path 拒绝 Windows 绝对路径，提出方案 F（虚拟路径 prompt）
- [2026-07-09-deepagent-backend-statebackend.md](./2026-07-09-deepagent-backend-statebackend.md) —— StateBackend 是内存虚拟 FS，换 LocalShellBackend 修落盘
- [2026-07-08-deepagent-native-only-tools.md](./2026-07-08-deepagent-native-only-tools.md) —— 9 工具版直接失败的三层根因

## TL;DR

本轮完成了四项修复，deepagent 路径**稳定成功**（`--agent both` 模式连续多次通过），工具零失败。但 deepagent 仍有**虚拟路径 vs shell 真实路径的认知困惑**，导致多余探索轮次。同时完成了三项实验基建对齐（ToolMessage 捕获、system_prompt 记录、turns 口径统一），使两路数据首次具备严格可比性。

## 四项修复

### 修复 1：`virtual_mode=True` 解决路径困惑

**问题**（前篇方案 F）：`virtual_mode=False` 时 `validate_path` 拒绝 Windows 绝对路径，模型自纠路径的选择是非确定性的。

**修复**：`deepagent/agent.py` 一行改动：

```python
backend=LocalShellBackend(
    root_dir=str(SANDBOX_DIR),
    virtual_mode=True,   # 虚拟根模式：模型看到 /hello.py，框架映射到 sandbox/hello.py
    inherit_env=True,
),
```

效果：模型用 `/hello.py` 这种 POSIX 虚拟路径，`validate_path` 通过（以 `/` 开头），框架内部映射到 `{root_dir}/hello.py` = `sandbox/hello.py`。`execute` 工具的 `cwd` 同样是 sandbox，shell 命令用相对路径 `python hello.py` 即可。

**同步 prompt 改动**：两路 prompt 统一为"工作目录"语义（去掉 Windows 绝对路径引用）：

```
# deepagent（虚拟路径）
文件路径请使用 POSIX 虚拟路径，以 / 开头，例如：
- /hello.py 表示工作目录下的 hello.py

# handroll（相对路径）
文件路径请使用相对路径，例如：
- hello.py 表示工作目录下的 hello.py
```

差异仅在路径表达形式（虚拟 `/hello.py` vs 相对 `hello.py`），核心指令一致——这是工具层语义差异所致，不可避免。

### 修复 2：ToolMessage 捕获（方案 B）

**问题**（07-08 finding 根因 #4）：`_ingest_event` 在 AIMessage 阶段硬编码 `ok=True`，ToolMessage 阶段 `pass` 掉，RunLog 里工具调用永远显示成功。

**修复**：AIMessage 阶段记录 `_tool_call_id` + `_pending: True`，ToolMessage 阶段用 `msg.status` 和 `msg.content` 回写真实结果：

```python
elif msg_type == "tool":
    content = getattr(msg, "content", "") or ""
    tc_id = getattr(msg, "tool_call_id", None) or ""
    status = getattr(msg, "status", "success")
    is_ok = (status != "error")
    for recorded in reversed(run_log.tool_calls):
        if recorded.get("_tool_call_id") == tc_id and recorded.get("_pending"):
            recorded["ok"] = is_ok
            recorded["_pending"] = False
            recorded["output_preview"] = content[:500]
            break
```

保存前调 `_cleanup_internal_fields()` 清除 `_tool_call_id` / `_pending`，保证 JSON 干净。

### 修复 3：system_prompt 记录

**问题**：实验 JSON 里看不到模型实际收到的完整 prompt，无法对比两路指令差异。

**修复**：
- RunLog 加 `system_prompt: str = ""` 字段
- deepagent 通过 `_SystemPromptCapture` callback 拦截第一次模型调用时 deepagents 运行时拼接的完整 prompt
- handroll 直接存入 `REACT_SYSTEM_PROMPT` 常量

### 修复 4：turns 口径统一

**问题**（07-08 finding「指标修正」一节）：handroll 的 `loop_turns` = LLM 调用次数；deepagent 的 `loop_turns` = LangGraph 节点更新事件数（每次 LLM 调用膨胀为 ~3 个事件）。

**修复**：deepagent 改为统计 AIMessage 数量（= LLM 调用次数），与 handroll 完全对齐：

```python
if msg_type == "ai":
    llm_calls += 1
```

notes 同步更新为：`"loop_turns 与 handroll 对齐口径：LLM 调用次数（AIMessage 数量）"`。

## 实验结果

`python -m cli run --agent both --task task_01_simple_script`

| 指标 | handroll | deepagent | 倍数 |
|------|----------|-----------|------|
| success | ✅ True | ✅ True | — |
| **turns** | **3** | **10** | 3.3× |
| tool_calls | 2 | 9 | 4.5× |
| failed tools | 0 | 0 | — |
| input tokens | 2,508 | 77,671 | **31×** |
| output tokens | 207 | 934 | 4.5× |
| duration_s | 7.3 | 15.2 | 2.1× |
| system_prompt | 264 chars | 7,909 chars | 30× |

### 与历史数据对比

| 阶段 | deepagent success | turns (LLM 调用) | in_tokens | 关键变化 |
|------|-------------------|-----------------|-----------|----------|
| 07-08（9 工具原始版） | ❌ False | ~3-4（被膨胀为 9） | 18,789 | StateBackend + 路径错位 |
| 07-09（LocalShellBackend） | ⚠️ 非确定性 | ~6-7（被膨胀为 18-22） | 44k-52k | execute 可用，validate_path 非确定性 |
| **07-10（virtual_mode=True）** | **✅ 稳定 True** | **10** | **77,671** | **路径稳定，工具零失败** |

## 剩余问题：虚拟路径 vs shell 真实路径的认知裂缝

虽然 deepagent 稳定成功了，但模型花了 10 次 LLM 调用（handroll 只要 3 次），多出的 7 次全在探索路径：

```
write_file('/hello.py', ...)           ← ✅ 虚拟路径写入成功
execute('python /hello.py')            ← ❌ 虚拟路径传给 shell，E:\hello.py 不存在
execute('ls /')                        ← ❌ Windows 没有 ls
execute('cd / && dir')                 ← 探索，看到 E:\ 根目录
execute('dir E:\hello.py')            ← 在 E:\ 根找 hello.py，找不到
read_file('/hello.py')                 ← ✅ 虚拟路径读取成功（确认文件存在）
execute('python -c "import os; print(os.getcwd())"')  ← 发现 cwd 是 sandbox
execute('dir E:\...\sandbox\hello.py') ← ✅ 用完整绝对路径确认文件存在
execute('python hello.py')             ← ✅ 终于用相对路径跑通
```

### 根因

deepagents 的文件系统工具（`write_file` / `read_file` / `ls`）和 `execute` 工具**运行在不同的路径语义空间**：

| 工具 | 路径语义 | 例子 |
|------|----------|------|
| `write_file` / `read_file` / `ls` | 虚拟路径（`/` = sandbox 根） | `/hello.py` → `sandbox/hello.py` |
| `execute` | 真实 shell（`cwd` = sandbox 目录） | `python hello.py` 或 `python E:\...\sandbox\hello.py` |

模型看到 `write_file('/hello.py')` 成功了，自然以为 `python /hello.py` 也能跑——但 `/hello.py` 对 shell 来说被 Windows 解析为 `E:\hello.py`（盘根）。模型不得不花 7 轮探索才搞清楚"文件工具用 `/hello.py`，shell 命令用 `hello.py`"。

handroll 没有这个问题——`file_write` 和 `bash_exec` 都用相对路径，语义空间一致。

### 这是框架的"抽象税"

`virtual_mode=True` 让文件工具的路径空间与真实磁盘解耦，但 `execute` 工具的 `cwd` 暴露了真实 shell 环境。**两套路径语义共存于同一个 agent 的工具表面**，模型必须自己学会区分。这是 deepagents 框架在 Windows 上固有的认知负担。

## Token 开销拆解

77,671 input tokens vs handroll 的 2,508——31 倍差距的来源：

| 来源 | 估算 | 说明 |
|------|------|------|
| system_prompt 差异 | ~7,600 × 10 = **76,000** | deepagent 每次 LLM 调用都带 7,909 字符 system prompt（≈7,600 tokens），handroll 只有 264 字符（≈250 tokens） |
| 工具 schema | ~2,000 × 10 = **20,000** | 9 个工具 schema（含 `task` subagent 长描述、`write_todos` 使用指南）vs 3 个精简 schema |
| 多余轮次 | — | 10 次 LLM 调用 vs 3 次，每次调用都有固定开销 |
| conversation 累积 | ~5,000 | 9 次工具调用的 input/output 累积到 context |

**system_prompt 是最大的单项开销**——7,909 字符的完整 prompt 中，我们自己写的 USER 段只有 ~300 字符，剩下 ~7,600 字符全是 deepagents 框架注入的（BASE 行为准则 + TodoList 指南 + Filesystem 工具说明 + SubAgent 使用指南）。每次 LLM 调用都为这些"框架税"付费。

这正好印证了 07-08 finding 的结论：**"deepagents 的真正代价不在多想了几次，而在每次想的 context 被框架的 schema 和中间件撑大了"**。

## 基建状态总结

| 维度 | handroll | deepagent | 可比？ |
|------|----------|-----------|--------|
| turns 定义 | LLM 调用次数 | LLM 调用次数 | ✅ 已对齐 |
| tool_calls 的 ok | 真实结果 | ToolMessage 回写 | ✅ 已对齐 |
| system_prompt | 记录了 | 记录了（完整拼接版） | ✅ 已对齐 |
| 路径语义 | 相对路径（统一） | 虚拟路径（文件）+ 相对路径（shell） | ❌ 框架限制 |
| 工具数量 | 3 | 9 | ❌ 设计如此 |

## 代码改动清单

| 文件 | 改动 |
|------|------|
| `deepagent/agent.py` | `virtual_mode=True`；prompt 改虚拟路径；加 `_SystemPromptCapture` callback；`_ingest_event` 返回 `llm_calls` 统计 AIMessage 数量；ToolMessage 回写 ok；`_cleanup_internal_fields` |
| `handroll/agent.py` | prompt 改相对路径；存入 `system_prompt` |
| `shared/tracker/run_logger.py` | 加 `system_prompt: str = ""` 字段 |

## 下一步

1. **虚拟路径 vs shell 路径裂缝**：可以在 prompt 里显式告诉模型"文件工具用 `/hello.py`，shell 命令用 `hello.py`（不要用 `/` 前缀）"。预期能砍掉多余探索轮次。
2. **更多任务**：当前只测了 `task_01_simple_script`。需要 benchmark 更多任务（多文件、需要编辑、需要测试等）才能判断 deepagent 的 subagent / write_todos 是否在复杂任务上有优势。
3. **subagent 穿透**：本轮未涉及。仍是最高优先级基建（07-08 finding 方案 D），当前 subagent 内部行为仍是 token 黑盒。
