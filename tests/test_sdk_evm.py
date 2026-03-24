"""Tests for the Evm SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.evm import Evm


@pytest.fixture
def evm(mock_subprocess):
    return Evm(AgcliRunner())


class TestEvm:
    def test_call(self, evm, mock_subprocess):
        evm.call("0xsrc", "0xtgt", "0xdata")
        cmd = mock_subprocess.call_args[0][0]
        assert "evm" in cmd and "call" in cmd
        assert "--source" in cmd and "--target" in cmd

    def test_call_with_opts(self, evm, mock_subprocess):
        evm.call("0xsrc", "0xtgt", "0xdata", value="100", gas_limit=21000, max_fee_per_gas="10")
        cmd = mock_subprocess.call_args[0][0]
        assert "--value" in cmd and "--gas-limit" in cmd and "--max-fee-per-gas" in cmd

    def test_withdraw(self, evm, mock_subprocess):
        evm.withdraw("5G...", "100")
        cmd = mock_subprocess.call_args[0][0]
        assert "withdraw" in cmd and "--address" in cmd and "--amount" in cmd
