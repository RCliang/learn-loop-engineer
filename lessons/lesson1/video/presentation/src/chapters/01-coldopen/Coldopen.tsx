import { MaskReveal } from "../../components/MaskReveal";
import type { ChapterStepProps } from "../../registry/types";
import "./Coldopen.css";

export default function Coldopen({ step }: ChapterStepProps) {
  /* Step 0 — Simulated terminal: agent running task */
  if (step === 0) {
    return (
      <div className="co-scene scene-pad">
        <div className="co-terminal">
          <div className="co-term-header">
            <span className="co-term-dot co-dot-r" />
            <span className="co-term-dot co-dot-y" />
            <span className="co-term-dot co-dot-g" />
            <span className="co-term-title">agent v4_final.py</span>
          </div>
          <div className="co-term-body">
            <MaskReveal show duration={400}>
              <div className="co-line">
                <span className="co-prompt">$ </span>
                <span>python v4_final.py</span>
              </div>
            </MaskReveal>
            <MaskReveal show delay={400} duration={400}>
              <div className="co-line co-dim">═══ Turn 1 ═══</div>
            </MaskReveal>
            <MaskReveal show delay={700} duration={400}>
              <div className="co-line">
                <span className="co-tool">🔧 file_write</span>
                <span className="co-dim"> → hello.py</span>
              </div>
            </MaskReveal>
            <MaskReveal show delay={1000} duration={400}>
              <div className="co-line co-success">   ✓ 已写入 20 字节</div>
            </MaskReveal>
            <MaskReveal show delay={1300} duration={400}>
              <div className="co-line co-dim">═══ Turn 2 ═══</div>
            </MaskReveal>
            <MaskReveal show delay={1600} duration={400}>
              <div className="co-line">
                <span className="co-tool">🔧 bash_exec</span>
                <span className="co-dim"> → python hello.py</span>
              </div>
            </MaskReveal>
            <MaskReveal show delay={1900} duration={400}>
              <div className="co-line co-success">   退出代码: 0 | 输出: hello world</div>
            </MaskReveal>
            <MaskReveal show delay={2200} duration={400}>
              <div className="co-line co-dim">═══ Turn 3 ═══</div>
            </MaskReveal>
            <MaskReveal show delay={2500} duration={500}>
              <div className="co-line co-done">✅ 任务完成</div>
            </MaskReveal>
          </div>
        </div>
      </div>
    );
  }

  /* Step 1 — Stats card: 3 turns, 2 tool calls, 150 lines */
  if (step === 1) {
    return (
      <div className="co-scene scene-pad co-center">
        <div className="co-stats">
          <MaskReveal show duration={500}>
            <div className="co-stat-item">
              <span className="co-stat-num hero-num">3</span>
              <span className="co-stat-label">轮对话</span>
            </div>
          </MaskReveal>
          <MaskReveal show delay={300} duration={500}>
            <div className="co-stat-item">
              <span className="co-stat-num hero-num">2</span>
              <span className="co-stat-label">次工具调用</span>
            </div>
          </MaskReveal>
          <MaskReveal show delay={600} duration={500}>
            <div className="co-stat-item">
              <span className="co-stat-num hero-num">150</span>
              <span className="co-stat-label">行代码</span>
            </div>
          </MaskReveal>
        </div>
      </div>
    );
  }

  /* Step 2 — Hero: all frameworks = for loop */
  if (step === 2) {
    return (
      <div className="co-scene scene-pad co-center">
        <MaskReveal show duration={600}>
          <div className="co-brands">
            <span className="co-brand">Claude Code</span>
            <span className="co-brand-sep">·</span>
            <span className="co-brand">Cursor</span>
            <span className="co-brand-sep">·</span>
            <span className="co-brand">Devin</span>
          </div>
        </MaskReveal>
        <MaskReveal show delay={400} duration={800}>
          <div className="co-hero-statement">
            <span className="co-hero-eq">=</span>
            <code className="co-hero-code">for loop</code>
          </div>
        </MaskReveal>
      </div>
    );
  }

  /* Step 3 — Transition: empty loop → working agent */
  return (
    <div className="co-scene scene-pad co-center">
      <MaskReveal show duration={700}>
        <div className="co-journey">
          <div className="co-journey-from">
            <code className="co-journey-code">for turn in range(n):</code>
            <div className="co-journey-label">空循环</div>
          </div>
          <div className="co-journey-arrow">→</div>
          <div className="co-journey-to">
            <div className="co-journey-agent">Agent</div>
            <div className="co-journey-label">能用的 Code Agent</div>
          </div>
        </div>
      </MaskReveal>
    </div>
  );
}
