"""Tests for the Client SDK module."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from taocli.sdk.admin import Admin
from taocli.sdk.audit import Audit
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
from taocli.sdk.explain import Explain
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
        assert isinstance(c.audit, Audit)
        assert isinstance(c.batch, Batch)
        assert isinstance(c.block, Block)
        assert isinstance(c.contracts, Contracts)
        assert isinstance(c.crowdloan, Crowdloan)
        assert isinstance(c.diff, Diff)
        assert isinstance(c.drand, Drand)
        assert isinstance(c.evm, Evm)
        assert isinstance(c.explain, Explain)
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
    def test_weights_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, {"0": "100", "1": "200"}, salt="round-42", version_key=7, wait=True)
        assert helpers == {
            "normalized_weights": "0:100,1:200",
            "status": "agcli weights status --netuid 1",
            "set": "agcli weights set --netuid 1 --weights 0:100,1:200 --version-key 7",
            "commit_reveal": "agcli weights commit-reveal --netuid 1 --weights 0:100,1:200 --version-key 7 --wait",
            "commit": "agcli weights commit --netuid 1 --weights 0:100,1:200 --salt round-42",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100,1:200 --salt round-42 --version-key 7",
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_rejects_invalid_salt_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="salt cannot be empty"):
            c.weights.workflow_help(1, "0:100", salt="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"pending_commits": 1}')
        c = Client()
        result = c.weights.status(3)
        assert result == {"pending_commits": 1}
        cmd = mock_run.call_args[0][0]
        assert "weights" in cmd and "status" in cmd and "3" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_rejects_duplicate_uids_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="duplicate uid in weights: 0"):
            c.weights.set(1, "0:100,0:200")

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.weights.commit_reveal_help(1, "@weights.json", version_key=9, wait=True)
        assert command == "agcli weights commit-reveal --netuid 1 --weights @weights.json --version-key 9 --wait"

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_mechanism_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.weights.set_mechanism_help(1, 4, {0: 100}, version_key=2)
        assert command == "agcli weights set-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --version-key 2"

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_mechanism_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.weights.commit_mechanism_help(1, 4, b"\x11" * 32)
        assert command == ("agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash 0x" + "11" * 32)

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_mechanism_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.weights.reveal_mechanism_help(1, 4, {0: 100}, salt=b"abc", version_key=2)
        assert command == (
            "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 2"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_timelocked_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.weights.commit_timelocked_help(1, {0: 100}, 42, salt="abc")
        assert command == "agcli weights commit-timelocked --netuid 1 --weights 0:100 --round 42 --salt abc"

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_flow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.commit_reveal_flow_help(1, "0:100", salt=b"abc", version_key=2)
        assert helpers == {
            "normalized_weights": "0:100",
            "commit": "agcli weights commit --netuid 1 --weights 0:100 --salt abc",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 2",
            "status": "agcli weights status --netuid 1",
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_runbook_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.commit_reveal_runbook_help(97, "0:100", version_key=6, salt="abc")
        assert helpers["netuid"] == 97
        assert helpers["normalized_salt"] == "abc"
        assert helpers["commit_reveal_command"] == (
            "agcli weights commit-reveal --netuid 97 --weights 0:100 --version-key 6"
        )
        assert helpers["reveal_command"] == (
            "agcli weights reveal --netuid 97 --weights 0:100 --salt abc --version-key 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_operator_note_for_atomic_commit_reveal_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.operator_note_for_atomic_commit_reveal_help(97, "0:100", version_key=6, salt="abc")
        assert "operator_note" in helpers
        assert "revealed manually later" in helpers["operator_note"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_unrevealed_commit_help_via_client_surface(self, mock_run, tmp_path) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        state_path = tmp_path / "weights-state.json"
        c.weights.save_commit_reveal_state_help(state_path, 97, "0:100", "abc", version_key=6)
        helpers = c.weights.troubleshoot_unrevealed_commit_help(state_path, error="Custom error: 16")
        assert helpers["likely_cause"] == "The runtime returned a generic reveal-side custom error."
        assert helpers["reveal_command"] == (
            "agcli weights reveal --netuid 97 --weights 0:100 --salt abc --version-key 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.status_help(4) == "agcli weights status --netuid 4"

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.set_help(1, '{"0": 100}', version_key=5) == (
            "agcli weights set --netuid 1 --weights 0:100 --version-key 5"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.reveal_help(1, [(0, 100)], salt="abc", version_key=5) == (
            "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 5"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.commit_help(1, {0: 100}, salt="abc") == (
            "agcli weights commit --netuid 1 --weights 0:100 --salt abc"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_accepts_file_marker_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "@weights.json", salt="abc")
        assert helpers["normalized_weights"] == "@weights.json"
        assert helpers["set"] == "agcli weights set --netuid 1 --weights @weights.json"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights @weights.json --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights @weights.json --salt abc"
        assert helpers["status"] == "agcli weights status --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_accepts_json_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, '{"0": 100}', salt="abc")
        assert helpers["normalized_weights"] == "0:100"
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100"

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_accepts_bytes_salt_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt=b"abc")
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc"

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.weights.workflow_help(0, "0:100", salt="abc")

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_help_rejects_invalid_version_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            c.weights.reveal_help(1, "0:100", salt="abc", version_key=-1)

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.weights.status_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_runs_with_normalized_json_weights_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.set(1, '{"0": 100, "1": 200}', version_key=3)
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "weights" in cmd and "set" in cmd and "0:100,1:200" in cmd and "--version-key" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_runs_with_wait_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.commit_reveal(1, {0: 100}, version_key=7, wait=True)
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "commit-reveal" in cmd and "0:100" in cmd and "--version-key" in cmd and "--wait" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_runs_with_bytes_salt_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.reveal(1, {0: 100}, salt=b"abc", version_key=8)
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "reveal" in cmd and "0:100" in cmd and "abc" in cmd and "--version-key" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_timelocked_runs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.commit_timelocked(1, {0: 100}, 42, salt="abc")
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "commit-timelocked" in cmd and "0:100" in cmd and "42" in cmd and "abc" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_mechanism_help_not_available_but_command_path_is_covered(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.commit_mechanism(1, 0, "11" * 32)
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "commit-mechanism" in cmd and "--mechanism-id" in cmd and "--hash" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_mechanism_runs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.reveal_mechanism(1, 0, {0: 100}, salt="abc", version_key=2)
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "reveal-mechanism" in cmd and "--mechanism-id" in cmd and "0:100" in cmd and "abc" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_mechanism_runs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.set_mechanism(1, 0, {0: 100}, version_key=2)
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "set-mechanism" in cmd and "--mechanism-id" in cmd and "0:100" in cmd and "--version-key" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_mechanism_rejects_bad_hash_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hash must be valid hex"):
            c.weights.commit_mechanism(1, 0, "xyz")

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_timelocked_rejects_bad_round_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="round must be greater than or equal to 0"):
            c.weights.commit_timelocked(1, "0:100", -1)

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_flow_help_rejects_invalid_version_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            c.weights.commit_reveal_flow_help(1, "0:100", salt="abc", version_key=-1)

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_help_rejects_invalid_salt_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="salt cannot be empty"):
            c.weights.commit_help(1, "0:100", salt="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_help_rejects_invalid_version_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            c.weights.commit_reveal_help(1, "0:100", version_key=-1)

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_help_rejects_invalid_version_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            c.weights.set_help(1, "0:100", version_key=-1)

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_help_rejects_invalid_salt_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="salt cannot be empty"):
            c.weights.reveal_help(1, "0:100", salt="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.weights.status(0)

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.weights.show(0)

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_runs_with_options_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout='{"ok": true}')
        c = Client()
        result = c.weights.show(1, hotkey_address="5G...", limit=5)
        assert result == {"ok": True}
        cmd = mock_run.call_args[0][0]
        assert "show" in cmd and "--hotkey-address" in cmd and "5G..." in cmd and "--limit" in cmd

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_matches_commit_reveal_flow_subset_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        workflow = c.weights.workflow_help(1, "0:100", salt="abc", version_key=2)
        flow = c.weights.commit_reveal_flow_help(1, "0:100", salt="abc", version_key=2)
        assert flow == {
            "normalized_weights": workflow["normalized_weights"],
            "commit": workflow["commit"],
            "reveal": workflow["reveal"],
            "status": workflow["status"],
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_includes_wait_only_on_commit_reveal_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc", wait=True)
        assert helpers["commit_reveal"].endswith(" --wait")
        assert "--wait" not in helpers["commit"]
        assert "--wait" not in helpers["reveal"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_troubleshooting_example_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(
            7,
            {"12": "65535"},
            salt="tempo-12",
            version_key=9,
            wait=True,
        )
        assert helpers["status"] == "agcli weights status --netuid 7"
        assert helpers["set"] == "agcli weights set --netuid 7 --weights 12:65535 --version-key 9"
        assert (
            helpers["commit_reveal"]
            == "agcli weights commit-reveal --netuid 7 --weights 12:65535 --version-key 9 --wait"
        )
        assert helpers["commit"] == "agcli weights commit --netuid 7 --weights 12:65535 --salt tempo-12"
        assert helpers["reveal"] == "agcli weights reveal --netuid 7 --weights 12:65535 --salt tempo-12 --version-key 9"

    @patch("taocli.runner.subprocess.run")
    def test_weights_mechanism_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.mechanism_workflow_help(1, 4, {0: 100}, salt="abc", hash_value="11" * 32, version_key=2)
        assert helpers == {
            "normalized_weights": "0:100",
            "normalized_salt": "abc",
            "hash": "11" * 32,
            "status": "agcli weights status --netuid 1",
            "set_mechanism": "agcli weights set-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --version-key 2",
            "commit_mechanism": ("agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash " + "11" * 32),
            "reveal_mechanism": (
                "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 2"
            ),
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_timelocked_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.timelocked_workflow_help(1, {0: 100}, 42, salt="abc", version_key=2)
        assert helpers == {
            "normalized_weights": "0:100",
            "normalized_salt": "abc",
            "hash": "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339",
            "round": 42,
            "status": "agcli weights status --netuid 1",
            "set": "agcli weights set --netuid 1 --weights 0:100 --version-key 2",
            "commit_timelocked": "agcli weights commit-timelocked --netuid 1 --weights 0:100 --round 42 --salt abc",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 2",
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_mechanism_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.troubleshoot_mechanism_help(
            1,
            4,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            hash_value="11" * 32,
            version_key=7,
            status={
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                        "blocks_until_action": 5,
                    }
                ],
            },
        )
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending mechanism commit is ready to reveal now."

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_mechanism_help_derives_hash_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.troubleshoot_mechanism_help(
            1,
            4,
            "NoWeightsCommitFound",
            "0:100",
            salt="abc",
            status={
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [],
            },
        )
        assert helpers["normalized_hash"] == "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339"
        assert helpers["commit_mechanism"] == (
            "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash "
            "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339"
        )
        assert helpers["recommended_command"] == helpers["commit_mechanism"]
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_mechanism_action_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        c = Client()
        helpers = c.weights.next_mechanism_action(7, 4, "0:100", hash_value="11" * 32)
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == (
            "agcli weights commit-mechanism --netuid 7 --mechanism-id 4 --hash " + "11" * 32
        )
        assert helpers["reason"] == "No mechanism commit is pending and this subnet uses commit-reveal."

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_timelocked_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.troubleshoot_timelocked_help(
            7,
            "ExpiredWeightCommit",
            "0:100",
            round=42,
            salt="abc",
            version_key=8,
            status={
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [{"commit_block": 100, "first_reveal": 110, "last_reveal": 130, "status": "EXPIRED"}],
            },
        )
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == (
            "agcli weights commit-timelocked --netuid 7 --weights 0:100 --round 42 --salt abc"
        )
        assert helpers["reason"] == (
            "A previous pending timelocked commit expired, so a fresh timelocked commit is required."
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_timelocked_action_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        c = Client()
        helpers = c.weights.next_timelocked_action(7, "0:100", round=42, salt="abc")
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == (
            "agcli weights commit-timelocked --netuid 7 --weights 0:100 --round 42 --salt abc"
        )
        assert helpers["reason"] == (
            "A previous pending timelocked commit expired, so a fresh timelocked commit is required."
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.troubleshoot_help(
            1,
            "IncorrectCommitRevealVersion",
            "0:100",
            salt="abc",
            version_key=7,
        )
        assert helpers == {
            "error": "IncorrectCommitRevealVersion",
            "likely_cause": "The subnet expects a different version_key than the one provided.",
            "next_step": "Inspect the subnet hyperparameters, then retry with the matching version_key.",
            "status": "agcli weights status --netuid 1",
            "normalized_weights": "0:100",
            "set": "agcli weights set --netuid 1 --weights 0:100 --version-key 7",
            "commit": "agcli weights commit --netuid 1 --weights 0:100 --salt abc",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7",
            "commit_reveal": "agcli weights commit-reveal --netuid 1 --weights 0:100 --version-key 7",
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_help_with_status_includes_next_action_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.troubleshoot_help(
            1,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            version_key=7,
            status={
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                        "blocks_until_action": 5,
                    }
                ],
            },
        )
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending commit is ready to reveal now."

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_help_rejects_invalid_error_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="error cannot be empty"):
            c.weights.troubleshoot_help(1, "   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_summary_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"commit_block": 100, "first_reveal": 120, "last_reveal": 130, '
                '"status": "READY TO REVEAL (5 blocks remaining)", "blocks_until_action": 5}]}'
            )
        )
        c = Client()
        summary = c.weights.status_summary(5)
        assert summary == {
            "status": "agcli weights status --netuid 5",
            "current_block": 125,
            "commit_reveal_enabled": True,
            "reveal_period_epochs": 3,
            "pending_commits": 1,
            "pending_statuses": ["READY TO REVEAL (5 blocks remaining)"],
            "next_action": "REVEAL",
            "commit_windows": [
                {
                    "index": 1,
                    "status": "READY TO REVEAL (5 blocks remaining)",
                    "commit_block": 100,
                    "first_reveal": 120,
                    "last_reveal": 130,
                    "blocks_until_action": 5,
                }
            ],
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_action_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.next_action_help(
            3,
            {
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [],
            },
            {0: 100},
            version_key=9,
            wait=True,
        )
        assert helpers == {
            "status": "agcli weights status --netuid 3",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
            "recommended_action": "NO_PENDING_COMMITS",
            "recommended_command": "agcli weights commit-reveal --netuid 3 --weights 0:100 --version-key 9 --wait",
            "reason": "No commit is pending and this subnet uses commit-reveal.",
            "normalized_weights": "0:100",
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_action_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        c = Client()
        helpers = c.weights.next_action(7, "0:100", salt="abc")
        assert helpers == {
            "status": "agcli weights status --netuid 7",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 1,
                "pending_statuses": ["EXPIRED"],
                "next_action": "RECOMMIT",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "EXPIRED",
                        "commit_block": 100,
                        "first_reveal": 110,
                        "last_reveal": 130,
                    }
                ],
            },
            "recommended_action": "RECOMMIT",
            "recommended_command": "agcli weights commit --netuid 7 --weights 0:100 --salt abc",
            "reason": "A previous pending commit expired, so fresh weights are required.",
            "normalized_weights": "0:100",
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        c = Client()
        helpers = c.weights.diagnose(7, "ExpiredWeightCommit")
        assert helpers == {
            "error": "ExpiredWeightCommit",
            "likely_cause": "The previous commit expired before it was revealed.",
            "next_step": "Commit again, then reveal inside the next valid reveal window.",
            "status": "agcli weights status --netuid 7",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 1,
                "pending_statuses": ["EXPIRED"],
                "next_action": "RECOMMIT",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "EXPIRED",
                        "commit_block": 100,
                        "first_reveal": 110,
                        "last_reveal": 130,
                    }
                ],
            },
            "recommended_action": "RECOMMIT",
            "recommended_command": "agcli weights status --netuid 7",
            "reason": "A previous pending commit expired, so fresh weights are required.",
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_fetches_live_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"commit_block": 100, "first_reveal": 120, '
                '"last_reveal": 130, "status": "READY TO REVEAL (5 blocks remaining)", '
                '"blocks_until_action": 5}]}'
            )
        )
        c = Client()
        helpers = c.weights.troubleshoot(1, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending commit is ready to reveal now."
        assert helpers["status_summary"]["next_action"] == "REVEAL"

    @patch("taocli.runner.subprocess.run")
    def test_weights_troubleshoot_rejects_non_mapping_status_output_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="[1, 2, 3]")
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            c.weights.troubleshoot(3, "NoWeightsCommitFound")

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_action_rejects_non_mapping_status_output_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="[1, 2, 3]")
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            c.weights.next_action(3)

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_rejects_non_mapping_status_output_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="[1, 2, 3]")
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            c.weights.diagnose(3, "NoWeightsCommitFound")

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_mechanism_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"commit_block": 100, "first_reveal": 120, '
                '"last_reveal": 130, "status": "READY TO REVEAL (5 blocks remaining)", '
                '"blocks_until_action": 5}]}'
            )
        )
        c = Client()
        helpers = c.weights.diagnose_mechanism(1, 4, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending mechanism commit is ready to reveal now."
        assert helpers["status_summary"]["next_action"] == "REVEAL"

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_mechanism_rejects_non_mapping_status_output_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="[1, 2, 3]")
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            c.weights.diagnose_mechanism(3, 4, "NoWeightsCommitFound")

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_timelocked_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        c = Client()
        helpers = c.weights.diagnose_timelocked(7, "ExpiredWeightCommit", "0:100", round=42, salt="abc")
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == (
            "agcli weights commit-timelocked --netuid 7 --weights 0:100 --round 42 --salt abc"
        )
        assert helpers["reason"] == (
            "A previous pending timelocked commit expired, so a fresh timelocked commit is required."
        )
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"
        assert helpers["round"] == 42

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_timelocked_rejects_non_mapping_status_output_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="[1, 2, 3]")
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            c.weights.diagnose_timelocked(3, "NoWeightsCommitFound")

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
