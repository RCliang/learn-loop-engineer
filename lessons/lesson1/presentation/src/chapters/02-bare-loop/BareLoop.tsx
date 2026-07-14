import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./BareLoop.css";

/**
 * Chapter 2 · v1-bare — 最小循环：能想，不能做
 *
 * 8 steps（0-based step 0..7），节奏跟 narrations.ts：
 *   0  转场标题：从零开始，最核心的结构是什么
 *   1  hero "就是一个循环" + 循环箭头意象（SVG 旋转）
 *   2  代码前 2 行揭示（for / resp）
 *   3  代码后 2 行揭示（reply / append），完整 v1 循环
 *   4  文件角标：v1_bare_loop.py · ~20 行 · 能想/不能做
 *   5  终端跑 python，LLM 说做了但实际没做
 *   6  椅子+门比喻（SVG）
 *   7  结论：需要"手"
 *
 * 视觉演示（CHAPTER-CRAFT.md 底线）：循环箭头 SVG + 代码逐行揭示 + 终端
 * 跑空 + 比喻 SVG。颜色/字体全走 token，不硬编码 hex/字体名。
 */
export default function BareLoop({ step }: ChapterStepProps) {
  return (
    <div className="bl-stage">
      {step === 0 && <TitleStep />}
      {step === 1 && <LoopHeroStep />}
      {step === 2 && <CodeStep revealedLines={2} />}
      {step === 3 && <CodeStep revealedLines={4} />}
      {step === 4 && <FileInfoStep />}
      {step === 5 && <TerminalRunStep />}
      {step === 6 && <MetaphorStep />}
      {step === 7 && <HandsStep />}
    </div>
  );
}

/* ─── step 0：章节转场标题 ─── */
function TitleStep() {
  return (
    <div className="bl-title">
      <div className="bl-title-kicker">v1 · 从零开始</div>
      <div className="bl-title-q">一个 Agent 最核心的结构</div>
      <div className="bl-title-q bl-title-em">到底是什么？</div>
      <div className="bl-title-cursor" aria-hidden />
    </div>
  );
}

/* ─── step 1：hero "就是一个循环" + 旋转循环箭头 ─── */
function LoopHeroStep() {
  return (
    <div className="bl-loop">
      <LoopGlyph />
      <div className="bl-loop-text">
        就是一个<span className="bl-loop-hl">循环</span>
      </div>
      <div className="bl-loop-sub">反复调 LLM，直到任务做完</div>
    </div>
  );
}

/* 旋转的循环箭头 SVG —— 三段弧 + 三个箭头，arcade 旋转 */
function LoopGlyph() {
  const arcs = [0, 120, 240];
  return (
    <svg
      className="bl-loop-glyph"
      viewBox="0 0 200 200"
      role="img"
      aria-label="循环箭头"
    >
      {arcs.map((deg) => (
        <g key={deg} transform={`rotate(${deg} 100 100)`}>
          <path
            d="M 100 20 A 80 80 0 0 1 169 140"
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
            strokeLinecap="butt"
          />
          <polygon points="160,128 176,148 150,150" fill="currentColor" />
        </g>
      ))}
      <circle cx="100" cy="100" r="22" fill="currentColor" opacity="0.18" />
      <text
        x="100"
        y="108"
        textAnchor="middle"
        className="bl-loop-glyph-label"
      >
        LLM
      </text>
    </svg>
  );
}

/* ─── step 2 / 3：代码逐行揭示 ─── */
const CODE_LINES: { n: number; code: string; tag?: string }[] = [
  { n: 1, code: "for turn in range(max_turns):", tag: "for" },
  { n: 2, code: "    resp = client.chat.completions.create(", tag: "resp" },
  { n: 3, code: "        model=MODEL, messages=messages)", tag: "resp" },
  { n: 4, code: "    reply = resp.choices[0].message.content", tag: "reply" },
  {
    n: 5,
    code: "    messages.append({\"role\": \"assistant\",", tag: "append",
  },
  {
    n: 6,
    code: "                     \"content\": reply})",
    tag: "append",
  },
];

function CodeStep({ revealedLines }: { revealedLines: number }) {
  // revealedLines=2 → 显示前 3 行（for/resp 两行合并算"前半"）
  // revealedLines=4 → 显示全部 6 行
  const visibleCount = revealedLines === 2 ? 3 : 6;
  return (
    <div className="bl-code">
      <div className="bl-code-label">
        <span className="bl-code-file">v1_bare_loop.py</span>
        <span className="bl-code-tagline">核心循环</span>
      </div>
      <div className="bl-code-block">
        {CODE_LINES.slice(0, visibleCount).map((ln, i) => (
          <CodeLine key={ln.n} ln={ln} delay={i * 120} />
        ))}
      </div>
    </div>
  );
}

function CodeLine({
  ln,
  delay,
}: {
  ln: { n: number; code: string; tag?: string };
  delay: number;
}) {
  const [up, setUp] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setUp(true), delay);
    return () => clearTimeout(t);
  }, [delay]);
  return (
    <div className={`bl-codeline ${up ? "is-up" : ""}`} data-tag={ln.tag}>
      <span className="bl-codeline-no">{ln.n}</span>
      <code className="bl-codeline-code">{ln.code}</code>
    </div>
  );
}

/* ─── step 4：文件角标 ─── */
function FileInfoStep() {
  return (
    <div className="bl-fileinfo">
      <div className="bl-fileinfo-card">
        <div className="bl-fileinfo-name">v1_bare_loop.py</div>
        <div className="bl-fileinfo-line">
          <span className="bl-fileinfo-key">~20 行</span>
          <span className="bl-fileinfo-sep">·</span>
          <span className="bl-fileinfo-status">
            <span className="bl-fileinfo-ok">能想</span>
            <span className="bl-fileinfo-slash">/</span>
            <span className="bl-fileinfo-bad">不能做</span>
          </span>
        </div>
      </div>
    </div>
  );
}

