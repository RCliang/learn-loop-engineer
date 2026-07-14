import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Recap.css";

/**
 * Chapter 6 · recap — 四步演进总览
 *
 * 8 steps（0-based step 0..7），节奏跟 narrations.ts：
 *   0   章节标题
 *   1   v1 行揭示（循环 + 能想/不能做 + ~20 行）
 *   2   v2 行揭示（+ 工具 + 能做事 + ~80 行）
 *   3   v3 行揭示（+ Evaluator + 会停 + ~110 行）
 *   4   v4 行揭示（+ Observation + 完整 + ~150 行）
 *   5   hero 收束数字 150
 *   6   5 节点环形图
 *   7   过渡引下一章
 *
 * 视觉演示（CHAPTER-CRAFT.md 底线）：四行版本渐进揭示 + hero 150 +
 * 5 节点循环 SVG。颜色/字体全走 token。
 */
export default function Recap({ step }: ChapterStepProps) {
  return (
    <div className="rc-stage">
      {step === 0 && <TitleStep />}
      {step >= 1 && step <= 4 && <VersionTableStep active={step} />}
      {step === 5 && <Hero150Step />}
      {step === 6 && <RingStep />}
      {step === 7 && <TransitionStep />}
    </div>
  );
}

/* ─── step 0：标题 ─── */
function TitleStep() {
  return (
    <div className="rc-title">
      <div className="rc-title-kicker">回顾</div>
      <div className="rc-title-main">从一个空的 for 循环</div>
      <div className="rc-title-em">加了四层东西</div>
    </div>
  );
}

/* ─── step 1~4：四行版本表渐进揭示 ─── */
const VERSIONS = [
  { v: "v1", add: "LLM 调用循环", tag: "能想", tagSub: "不能做", lines: "~20 行", color: "text-faint" },
  { v: "v2", add: "+ 工具定义与执行", tag: "能做事", tagSub: "", lines: "~80 行", color: "mint" },
  { v: "v3", add: "+ Evaluator 三层刹车", tag: "会停", tagSub: "", lines: "~110 行", color: "amber" },
  { v: "v4", add: "+ Observation 格式化", tag: "看得懂结果", tagSub: "", lines: "~150 行", color: "accent" },
];

function VersionTableStep({ active }: { active: number }) {
  return (
    <div className="rc-table">
      <div className="rc-table-head">
        <span className="rc-th-v">版本</span>
        <span className="rc-th-add">加入能力</span>
        <span className="rc-th-tag">状态</span>
        <span className="rc-th-lines">行数</span>
      </div>
      {VERSIONS.map((row, i) => {
        const shown = i < active;
        const isCurrent = i === active - 1;
        return (
          <VersionRow key={row.v} row={row} shown={shown} current={isCurrent} index={i} />
        );
      })}
    </div>
  );
}

function VersionRow({
  row,
  shown,
  current,
  index,
}: {
  row: (typeof VERSIONS)[number];
  shown: boolean;
  current: boolean;
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
      className={`rc-row ${up ? "is-up" : ""} ${current ? "is-current" : "is-past"}`}
      data-color={row.color}
      style={{ transitionDelay: `${index * 40}ms` }}
    >
      <span className="rc-td-v">{row.v}</span>
      <span className="rc-td-add">{row.add}</span>
      <span className="rc-td-tag">
        {row.tag}
        {row.tagSub && <span className="rc-td-tagsub"> / {row.tagSub}</span>}
      </span>
      <span className="rc-td-lines">{row.lines}</span>
    </div>
  );
}

/* ─── step 5：hero 150 ─── */
function Hero150Step() {
  const [n, setN] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const dur = 700;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      setN(Math.round(eased * 150));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, []);
  return (
    <div className="rc-hero150">
      <div className="rc-hero150-kicker">一个完整能跑的 Code Agent</div>
      <div className="rc-hero150-num hero-num">{n}</div>
      <div className="rc-hero150-unit">行 Python</div>
    </div>
  );
}

/* ─── step 6：5 节点环形图 ─── */
function RingStep() {
  const [lit, setLit] = useState(0);
  useEffect(() => {
    const timers = [1, 2, 3, 4, 5].map((n) =>
      setTimeout(() => setLit(n), 200 + n * 380)
    );
    return () => timers.forEach(clearTimeout);
  }, []);
  const nodes = [
    { n: 1, label: "调 LLM" },
    { n: 2, label: "有 tool_calls?" },
    { n: 3, label: "执行工具" },
    { n: 4, label: "格式化回传" },
    { n: 5, label: "Evaluator" },
  ];
  return (
    <div className="rc-ring">
      <svg className="rc-ring-svg" viewBox="0 0 600 600" role="img" aria-label="完整循环">
        {/* 环形连线 */}
        {nodes.map((_, i) => {
          const angle = (i / nodes.length) * 360 - 90;
          const next = ((i + 1) / nodes.length) * 360 - 90;
          const r = 220;
          const x1 = 300 + r * Math.cos((angle * Math.PI) / 180);
          const y1 = 300 + r * Math.sin((angle * Math.PI) / 180);
          const x2 = 300 + r * Math.cos((next * Math.PI) / 180);
          const y2 = 300 + r * Math.sin((next * Math.PI) / 180);
          return (
            <line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              className={`rc-ring-line ${lit > i + 1 ? "is-lit" : ""}`}
            />
          );
        })}
        {/* 节点 */}
        {nodes.map((node, i) => {
          const angle = (i / nodes.length) * 360 - 90;
          const r = 220;
          const x = 300 + r * Math.cos((angle * Math.PI) / 180);
          const y = 300 + r * Math.sin((angle * Math.PI) / 180);
          return (
            <g
              key={node.n}
              transform={`translate(${x}, ${y})`}
              className={`rc-ring-node ${lit >= node.n ? "is-lit" : ""}`}
            >
              <circle r="56" />
              <text textAnchor="middle" dy="-4" className="rc-ring-node-n">
                {node.n}
              </text>
              <text textAnchor="middle" dy="22" className="rc-ring-node-label">
                {node.label}
              </text>
            </g>
          );
        })}
        {/* 中心 */}
        <text x="300" y="296" textAnchor="middle" className="rc-ring-center">
          for
        </text>
        <text x="300" y="332" textAnchor="middle" className="rc-ring-center">
          循环
        </text>
      </svg>
    </div>
  );
}

/* ─── step 7：过渡 ─── */
function TransitionStep() {
  return (
    <div className="rc-trans">
      <div className="rc-trans-q">给你留个思考题</div>
      <div className="rc-trans-cursor" aria-hidden />
    </div>
  );
}
