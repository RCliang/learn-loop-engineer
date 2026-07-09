# LocalShellBackend 启用 execute，却撞上 validate_path 拒绝 Windows 绝对路径

**日期：** 2026-07-09
**任务：** `task_01_simple_script`
**触发场景：** 把 baseline 从 `FilesystemBackend` 换成 `LocalShellBackend`（加上 `execute` 工具），重跑 `python -m cli run --agent both --task task_01_simple_script`
**前置文档：**
- [2026-07-09-deepagent-backend-statebackend.md](./2026-07-09-deepagent-backend-statebackend.md) —— StateBackend 是病根，FilesystemBackend 修好了落盘
- 官方 backend 文档：https://docs.langchain.com/oss/python/deepagents/backends
- 官方 sandbox 文档：https://docs.langchain.com/oss/python/deepagents/sandboxes

## TL;DR

按官方文档把 backend 切到 `LocalShellBackend`，目标是让模型自己也能 `execute`（FilesystemBackend 不实现 `SandboxBackendProtocol`，execute 工具一调就报错）。**结果：deepagent 单跑成功；`--agent both` 模式下非确定性失败**——同样的代码、同样的任务、同样的 prompt，连跑两次结果不一样。

深挖根因，失败不在 backend 层，而在**路径校验层**：deepagents 的 `validate_path`（`backends/utils.py:506-509`）**显式拒绝 Windows 绝对路径**（`^[a-zA-Z]:` 正则），告诉模型"请用以 / 开头的虚拟路径"。模型照着错误提示自纠，**但自纠时挑哪种 `/...` 形式，决定了它在 Windows 上最终落到哪**——`/2026projects/loop-engineer/sandbox/hello.py` 在 Windows 上 drive-anchored 后正好命中正确位置；`/E/2026projects/...` 则会被 anchor 成 `E:/E/2026projects/...`（错位）。

回看上一篇 FilesystemBackend 那次"成功"——其实同样是 `validate_path` 把 `E:/...` 拒了，只是模型当时自纠到了 `/2026projects/...`（无 `/E` 前缀）那条幸运路径。**LocalShellBackend 的"失败"和 FilesystemBackend 的"成功"都不是 backend 决定的，是模型自纠路径的选择决定的**。

## LocalShellBackend 是什么

`backends/local_shell.py:27`：

```python
class LocalShellBackend(FilesystemBackend, SandboxBackendProtocol):
    """Filesystem backend with unrestricted local shell command execution."""
```

它继承 `FilesystemBackend`（拿到真实磁盘 I/O），同时实现 `SandboxBackendProtocol`（拿到 `execute` 方法）。`execute` 内部就是 `subprocess.run(command, shell=True, cwd=str(self.cwd))`——直接在主机跑，无任何沙箱。

构造参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `root_dir` | `None`（→ `Path.cwd()`） | filesystem 操作 + execute 的 cwd |
| `virtual_mode` | `None`（→ deprecation warning → False） | True 时 root_dir 作虚拟根 |
| `timeout` | 120s | execute 超时 |
| `max_output_bytes` | 100_000 | 输出截断 |
| `env` / `inherit_env` | `{}` / `False` | 子进程环境变量 |

deepagent baseline 改动（`deepagent/agent.py`）：

```python
return create_deep_agent(
    model=model,
    tools=[],
    system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
    backend=LocalShellBackend(
        root_dir=str(SANDBOX_DIR),
        virtual_mode=False,
        inherit_env=True,  # 让 PATH 上的 python 可见
    ),
)
```

## 实验 1：deepagent 单跑 → 成功

`python -m cli run --agent deepagent --task task_01_simple_script`：

| success | turns | in_tokens | out_tokens | duration_s |
|---------|-------|-----------|------------|------------|
| **True**    | 18    | 43905     | 491        | 7.46       |

模型轨迹：

```
1. ls(E:/2026projects/loop-engineer/sandbox)
2. ls('/')
3. ls('/2026projects/loop-engineer/sandbox')
4. write_file('/2026projects/loop-engineer/sandbox/hello.py')  ← 关键
5. execute('python /2026projects/loop-engineer/sandbox/hello.py')
```

磁盘验证：`sandbox/hello.py` 存在，内容 `print('hello world')\n`。`execute` 把 `python` 跑通，输出 `hello world`。**success_criterion 满足**。

注意第 4 步：模型没用 Windows 绝对路径（`E:/...`），而是用了 POSIX 风格 `/2026projects/loop-engineer/sandbox/hello.py`。**这次模型自纠路径选对了**——在 Windows 上，`Path("/2026projects/loop-engineer/sandbox/hello.py")` 不是绝对路径（无盘符），join 到 cwd 后变成 drive-anchored `E:/2026projects/loop-engineer/sandbox/hello.py`，正好命中。

## 实验 2：`--agent both` → deepagent 失败

`python -m cli run --agent both --task task_01_simple_script`（连跑两次都失败）：

