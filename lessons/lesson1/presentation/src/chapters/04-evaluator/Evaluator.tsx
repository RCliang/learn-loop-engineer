import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Evaluator.css";

/**
 * Chapter 4 · v3-evaluator — 装上刹车：Evaluator 三层
 *
 * 11 steps（0-based step 0..10），节奏跟 narrations.ts：
 *   0   hero 金句：没有刹车的 Agent 会烧光 token
 *   1   死循环演示终端：反复 pip3 install magic 失败，烧钱数字跳
 *   2   章节标题：给它装三道刹车
 *   3   刹车 1：max_turns 硬上限 + 代码
 *   4   刹车 2 高亮：死循环检测
 *   5   刹车 2 代码：md5 + count >= 2 + loop_detected
 *   6   刹车 3（虚化/待办）：self-critique，下一课展开
 *   7   核心论断 hero：可靠性 ≠ LLM 更强 = Evaluator 更靠谱
 *   8   死循环演示重来（有 Evaluator）
 *   9   loop_detected 截断 + 账单截住
 *   10  文件角标：v3_with_evaluator.py · ~110 行 · 会停
 *
 * 视觉演示（CHAPTER-CRAFT.md 底线）：烧钱终端演出 + 三道刹车编号锚点 +
 * md5 hash 代码 + 可靠性天平对比 + loop_detected 红色截断。颜色/字体全走 token。
 */
export default function Evaluator({ step }: ChapterStepProps) {
  return (
    <div className="ve-stage">
      {step === 0 && <HeroQuoteStep />}
      {step === 1 && <InfiniteLoopStep />}
      {step === 2 && <TitleStep />}
      {step === 3 && <BrakeOneStep />}
      {step === 4 && <BrakeTwoIntroStep />}
      {step === 5 && <BrakeTwoCodeStep />}
      {step === 6 && <BrakeThreeStep />}
      {step === 7 && <ReliabilityStep />}
      {step === 8 && <LoopCuredStep />}
      {step === 9 && <CutoffStep />}
      {step === 10 && <FileInfoStep />}
    </div>
  );
}

/* ─── step 0：hero 金句 ─── */
function HeroQuoteStep() {
  return (
    <div className="ve-quote">
      <div className="ve-quote-kicker">没有刹车的 Agent 是危险的</div>
      <div className="ve-quote-main">
        不是它会<span className="ve-quote-strike">伤害你</span>
      </div>
      <div className="ve-quote-em">
        是它会<span className="ve-quote-hl">烧光你的 token</span>
      </div>
    </div>
  );
}

/* ─── step 1：死循环终端（无刹车，烧钱）─── */
function InfiniteLoopStep() {
  const [turns, setTurns] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTurns((t) => t + 1), 850);
    return () => clearInterval(id);
  }, []);
  const cost = (turns * 2.34).toFixed(2);
  const visibleTurns = Math.min(turns, 7);
  return (
    <div className="ve-infloop">
      <div className="ve-infloop-term">
        <div className="ve-term-bar">
          <span className="ve-dot ve-dot-r" />
          <span className="ve-dot ve-dot-y" />
          <span className="ve-dot ve-dot-g" />
          <span className="ve-term-title">v2 · 无刹车</span>
        </div>
        <div className="ve-term-body">
          <div className="ve-term-cmd">$ python v2_with_tools.py</div>
          {Array.from({ length: visibleTurns }).map((_, i) => (
            <div key={i} className="ve-infloop-turn">
              <div className="ve-term-divider">── Turn {i + 1} ──</div>
              <div className="ve-term-tool">
                <span className="ve-term-tag">工具</span>bash_exec
              </div>
              <div className="ve-term-res ve-term-fail">
                ✗ pip3 install magic → 失败
              </div>
            </div>
          ))}
          {turns > 7 && (
            <div className="ve-infloop-more">... 还在跑 ...</div>
          )}
        </div>
      </div>
      <div className="ve-infloop-cost">
        <span className="ve-infloop-cost-label">已烧</span>
        <span className="ve-infloop-cost-num hero-num">${cost}</span>
      </div>
    </div>
  );
}

