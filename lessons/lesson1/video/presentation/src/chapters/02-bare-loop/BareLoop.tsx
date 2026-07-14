import { MaskReveal } from "../../components/MaskReveal";
import type { ChapterStepProps } from "../../registry/types";
import "./BareLoop.css";

/* ── The full v1_bare_loop.py source (left panel, always visible) ── */
function CodePanel({ highlight }: { highlight?: number[] }) {
  const lines = [
    { n: 1,  text: <><span className="bl-cm"># Agent 最核心的结构 = 一个循环</span></> },
    { n: 2,  text: <></> },
    { n: 3,  text: <><span className="bl-kw">def</span> <span className="bl-fn">run_agent</span>(user_task, max_turns=<span className="bl-str">5</span>):</> },
    { n: 4,  text: <>    messages = [{"{"}<span className="bl-str">"role"</span>: <span className="bl-str">"user"</span>, <span className="bl-str">"content"</span>: user_task{"}"}]</> },
    { n: 5,  text: <></> },
    { n: 6,  text: <>    <span className="bl-kw">for</span> turn <span className="bl-kw">in</span> <span className="bl-fn">range</span>(max_turns):</> },
    { n: 7,  text: <>        resp = client.chat.completions.<span className="bl-fn">create</span>(</> },
    { n: 8,  text: <>            model=MODEL, messages=messages</> },
    { n: 9,  text: <>        )</> },
    { n: 10, text: <>        reply = resp.choices[<span className="bl-str">0</span>].message.content</> },
    { n: 11, text: <>        messages.<span className="bl-fn">append</span>({"{"}<span className="bl-str">"role"</span>: <span className="bl-str">"assistant"</span>, <span className="bl-str">"content"</span>: reply{"}"})</> },
    { n: 12, text: <></> },
    { n: 13, text: <>    <span className="bl-cm"># 此时没有停止判断——跑满 max_turns 就结束</span></> },
    { n: 14, text: <>    <span className="bl-cm"># 问题：LLM 只能说话，不能执行任何操作</span></> },
  ];

  const hl = new Set(highlight ?? []);

  return (
    <div className="bl-left">
      <div className="bl-file-tab">v1_bare_loop.py</div>
      <div className="bl-code-area">
        <div className="bl-line-nums">
          {lines.map(l => <div key={l.n}>{l.n}</div>)}
        </div>
        <pre className="bl-code-pre">
          {lines.map(l => (
            <div key={l.n} className={hl.has(l.n) ? "bl-hl-line" : undefined}>
              {l.text}
              {"\n"}
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

export default function BareLoop({ step }: ChapterStepProps) {
  /* Step 0 — Intro: "核心结构 = 一个循环" */
  if (step === 0) {
    return (
      <div className="bl-scene">
        <div className="bl-split">
          <CodePanel highlight={[1]} />
          <div className="bl-right">
            <MaskReveal show duration={600}>
              <div className="bl-hero-text">
                核心结构
                <br />= 一个循环
              </div>
            </MaskReveal>
            <MaskReveal show delay={400} duration={500}>
              <div className="bl-sub-text">反复调 LLM，直到任务完成</div>
            </MaskReveal>
          </div>
        </div>
      </div>
    );
  }

  /* Step 1 — Code highlight: for / create / append */
  if (step === 1) {
    return (
      <div className="bl-scene">
        <div className="bl-split">
          <CodePanel highlight={[6, 7, 8, 9, 10, 11]} />
          <div className="bl-right">
            <MaskReveal show duration={500}>
              <div className="bl-hero-text">就这几行</div>
            </MaskReveal>
            <MaskReveal show delay={400} duration={500}>
              <div className="bl-sub-text">
                for 循环
                <br />→ 调一次 LLM
                <br />→ 拿回复
                <br />→ 追加到消息列表
              </div>
            </MaskReveal>
            <MaskReveal show delay={800} duration={500}>
              <div className="bl-sub-text" style={{ color: "var(--accent)", marginTop: 32 }}>
                这就是 v1
              </div>
            </MaskReveal>
          </div>
        </div>
      </div>
    );
  }

  /* Step 2 — Terminal: run v1, nothing happens */
  if (step === 2) {
    return (
      <div className="bl-scene">
        <div className="bl-split">
          <CodePanel highlight={[13, 14]} />
          <div className="bl-right">
            <div className="bl-term-output">
              <MaskReveal show duration={400}>
                <div className="bl-tline"><span className="bl-prompt">$ </span>python v1_bare_loop.py</div>
              </MaskReveal>
              <MaskReveal show delay={400} duration={400}>
                <div className="bl-tline bl-dim">── Turn 1 ──</div>
              </MaskReveal>
              <MaskReveal show delay={800} duration={500}>
                <div className="bl-tline">LLM: 好的，我来帮你创建 hello.py...</div>
              </MaskReveal>
              <MaskReveal show delay={1300} duration={500}>
                <div className="bl-tline bl-dim">── Turn 2 ──</div>
              </MaskReveal>
              <MaskReveal show delay={1700} duration={500}>
                <div className="bl-tline">LLM: 文件已经创建好了！</div>
              </MaskReveal>
              <MaskReveal show delay={2200} duration={600}>
                <div className="bl-tline bl-error">（但实际上什么都没发生）</div>
              </MaskReveal>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* Step 3 — Metaphor: door analogy */
  if (step === 3) {
    return (
      <div className="bl-scene">
        <div className="bl-split">
          <CodePanel highlight={[13, 14]} />
          <div className="bl-right">
            <div className="bl-metaphor">
              <div className="bl-metaphor-row">
                <MaskReveal show duration={600}>
                  <div className="bl-metaphor-box">
                    <div className="bl-metaphor-icon">🗣️</div>
                    <div className="bl-metaphor-text">「我帮你把门关了」</div>
                  </div>
                </MaskReveal>
                <MaskReveal show delay={500} duration={500}>
                  <div className="bl-metaphor-vs">VS</div>
                </MaskReveal>
                <MaskReveal show delay={900} duration={600}>
                  <div className="bl-metaphor-box bl-metaphor-reality">
                    <div className="bl-metaphor-icon">🚪</div>
                    <div className="bl-metaphor-text">门还开着</div>
                  </div>
                </MaskReveal>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  /* Step 4 — Conclusion: needs "hands" (full screen) */
  return (
    <div className="bl-scene bl-center">
      <MaskReveal show duration={800}>
        <div className="bl-conclusion">
          <div className="bl-conclusion-label">问题明确：</div>
          <div className="bl-conclusion-hero">Agent 需要「手」</div>
        </div>
      </MaskReveal>
    </div>
  );
}