/* ─── step 5：终端跑空演出 ─── */
function TerminalRunStep() {
  const [phase, setPhase] = useState(0);
  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 400),
      setTimeout(() => setPhase(2), 1800),
      setTimeout(() => setPhase(3), 3400),
    ];
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <div className="bl-trun">
      <div className="bl-trun-term">
        <div className="bl-trun-bar">
          <span className="bl-trun-dot bl-trun-r" />
          <span className="bl-trun-dot bl-trun-y" />
          <span className="bl-trun-dot bl-trun-g" />
          <span className="bl-trun-title">TERMINAL</span>
        </div>
        <div className="bl-trun-body">
          <div className="bl-trun-line bl-trun-cmd">$ python v1_bare_loop.py</div>
          {phase >= 1 && (
            <div className="bl-trun-divider">── Turn 1 ──</div>
          )}
          {phase >= 1 && (
            <div className="bl-trun-llm">
              LLM: 好的，我来帮你创建 hello.py，内容是
              print('hello world')……
            </div>
          )}
          {phase >= 2 && (
            <div className="bl-trun-divider">── Turn 2 ──</div>
          )}
          {phase >= 2 && (
            <div className="bl-trun-llm">
              LLM: 文件已经创建好了，运行结果应该是 hello world。
            </div>
          )}
          {phase >= 3 && (
            <>
              <div className="bl-trun-empty">（hello.py 不存在）</div>
              <div className="bl-trun-flag">⚠ 什么都没发生</div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── step 6：椅子+门比喻 ─── */
function MetaphorStep() {
  return (
    <div className="bl-meta">
      <div className="bl-meta-scene">
        <DoorGlyph />
        <ChairGlyph />
      </div>
      <div className="bl-meta-quote">
        <span className="bl-meta-q">"我帮你把门关了"</span>
      </div>
      <div className="bl-meta-punch">
        话说完了，<span className="bl-meta-hl">门还开着</span>
      </div>
    </div>
  );
}

/* 门 SVG —— 一扇开着的门（强调"没关上"） */
function DoorGlyph() {
  return (
    <svg
      className="bl-meta-door"
      viewBox="0 0 120 160"
      role="img"
      aria-label="一扇开着的门"
    >
      {/* 门框 */}
      <rect x="10" y="10" width="100" height="140" fill="none" stroke="currentColor" strokeWidth="6" />
      {/* 打开的门扇 */}
      <polygon points="10,150 10,30 78,16 78,150" fill="currentColor" opacity="0.12" stroke="currentColor" strokeWidth="4" />
      {/* 门把手 */}
      <circle cx="72" cy="84" r="5" fill="currentColor" />
      {/* 缝隙线（门开着） */}
      <line x1="10" y1="30" x2="78" y2="16" stroke="currentColor" strokeWidth="4" />
    </svg>
  );
}

/* 椅子 + 人 SVG —— 极简像素人坐在椅子上说话 */
function ChairGlyph() {
  return (
    <svg
      className="bl-meta-chair"
      viewBox="0 0 160 180"
      role="img"
      aria-label="坐在椅子上说话的人"
    >
      {/* 椅子靠背 */}
      <rect x="20" y="60" width="16" height="80" fill="currentColor" opacity="0.5" />
      {/* 椅座 */}
      <rect x="20" y="130" width="90" height="14" fill="currentColor" opacity="0.6" />
      {/* 椅腿 */}
      <rect x="24" y="144" width="8" height="26" fill="currentColor" opacity="0.5" />
      <rect x="100" y="144" width="8" height="26" fill="currentColor" opacity="0.5" />
      {/* 人头 */}
      <circle cx="78" cy="50" r="18" fill="currentColor" opacity="0.85" />
      {/* 人身 */}
      <rect x="64" y="68" width="28" height="56" fill="currentColor" opacity="0.75" />
      {/* 对话气泡 */}
      <ellipse cx="120" cy="36" rx="30" ry="20" fill="none" stroke="currentColor" strokeWidth="4" />
      <polygon points="108,48 100,64 120,52" fill="none" stroke="currentColor" strokeWidth="4" />
      <text x="120" y="42" textAnchor="middle" className="bl-meta-bubble">...</text>
    </svg>
  );
}

/* ─── step 7：结论 —— Agent 需要一双手 ─── */
function HandsStep() {
  return (
    <div className="bl-hands">
      <div className="bl-hands-label">问题很明确</div>
      <div className="bl-hands-line">
        Agent 需要<span className="bl-hands-hl">一双手</span>
      </div>
      <HandGlyph />
    </div>
  );
}

/* 手 SVG —— 一只像素手 */
function HandGlyph() {
  return (
    <svg
      className="bl-hands-glyph"
      viewBox="0 0 140 160"
      role="img"
      aria-label="一只手"
    >
      {/* 手掌 */}
      <rect x="40" y="70" width="60" height="70" rx="8" fill="currentColor" opacity="0.85" />
      {/* 五指 */}
      <rect x="44" y="30" width="12" height="48" rx="6" fill="currentColor" opacity="0.85" />
      <rect x="60" y="20" width="12" height="58" rx="6" fill="currentColor" opacity="0.85" />
      <rect x="76" y="18" width="12" height="60" rx="6" fill="currentColor" opacity="0.85" />
      <rect x="92" y="26" width="12" height="52" rx="6" fill="currentColor" opacity="0.85" />
      {/* 拇指 */}
      <rect x="24" y="76" width="12" height="36" rx="6" fill="currentColor" opacity="0.8" transform="rotate(-30 30 94)" />
    </svg>
  );
}
