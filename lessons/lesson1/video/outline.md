# Video Outline

> **主题**：`terminal-green`（Checkpoint Plan 待选定）—— 纯黑底 + 磷光绿，等宽字体，CRT/终端黑客气质
> **总时长**：约 9 分钟（口播 ~1800 字，代码块按演示时长另计）
> **章节数**：7 章 / 64 步

> **节奏校验**：每章 step 的 `(~Ts)` 累加 = 章节标题 `~<T>s`；7 章合计 540s = 9m。
> 代码块 step 按"演示时长"估时（narrator 描述代码而非逐字念），非纯字数 ÷ 4。

---

## 1. coldopen — 先看效果：一个能自己干活的程序（8 steps · ~80s）

**信息池**（chapter agent 按需挂角标 / 副标 / pull-quote / mono cue）：
- 数字：150 行 Python —— 整个 Agent 核心代码量 —— 来源 article 开场 §1 / v4_final.py 总行数
- 数字：3 轮对话、2 次工具调用 —— Agent 解决 hello.py 任务的统计 —— 来源 article 开场 §1
- 任务原文："创建一个 hello.py 文件，然后运行它" —— 来源 v1~v4 run_agent 入参
- AI coding agent 名：Cursor、Claude Code、Cline —— 都"核心是一个 for 循环" —— 来源 article 开场 §1
- 工具名：file_write（写文件）、bash_exec（跑命令）—— Agent 实际调的两个工具 —— 来源 v2/v3/v4 TOOLS
- 终端输出语义：Turn 1 file_write → Turn 2 bash_exec → Turn 3 看到 hello world 判定完成 —— 来源 slides.html s2

**开发计划**：

- step 1 (~3s) — hero 大字开场，一条"先看个东西"标语，吊住注意力
- step 2 (~11s) — 模拟终端出现，逐行打字出任务："创建一个 hello.py 文件，然后运行它"
- step 3 (~15s) — Turn 1 演出：终端出现"💭 思考"行 + file_write 工具调用块（参数路径 hello.py）
- step 4 (~15s) — Turn 2 演出：bash_exec 工具调用块 + 结果"hello world"；Turn 3 ✅ 完成
- step 5 (~6s) — 数据条 hero 数字浮现：3 轮 / 2 次工具调用（"整个过程没人插手"）
- step 6 (~8s) — hero 数字浮现：150 行（核心代码量）
- step 7 (~7s) — 反差铺垫："这事跟你的直觉可能不一样"——引出框架论断
- step 8 (~15s) — 金句演出：Cursor / Claude Code / Cline 三个名字逐个浮现，落点"核心都是一个 for 循环"

口播节选：
> 我给这个程序一个任务……三轮对话，两次工具调用，整个过程没人插手。这个 Agent 的核心代码 150 行 Python。市面上你叫得出名字的 Agent 框架……核心都是一个 for 循环。

---

## 2. v1-bare — 最小循环：能想，不能做（8 steps · ~52s）

**信息池**：
- 核心代码块：v1 的 for 循环（4 行：for / resp / reply / messages.append）—— 来源 v1_bare_loop.py L25-35
- 文件名：v1_bare_loop.py —— 来源 code/
- 行数：约 20 行（含配置）—— 来源 article 收尾表 / slides.html s12
- 状态标签：能想 / 不能做 —— 来源 article 收尾表
- 比喻句："就像一个人坐椅子上跟你说'我帮你把门关了'，话说完了门还开着" —— 来源 article §1
- SYSTEM_PROMPT："你是一个 Code Agent。请根据用户需求完成任务。" —— 来源 v1_bare_loop.py L19
- 问题点：v1 没有 tools 参数、没有停止判断、跑满 max_turns 就结束 —— 来源 v1 L37-38 注释
- 终端演出：LLM 说"好的，我来帮你创建 hello.py..."但实际无操作 —— 来源 slides.html s4

**开发计划**：

