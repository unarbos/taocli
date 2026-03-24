"""Tests for the Multisig SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.multisig import Multisig


@pytest.fixture
def multisig(mock_subprocess):
    return Multisig(AgcliRunner())


class TestMultisig:
    def test_address(self, multisig, mock_subprocess):
        multisig.address("5G...,5H...", 2)
        cmd = mock_subprocess.call_args[0][0]
        assert "multisig" in cmd and "address" in cmd
        assert "--signatories" in cmd and "--threshold" in cmd

    def test_submit(self, multisig, mock_subprocess):
        multisig.submit("5G...", 2, "Balances", "transfer")
        cmd = mock_subprocess.call_args[0][0]
        assert "multisig" in cmd and "submit" in cmd
        assert "--pallet" in cmd and "--call" in cmd

    def test_submit_with_args(self, multisig, mock_subprocess):
        multisig.submit("5G...", 2, "Balances", "transfer", args='["5H...", 100]')
        cmd = mock_subprocess.call_args[0][0]
        assert "--args" in cmd

    def test_approve(self, multisig, mock_subprocess):
        multisig.approve("5G...", 2, "0xabc")
        cmd = mock_subprocess.call_args[0][0]
        assert "approve" in cmd and "--call-hash" in cmd

    def test_execute(self, multisig, mock_subprocess):
        multisig.execute("5G...", 2, "Balances", "transfer")
        cmd = mock_subprocess.call_args[0][0]
        assert "execute" in cmd

    def test_execute_with_timepoint(self, multisig, mock_subprocess):
        multisig.execute("5G...", 2, "Balances", "transfer", timepoint_height=100, timepoint_index=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--timepoint-height" in cmd and "--timepoint-index" in cmd

    def test_execute_with_args(self, multisig, mock_subprocess):
        multisig.execute("5G...", 2, "Balances", "transfer", args="[]")
        cmd = mock_subprocess.call_args[0][0]
        assert "--args" in cmd

    def test_cancel(self, multisig, mock_subprocess):
        multisig.cancel("5G...", 2, "0xabc", 100, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "cancel" in cmd and "--timepoint-height" in cmd

    def test_list(self, multisig, mock_subprocess):
        multisig.list("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "list" in cmd and "--address" in cmd
