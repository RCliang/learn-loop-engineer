import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Tools.css";

/**
 * Chapter 3 · v2-tools — 给 Agent 装上手：工具三件事
 *
 * 13 steps（0-based step 0..12），节奏跟 narrations.ts：
 *   0   转场标题：需要一双手 → 得解决三件事
 *   1   三件事总览：①②③ 一次列清（总览锚点）
 *   2   ① 高亮：告诉 LLM 有哪些工具
 *   3   TOOLS 代码：bash_exec 的 name/description/parameters
 *   4   第二个工具 file_write 并列，两个工具卡
 *   5   description 金句高亮
 *   6   ② 高亮：解析工具调用
 *   7   ③ 高亮：执行 + 回传
 *   8   execute_tool bash_exec 分支代码
 *   9   execute_tool file_write 分支代码
 *   10  完成判断代码：if not msg.tool_calls
 *   11  终端跑 v2：Turn1 file_write → Turn2 bash_exec → Turn3 完成
 *   12  隐患引子收尾
 *
 * 视觉演示（CHAPTER-CRAFT.md 底线）：三件事编号锚点 + 代码逐行揭示 +
 * description 聚焦拉框 + 终端逐 Turn 演出 + 隐患意象。颜色/字体全走 token。
 */
export default function Tools({ step }: ChapterStepProps) {
  return (
    <div className="vt-stage">
      {step === 0 && <TitleStep />}
      {step === 1 && <OverviewStep />}
      {step === 2 && <OneHighlightStep />}
      {step === 3 && <ToolDefStep toolIndex={0} />}
      {step === 4 && <TwoToolsStep />}
      {step === 5 && <DescriptionQuoteStep />}
      {step === 6 && <TwoHighlightStep />}
      {step === 7 && <ThreeHighlightStep />}
      {step === 8 && <ExecBashStep />}
      {step === 9 && <ExecFileStep />}
      {step === 10 && <DoneCheckStep />}
      {step === 11 && <TerminalRunStep />}
      {step === 12 && <PitfallStep />}
    </div>
  );
}

/* ─── step 0：转场标题 ─── */
function TitleStep() {
  return (
    <div className="vt-title">
      <div className="vt-title-kicker">v2 · 给 Agent 装上工具</div>
      <div className="vt-title-q">需要一双手</div>
      <div className="vt-title-arrow" aria-hidden>↓</div>
      <div className="vt-title-em">得解决三件事</div>
    </div>
  );
}

/* ─── step 1：三件事总览 ─── */
const THREE_THINGS = [
  { n: "①", title: "告诉 LLM 有哪些工具", sub: "工具定义" },
  { n: "②", title: "解析返回的工具调用", sub: "parse tool_calls" },
  { n: "③", title: "执行，回传结果", sub: "execute + feedback" },
];

