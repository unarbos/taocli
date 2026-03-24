"""Tests for the Audit SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.audit import Audit


@pytest.fixture
def audit(mock_subprocess):
    return Audit(AgcliRunner())


class TestAudit:
    def test_run_default(self, audit, mock_subprocess):
        audit.run()
        cmd = mock_subprocess.call_args[0][0]
        assert "audit" in cmd
        assert "--address" not in cmd

    def test_run_with_address(self, audit, mock_subprocess):
        audit.run("5FHneW46...")
        cmd = mock_subprocess.call_args[0][0]
        assert "audit" in cmd and "--address" in cmd
