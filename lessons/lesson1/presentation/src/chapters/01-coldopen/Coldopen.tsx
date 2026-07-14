import { useEffect, useRef, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Coldopen.css";

/**
 * Chapter 1 · coldopen — 先看效果：一个能自己干活的程序
 *
 * 8 steps（0-based step 0..7），节奏跟 narrations.ts：
 *   0  hero"先看个东西"
 *   1  终端出现，任务打字进来
 *   2  Turn 1：思考 + file_write 工具块
 *   3  Turn 2：bash_exec 工具块 + Turn 3 完成
 *   4  数据条：3 轮 / 2 次工具调用
 *   5  hero 数字 150
 *   6  反差铺垫
 *   7  三个框架名 + for 循环金句
 *
 * 视觉演示（CHAPTER-CRAFT.md 底线）：模拟终端逐 Turn 演出 + 数据条生长 +
 * 框架名逐个浮现。颜色/字体全走 token，不硬编码 hex/字体名。
 */
export default function Coldopen({ step }: ChapterStepProps) {
  return (
    <div className="co-stage">
      {step === 0 && <HookStep />}
      {step >= 1 && step <= 3 && <TerminalStep step={step} />}
      {step === 4 && <StatsStep />}
      {step === 5 && <Hero150Step />}
      {step === 6 && <TurnStep />}
      {step === 7 && <FrameworksStep />}
    </div>
  );
}

/* ─── step 0：钩子 ─── */
function HookStep() {
  return (
    <div className="co-hook">
      <div className="co-hook-blink" aria-hidden />
      <div className="co-hook-text">先看个东西</div>
      <div className="co-hook-sub">CLICK / →</div>
    </div>
  );
}

/* ─── step 1~3：终端演出 ─── */
function TerminalStep({ step }: { step: number }) {
  // 任务输入（step 1 起）
  // Turn 1 file_write（step 2 起）
  // Turn 2 bash_exec + Turn 3 完成（step 3 起）
  return (
    <div className="co-term-wrap">
      <div className="co-term" role="img" aria-label="Agent 运行终端">
        <div className="co-term-bar">
          <span className="co-dot co-dot-r" />
          <span className="co-dot co-dot-y" />
          <span className="co-dot co-dot-g" />
          <span className="co-term-title">AGENT · v4_final.py</span>
        </div>

        <div className="co-term-body">
          {/* 任务输入行：step 1 打字进来 */}
          {step >= 1 && (
            <div className="co-line co-line-input">
              <span className="co-prompt">$</span>
              <Typewriter text=" 创建 hello.py，运行它" active={step === 1} />
            </div>
          )}

          {/* Turn 1：思考 + file_write —— step 2 起 */}
          {step >= 2 && (
            <>
              <div className="co-divider">── Turn 1 ──</div>
              <div className="co-line co-think">思考：需要先写文件</div>
              <div className="co-tool">
                <span className="co-tool-tag">工具</span>
                <span className="co-tool-name">file_write</span>
              </div>
              <div className="co-arg">{"{ path: \"hello.py\", content: \"print('hello world')\" }"}</div>
              <div className="co-result co-ok">✓ 已写入 20 字节到 hello.py</div>
            </>
          )}

          {/* Turn 2：bash_exec —— step 3 起 */}
          {step >= 3 && (
            <>
              <div className="co-divider">── Turn 2 ──</div>
              <div className="co-tool">
                <span className="co-tool-tag">工具</span>
                <span className="co-tool-name">bash_exec</span>
              </div>
              <div className="co-arg">{"{ command: \"python hello.py\" }"}</div>
              <div className="co-result co-ok">退出代码: 0</div>
              <div className="co-result co-out">输出: hello world</div>

              <div className="co-divider">── Turn 3 ──</div>
              <div className="co-done">✅ 任务完成</div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── step 4：数据条 3 轮 / 2 次 ─── */
function StatsStep() {
  return (
    <div className="co-stats">
      <div className="co-stats-label">整个过程没人插手</div>
      <div className="co-stats-row">
        <StatBlock value="3" unit="轮对话" delay={0} />
        <StatBlock value="2" unit="次工具调用" delay={220} />
      </div>
    </div>
  );
}

function StatBlock({ value, unit, delay }: { value: string; unit: string; delay: number }) {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setShown(true), delay);
    return () => clearTimeout(t);
  }, [delay]);
  return (
    <div className={`co-stat ${shown ? "is-shown" : ""}`}>
      <div className="co-stat-num hero-num">{value}</div>
      <div className="co-stat-unit">{unit}</div>
    </div>
  );
}

/* ─── step 5：hero 150 行 ─── */
function Hero150Step() {
  return (
    <div className="co-hero150">
      <div className="co-hero150-kicker">核心代码</div>
      <div className="co-hero150-num hero-num">
        <CountUp to={150} />
      </div>
      <div className="co-hero150-unit">行 Python</div>
    </div>
  );
}

function CountUp({ to }: { to: number }) {
  const [n, setN] = useState(0);
  const ref = useRef<number | undefined>(undefined);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const dur = 700;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / dur);
      const eased = 1 - Math.pow(1 - p, 3);
      setN(Math.round(eased * to));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    ref.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to]);
  return <>{n}</>;
}

/* ─── step 6：反差铺垫 ─── */
function TurnStep() {
  return (
    <div className="co-turn">
      <div className="co-turn-line">这件事可能</div>
      <div className="co-turn-line co-turn-em">跟你的直觉不一样</div>
    </div>
  );
}

/* ─── step 7：三个框架名 + for 循环 ─── */
function FrameworksStep() {
  const names = ["Cursor", "Claude Code", "Cline"];
  const [revealed, setRevealed] = useState(0);
  useEffect(() => {
    const timers = names.map((_, i) =>
      setTimeout(() => setRevealed(i + 1), 300 + i * 360)
    );
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <div className="co-fw">
      <div className="co-fw-label">市面上的 Agent 框架</div>
      <div className="co-fw-names">
        {names.map((nm, i) => (
          <div
            key={nm}
            className={`co-fw-name ${i < revealed ? "is-up" : ""}`}
            style={{ transitionDelay: `${i * 60}ms` }}
          >
            {nm}
          </div>
        ))}
      </div>
      <div className={`co-fw-punch ${revealed >= 3 ? "is-up" : ""}`}>
        核心都是一个 <span className="co-fw-for">for 循环</span>
      </div>
    </div>
  );
}

/* ─── 打字机：仅在 active 时逐字吐，否则直接显示全文 ─── */
function Typewriter({ text, active }: { text: string; active: boolean }) {
  const [n, setN] = useState(active ? 0 : text.length);
  useEffect(() => {
    if (!active) {
      setN(text.length);
      return;
    }
    setN(0);
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setN(i);
      if (i >= text.length) clearInterval(id);
    }, 55);
    return () => clearInterval(id);
  }, [active, text.length]);
  return (
    <span className="co-type">
      {text.slice(0, n)}
      <span className="co-caret" aria-hidden />
    </span>
  );
}
