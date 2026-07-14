import type { Narration } from "../../registry/types";

export const narrations: Narration[] = [
  // step 0 — terminal demo: agent executing task
  "大家好，从今天开始我们做一个系列——从零构建 Agent 应用。先看一个效果：我给 Agent 一个任务——创建一个 hello.py 文件，然后运行它。你看，它自己思考了一下，调了 file_write 写了文件，然后调了 bash_exec 运行，看到输出是 hello world，判断任务完成了。",
  // step 1 — stats card: 3 turns / 2 tools / 150 lines
  "整个过程 3 轮对话，2 次工具调用。这个 Agent 的核心代码，只有 150 行。",
  // step 2 — hero statement: all frameworks = for loop
  "而且，市面上所有 Agent 框架——LangChain、CrewAI、AutoGen——它们的核心，都是一个 for 循环。",
  // step 3 — transition: today's journey
  "今天我们就从一个空的 for 循环开始，一步步把它变成刚才你看到的这个 Agent。",
];
