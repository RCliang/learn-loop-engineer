import { useEffect, useState } from "react";
import type { ChapterStepProps } from "../../registry/types";
import "./Observation.css";

/**
 * Chapter 5 · v4-observation — 看得懂结果：Observation 格式化
 *
 * 11 steps（0-based step 0..10），节奏跟 narrations.ts：
 *   0   章节标题：最后一个组件
 *   1   问题抛出：结果长什么样？
 *   2   原始 JSON 成功样例（一坨）
 *   3   原始 JSON 失败样例（更乱）
 *   4   转场箭头：格式化之后呢？
 *   5   格式化后一行 + 对比反差
 *   6   format_observation 代码揭示
 *   7   金句：不是好看，是更好的下一步决策
 *   8   预告角标：structured vs raw A/B 实验
 *   9   file_read 角标
 *   10  文件角标：v4_final.py · ~150 行 · 完整 Agent
 *
 * 视觉演示（CHAPTER-CRAFT.md 底线）：raw JSON 乱 vs formatted 一行的反差 +
 * 代码逐行揭示 + 金句。颜色/字体全走 token。
 */
export default function Observation({ step }: ChapterStepProps) {
  return (
    <div className="vo-stage">
      {step === 0 && <TitleStep />}
      {step === 1 && <QuestionStep />}
      {step === 2 && <RawJsonStep variant="ok" />}
      {step === 3 && <RawJsonStep variant="fail" />}
      {step === 4 && <TransitionStep />}
      {step === 5 && <FormattedStep />}
      {step === 6 && <FormatCodeStep />}
      {step === 7 && <QuoteStep />}
      {step === 8 && <TeaserStep />}
      {step === 9 && <FileReadStep />}
      {step === 10 && <FileInfoStep />}
    </div>
  );
}

/* ─── step 0：章节标题 ─── */
function TitleStep() {
  return (
    <div className="vo-title">
      <div className="vo-title-kicker">v4 · 最后一个组件</div>
      <div className="vo-title-em">Observation 格式化</div>
      <div className="vo-title-sub">看得懂结果</div>
    </div>
  );
}

/* ─── step 1：问题抛出 ─── */
function QuestionStep() {
  return (
    <div className="vo-q">
      <div className="vo-q-label">工具执行完了</div>
      <div className="vo-q-main">结果<span className="vo-q-hl">长什么样？</span></div>
    </div>
  );
}

/* ─── step 2 / 3：原始 JSON（一坨）─── */
function RawJsonStep({ variant }: { variant: "ok" | "fail" }) {
  const isOk = variant === "ok";
  const json = isOk
    ? '{"ok": true, "exit_code": 0, "stdout": "hello world\\n", "stderr": "", "duration_s": 0.123}'
    : '{"ok": false, "error_type": "TimeoutExpired", "message": "超时 30s", "stdout": "", "stderr": "", "exit_code": -1}';
  return (
    <div className="vo-raw">
      <div className={`vo-raw-label ${isOk ? "" : "is-fail"}`}>
        {isOk ? "原始输出 · 成功" : "原始输出 · 失败"}
      </div>
      <div className="vo-raw-block">
        <code className="vo-raw-json">{json}</code>
      </div>
      <div className="vo-raw-note">
        {isOk ? "LLM 能看懂，但费劲" : "出错的时候更费劲"}
      </div>
    </div>
  );
}

/* ─── step 4：转场 ─── */
function TransitionStep() {
  return (
    <div className="vo-trans">
      <div className="vo-trans-arrow" aria-hidden>↓</div>
      <div className="vo-trans-text">格式化之后呢？</div>
    </div>
  );
}

/* ─── step 5：格式化后一行 ─── */
function FormattedStep() {
  const [up, setUp] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setUp(true), 200);
    return () => clearTimeout(t);
  }, []);
  return (
    <div className="vo-fmt">
      <div className="vo-fmt-label">格式化之后</div>
      <div className={`vo-fmt-line ${up ? "is-up" : ""}`}>
        <span className="vo-fmt-tag">[错误]</span> bash_exec 失败: 命令超时(30s)
      </div>
      <div className="vo-fmt-note">
        <span className="vo-fmt-ok">一目了然</span>
        <span className="vo-fmt-sep">·</span>
        LLM 立刻知道下一步该怎么处理
      </div>
    </div>
  );
}

/* ─── step 6：format_observation 代码 ─── */
const FMT_LINES: { code: string; tag?: string }[] = [
  { code: "def format_observation(tool_name, result):", tag: "def" },
  { code: "    if not result.get(\"ok\"):", tag: "if" },
  { code: "        return f\"[错误] {tool_name} 失败: {message}\"", tag: "ret" },
  { code: "    if tool_name == \"bash_exec\":", tag: "if" },
  { code: "        return f\"退出代码: {exit_code}\\n输出: {stdout}\"", tag: "ret" },
  { code: "    elif tool_name == \"file_write\":", tag: "if" },
  { code: "        return f\"✓ 已写入 {bytes} 字节\"", tag: "ret" },
];

function FormatCodeStep() {
  return (
    <div className="vo-fcode">
      <div className="vo-fcode-label">format_observation · 实现</div>
      <div className="vo-codeblock">
        {FMT_LINES.map((ln, i) => (
          <CodeLine key={i} code={ln.code} tag={ln.tag} delay={i * 120} />
        ))}
      </div>
    </div>
  );
}

/* ─── step 7：金句 ─── */
function QuoteStep() {
  return (
    <div className="vo-golden">
      <div className="vo-golden-not">
        格式化的目标<span className="vo-golden-strike">不是好看</span>
      </div>
      <div className="vo-golden-em">
        是让 LLM 做出<span className="vo-golden-hl">更好的下一步决策</span>
      </div>
    </div>
  );
}

/* ─── step 8：预告角标 ─── */
function TeaserStep() {
  return (
    <div className="vo-teaser">
      <div className="vo-teaser-tag">后续预告</div>
      <div className="vo-teaser-main">
        <span className="vo-teaser-a">structured</span>
        <span className="vo-teaser-vs">vs</span>
        <span className="vo-teaser-b">raw</span>
      </div>
      <div className="vo-teaser-note">A/B 实验 · 拿数据说话</div>
    </div>
  );
}

/* ─── step 9：file_read 角标 ─── */
function FileReadStep() {
  return (
    <div className="vo-fr">
      <div className="vo-fr-tag">v4 新增工具</div>
      <div className="vo-fr-name">file_read</div>
      <div className="vo-fr-desc">能读文件了</div>
    </div>
  );
}

/* ─── step 10：文件角标 ─── */
function FileInfoStep() {
  return (
    <div className="vo-fileinfo">
      <div className="vo-fileinfo-card">
        <div className="vo-fileinfo-name">v4_final.py</div>
        <div className="vo-fileinfo-line">
          <span className="vo-fileinfo-key">~150 行</span>
          <span className="vo-fileinfo-sep">·</span>
          <span className="vo-fileinfo-status">完整 Agent</span>
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
    <div className={`vo-codeline ${up ? "is-up" : ""}`} data-tag={tag}>
      <code className="vo-codeline-code">{code}</code>
    </div>
  );
}
