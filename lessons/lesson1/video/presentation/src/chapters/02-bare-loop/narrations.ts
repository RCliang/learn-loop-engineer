import type { Narration } from "../../registry/types";

export const narrations: Narration[] = [
  // step 0 — editor: start from scratch
  "好，打开编辑器，我们从零开始。一个 Agent 最核心的结构是什么？就是一个循环——反复调 LLM，直到任务完成。",
  // step 1 — code reveal: for / create / append
  "for turn in range max_turns，调一次 LLM，拿到回复，追加到消息列表里。就这几行，这就是 v1。",
  // step 2 — terminal run v1: nothing happens
  "我们跑一下看看什么效果。你看，LLM 很努力地告诉你「我帮你创建了 hello.py」，但实际上什么都没发生。因为它只能说话，不能动手。",
  // step 3 — metaphor: saying door is closed
  "这就像一个人坐在椅子上告诉你「我帮你把门关了」——嘴上说完了，门还开着。",
  // step 4 — conclusion: agent needs hands
  "此时的问题很明确：Agent 需要「手」。",
];
