import type { ChapterDef } from "./types";
import Coldopen from "../chapters/01-coldopen/Coldopen";
import { narrations as coldopenNarrations } from "../chapters/01-coldopen/narrations";
import BareLoop from "../chapters/02-bare-loop/BareLoop";
import { narrations as bareLoopNarrations } from "../chapters/02-bare-loop/narrations";

export const CHAPTERS: ChapterDef[] = [
  {
    id: "coldopen",
    title: "开场 Hook",
    narrations: coldopenNarrations,
    Component: Coldopen,
  },
  {
    id: "bare-loop",
    title: "最简循环：能想不能做",
    narrations: bareLoopNarrations,
    Component: BareLoop,
  },
];
