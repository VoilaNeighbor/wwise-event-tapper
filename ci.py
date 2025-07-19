from collections.abc import Iterable
from pathlib import Path
from typing import Any
from fire import Fire
import subprocess as sp

_repo_dir = Path(__file__).parent.resolve(strict=True)


def _tool_call(args: Iterable[str]) -> None:
    sp.call(["uv", "run", *args], cwd=_repo_dir)


def lint(unsafe: Any = False) -> None:
    if unsafe:
        _tool_call(["ruff", "check", "wet", "--fix", "--unsafe-fixes"])
    else:
        _tool_call(["ruff", "check", "wet", "--fix"])

    _tool_call(["ruff", "format", "wet"])


if __name__ == "__main__":
    Fire({"lint": lint})
