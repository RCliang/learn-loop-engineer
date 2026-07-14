import type { Narration } from "../../registry/types";

/**
 * Chapter 5 · v4-observation — 看得懂结果：Observation 格式化
 *
 * 11 steps · ~62s
 * 口播文本是音频合成 + Auto 模式自动推进的唯一真相源。
 * step 索引 0-based；数组长度 = 章节步数。
 * 文本与 script.md 对应段落语义一致（可为 TTS 微调标点断句）。
 */
export const narrations: Narration[] = [
  // step 0 (~7s) — 章节标题：最后一个组件
  "最后一个组件。Observation 格式化。",

  // step 1 (~6s) — 问题抛出
  "工具执行完了，结果长什么样？",

  // step 2 (~5s) — 原始 JSON 成功样例（一坨）
  "直接把 subprocess 的原始输出扔给 LLM，是这样一坨。",

  // step 3 (~5s) — 原始 JSON 失败样例（更乱）
  "LLM 能看懂吗？能，但费劲。尤其出错的时候。",

  // step 4 (~6s) — 转场：格式化之后呢？
  "格式化之后呢？",

  // step 5 (~6s) — 格式化后一行，对比反差
  "[错误] bash_exec 失败，命令超时。一目了然。LLM 立刻知道发生了什么、下一步该怎么处理。",

  // step 6 (~14s) — format_observation 代码揭示
  "format_observation 干的就是这件事。ok 是 false 就报错，是 bash_exec 就给退出码和输出，是 file_write 就说写了多少字节。",

  // step 7 (~5s) — 金句
  "格式化的目标不是好看，是让 LLM 做出更好的下一步决策。",

  // step 8 (~4s) — 预告角标
  "structured 还是 raw，这件事后面我们会做 A/B 实验，拿数据说话。",

  // step 9 (~2s) — file_read 角标
  "另外 v4 还加了一个 file_read 工具，能读文件了。",

  // step 10 (~2s) — 文件角标
  "这就是 v4，v4_final.py，约 150 行。一个完整的 Agent。",
];
