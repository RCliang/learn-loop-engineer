"""工具 JSON Schema 注册表 + LangChain 适配。

双形式导出：
- ALL_TOOLS              给 handroll 直接构造 OpenAI tools API 请求
- ALL_TOOLS_AS_CALLABLES 给 deepagents 经 LangChain 调度

两套形式共享相同的 name/description/input_schema，
通过 to_langchain_tool(schema, fn) 派生保证一致。

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from typing import Callable

from langchain_core.tools import StructuredTool


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


BASH_EXEC_SCHEMA = _schema(
    name="bash_exec",
    description=(
        "在沙箱 shell（限制在 sandbox/ 工作目录）中执行一条 bash 命令，"
        "返回 stdout、stderr 和 exit_code。超时默认 30 秒。"
    ),
    properties={
        "command": {"type": "string", "description": "要执行的 bash 命令"},
        "timeout": {"type": "integer", "description": "超时秒数，默认 30", "default": 30},
    },
    required=["command"],
)

FILE_READ_SCHEMA = _schema(
    name="file_read",
    description="读取 sandbox/ 工作目录下的文件内容，返回文本字符串。",
    properties={
        "path": {"type": "string", "description": "文件路径（相对 sandbox/ 或绝对）"},
        "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
    },
    required=["path"],
)

FILE_WRITE_SCHEMA = _schema(
    name="file_write",
    description=(
        "将内容写入 sandbox/ 工作目录下的文件。"
        "若文件不存在则创建，若存在则覆盖。自动创建缺失的父目录。"
    ),
    properties={
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "要写入的内容"},
        "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
    },
    required=["path", "content"],
)

ALL_TOOLS = [BASH_EXEC_SCHEMA, FILE_READ_SCHEMA, FILE_WRITE_SCHEMA]


def to_langchain_tool(schema: dict, fn: Callable) -> StructuredTool:
    """从 schema dict + Python 函数派生一个 LangChain StructuredTool。
    共享 schema 的 name/description/input_schema，保证两路 LLM 看到相同描述。"""
    return StructuredTool.from_function(
        func=fn,
        name=schema["name"],
        description=schema["description"],
        args_schema=None,  # input_schema 不直接用 pydantic；依赖 StructuredTool 推断
    )


# 注：LangChain 工具的 args schema 通过函数签名推断（**kwargs 不行，需显式参数）
# 因此我们直接 wrap 一个有签名的函数
from shared.tools import bash_exec as _bash
from shared.tools import file_read as _fread
from shared.tools import file_write as _fwrite


def _bash_wrapped(command: str, timeout: int = 30) -> dict:
    """bash_exec 的 LangChain 入口（签名必须显式，不能用 **kwargs）"""
    return _bash.run(command=command, timeout=timeout)


def _file_read_wrapped(path: str, encoding: str = "utf-8") -> dict:
    return _fread.run(path=path, encoding=encoding)


def _file_write_wrapped(path: str, content: str, encoding: str = "utf-8") -> dict:
    return _fwrite.run(path=path, content=content, encoding=encoding)


ALL_TOOLS_AS_CALLABLES = [
    to_langchain_tool(BASH_EXEC_SCHEMA, _bash_wrapped),
    to_langchain_tool(FILE_READ_SCHEMA, _file_read_wrapped),
    to_langchain_tool(FILE_WRITE_SCHEMA, _file_write_wrapped),
]
