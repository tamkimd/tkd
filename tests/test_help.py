from __future__ import annotations

import asyncio

from tkd.cli import build_parser


def test_help_command(capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(["help", "sync"])

    assert asyncio.run(args.func(args)) == 0

    captured = capsys.readouterr()
    assert "usage: tkd sync" in captured.out


def test_root_help_shows_check_not_legacy_aliases(capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(["help"])

    assert asyncio.run(args.func(args)) == 0

    captured = capsys.readouterr()
    assert "check" in captured.out
    assert "validate" not in captured.out
    assert "list" not in captured.out


def test_sync_help_shows_ask_env(capsys) -> None:
    parser = build_parser()
    args = parser.parse_args(["help", "sync"])

    assert asyncio.run(args.func(args)) == 0

    captured = capsys.readouterr()
    assert "--ask-env" in captured.out
