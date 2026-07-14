import type { Narration } from "../../registry/types";

/**
 * Chapter 3 · v2-tools — 给 Agent 装上手：工具三件事
 *
 * 13 steps · ~134s
 * 口播文本是音频合成 + Auto 模式自动推进的唯一真相源。
 * step 索引 0-based；数组长度 = 章节步数。
 * 文本与 script.md 对应段落语义一致（可为 TTS 微调标点断句）。
 */
export const narrations: Narration[] = [
  // step 0 (~9s) — 转场：接上章"需要一双手"，本章标题"得解决三件事"
  "问题很明确，Agent 需要一双手。要让它能做事，得解决三件事。",

  // step 1 (~11s) — 三件事总览：①②③ 一次列清
  "第一，告诉 LLM 它有哪些工具。第二，解析它返回的工具调用。第三，执行，把结果回传给它。",

  // step 2 (~6s) — ① 高亮
  "先看第一件。告诉 LLM 它有哪些工具——这就是工具定义。",

  // step 3 (~14s) — TOOLS 代码揭示：bash_exec 的 name/description/parameters
  "这是一段 JSON Schema。type，function，name 叫 bash_exec，description 说在工作目录执行 shell 命令。",

  // step 4 (~8s) — 第二个工具 file_write 并列揭示
  "再加一个 file_write，能创建或覆盖文件。两个工具，并排放着。",

  // step 5 (~10s) — description 金句高亮
  "关键是那个 description。写得越清楚，LLM 选对工具的概率越高。",

  // step 6 (~6s) — ② 高亮
  "第二件，解析 LLM 返回的工具调用。它说要调 file_write，你得接得住。",

  // step 7 (~6s) — ③ 高亮
  "第三件，执行，然后把结果回传给 LLM。",

  // step 8 (~16s) — execute_tool bash_exec 分支代码
  "执行器长这样。bash_exec 这条分支，subprocess.run 跑命令，把退出码和输出拼成字符串返回。",

  // step 9 (~12s) — execute_tool file_write 分支代码
  "file_write 这条分支，write_text 写文件，回一句已写入多少字节。",

  // step 10 (~10s) — 完成判断代码
  "循环里还得加一个判断。当 LLM 不再调用任何工具，就表示任务做完了。这是 function calling 的隐式约定。",

  // step 11 (~16s) — 终端跑 v2：Turn1 file_write → Turn2 bash_exec → Turn3 完成
  "跑一下 v2。Turn 1 调 file_write 写文件，Turn 2 调 bash_exec 运行，Turn 3 看输出对，不再调工具，结束。能做事了。",

  // step 12 (~10s) — 隐患引子收尾
  "但有个隐患。万一 LLM 出 bug，一直不停调同一个工具呢？这就引出下一个组件。",
];
