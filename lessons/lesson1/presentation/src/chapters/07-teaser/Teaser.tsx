import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Teaser.css";

/**
 * Chapter 7 · teaser — 思考题 + 下集预告
 *
 * 5 steps（0-based step 0..4），节奏跟 narrations.ts：
 *   0   思考题 hero：150 行 vs 5 行反差
 *   1   金句：省掉了什么？又偷偷加了什么？
 *   2   对比表三行指标逐行揭示（30× / 31× / 3.3×）
 *   3   下集预告 + 抽象的代价
 *   4   CTA 收束
 *
 * 视觉演示（CHAPTER-CRAFT.md 底线）：150 vs 5 并排反差 + 对比表逐行揭示 +
 * 抽象代价 hero。颜色/字体全走 token。
 *
 * 注：对比数据来自仓库 deepagent/ vs handroll/ 真实测量，非编造。
 */
export default function Teaser({ step }: ChapterStepProps) {
  return (
    <div className="ts-stage">
      {step === 0 && <PuzzleStep />}
      {step === 1 && <GoldenQStep />}
      {step === 2 && <CompareTableStep />}
      {step === 3 && <NextLessonStep />}
      {step === 4 && <CtaStep />}
    </div>
  );
}

/* ─── step 0：思考题 150 vs 5 ─── */
function PuzzleStep() {
  return (
    <div className="ts-puzzle">
      <div className="ts-puzzle-label">思考题</div>
      <div className="ts-puzzle-row">
        <div className="ts-puzzle-side ts-puzzle-handroll">
          <div className="ts-puzzle-num hero-num">150</div>
          <div className="ts-puzzle-unit">行 · 手写</div>
        </div>
        <div className="ts-puzzle-vs">vs</div>
        <div className="ts-puzzle-side ts-puzzle-langchain">
          <div className="ts-puzzle-num hero-num">5</div>
          <div className="ts-puzzle-unit">
            行 · <span className="ts-puzzle-lc">LangChain</span>
          </div>
          <div className="ts-puzzle-fn">create_react_agent</div>
        </div>
      </div>
    </div>
  );
}

/* ─── step 1：金句 ─── */
function GoldenQStep() {
  return (
    <div className="ts-golden">
      <div className="ts-golden-q1">
        省掉了<span className="ts-golden-hl">什么？</span>
      </div>
      <div className="ts-golden-q2">
        又偷偷加了<span className="ts-golden-hl2">什么？</span>
      </div>
    </div>
  );
}

/* ─── step 2：对比表 ─── */
const COMPARE_ROWS = [
  { metric: "System Prompt", handroll: "264 字符", framework: "7,909 字符", ratio: "30×" },
  { metric: "Input Tokens", handroll: "2,508", framework: "77,671", ratio: "31×" },
  { metric: "轮次", handroll: "3", framework: "10", ratio: "3.3×" },
];

function CompareTableStep() {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const timers = [1, 2, 3].map((n) =>
      setTimeout(() => setShown(n), 400 + n * 900)
    );
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <div className="ts-compare">
      <div className="ts-compare-head">
        <span className="ts-ch-metric">指标</span>
        <span className="ts-ch-hand">手写</span>
        <span className="ts-ch-frame">框架</span>
        <span className="ts-ch-ratio">差距</span>
      </div>
      {COMPARE_ROWS.map((row, i) => (
        <CompareRow key={row.metric} row={row} shown={i < shown} index={i} />
      ))}
      <div className={`ts-compare-note ${shown >= 3 ? "is-up" : ""}`}>
        干的活<span className="ts-compare-same">一样</span>
      </div>
    </div>
  );
}

function CompareRow({
  row,
  shown,
  index,
}: {
  row: (typeof COMPARE_ROWS)[number];
  shown: boolean;
  index: number;
}) {
  const [up, setUp] = useState(false);
  useEffect(() => {
    if (shown) {
      const t = setTimeout(() => setUp(true), 60);
      return () => clearTimeout(t);
    }
  }, [shown]);
  if (!shown) return null;
  return (
    <div
      className={`ts-crow ${up ? "is-up" : ""}`}
      style={{ transitionDelay: `${index * 40}ms` }}
    >
      <span className="ts-cd-metric">{row.metric}</span>
      <span className="ts-cd-hand">{row.handroll}</span>
      <span className="ts-cd-frame">{row.framework}</span>
      <span className="ts-cd-ratio hero-num">{row.ratio}</span>
    </div>
  );
}

/* ─── step 3：下集预告 + 抽象的代价 ─── */
function NextLessonStep() {
  return (
    <div className="ts-next">
      <div className="ts-next-tag">下一课</div>
      <div className="ts-next-main">把框架一行一行拆开看</div>
      <div className="ts-next-cost">
        这是<span className="ts-next-hl">抽象的代价</span>
      </div>
    </div>
  );
}

/* ─── step 4：CTA ─── */
function CtaStep() {
  return (
    <div className="ts-cta">
      <div className="ts-cta-path">
        <span className="ts-cta-bracket">[</span>
        <span className="ts-cta-repo">github</span>
        <span className="ts-cta-sep">/</span>
        <span className="ts-cta-dir">lesson1</span>
        <span className="ts-cta-sep">/</span>
        <span className="ts-cta-dir">code</span>
        <span className="ts-cta-bracket">]</span>
      </div>
      <div className="ts-cta-files">v1 → v2 → v3 → v4</div>
      <div className="ts-cta-action">照着敲一遍就懂了</div>
      <div className="ts-cta-bye">下期见。</div>
    </div>
  );
}
