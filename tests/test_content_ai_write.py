"""Regression tests for the AI_WRITE switch in core.content.build_post().

The daily workflow exports AI_WRITE from a repository variable
(docs/github-actions-daily.yml) and .env.example ships AI_WRITE=no, but
build_post() only looked at its own ai_write argument, so setting the variable
to "yes" silently produced the built-in caption.
"""
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import content  # noqa: E402

DAY = date(2026, 11, 16)


@pytest.fixture()
def rewritten(monkeypatch):
    calls = []
    monkeypatch.setattr(content, "_ai_caption", lambda h, b: calls.append(h) or "REWRITTEN")
    return calls


@pytest.mark.parametrize("value", ["yes", "YES", "true", "1"])
def test_env_variable_turns_the_rewrite_on(value, rewritten, monkeypatch):
    monkeypatch.setenv("AI_WRITE", value)
    post = content.build_post(DAY)
    assert rewritten, "AI_WRITE should have asked the model for a caption"
    assert "REWRITTEN" in post["caption"]


@pytest.mark.parametrize("value", ["", "no", "0", "false"])
def test_env_variable_left_off_keeps_the_built_in_copy(value, rewritten, monkeypatch):
    monkeypatch.setenv("AI_WRITE", value)
    post = content.build_post(DAY)
    assert not rewritten
    assert post["caption"].startswith(post["headline"])


def test_explicit_argument_still_wins(rewritten, monkeypatch):
    monkeypatch.setenv("AI_WRITE", "no")
    assert "REWRITTEN" in content.build_post(DAY, ai_write=True)["caption"]
