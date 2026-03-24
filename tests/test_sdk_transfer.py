"""Tests for the Transfer SDK module."""

from __future__ import annotations

import pytest

from pytao.runner import AgcliRunner
from pytao.sdk.transfer import Transfer


@pytest.fixture
def xfer(mock_subprocess):
    return Transfer(AgcliRunner())


class TestTransfer:
    def test_transfer(self, xfer, mock_subprocess):
        xfer.transfer("5G...", 10.0)
        cmd = mock_subprocess.call_args[0][0]
        assert "transfer" in cmd
        assert "--dest" in cmd and "5G..." in cmd
        assert "--amount" in cmd and "10.0" in cmd

    def test_transfer_all(self, xfer, mock_subprocess):
        xfer.transfer_all("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "transfer-all" in cmd
        assert "--dest" in cmd

    def test_transfer_all_keep_alive(self, xfer, mock_subprocess):
        xfer.transfer_all("5G...", keep_alive=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--keep-alive" in cmd

    def test_transfer_keep_alive(self, xfer, mock_subprocess):
        xfer.transfer_keep_alive("5G...", 5.0)
        cmd = mock_subprocess.call_args[0][0]
        assert "transfer-keep-alive" in cmd
        assert "--amount" in cmd
