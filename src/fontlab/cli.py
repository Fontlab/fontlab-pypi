# this_file: src/fontlab/cli.py
"""Install FontLab and request local or Remopy-backed automation."""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
import subprocess
import sys
from pathlib import Path

from . import automation, installer


def _timeout(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive finite number")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--beta", action="store_true", help="Install beta if FontLab is absent"
    )
    common.add_argument(
        "--destination",
        type=Path,
        help="Application bundle (macOS) or executable (Windows)",
    )
    common.add_argument(
        "--verbose", action="store_true", help="Show exception details on failure"
    )
    commands = parser.add_subparsers(dest="operation", required=True)
    for operation in (
        "install",
        "latest",
        "launch",
        "submit",
        "run",
        "eval",
        "tools",
        "call",
    ):
        command = commands.add_parser(operation, parents=[common])
        if operation == "submit":
            command.add_argument("path", type=Path)
        if operation in {"run", "eval", "tools", "call"}:
            command.add_argument("--timeout", type=_timeout, default=30)
        if operation == "run":
            command.add_argument("path", type=Path)
        if operation == "eval":
            command.add_argument("expression")
        if operation == "call":
            command.add_argument("name")
            command.add_argument("--arguments", type=json.loads, default={})
    args = parser.parse_args(argv)
    options = {"beta": args.beta, "destination": args.destination}
    try:
        match args.operation:
            case "latest":
                result = dataclasses.asdict(installer.latest_release(beta=args.beta))
            case "install":
                result = {"application": str(installer.install(**options))}
            case "launch":
                result = {
                    "application": str(automation.launch(**options)),
                    "launch_requested": True,
                }
            case "submit":
                automation.submit_script(args.path, **options)
                result = {"path": str(args.path), "execution_verified": False}
            case _:
                if args.operation == "run" and not args.path.is_file():
                    raise FileNotFoundError(args.path)
                if args.operation == "call" and not isinstance(args.arguments, dict):
                    raise ValueError("--arguments must be a JSON object")
                with automation.connect(**options, timeout=args.timeout) as client:
                    match args.operation:
                        case "run":
                            result = dataclasses.asdict(
                                client.execute_script(args.path)
                            )
                        case "eval":
                            result = client.eval(args.expression)
                        case "tools":
                            result = [
                                tool.model_dump(mode="json") for tool in client.tools()
                            ]
                        case "call":
                            result = client.tool(args.name, **args.arguments)
        print(json.dumps(result, indent=2))
    except Exception as error:
        if args.verbose:
            raise
        print(f"fontlab-cli: {type(error).__name__}: {error}", file=sys.stderr)
        notes = getattr(error, "__notes__", ()) or getattr(
            error.__cause__, "__notes__", ()
        )
        for note in notes:
            print(note, file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            detail = error.stderr
            if isinstance(detail, bytes):
                detail = detail.decode(errors="replace")
            print(detail.rstrip(), file=sys.stderr)
        if isinstance(error, (TimeoutError, ExceptionGroup)):
            print(
                "Execution outcome may be unknown; inspect FontLab before retrying.",
                file=sys.stderr,
            )
        return 1
    return 0
