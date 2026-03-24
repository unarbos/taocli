"""Shared fixtures for pytao tests."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from pytao.runner import AgcliRunner


def make_completed_process(
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["agcli"],
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run to return a configurable CompletedProcess."""
    with patch("pytao.runner.subprocess.run") as mock_run:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        yield mock_run


@pytest.fixture
def runner(mock_subprocess):
    """AgcliRunner with mocked subprocess."""
    return AgcliRunner()


@pytest.fixture
def json_runner(mock_subprocess):
    """AgcliRunner configured for SDK use (json + batch + yes)."""
    return AgcliRunner(yes=True, batch=True, output="json")
