import type { Narration } from "../../registry/types";

/**
 * Chapter 4 · v3-evaluator — 装上刹车：Evaluator 三层
 *
 * 11 steps · ~103s
 * 口播文本是音频合成 + Auto 模式自动推进的唯一真相源。
 * step 索引 0-based；数组长度 = 章节步数。
 * 文本与 script.md 对应段落语义一致（可为 TTS 微调标点断句）。
 */
export const narrations: Narration[] = [
  // step 0 (~12s) — 接上章隐患，hero 金句：会烧光 token
  "没有刹车的 Agent 是危险的。不是它会伤害你，是它会烧光你的 token 账单。",

  // step 1 (~14s) — 死循环演示终端：反复 pip3 install magic 失败，烧钱数字跳
  "你看，构造一个一定失败的命令。LLM 反复重试，一直跑下去，钱就这么烧没了。",

  // step 2 (~7s) — 章节标题：给它装三道刹车
  "给它装三道刹车。",

  // step 3 (~8s) — 刹车 1：max_turns 硬上限 + 代码
  "第一道，硬上限。max_turns 到了就停，无论如何。这是最后那根保险丝。",

  // step 4 (~8s) — 刹车 2 高亮：死循环检测
  "第二道，死循环检测。同一个操作连续出现三次，强制停。",

  // step 5 (~14s) — 刹车 2 代码：md5 + count >= 2 + loop_detected
  "实现就是把每次操作 hash 一下存起来。发现这个 hash 已经出现两次，就停。",

  // step 6 (~16s) — 刹车 3 高亮（虚化）：self-critique，下一课展开
  "第三道更高级，self-critique。再开一次 LLM 调用，问它任务做完了吗。这条 v3 先不做，留到下一课。",

  // step 7 (~10s) — 核心论断 hero：可靠性 ≠ LLM 更强 = Evaluator 更靠谱
  "有个点你得记住。Agent 可不可靠，不是看 LLM 有多强，是看 Evaluator 有多靠谱。",

  // step 8 (~5s) — 死循环演示重来，第 3 次 Evaluator 触发
  "再看刚才那个死循环。这回有了 Evaluator。",

  // step 9 (~5s) — 红色 loop_detected 截断，对比无刹车的烧钱
  "三次重复，自动停。账单截住了。",

  // step 10 (~4s) — 文件角标：v3_with_evaluator.py · ~110 行 · 会停
  "这就是 v3，v3_with_evaluator.py，约 110 行。它会停了。",
];
