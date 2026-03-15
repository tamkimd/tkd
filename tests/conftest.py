from __future__ import annotations

from pathlib import Path

import pytest


class Args:
    def __init__(self, config: str, env=None, ask_env: bool = False) -> None:
        self.config = config
        self.env = env
        self.ask_env = ask_env


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def test_helpers():
    class Helpers:
        @staticmethod
        def write(path: Path, content: str) -> None:
            write(path, content)

    return Helpers