- step 1 (~9s) — 章节标题转场：打开编辑器从零开始，问"最核心的结构是什么"
- step 2 (~6s) — hero 标语"就是一个循环" + 反复调 LLM 的意象（循环箭头/环形图）
- step 3 (~7s) — 代码块开头揭示 v1 核心 4 行的前 2 行（for / resp = client...）
- step 4 (~7s) — 代码块后 2 行揭示（reply / messages.append），完整 v1 循环可见
- step 5 (~5s) — 文件角标浮现：v1_bare_loop.py · ~20 行 · 状态 tag"能想 / 不能做"
- step 6 (~6s) — 切模拟终端跑 python v1_bare_loop.py，LLM 输出"好的我来帮你创建 hello.py..."
- step 7 (~7s) — 比喻画面演出：椅子 + 门（极简 SVG/ASCII 演关门动作落空），"话说完了门还开着"
- step 8 (~5s) — 结论收束：问题明确——Agent 需要一双手（"手"字 hero 强调）

口播节选：
> 一个 Agent 最核心的结构到底是什么？就是一个循环……就这么几行，这就是 v1。LLM 很努力地告诉你"我帮你创建了 hello.py"，但实际什么都没发生……就像一个人坐椅子上跟你说"我帮你把门关了"。Agent 需要一双手。

---

## 3. v2-tools — 给 Agent 装上手：工具三件事（13 steps · ~134s）

> ⚠️ 本章 13 步，超出"每章 3~8 步"经验法则。但内容是本课最重的一章（v2 是 Agent 真正"能做事"的转折），
> 三件事 + 工具定义 + 执行器 + 完成判断 + 运行演示 + 隐患引子，强行拆成两章会割裂"装手"这个聚焦主题。
> chapter agent 实现时可把 ①②③ 三件事总览 + 完成判断 + 运行演示各压缩成更紧凑的 sub-block。

**信息池**：
- 三件事编号：① 告诉 LLM 有哪些工具（tools schema）② 解析 tool_calls ③ 执行 + 回传结果 —— 来源 article §2
- 工具定义代码：TOOLS = [{type/function/name/description/parameters}] —— 来源 v2_with_tools.py L30-60
- 工具 1：bash_exec，description "在工作目录中执行 shell 命令" —— 来源 v2 L34-43
- 工具 2：file_write，description "在工作目录中创建或覆盖文件" —— 来源 v2 L45-58
- 关键论断："description 写得越清晰，LLM 选对工具的概率越高" —— 来源 article §2
- 执行器代码：execute_tool(name, args) 分支 bash_exec/file_write —— 来源 v2 L63-82
- bash_exec 实现：subprocess.run + returncode/stdout/stderr 字符串 —— 来源 v2 L66-73
- 隐式约定：not msg.tool_calls → 任务完成 —— 来源 article §2 / v2 L107
- 运行结果：Turn1 file_write → Turn2 bash_exec → Turn3 完成 —— 来源 article §2 / slides s7
- 隐患引子：LLM 出 bug 反复调同一工具停不下来 —— 来源 article §2 末

**开发计划**：

- step 1 (~9s) — 章节转场：接上章"需要一双手"，本章标题"要让它能做事，得解决三件事"
- step 2 (~11s) — 三件事总览，三行编号 ①②③ 一次列清（总览锚点，不是逐项清单）
- step 3 (~6s) — ① 高亮：告诉 LLM 有哪些工具（工具定义）
- step 4 (~14s) — 代码块揭示 TOOLS 定义：type / function / name=bash_exec / description / parameters
- step 5 (~8s) — 第二个工具 file_write 并列揭示，两个工具卡并排
- step 6 (~10s) — description 高亮金句："写得越清楚，选对工具概率越高"——拉框聚焦 description 字段
- step 7 (~6s) — ② 高亮：解析 LLM 返回的工具调用
- step 8 (~6s) — ③ 高亮：执行 + 回传结果
- step 9 (~16s) — execute_tool 代码揭示 bash_exec 分支（subprocess.run + returncode/stdout 拼串）
- step 10 (~12s) — execute_tool 代码揭示 file_write 分支（Path.write_text + 返回"已写入 N 字节"）
- step 11 (~10s) — 关键判断代码：if not msg.tool_calls: 任务完成——配旁注"不调工具 = 做完了"
- step 12 (~16s) — 模拟终端跑 v2：Turn1 file_write → Turn2 bash_exec → Turn3 完成，逐 Turn 揭示
- step 13 (~10s) — 隐患引子收尾：但万一 LLM 出 bug 一直调同一工具呢？引出下一章

口播节选：
> 要让它能做事，得解决三件事。第一，告诉 LLM 它有哪些工具……关键是那个 description……循环里还得加一个判断，不调工具就是做完了……但有个隐患，万一 LLM 出 bug 一直调同一个工具呢？

