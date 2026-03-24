"""Tests for the Liquidity SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.liquidity import Liquidity


@pytest.fixture
def liquidity(mock_subprocess):
    return Liquidity(AgcliRunner())


class TestLiquidity:
    def test_add(self, liquidity, mock_subprocess):
        liquidity.add(1, "0.5", "2.0", "100")
        cmd = mock_subprocess.call_args[0][0]
        assert "liquidity" in cmd and "add" in cmd
        assert "--price-low" in cmd and "--price-high" in cmd

    def test_add_with_hotkey(self, liquidity, mock_subprocess):
        liquidity.add(1, "0.5", "2.0", "100", hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd

    def test_remove(self, liquidity, mock_subprocess):
        liquidity.remove(1, "pos123")
        cmd = mock_subprocess.call_args[0][0]
        assert "remove" in cmd and "--position-id" in cmd

    def test_remove_with_hotkey(self, liquidity, mock_subprocess):
        liquidity.remove(1, "pos123", hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd

    def test_modify(self, liquidity, mock_subprocess):
        liquidity.modify(1, "pos123", "50")
        cmd = mock_subprocess.call_args[0][0]
        assert "modify" in cmd and "--delta" in cmd

    def test_modify_with_hotkey(self, liquidity, mock_subprocess):
        liquidity.modify(1, "pos123", "50", hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd

    def test_toggle(self, liquidity, mock_subprocess):
        liquidity.toggle(1, True)
        cmd = mock_subprocess.call_args[0][0]
        assert "toggle" in cmd and "--enable" in cmd
