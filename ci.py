import subprocess as sp
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from fire import Fire  # type: ignore

_repo_dir = Path(__file__).parent.resolve(strict=True)


def _tool_call(args: Iterable[str]) -> None:
    sp.call(["uv", "run", *args], cwd=_repo_dir)


def lint(unsafe: Any = False) -> None:
    targets = ["wet", "ci.py"]

    if unsafe:
        _tool_call(["ruff", "check", "--fix", "--unsafe-fixes", *targets])
    else:
        _tool_call(["ruff", "check", "--fix", *targets])

    # Weird enough, in Ruff isort is in the `check` command.
    _tool_call(["ruff", "check", "--select", "I,RUF022", "--fix", *targets])
    _tool_call(["ruff", "format", *targets])


def type_check() -> None:
    _tool_call(["pyright", "-p", "wet", "--threads", "16"])


def run_all() -> None:
    lint()
    type_check()


if __name__ == "__main__":
    Fire({"all": run_all, "lint": lint, "type-check": type_check})