| agent     | success | turns | in_tokens | out_tokens | duration_s |
|-----------|---------|-------|-----------|------------|------------|
| handroll  | True    | 3     | 2559-2654 | 240-339    | 7.10-8.40  |
| deepagent | **False**   | 18-22 | 44256-52655 | 561-889  | 8.59-11.49 |

deepagent 轨迹（两次都类似）：

```
1. write_file('E:/2026projects/loop-engineer/sandbox/hello.py')   ← 被拒绝
2. ls('/')
3. write_file('/E/2026projects/loop-engineer/sandbox/hello.py')   ← 自纠到错路径
4. read_file('/E/2026projects/loop-engineer/sandbox/hello.py')
5. execute('python /E/2026projects/loop-engineer/sandbox/hello.py')
```

磁盘查证：

```
sandbox/hello.py                                 exists: False
E:/E/2026projects/loop-engineer/sandbox/hello.py exists: True   ← 错位落地
```

`success_criterion` 查 `SANDBOX_DIR/hello.py`，找不到 → False。

### 实验 1 vs 实验 2 的唯一差异

```
单跑成功：模型自纠到 /2026projects/loop-engineer/sandbox/hello.py
both 失败：模型自纠到 /E/2026projects/loop-engineer/sandbox/hello.py
```

两次模型都因为 `validate_path` 拒绝 `E:/...` 后被错误提示引导改用 `/...`，区别只在**前面加不加 `/E`**。在 Windows pathlib 下：

| 自纠路径 | `.is_absolute()` | `(cwd / path).resolve()` | 落点 |
|----------|------------------|--------------------------|------|
| `/2026projects/loop-engineer/sandbox/hello.py` | False（无盘符） | `E:/2026projects/loop-engineer/sandbox/hello.py` | ✅ 正确 |
| `/E/2026projects/loop-engineer/sandbox/hello.py` | False（无盘符） | `E:/E/2026projects/loop-engineer/sandbox/hello.py` | ❌ 错位 |

第二种情况里，Windows pathlib 把 `cwd` 的盘符 `E:` 拼到 `/E/...` 前面，得到 `E:/E/...`。这是个非常微妙的 drive-anchoring 行为——只要自纠路径的前缀不是合法的"目录名"（这里是单字母 `E`），就会落到磁盘上一个意外位置。

**模型非确定性是 true source of flakiness**——同样的 prompt、同样的 temperature=0，模型两次选了不同的自纠路径。

## 根因：`validate_path` 拒绝 Windows 绝对路径

`backends/utils.py:463-509`：

```python
def validate_path(path: str, *, allowed_prefixes=None) -> str:
    """Validate and normalize file path for security.

    This function is designed for virtual filesystem paths and rejects
    Windows absolute paths (e.g., `C:/...`, `F:/...`) to maintain consistency
    and prevent path format ambiguity.
    """
    # ...
    # Reject Windows absolute paths (e.g., C:\..., D:/...)
    if re.match(r"^[a-zA-Z]:", path):
        msg = (
            f"Windows absolute paths are not supported: {path}. "
            "Please use virtual paths starting with / (e.g., /workspace/file.txt)"
        )
        raise ValueError(msg)
    # ...
```

`write_file` / `read_file` / `ls` / `edit_file` / `delete` / `glob` / `grep` 这些 tool 在调 `backend.write/read/ls/...` 之前，都会先过 `validate_path`（`middleware/filesystem.py:1226`）：

```python
def sync_write_file(file_path, content, runtime):
    resolved_backend = self._get_backend(runtime)
    try:
        validated_path = validate_path(file_path)   # ← 这一关
    except ValueError as e:
        return ToolMessage(
            content=f"Error: {e}",
            name="write_file",
            tool_call_id=runtime.tool_call_id,
            status="error",                          # ← 工具直接返回错误
        )
    res: WriteResult = resolved_backend.write(validated_path, content)
    # ...
```

所以即便我们用了 `virtual_mode=False` 的 `FilesystemBackend` / `LocalShellBackend`（理论上支持任意绝对路径），**模型传入的 `E:/...` 路径在到 backend 之前就被 `validate_path` 拦下了**。

### 这个设计是合理的——只是和我们的用法不匹配

`validate_path` 的 docstring 说："designed for virtual filesystem paths"。deepagents 框架的心智模型是：
- backend 是虚拟 FS（`StateBackend` 默认就是）
- 路径以 `/` 为根，POSIX 风格
- backend 负责把虚拟路径翻译到实际存储

我们用 `FilesystemBackend(virtual_mode=False)` / `LocalShellBackend(virtual_mode=False)`，等于把"虚拟 FS"的口子撕开，让 backend 直接读写真实磁盘。**但 `validate_path` 不是 backend 层的代码**，它在中间件层，无视 backend 的 `virtual_mode` 配置。这就产生了一个错位：backend 允许 Windows 绝对路径，但中间件层不允许。

`execute` 工具不走 `validate_path`（它直接传给 `subprocess.run`），所以模型能跑 `python E:/...`，**但文件工具永远拒绝 `E:/...`**。

## 回看 FilesystemBackend 那次"成功" —— 同样是 `validate_path` 拒绝，只是模型幸运自纠

