import type { Narration } from "../../registry/types";

/**
 * Chapter 7 · teaser — 思考题 + 下集预告
 *
 * 5 steps · ~65s
 * 口播文本是音频合成 + Auto 模式自动推进的唯一真相源。
 * step 索引 0-based；数组长度 = 章节步数。
 * 文本与 script.md 对应段落语义一致（可为 TTS 微调标点断句）。
 *
 * 注：对比数据（30×/31×/3.3×）来自仓库 deepagent/agent.py（LangChain
 * deepagents 薄包装）vs handroll/ 的真实测量值，非编造。teaser 保留
 * LangChain 正是因为这组数据是 LangChain 特定的。
 */
export const narrations: Narration[] = [
  // step 0 (~16s) — 思考题 hero：150 行 vs 5 行反差
  "给你留个思考题。这 150 行，用 LangChain 的 create_react_agent 写，大概 5 行就够。",

  // step 1 (~6s) — 金句
  "那它帮你省掉了什么？又偷偷加了什么？",

  // step 2 (~27s) — 对比表三行指标逐行揭示
  "下一课我们把同样的任务用 LangChain 跑一遍。你会发现，框架的 system prompt 比我们手写的长 30 倍，token 消耗高 31 倍，干的活却一样。",

  // step 3 (~10s) — 下集预告 + 抽象的代价
  "这就是抽象的代价。下一课，把框架一行一行拆开看。",

  // step 4 (~6s) — CTA 收束
  "代码在 GitHub 仓库 lesson1/code 目录下，v1 到 v4 四个文件，照着敲一遍就懂了。下期见。",
];
