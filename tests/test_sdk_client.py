"""Tests for the Client SDK module."""

from __future__ import annotations

from unittest.mock import patch

from taocli.sdk.admin import Admin
from taocli.sdk.batch import Batch
from taocli.sdk.block import Block
from taocli.sdk.client import Client
from taocli.sdk.commitment import Commitment
from taocli.sdk.config import Config
from taocli.sdk.contracts import Contracts
from taocli.sdk.crowdloan import Crowdloan
from taocli.sdk.delegate import Delegate
from taocli.sdk.diff import Diff
from taocli.sdk.drand import Drand
from taocli.sdk.evm import Evm
from taocli.sdk.identity import Identity
from taocli.sdk.liquidity import Liquidity
from taocli.sdk.localnet import Localnet
from taocli.sdk.multisig import Multisig
from taocli.sdk.preimage import Preimage
from taocli.sdk.proxy import Proxy
from taocli.sdk.root import Root
from taocli.sdk.safe_mode import SafeMode
from taocli.sdk.scheduler import Scheduler
from taocli.sdk.serve import Serve
from taocli.sdk.stake import Stake
from taocli.sdk.subnet import Subnet
from taocli.sdk.subscribe import Subscribe
from taocli.sdk.swap import Swap
from taocli.sdk.transfer import Transfer
from taocli.sdk.utils import Utils
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
        assert isinstance(c.identity, Identity)
        assert isinstance(c.proxy, Proxy)
        assert isinstance(c.serve, Serve)
        assert isinstance(c.commitment, Commitment)
        assert isinstance(c.utils, Utils)
        assert isinstance(c.config, Config)
        assert isinstance(c.swap, Swap)
        assert isinstance(c.admin, Admin)
        assert isinstance(c.batch, Batch)
        assert isinstance(c.block, Block)
        assert isinstance(c.contracts, Contracts)
        assert isinstance(c.crowdloan, Crowdloan)
        assert isinstance(c.diff, Diff)
        assert isinstance(c.drand, Drand)
        assert isinstance(c.evm, Evm)
        assert isinstance(c.liquidity, Liquidity)
        assert isinstance(c.localnet, Localnet)
        assert isinstance(c.multisig, Multisig)
        assert isinstance(c.preimage, Preimage)
        assert isinstance(c.safe_mode, SafeMode)
        assert isinstance(c.scheduler, Scheduler)
        assert isinstance(c.subscribe, Subscribe)

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