把上一篇的 [FilesystemBackend run log](../../outputs/runs/20260709_151129_395769_deepagent_task_01_simple_script.json) 拉出来重看：

```
1. write_file('E:/2026projects/loop-engineer/sandbox/hello.py')   ← 被拒绝
2. ls('/')
3. ls('/2026projects/loop-engineer/sandbox')
4. write_file('/2026projects/loop-engineer/sandbox/hello.py')     ← 自纠到对路径
5. task subagent
6. read_file('/2026projects/loop-engineer/sandbox/hello.py')
```

那次第一次 `write_file` 也是 `E:/...`，也被 `validate_path` 拒。但模型在 ls 探查之后，第二次 `write_file` 选了 `/2026projects/loop-engineer/sandbox/hello.py`（**没有 `/E` 前缀**）——drive-anchored 后正好是 `E:/2026projects/loop-engineer/sandbox/hello.py`，命中 sandbox 目录。

**所以 FilesystemBackend 那次的"成功"和 LocalShellBackend 这次的"失败"，本质区别只在模型自纠路径的运气**。backend 都一样过，`validate_path` 都一样拒，差别在模型读到错误提示后挑了哪种 `/...` 形式。

## 教学要点

1. **"换 backend" 不是单一变量**。本以为 `FilesystemBackend → LocalShellBackend` 是只换 execute 能力、其他不变。实际上 `validate_path` 这一层一直存在，只是 FilesystemBackend 那次"幸运"地没暴露。`validate_path` 是中间件层的关卡，与 backend 的 `virtual_mode` 独立——这种"分层但配置不对齐"是框架设计里很常见的陷阱。
2. **Windows 是 LLM agent 的次等公民**。deepagents 的路径模型是 POSIX-style 虚拟 FS。Windows 绝对路径（带盘符）在 `validate_path` 这一层就被显式拒绝。错误提示让模型用 `/...`，但 Windows + Python pathlib 对 `/...` 的 drive-anchoring 行为非常微妙，模型不一定能挑对前缀。
3. **temperature=0 不等于确定性**。模型在"自纠路径"这种 creative 选择上仍有非确定性。两次 `--agent both` 跑出 18 / 22 turns、44k / 52k tokens、不同的 tool_call 序列——这是 LLM agent 项目普遍要注意的：**确定性只在 prompt + tool schema 层面，不在模型生成层面**。
4. **回看老结论要带新证据**。前一篇 doc 把 FilesystemBackend run 当成"成功的对照实验"，结论是"换 backend 就修好了"。带 `validate_path` 这个新证据重看，那次成功里也有 `validate_path` 拒绝 + 模型自纠的痕迹——只是自纠到对路径了。**"成功"和"修对了"不是一回事**。

## Week 2 方案再评估（再次重排）

| 方案 | 之前评估 | 本轮后 |
|------|----------|--------|
| **方案 A（prompt 增强）** | 已证伪（StateBackend 才是病根） | **再次证伪，但方向变了**。现在的 prompt 显式让模型用 `E:/.../sandbox/hello.py`——正好是 `validate_path` 拒绝的格式。改成"用相对路径"或"用以 / 开头的虚拟路径"预期能修掉这一层。 |
| **方案 B（捕获 ToolMessage）** | 降级 | **重新升级**。本轮的诊断之所以能定位到 `validate_path`，靠的就是 ToolMessage 的错误内容（错误提示里写明"Windows absolute paths are not supported"）。不捕获 ToolMessage，永远只看到 `ok: true` 的估计值，看不到这一层。 |
| **方案 C（只留共享工具）** | 待试 | 不变。共享工具 `file_write` 不走 `validate_path`（我们自己写的，无此校验），天然回避这个问题。 |
| **方案 D（穿透 subagent 流）** | 最高优先级 | 仍最高。LocalShellBackend 在 both 模式失败时，token 涨到 44-52k，subagent / 多轮探查贡献了大头。 |
| **新方案 F（POSIX 路径 prompt）** | —— | **本篇发现催生的新方案**。把 prompt 改成"用 `hello.py` 这种相对路径"或"用 `/hello.py` 这种虚拟路径"，绕开 `validate_path`。预期修掉 both 模式的非确定性失败。 |

**下一个实验**：方案 F（POSIX 路径 prompt）。一行改动，预期让 LocalShellBackend 在 `--agent both` 模式下也稳定成功。如果还失败，再上方案 B 捕获 ToolMessage 看具体卡在哪。

## 代码状态

`deepagent/agent.py` 的 baseline 已切换为 `LocalShellBackend`。这个切换本身是**正确的方向**——它让 `execute` 工具真正可用，模型不再需要委派 subagent 间接跑命令（实验 1 单跑成功的轨迹里，模型直接调 `execute` 跑 `python hello.py`，干净利落）。

但**当前 baseline 在 `--agent both` 模式下非确定性失败**。下一篇 finding 应当评估方案 F 是否能把这个失败修掉。在那之前，如果需要稳定的 deepagent 成功，跑 `--agent deepagent` 单跑模式。
