"""Tests for the Swap SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.swap import Swap


@pytest.fixture
def swap(mock_subprocess):
    return Swap(AgcliRunner())


class TestSwap:
    def test_schedule(self, swap, mock_subprocess):
        swap.schedule("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd and "schedule" in cmd and "--new-coldkey" in cmd

    def test_status(self, swap, mock_subprocess):
        swap.status()
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd and "status" in cmd