---

## 4. v3-evaluator — 装上刹车：Evaluator 三层（11 steps · ~103s）

**信息池**：
- 金句："没有刹车的 Agent 是危险的，不是它会伤害你，是它会烧光你的 token 账单" —— 来源 article §3
- 刹车 1：max_turns 硬上限，无论如何 —— 来源 article §3 / v3 L95-97
- 刹车 2：死循环检测，同一操作连续 3 次 —— 来源 article §3 / v3 L99-104
- 刹车 2 代码：md5(json.dumps(last_action, sort_keys=True)) + count(h) >= 2 —— 来源 v3 L101-103
- 刹车 3：self-critique（v3 先不做，下一课展开）—— 来源 article §3 / v3 L6 注释
- 核心论断："Agent 可不可靠不是看 LLM 有多强，是看 Evaluator 有多靠谱" —— 来源 article §3
- 死循环演示场景：反复跑不存在的命令（pip3 install magic）—— 来源 article §3 / slides s8
- 演示数字：可烧到 $47.83（slides.html s8 夸张演示）—— 来源 slides.html s8
- 文件名：v3_with_evaluator.py，约 110 行 —— 来源 article 收尾表 / slides s12

**开发计划**：

- step 1 (~12s) — 接上章隐患，hero 金句浮现："没有刹车的 Agent 会烧光你的 token"
- step 2 (~14s) — 死循环演示终端：同一 bash_exec("pip3 install magic") 连续失败多行，烧钱数字往上跳
- step 3 (~7s) — 章节标题：给它装三道刹车
- step 4 (~8s) — 刹车 1 高亮条 + 一行代码：if turn >= self.max_turns: return True, "max_turns"
- step 5 (~8s) — 刹车 2 高亮条：死循环检测，连续 3 次同一操作
- step 6 (~14s) — 刹车 2 代码揭示：md5 → count >= 2 → loop_detected，旁注"hash 一下，发现两次就停"
- step 7 (~16s) — 刹车 3 高亮条（虚化/待办样式）：self-critique，标注"下一课展开"
- step 8 (~10s) — 核心论断 hero 浮现：可靠性 ≠ LLM 更强 = Evaluator 更靠谱（天平/对比图演出）
- step 9 (~5s) — 死循环演示重来，第 3 次重复时 Evaluator 触发
- step 10 (~5s) — 红色"⚠ loop_detected"截断演出，对比无刹车的烧钱画面
- step 11 (~4s) — 文件角标：v3_with_evaluator.py · ~110 行 · 状态"会停"

口播节选：
> 没有刹车的 Agent 是危险的，不是它会伤害你，是它会烧光你的 token 账单。给它装三道刹车……Agent 可不可靠，不是看 LLM 有多强，是看 Evaluator 有多靠谱。

---

## 5. v4-observation — 看得懂结果：Observation 格式化（11 steps · ~62s）

**信息池**：
- 对比组 A（原始 JSON 成功）：{"ok": true, "exit_code": 0, "stdout": "hello world\n", ...} —— 来源 article §4 / slides s10
- 对比组 B（原始 JSON 失败）：{"ok": false, "error_type": "TimeoutExpired", "message": "超时 30s", ...} —— 来源 article §4 / slides s10
- 格式化后（失败）：[错误] bash_exec 失败: 命令超时(30s) —— 来源 article §4 / slides s10
- format_observation 代码：if not result.get("ok"): return f"[错误] ..." —— 来源 article §4 / v4_final.py L116-132
- v4 新增：execute_tool 改返回结构化 dict（ok/exit_code/stdout/stderr）—— 来源 v4 L83-112
- v4 新增工具：file_read —— 来源 v4 L66-80（口播没念，可挂角标补充信息密度）
- 核心论断："格式化的目标不是好看，是让 LLM 下一轮推理做出更好决策" —— 来源 article §4
- 预告：structured vs raw 后续 A/B 实验 —— 来源 article §4
- 文件名：v4_final.py，约 150 行 —— 来源 article 收尾表 / slides s12

**开发计划**：

