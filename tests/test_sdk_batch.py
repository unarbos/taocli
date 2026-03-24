"""Tests for the Batch SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.batch import Batch


@pytest.fixture
def batch(mock_subprocess):
    return Batch(AgcliRunner())


class TestBatch:
    def test_run(self, batch, mock_subprocess):
        batch.run("ops.json")
        cmd = mock_subprocess.call_args[0][0]
        assert "batch" in cmd and "--file" in cmd

    def test_run_no_atomic(self, batch, mock_subprocess):
        batch.run("ops.json", no_atomic=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--no-atomic" in cmd

    def test_run_force(self, batch, mock_subprocess):
        batch.run("ops.json", force=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--force" in cmd
