"""统一 CLI 入口。

用法：
  python -m cli run --agent handroll --task task_01_simple_script
  python -m cli run --agent deepagent --task task_01_simple_script
  python -m cli run --agent both    --task task_01_simple_script
  python -m cli tasks
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from shared.utils.sandbox import reset_sandbox
from tasks import TASKS


def _run_one(agent_name: str, task):
    reset_sandbox()
    if agent_name == "handroll":
        from handroll.agent import run as agent_run
    elif agent_name == "deepagent":
        from deepagent.agent import run as agent_run
    else:
        raise ValueError(f"unknown agent: {agent_name}")
    return agent_run(task)


def cmd_run(args):
    if args.task not in TASKS:
        print(f"unknown task: {args.task}", file=sys.stderr)
        sys.exit(2)
    task = TASKS[args.task]
    agents = ["handroll", "deepagent"] if args.agent == "both" else [args.agent]

    logs = []
    for ag in agents:
        print(f"\n=== running {ag} on {task.id} ===")
        try:
            log = _run_one(ag, task)
        except Exception as e:
            print(f"[{ag}] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        logs.append((ag, log))

    if logs:
        _print_table(logs)


def _print_table(logs):
    console = Console()
    table = Table(title="Run Summary")
    table.add_column("agent")
    table.add_column("success")
    table.add_column("turns")
    table.add_column("in_tokens")
    table.add_column("out_tokens")
    table.add_column("duration_s")
    for ag, log in logs:
        table.add_row(
            ag,
            str(log.success),
            str(log.loop_turns),
            str(log.total_input_tokens),
            str(log.total_output_tokens),
            f"{log.duration_s:.2f}",
        )
    console.print(table)


def cmd_tasks(args):
    print("Available tasks:")
    for tid, t in TASKS.items():
        print(f"  - {tid}: {t.prompt[:60]}...")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="loop-engineer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run an agent on a task")
    p_run.add_argument("--agent", required=True, choices=["handroll", "deepagent", "both"])
    p_run.add_argument("--task", required=True)
    p_run.set_defaults(func=cmd_run)

    p_tasks = sub.add_parser("tasks", help="list available tasks")
    p_tasks.set_defaults(func=cmd_tasks)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