- step 1 (~7s) — 章节标题：最后一个组件——Observation 格式化
- step 2 (~6s) — 问题抛出：工具执行完了，结果长什么样？
- step 3 (~5s) — 原始 JSON 成功样例出现（一坨），旁注"LLM 能看懂，但费劲"
- step 4 (~5s) — 原始 JSON 失败样例出现（更长更乱），旁注"出错时更费劲"
- step 5 (~6s) — 转场箭头/分隔：格式化之后呢？
- step 6 (~6s) — 格式化后一行出现：[错误] bash_exec 失败: 命令超时(30s)，对比反差强调
- step 7 (~14s) — format_observation 代码揭示：if not ok / bash_exec 分支 / file_write 分支
- step 8 (~5s) — 金句浮现："格式化的目标不是好看，是让 LLM 做出更好的下一步决策"
- step 9 (~4s) — 预告角标：structured vs raw 后续 A/B 实验（数据说话）
- step 10 (~2s) — file_read 工具角标（口播没念的新增工具，挂信息密度）
- step 11 (~2s) — 文件角标：v4_final.py · ~150 行 · 状态"完整 Agent"

口播节选：
> 工具执行完了，结果长什么样？直接把原始输出扔给 LLM，是这样一坨……格式化之后呢？[错误] bash_exec 失败: 命令超时。一目了然。格式化的目标不是好看，是让 LLM 做出更好的下一步决策。

---

## 6. recap — 四步演进总览（8 steps · ~44s）

**信息池**：
- v1：LLM 调用循环，能想不能做，~20 行 —— 来源 article 收尾表
- v2：+ 工具定义与执行，能做事，~80 行 —— 来源 article 收尾表
- v3：+ Evaluator 三层刹车，会停，~110 行 —— 来源 article 收尾表
- v4：+ Observation 格式化，看得懂结果，~150 行 —— 来源 article 收尾表
- 完整循环 5 节点图：①调 LLM → ②有 tool_calls? → ③执行工具 → ④格式化回传 → ⑤Evaluator 刹车 → 回 ① —— 来源 slides.html s11 SVG
- hero 收束数字：150 行，完整可运行 Code Agent —— 来源 article 收尾 §

**开发计划**：

- step 1 (~7s) — 章节标题：回顾，从一个空的 for 循环加了四层
- step 2 (~7s) — v1 行揭示：循环 + LLM 调用，tag"能想 / 不能做"，~20 行
- step 3 (~6s) — v2 行揭示：+ 工具定义与执行，tag"能做事"，~80 行（v1 行灰化保留）
- step 4 (~9s) — v3 行揭示：+ Evaluator 三层刹车，tag"会停"，~110 行
- step 5 (~8s) — v4 行揭示：+ Observation 格式化，tag"完整"，~150 行
- step 6 (~4s) — hero 收束数字 150 浮现：一个完整能跑的 Code Agent
- step 7 (~2s) — 完整循环 5 节点环形图演出（调 LLM / tool_calls? / 执行 / 格式化 / Evaluator）逐个点亮连线
- step 8 (~1s) — 过渡：给你留个思考题（引下一章）

口播节选：
> 回顾一下，从一个空的 for 循环加了四层东西。v1 能想不能做，v2 能做事，v3 会停，v4 看得懂结果。150 行，一个完整能跑的 Code Agent。

---

## 7. teaser — 思考题 + 下集预告（5 steps · ~65s）

**信息池**：
- 思考题：150 行 vs LangChain create_react_agent 5 行 —— 来源 article 收尾 §
- 对比指标：System Prompt 264 字符 vs 7,909 字符（30×）—— 来源 slides.html s13
- 对比指标：Input Tokens 2,508 vs 77,671（31×）—— 来源 slides.html s13
- 对比指标：轮次 3 vs 10（3.3×）—— 来源 slides.html s13
- 下集主题：LangChain deepagents 拆解 —— 来源 article 收尾 §
- 金句："框架帮你省掉了什么？又偷偷加了什么？" —— 来源 article 收尾 §
- 收束："这是抽象的代价" —— 来源 article 收尾 §
- CTA：代码在 GitHub 仓库 lesson1/code 目录，v1 到 v4 四个文件 —— 来源 article 收尾 §

**开发计划**：

