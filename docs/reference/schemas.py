"""
Tool JSON Schema 定义
所有工具的 schema 在此处集中管理，供 handroll 和 deepagent 共用。
"""

BASH_EXEC_SCHEMA = {
    "name": "bash_exec",
    "description": (
        "在沙箱 shell 中执行一条 bash 命令，返回 stdout、stderr 和退出码。"
        "适合运行脚本、安装依赖、编译代码等操作。"
        "超时默认 30 秒。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "要执行的 bash 命令，支持管道和重定向",
            },
            "timeout": {
                "type": "integer",
                "description": "超时秒数，默认 30",
                "default": 30,
            },
        },
        "required": ["command"],
    },
}

FILE_READ_SCHEMA = {
    "name": "file_read",
    "description": (
        "读取指定路径的文件内容，返回文本字符串。"
        "支持相对路径（相对于工作目录）和绝对路径。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径",
            },
            "encoding": {
                "type": "string",
                "description": "文件编码，默认 utf-8",
                "default": "utf-8",
            },
        },
        "required": ["path"],
    },
}

FILE_WRITE_SCHEMA = {
    "name": "file_write",
    "description": (
        "将内容写入指定路径的文件。若文件不存在则创建，若存在则覆盖。"
        "自动创建缺失的父目录。"
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "文件路径",
            },
            "content": {
                "type": "string",
                "description": "要写入的内容",
            },
        },
        "required": ["path", "content"],
    },
}

ALL_TOOLS = [BASH_EXEC_SCHEMA, FILE_READ_SCHEMA, FILE_WRITE_SCHEMA]
