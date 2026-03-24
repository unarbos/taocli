"""Tests for the SafeMode SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.safe_mode import SafeMode


@pytest.fixture
def safe_mode(mock_subprocess):
    return SafeMode(AgcliRunner())


class TestSafeMode:
    def test_enter(self, safe_mode, mock_subprocess):
        safe_mode.enter()
        cmd = mock_subprocess.call_args[0][0]
        assert "safe-mode" in cmd and "enter" in cmd

    def test_extend(self, safe_mode, mock_subprocess):
        safe_mode.extend()
        cmd = mock_subprocess.call_args[0][0]
        assert "safe-mode" in cmd and "extend" in cmd

    def test_force_enter(self, safe_mode, mock_subprocess):
        safe_mode.force_enter(100)
        cmd = mock_subprocess.call_args[0][0]
        assert "force-enter" in cmd and "--duration" in cmd

    def test_force_exit(self, safe_mode, mock_subprocess):
        safe_mode.force_exit()
        cmd = mock_subprocess.call_args[0][0]
        assert "force-exit" in cmd
