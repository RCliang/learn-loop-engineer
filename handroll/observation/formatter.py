"""Observation 格式化器 —— 把工具返回的 dict 渲染成 LLM 易消化的字符串。

设计：
- structured（默认）：每工具一个对齐模板，错误统一前缀 [错误]
- raw：直接 json.dumps（Week 2 做 A/B 对比时启用）

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import json


def format_observation(tool_name: str, tool_input: dict, result: dict, mode: str = "structured") -> str:
    if mode == "raw":
        return json.dumps(result, ensure_ascii=False, indent=2)
    if not result.get("ok"):
        return _format_error(tool_name, result)
    if tool_name == "bash_exec":
        return _format_bash_success(result)
    if tool_name == "file_read":
        return _format_read_success(tool_input, result)
    if tool_name == "file_write":
        return _format_write_success(tool_input, result)
    return json.dumps(result, ensure_ascii=False, indent=2)


def _format_error(tool_name: str, result: dict) -> str:
    return f"[错误] {tool_name} 失败：{result.get('message', '')}（类型：{result.get('error_type', 'Unknown')}）"


def _format_bash_success(result: dict) -> str:
    return (
        f"退出代码 {result.get('exit_code', -1)}\n"
        f"--- stdout ---\n{result.get('stdout', '')}\n"
        f"--- stderr ---\n{result.get('stderr', '')}"
    )


def _format_read_success(tool_input: dict, result: dict) -> str:
    return f"已读取 {tool_input.get('path')}（{result.get('lines', 0)} 行）：\n\n{result.get('content', '')}"


def _format_write_success(tool_input: dict, result: dict) -> str:
    return f"已写入 {result.get('bytes', 0)} 字节到 {tool_input.get('path')}"
