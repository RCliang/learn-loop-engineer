import type { Narration } from "../../registry/types";

/**
 * Chapter 1 · coldopen — 先看效果：一个能自己干活的程序
 *
 * 8 steps · ~80s
 * 口播文本是音频合成 + Auto 模式自动推进的唯一真相源。
 * step 索引 0-based；数组长度 = 章节步数。
 * 文本与 script.md 对应段落语义一致（可为 TTS 微调标点断句）。
 */
export const narrations: Narration[] = [
  // step 0 (~3s) — hero 大字开场"先看个东西"
  "先看个东西。",

  // step 1 (~11s) — 任务输入：创建 hello.py 并运行它
  "我给这个程序一个任务。就一句话：创建一个 hello.py 文件，然后运行它。",

  // step 2 (~15s) — Turn 1 演出：思考 + file_write
  "它自己想了一下，调了个工具写了文件。",

  // step 3 (~15s) — Turn 2 bash_exec + Turn 3 完成
  "又调了个工具运行文件。看到输出是 hello world，判断任务做完了。",

  // step 4 (~6s) — 数据条：3 轮 / 2 次工具调用
  "三轮对话，两次工具调用。整个过程没人插手。",

  // step 5 (~8s) — hero 数字 150 行
  "这个 Agent 的核心代码，150 行 Python。",

  // step 6 (~7s) — 反差铺垫
  "而且这件事可能跟你的直觉不一样。",

  // step 7 (~15s) — 三个 AI coding agent 名 + "for 循环" 金句
  "市面上你天天在用的 AI coding agent——Cursor、Claude Code、Cline——剥到底，核心都是一个 for 循环。",
];
