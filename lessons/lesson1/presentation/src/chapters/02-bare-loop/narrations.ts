import type { Narration } from "../../registry/types";

/**
 * Chapter 2 · v1-bare — 最小循环：能想，不能做
 *
 * 8 steps · ~52s
 * 口播文本是音频合成 + Auto 模式自动推进的唯一真相源。
 * step 索引 0-based；数组长度 = 章节步数。
 * 文本与 script.md 对应段落语义一致（可为 TTS 微调标点断句）。
 */
export const narrations: Narration[] = [
  // step 0 (~9s) — 章节标题转场：从零开始，最核心的结构是什么
  "打开编辑器，从零开始。一个 Agent 最核心的结构，到底是什么？",

  // step 1 (~6s) — hero "就是一个循环" + 循环箭头意象
  "就是一个循环。反复调 LLM，直到任务做完。",

  // step 2 (~7s) — 代码块前 2 行揭示：for + resp
  "就这几行。先看前半部分：一个 for 循环，每轮调一次 LLM，拿到回复。",

  // step 3 (~7s) — 代码块后 2 行揭示：reply + append，完整循环
  "再把回复塞回消息列表，下一轮 LLM 就能看到之前说过什么。整个 v1 就这么多。",

  // step 4 (~5s) — 文件角标：v1_bare_loop.py · ~20 行 · 能想/不能做
  "这就是 v1，v1_bare_loop.py，算上配置大概 20 行。它能想，不能做。",

  // step 5 (~6s) — 终端跑 python，LLM 说做了但实际没做
  "我们跑一下。LLM 很努力地说，我帮你创建了 hello.py。但实际什么都没发生。",

  // step 6 (~7s) — 椅子+门比喻
  "就像一个人坐在椅子上跟你说，我帮你把门关了。话说完了，门还开着。",

  // step 7 (~5s) — 结论：需要"手"
  "问题很明确。Agent 需要一双手。",
];