/* ─── step 2：章节标题 ─── */
function TitleStep() {
  return (
    <div className="ve-title">
      <div className="ve-title-kicker">v3 · Evaluator</div>
      <div className="ve-title-main">给它装</div>
      <div className="ve-title-em">三道刹车</div>
    </div>
  );
}

/* ─── 通用：刹车条 ─── */
function BrakeBar({
  n,
  name,
  desc,
  state,
}: {
  n: string;
  name: string;
  desc: string;
  state: "active" | "todo";
}) {
  return (
    <div className={`ve-brake ${state === "todo" ? "is-todo" : ""}`}>
      <div className="ve-brake-n">{n}</div>
      <div className="ve-brake-body">
        <div className="ve-brake-name">{name}</div>
        <div className="ve-brake-desc">{desc}</div>
      </div>
      {state === "todo" && <div className="ve-brake-tag">下一课</div>}
    </div>
  );
}

/* ─── step 3：刹车 1（max_turns + 代码）─── */
const BRAKE1_LINES: { code: string; tag?: string }[] = [
  { code: "# 刹车 1：硬上限", tag: "cmt" },
  { code: "if turn >= self.max_turns:", tag: "if" },
  { code: '    return True, "max_turns"', tag: "ret" },
];

function BrakeOneStep() {
  return (
    <div className="ve-brake-show">
      <BrakeBar n="①" name="硬上限" desc="max_turns 到了就停，无论如何" state="active" />
      <div className="ve-brake-code">
        {BRAKE1_LINES.map((ln, i) => (
          <CodeLine key={i} code={ln.code} tag={ln.tag} delay={i * 160} />
        ))}
      </div>
    </div>
  );
}

/* ─── step 4：刹车 2 高亮 ─── */
function BrakeTwoIntroStep() {
  return (
    <div className="ve-brake-show">
      <BrakeBar n="②" name="死循环检测" desc="同一操作连续三次，强制停" state="active" />
      <div className="ve-brake2-scene">
        <RepeatGlyph />
        <div className="ve-brake2-label">同一操作 ×3 → 停</div>
      </div>
    </div>
  );
}

/* 重复箭头 SVG —— 同一动作循环三次 */
function RepeatGlyph() {
  return (
    <svg className="ve-repeat" viewBox="0 0 280 120" role="img" aria-label="重复三次">
      {[0, 1, 2].map((i) => (
        <g key={i} transform={`translate(${i * 96 + 10}, 20)`}>
          <rect x="0" y="0" width="76" height="76" fill="none" stroke="currentColor" strokeWidth="6" />
          <text x="38" y="48" textAnchor="middle" className="ve-repeat-label">{i + 1}</text>
        </g>
      ))}
      <path d="M 86 58 L 96 58" stroke="currentColor" strokeWidth="4" />
      <path d="M 182 58 L 192 58" stroke="currentColor" strokeWidth="4" />
    </svg>
  );
}

/* ─── step 5：刹车 2 代码 ─── */
const BRAKE2_LINES: { code: string; tag?: string }[] = [
  { code: "h = hashlib.md5(", tag: "run" },
  { code: "    json.dumps(last_action, sort_keys=True)", tag: "run" },
  { code: "    .encode()).hexdigest()", tag: "run" },
  { code: "if self._action_hashes.count(h) >= 2:", tag: "if" },
  { code: '    return True, "loop_detected"', tag: "ret" },
];

function BrakeTwoCodeStep() {
  return (
    <div className="ve-b2code">
      <div className="ve-b2code-label">② 死循环检测 · 实现</div>
      <div className="ve-brake-code">
        {BRAKE2_LINES.map((ln, i) => (
          <CodeLine key={i} code={ln.code} tag={ln.tag} delay={i * 150} />
        ))}
      </div>
      <div className="ve-b2code-note">
        hash 一下，发现<span className="ve-b2code-hl">两次</span>就停
      </div>
    </div>
  );
}

