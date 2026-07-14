import type { Narration } from "../../registry/types";

/**
 * Chapter 6 · recap — 四步演进总览
 *
 * 8 steps · ~44s
 * 口播文本是音频合成 + Auto 模式自动推进的唯一真相源。
 * step 索引 0-based；数组长度 = 章节步数。
 * 文本与 script.md 对应段落语义一致（可为 TTS 微调标点断句）。
 */
export const narrations: Narration[] = [
  // step 0 (~7s) — 章节标题
  "回顾一下。从一个空的 for 循环，加了四层东西。",

  // step 1 (~7s) — v1 行
  "第一层，v1，LLM 调用循环。能想，不能做。",

  // step 2 (~6s) — v2 行
  "第二层，v2，加上工具定义和执行。能做事了。",

  // step 3 (~9s) — v3 行
  "第三层，v3，Evaluator 三道刹车。知道什么时候该停。",

  // step 4 (~8s) — v4 行
  "第四层，v4，Observation 格式化。看得懂结果。",

  // step 5 (~4s) — hero 150
  "150 行，一个完整能跑的 Code Agent。",

  // step 6 (~2s) — 5 节点环形图
  "整个循环就是这样：调 LLM，有工具调用就执行，格式化，Evaluator 把关，再回去。",

  // step 7 (~1s) — 过渡引下一章
  "给你留个思考题。",
];
