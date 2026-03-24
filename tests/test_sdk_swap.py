"""Tests for the Swap SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.swap import Swap


@pytest.fixture
def swap(mock_subprocess):
    return Swap(AgcliRunner())


class TestSwap:
    def test_hotkey(self, swap, mock_subprocess):
        swap.hotkey("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd and "hotkey" in cmd and "--new-hotkey" in cmd

    def test_coldkey(self, swap, mock_subprocess):
        swap.coldkey("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd and "coldkey" in cmd and "--new-coldkey" in cmd

    def test_evm_key(self, swap, mock_subprocess):
        swap.evm_key("0xabc123", 100, "0xsig")
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd and "evm-key" in cmd
        assert "--evm-address" in cmd and "--block-number" in cmd and "--signature" in cmd

    def test_schedule_alias(self, swap, mock_subprocess):
        swap.schedule("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd and "coldkey" in cmd and "--new-coldkey" in cmd

    def test_status(self, swap, mock_subprocess):
        swap.status()
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd and "status" in cmd
