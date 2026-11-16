"""Regression tests for core.host.upload()'s remote media name.

The name must be stable for identical bytes: Instagram and Facebook fetch the
file by URL, and a name that changes on every run means the same card is
re-uploaded (and re-downloaded) every day instead of reusing the existing blob.

The name embedded abs(hash(path.name)), and str.__hash__ is salted per process,
so the same file produced a different remote name in every process. The
subprocess test below pins PYTHONHASHSEED, so it fails on the old code whatever
seed this process happened to start with.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core import host  # noqa: E402

_CHILD = """
import sys
sys.path.insert(0, {root!r})
from core import host

def fake_request(method, url, json_body=None, **kwargs):
    return 422, {{"message": "already exists"}}

host.request = fake_request
print(host.upload({media!r}, remote_dir="media"))
"""


def _upload_in_child(media_file, seed):
    env = dict(os.environ, PYTHONHASHSEED=str(seed))
    out = subprocess.run(
        [sys.executable, "-c", _CHILD.format(root=str(ROOT), media=str(media_file))],
        capture_output=True, text=True, env=env, check=True,
    )
    return out.stdout.strip()


@pytest.fixture()
def media_file(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_REPO", "owner/repo")
    monkeypatch.setenv("GITHUB_PAGES_URL", "https://owner.github.io/repo")
    path = tmp_path / "card.jpg"
    path.write_bytes(b"identical bytes")
    return path


def test_name_is_stable_across_processes_with_different_hash_seeds(media_file):
    assert _upload_in_child(media_file, 1) == _upload_in_child(media_file, 2)


def test_name_is_a_pure_function_of_bytes_and_mtime(media_file, monkeypatch):
    monkeypatch.setattr(host, "request", lambda *a, **k: (201, {"content": {}}))
    first = host.upload(media_file, remote_dir="media")
    second = host.upload(media_file, remote_dir="media")
    assert first == second
    assert first.rsplit("/", 1)[-1].startswith("card-")


def test_upload_is_a_noop_without_hosting_config(media_file, monkeypatch):
    monkeypatch.delenv("GITHUB_PAGES_URL", raising=False)
    assert host.upload(media_file) is None