/* ─── step 6：刹车 3（虚化/待办）─── */
function BrakeThreeStep() {
  return (
    <div className="ve-brake-show">
      <BrakeBar n="③" name="self-critique" desc="再问一次 LLM：做完了吗" state="todo" />
      <div className="ve-b3-pseudo">
        <div className="ve-b3-line">def self_critique(task, result):</div>
        <div className="ve-b3-line">    <span className="ve-b3-todo"># 下一课展开 ...</span></div>
      </div>
    </div>
  );
}

/* ─── step 7：核心论断（可靠性天平）─── */
function ReliabilityStep() {
  return (
    <div className="ve-relia">
      <div className="ve-relia-q">Agent 可不可靠</div>
      <div className="ve-relia-scale">
        <div className="ve-relia-side ve-relia-wrong">
          <div className="ve-relia-x">✗</div>
          <div className="ve-relia-txt">LLM 更强</div>
        </div>
        <div className="ve-relia-vs">≠</div>
        <div className="ve-relia-side ve-relia-right">
          <div className="ve-relia-ok">✓</div>
          <div className="ve-relia-txt">Evaluator 更靠谱</div>
        </div>
      </div>
      <div className="ve-relia-punch">越靠谱，越可控</div>
    </div>
  );
}

/* ─── step 8：死循环重来（有 Evaluator）─── */
function LoopCuredStep() {
  return (
    <div className="ve-cured">
      <div className="ve-cured-label">再看刚才那个死循环</div>
      <div className="ve-cured-row">
        <CuredTurn n={1} delay={0} />
        <CuredTurn n={2} delay={500} />
        <CuredTurn n={3} delay={1000} hit />
      </div>
      <div className="ve-cured-note">这回有了 Evaluator</div>
    </div>
  );
}

function CuredTurn({ n, delay, hit }: { n: number; delay: number; hit?: boolean }) {
  const [up, setUp] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setUp(true), delay + 200);
    return () => clearTimeout(t);
  }, [delay]);
  return (
    <div className={`ve-cured-turn ${hit ? "is-hit" : ""} ${up ? "is-up" : ""}`}>
      <div className="ve-cured-n">Turn {n}</div>
      <div className="ve-cured-tool">bash_exec</div>
      <div className="ve-cured-res">✗ 失败</div>
      {hit && <div className="ve-cured-flag">⚠ loop_detected</div>}
    </div>
  );
}

/* ─── step 9：截断对比 ─── */
function CutoffStep() {
  return (
    <div className="ve-cutoff">
      <div className="ve-cutoff-red">⚠ loop_detected</div>
      <div className="ve-cutoff-text">
        三次重复，自动停。<br />
        <span className="ve-cutoff-hl">账单截住了</span>
      </div>
    </div>
  );
}

/* ─── step 10：文件角标 ─── */
function FileInfoStep() {
  return (
    <div className="ve-fileinfo">
      <div className="ve-fileinfo-card">
        <div className="ve-fileinfo-name">v3_with_evaluator.py</div>
        <div className="ve-fileinfo-line">
          <span className="ve-fileinfo-key">~110 行</span>
          <span className="ve-fileinfo-sep">·</span>
          <span className="ve-fileinfo-status">会停了</span>
        </div>
      </div>
    </div>
  );
}

/* ─── 通用：代码逐行揭示 ─── */
function CodeLine({
  code,
  tag,
  delay,
}: {
  code: string;
  tag?: string;
  delay: number;
}) {
  const [up, setUp] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setUp(true), delay);
    return () => clearTimeout(t);
  }, [delay]);
  return (
    <div className={`ve-codeline ${up ? "is-up" : ""}`} data-tag={tag}>
      <code className="ve-codeline-code">{code}</code>
    </div>
  );
}