- step 1 (~16s) — 思考题 hero：150 行 vs 5 行（LangChain create_react_agent），并排反差
- step 2 (~6s) — 金句浮现："省掉了什么？又偷偷加了什么？"
- step 3 (~27s) — 对比表演出：三行指标逐行揭示（System Prompt 30× / Token 31× / 轮次 3.3×），数字高亮
- step 4 (~10s) — 下集预告 hero："下一课，把框架一行一行拆开看"+ "这是抽象的代价"
- step 5 (~6s) — 收束 CTA：GitHub lesson1/code，v1~v4，照着敲一遍。"下期见。"

口播节选：
> 给你留个思考题。这 150 行，用 LangChain 的 create_react_agent 写大概 5 行就够。那它帮你省掉了什么？又偷偷加了什么？下一课我们把同样的任务用 LangChain 跑一遍……这就是抽象的代价。代码在 GitHub lesson1/code 目录下，下期见。

---

## 素材清单

### 1. coldopen
- ✓ v4 完整运行终端日志（Turn 1/2/3 + 统计）—— 来源 slides.html s2 可直接参考文本结构
- ⚠️ 实拍终端录屏（可选，用 CSS 模拟终端更可控，建议纯 CSS 演出）
- ✓ 三个 AI coding agent 名（Cursor / Claude Code / Cline）—— 用文字即可，不强行找 logo

### 2. v1-bare
- ✓ v1 核心循环代码 4 行 —— 来源 v1_bare_loop.py L25-35
- ✓ v1 SYSTEM_PROMPT 文本 —— 来源 v1_bare_loop.py L19
- ⚠️ "椅子+门"比喻插画 —— 建议用极简 SVG/ASCII 演出落空的关门动作，不用真插画
- ✓ v1 终端失败演出 —— 来源 slides.html s4

### 3. v2-tools
- ✓ TOOLS 定义代码 —— 来源 v2_with_tools.py L30-60
- ✓ execute_tool 代码 —— 来源 v2_with_tools.py L63-82
- ✓ not msg.tool_calls 判断代码 —— 来源 v2_with_tools.py L107
- ✓ v2 运行终端演出 —— 来源 slides.html s7

### 4. v3-evaluator
- ✓ Evaluator.should_stop 代码 —— 来源 v3_with_evaluator.py L88-106
- ✓ 死循环演示文本（pip3 install magic 反复失败）—— 来源 slides.html s8
- ✓ md5 死循环检测代码 —— 来源 v3_with_evaluator.py L101-103

### 5. v4-observation
- ✓ 原始 JSON 成功/失败样例 —— 来源 article §4 / slides.html s10
- ✓ format_observation 代码 —— 来源 v4_final.py L116-132
- ✓ 格式化后对比文本 —— 来源 article §4

### 6. recap
- ✓ 四版本对比表 —— 来源 article 收尾表 / slides.html s12
- ✓ 完整循环 5 节点 SVG 图 —— 来源 slides.html s11（作结构参考，用主题 token 重画）

### 7. teaser
- ✓ 框架对比表（System Prompt / Token / 轮次 三指标）—— 来源 slides.html s13
- ✓ 三个对比数字 30× / 31× / 3.3× —— 来源 slides.html s13
- ⚠️ GitHub 仓库链接/截图 —— 用文字 CTA 即可，不强行做截图

---

## 关于主题的备注（给 Checkpoint Plan）

原 slides.html 是一套**复古像素 CRT** 风格（Press Start 2P + VT323 字体，
深海军蓝 #1a1a2e + 红/绿/黄三色 + CRT 扫描线）。这是一套强烈的个人风格。

web-video-presentation 内置主题里没有"像素 CRT"主题，最接近的三条路：

- **terminal-green（终端绿）**：纯黑底 + 磷光绿 + 等宽字体，黑客/终端气质，
  跟"代码教学 + 终端演示"高度契合，是技术教程的安全牌。**与原 slides 气质最近。**
- **blueprint（蓝图）**：深藏青 + 青色 + IBM Plex Mono，工程图纸气质，
  适合"系统拆解"叙事，比 terminal-green 更冷静克制
- **neon-cyber（霓虹赛博）**：深海军底 + 电光青 + 玫红双霓虹，赛博朋克未来派，
  视觉冲击最强但偏"AI 评测"调性，技术教程用它略浮夸

第四种：复用原 slides.html 的像素 CRT 风格，**新做一套自定义主题**
（详见 themes/THEMES.md 创作流程），保留 Press Start 2P / VT323 + 扫描线。
工作量更大但风格延续性最强。