function OverviewStep() {
  const [shown, setShown] = useState(0);
  useEffect(() => {
    const timers = THREE_THINGS.map((_, i) =>
      setTimeout(() => setShown(i + 1), 240 + i * 560)
    );
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <div className="vt-overview">
      <div className="vt-overview-label">工具三件事</div>
      <div className="vt-overview-list">
        {THREE_THINGS.map((t, i) => (
          <div
            key={t.n}
            className={`vt-thing ${i < shown ? "is-up" : ""}`}
          >
            <span className="vt-thing-n">{t.n}</span>
            <div className="vt-thing-body">
              <div className="vt-thing-title">{t.title}</div>
              <div className="vt-thing-sub">{t.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── step 2 / 6 / 7：单件事高亮 ─── */
function HighlightStep({ idx }: { idx: number }) {
  const t = THREE_THINGS[idx];
  return (
    <div className="vt-hi">
      <div className="vt-hi-thing">
        <span className="vt-hi-n">{t.n}</span>
        <div className="vt-hi-text">{t.title}</div>
      </div>
      <div className="vt-hi-list">
        {THREE_THINGS.map((tt, i) => (
          <div
            key={tt.n}
            className={`vt-hi-row ${i === idx ? "is-active" : ""} ${
              i < idx ? "is-done" : ""
            }`}
          >
            <span className="vt-hi-row-n">{tt.n}</span>
            <span className="vt-hi-row-t">{tt.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
function OneHighlightStep() {
  return <HighlightStep idx={0} />;
}
function TwoHighlightStep() {
  return <HighlightStep idx={1} />;
}
function ThreeHighlightStep() {
  return <HighlightStep idx={2} />;
}

/* ─── step 3：单个工具定义代码（bash_exec）─── */
const TOOL_BASH_LINES: { code: string; tag?: string }[] = [
  { code: 'TOOLS = [{', tag: "def" },
  { code: '    "type": "function",', tag: "key" },
  { code: '    "function": {', tag: "key" },
  { code: '        "name": "bash_exec",', tag: "name" },
  { code: '        "description": "在工作目录中执行 shell 命令",', tag: "desc" },
  { code: '        "parameters": { ... }', tag: "key" },
  { code: '    }', tag: "key" },
  { code: '}]', tag: "def" },
];

function ToolDefStep({ toolIndex }: { toolIndex: number }) {
  const lines = toolIndex === 0 ? TOOL_BASH_LINES : TOOL_BASH_LINES;
  return (
    <div className="vt-tdef">
      <div className="vt-tdef-label">① 工具定义 · JSON Schema</div>
      <div className="vt-codeblock">
        {lines.map((ln, i) => (
          <CodeLine key={i} code={ln.code} tag={ln.tag} delay={i * 110} />
        ))}
      </div>
    </div>
  );
}

/* ─── step 4：两个工具卡并列 ─── */
function TwoToolsStep() {
  return (
    <div className="vt-twotools">
      <div className="vt-twotools-label">两个工具并排放着</div>
      <div className="vt-twotools-row">
        <ToolCard
          name="bash_exec"
          desc="在工作目录中执行 shell 命令"
          params={['command: 要执行的命令']}
          delay={120}
        />
        <ToolCard
          name="file_write"
          desc="在工作目录中创建或覆盖文件"
          params={['path: 文件相对路径', 'content: 文件内容']}
          delay={440}
        />
      </div>
    </div>
  );
}

function ToolCard({
  name,
  desc,
  params,
  delay,
}: {
  name: string;
  desc: string;
  params: string[];
  delay: number;
}) {
  const [up, setUp] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setUp(true), delay);
    return () => clearTimeout(t);
  }, [delay]);
  return (
    <div className={`vt-tcard ${up ? "is-up" : ""}`}>
      <div className="vt-tcard-name">{name}</div>
      <div className="vt-tcard-desc">{desc}</div>
      <div className="vt-tcard-params">
        {params.map((p) => (
          <div key={p} className="vt-tcard-param">{p}</div>
        ))}
      </div>
    </div>
  );
}

/* ─── step 5：description 金句高亮 ─── */
function DescriptionQuoteStep() {
  return (
    <div className="vt-quote">
      <div className="vt-quote-frame">
        <div className="vt-quote-field">"description"</div>
        <div className="vt-quote-val">"在工作目录中执行 shell 命令"</div>
      </div>
      <div className="vt-quote-punch">
        写得越清楚，<br />
        LLM 选对工具的概率
        <span className="vt-quote-hl">越高</span>
      </div>
    </div>
  );
}

/* ─── step 8：execute_tool bash_exec 分支 ─── */
const EXEC_BASH_LINES: { code: string; tag?: string }[] = [
  { code: "def execute_tool(name, args):", tag: "def" },
  { code: "    if name == \"bash_exec\":", tag: "if" },
  { code: "        proc = subprocess.run(", tag: "run" },
  { code: "            args[\"command\"],", tag: "run" },
  { code: "            shell=True, capture_output=True)", tag: "run" },
  { code: "        return f\"exit_code={proc.returncode}\\n\"", tag: "ret" },
  { code: "               f\"stdout: {proc.stdout}\"", tag: "ret" },
];

function ExecBashStep() {
  return (
    <div className="vt-exec">
      <div className="vt-exec-label">③ 执行器 · bash_exec 分支</div>
      <div className="vt-codeblock">
        {EXEC_BASH_LINES.map((ln, i) => (
          <CodeLine key={i} code={ln.code} tag={ln.tag} delay={i * 130} />
        ))}
      </div>
    </div>
  );
}

/* ─── step 9：execute_tool file_write 分支 ─── */
const EXEC_FILE_LINES: { code: string; tag?: string }[] = [
  { code: "    elif name == \"file_write\":", tag: "if" },
  { code: "        p = Path(args[\"path\"])", tag: "run" },
  { code: "        p.write_text(args[\"content\"])", tag: "run" },
  { code: "        return f\"已写入 {len(args['content'])}", tag: "ret" },
  { code: "                 字节到 {args['path']}\"", tag: "ret" },
];

function ExecFileStep() {
  return (
    <div className="vt-exec">
      <div className="vt-exec-label">③ 执行器 · file_write 分支</div>
      <div className="vt-codeblock">
        {EXEC_FILE_LINES.map((ln, i) => (
          <CodeLine key={i} code={ln.code} tag={ln.tag} delay={i * 150} />
        ))}
      </div>
    </div>
  );
}

/* ─── step 10：完成判断 ─── */
const DONE_LINES: { code: string; tag?: string }[] = [
  { code: "# 没有工具调用 → 任务完成", tag: "cmt" },
  { code: "if not msg.tool_calls:", tag: "if" },
  { code: "    print(\"✓ 任务完成\")", tag: "do" },
  { code: "    return", tag: "do" },
];

function DoneCheckStep() {
  return (
    <div className="vt-done">
      <div className="vt-done-label">循环里的关键判断</div>
      <div className="vt-codeblock vt-codeblock--sm">
        {DONE_LINES.map((ln, i) => (
          <CodeLine key={i} code={ln.code} tag={ln.tag} delay={i * 160} />
        ))}
      </div>
      <div className="vt-done-note">
        不调工具<span className="vt-done-eq">=</span>做完了
      </div>
    </div>
  );
}

/* ─── step 11：终端跑 v2 ─── */
function TerminalRunStep() {
  const [phase, setPhase] = useState(0);
  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 1700),
      setTimeout(() => setPhase(3), 3600),
      setTimeout(() => setPhase(4), 5600),
    ];
    return () => timers.forEach(clearTimeout);
  }, []);
  return (
    <div className="vt-trun">
      <div className="vt-trun-term">
        <div className="vt-trun-bar">
          <span className="vt-trun-dot vt-trun-r" />
          <span className="vt-trun-dot vt-trun-y" />
          <span className="vt-trun-dot vt-trun-g" />
          <span className="vt-trun-title">v2_with_tools.py</span>
        </div>
        <div className="vt-trun-body">
          <div className="vt-trun-cmd">$ python v2_with_tools.py</div>

          {phase >= 1 && (
            <>
              <div className="vt-trun-turn">── Turn 1 ──</div>
              <div className="vt-trun-tool">
                <span className="vt-trun-tag">工具</span>file_write
              </div>
              <div className="vt-trun-res vt-trun-ok">✓ 已写入 20 字节到 hello.py</div>
            </>
          )}

          {phase >= 2 && (
            <>
              <div className="vt-trun-turn">── Turn 2 ──</div>
              <div className="vt-trun-tool">
                <span className="vt-trun-tag">工具</span>bash_exec
              </div>
              <div className="vt-trun-res vt-trun-ok">exit_code=0</div>
              <div className="vt-trun-res vt-trun-out">stdout: hello world</div>
            </>
          )}

          {phase >= 3 && (
            <>
              <div className="vt-trun-turn">── Turn 3 ──</div>
              <div className="vt-trun-done">✓ 任务完成</div>
            </>
          )}

          {phase >= 4 && (
            <div className="vt-trun-flag">能做事了</div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── step 12：隐患引子 ─── */
function PitfallStep() {
  return (
    <div className="vt-pitfall">
      <div className="vt-pitfall-q">但有个隐患</div>
      <LoopGlyph />
      <div className="vt-pitfall-text">
        LLM 出 bug，<span className="vt-pitfall-hl">一直不停</span>
        <br />
        调同一个工具？
      </div>
    </div>
  );
}

/* 反复循环箭头 SVG —— 暗示"停不下来" */
function LoopGlyph() {
  const arcs = [0, 120, 240];
  return (
    <svg
      className="vt-pitfall-glyph"
      viewBox="0 0 200 200"
      role="img"
      aria-label="停不下来的循环"
    >
      {arcs.map((deg) => (
        <g key={deg} transform={`rotate(${deg} 100 100)`}>
          <path
            d="M 100 20 A 80 80 0 0 1 169 140"
            fill="none"
            stroke="currentColor"
            strokeWidth="10"
          />
          <polygon points="160,128 176,148 150,150" fill="currentColor" />
        </g>
      ))}
      <text
        x="100"
        y="92"
        textAnchor="middle"
        className="vt-pitfall-glyph-label"
      >
        同一个
      </text>
      <text
        x="100"
        y="120"
        textAnchor="middle"
        className="vt-pitfall-glyph-label"
      >
        工具
      </text>
    </svg>
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
    <div className={`vt-codeline ${up ? "is-up" : ""}`} data-tag={tag}>
      <code className="vt-codeline-code">{code}</code>
    </div>
  );
}
