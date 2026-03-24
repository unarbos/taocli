"""Tests for the Client SDK module."""

from __future__ import annotations

from unittest.mock import patch

from taocli.sdk.client import Client
from taocli.sdk.delegate import Delegate
from taocli.sdk.root import Root
from taocli.sdk.stake import Stake
from taocli.sdk.subnet import Subnet
from taocli.sdk.transfer import Transfer
from taocli.sdk.view import View
from taocli.sdk.wallet import Wallet
from taocli.sdk.weights import Weights
from tests.conftest import make_completed_process


class TestClientInit:
    @patch("taocli.runner.subprocess.run")
    def test_default_init(self, mock_run):
        mock_run.return_value = make_completed_process()
        c = Client()
        assert isinstance(c.wallet, Wallet)
        assert isinstance(c.stake, Stake)
        assert isinstance(c.transfer, Transfer)
        assert isinstance(c.subnet, Subnet)
        assert isinstance(c.weights, Weights)
        assert isinstance(c.delegate, Delegate)
        assert isinstance(c.root, Root)
        assert isinstance(c.view, View)

    @patch("taocli.runner.subprocess.run")
    def test_custom_init(self, mock_run):
        mock_run.return_value = make_completed_process()
        c = Client(
            binary="/usr/bin/agcli",
            network="test",
            endpoint="ws://localhost:9944",
            wallet="mywallet",
            hotkey_name="hk",
            password="pw",
            proxy="5G...",
            timeout=30,
            wallet_dir="/tmp",
        )
        assert c._runner.binary == "/usr/bin/agcli"
        assert c._runner.network == "test"
        assert c._runner.yes is True
        assert c._runner.batch is True
        assert c._runner.output == "json"


class TestClientMethods:
    @patch("taocli.runner.subprocess.run")
    def test_balance(self, mock_run):
        mock_run.return_value = make_completed_process(stdout='{"free": 100}')
        c = Client()
        result = c.balance()
        assert result == {"free": 100}

    @patch("taocli.runner.subprocess.run")
    def test_balance_with_address(self, mock_run):
        mock_run.return_value = make_completed_process(stdout='{"free": 50}')
        c = Client()
        c.balance(address="5G...")
        cmd = mock_run.call_args[0][0]
        assert "--address" in cmd
        assert "5G..." in cmd

    @patch("taocli.runner.subprocess.run")
    def test_balance_at_block(self, mock_run):
        mock_run.return_value = make_completed_process(stdout='{"free": 50}')
        c = Client()
        c.balance(at_block=1000)
        cmd = mock_run.call_args[0][0]
        assert "--at-block" in cmd
        assert "1000" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_doctor(self, mock_run):
        mock_run.return_value = make_completed_process(stdout="All checks passed\n")
        c = Client()
        result = c.doctor()
        assert "All checks passed" in result

    @patch("taocli.runner.subprocess.run")
    def test_version(self, mock_run):
        mock_run.return_value = make_completed_process(stdout="agcli 0.1.0\n")
        c = Client()
        assert c.version() == "agcli 0.1.0"
