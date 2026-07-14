import type { ChapterDef } from "./types";
import Coldopen from "../chapters/01-coldopen/Coldopen";
import { narrations as coldopenNarrations } from "../chapters/01-coldopen/narrations";
import BareLoop from "../chapters/02-bare-loop/BareLoop";
import { narrations as bareLoopNarrations } from "../chapters/02-bare-loop/narrations";
import Tools from "../chapters/03-tools/Tools";
import { narrations as toolsNarrations } from "../chapters/03-tools/narrations";
import Evaluator from "../chapters/04-evaluator/Evaluator";
import { narrations as evaluatorNarrations } from "../chapters/04-evaluator/narrations";
import Observation from "../chapters/05-observation/Observation";
import { narrations as observationNarrations } from "../chapters/05-observation/narrations";
import Recap from "../chapters/06-recap/Recap";
import { narrations as recapNarrations } from "../chapters/06-recap/narrations";
import Teaser from "../chapters/07-teaser/Teaser";
import { narrations as teaserNarrations } from "../chapters/07-teaser/narrations";

/**
 * Order = order of presentation.
 *
 * Each chapter MUST provide a `narrations: Narration[]` array. Its length
 * is the chapter's step count — there is no `totalSteps` to maintain
 * separately. This guarantees the audio synthesis pipeline, the runtime
 * stepper, and the chapter `.tsx` switch on `step` cannot drift apart.
 *
 * Visual styling (color, fonts) comes entirely from the active theme —
 * chapters never hard-code palette / font names. See THEMES.md.
 */
export const CHAPTERS: ChapterDef[] = [
  {
    id: "coldopen",
    title: "先看效果：一个能自己干活的程序",
    narrations: coldopenNarrations,
    Component: Coldopen,
  },
  {
    id: "bare-loop",
    title: "最小循环：能想，不能做",
    narrations: bareLoopNarrations,
    Component: BareLoop,
  },
  {
    id: "tools",
    title: "给 Agent 装上手：工具三件事",
    narrations: toolsNarrations,
    Component: Tools,
  },
  {
    id: "evaluator",
    title: "装上刹车：Evaluator 三层",
    narrations: evaluatorNarrations,
    Component: Evaluator,
  },
  {
    id: "observation",
    title: "看得懂结果：Observation 格式化",
    narrations: observationNarrations,
    Component: Observation,
  },
  {
    id: "recap",
    title: "四步演进总览",
    narrations: recapNarrations,
    Component: Recap,
  },
  {
    id: "teaser",
    title: "思考题 + 下集预告",
    narrations: teaserNarrations,
    Component: Teaser,
  },
];
