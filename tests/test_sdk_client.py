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
            "show": "agcli weights show --netuid 1",
            "show_command": "agcli weights show --netuid 1",
            "pending_commits": "agcli subnet commits --netuid 1",
            "hyperparams": "agcli subnet hyperparams --netuid 1",
            "set": "agcli weights set --netuid 1 --weights 0:100,1:200 --version-key 7",
            "commit_reveal": "agcli weights commit-reveal --netuid 1 --weights 0:100,1:200 --version-key 7 --wait",
            "commit": "agcli weights commit --netuid 1 --weights 0:100,1:200 --salt round-42",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100,1:200 --salt round-42 --version-key 7",
            "inspect_metagraph_command": "agcli subnet metagraph --netuid 1",
            "inspect_chain_data_command": "agcli subnet show --netuid 1",
            "inspect_subnets_command": "agcli subnet list",
            "inspect_subnet_command": "agcli subnet show --netuid 1",
            "inspect_hyperparams_command": "agcli subnet hyperparams --netuid 1",
            "inspect_emissions_command": "agcli view emissions --netuid 1",
            "inspect_neuron_command": "agcli view neuron --netuid 1 --uid 0",
            "inspect_validators_command": "agcli view validators --netuid 1",
            "inspect_stake_command": "agcli stake list --netuid 1",
            "inspect_config_show_command": "agcli config show",
            "inspect_wallet_show_command": "agcli wallet show --all",
            "inspect_wallet_current_command": "agcli wallet show",
            "inspect_wallet_associate_command": "agcli wallet associate-hotkey",
            "inspect_wallet_derive_command": "agcli wallet derive --input <pubkey-or-mnemonic>",
            "inspect_wallet_sign_command": "agcli wallet sign --message <message>",
            "inspect_wallet_verify_command": (
                "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
            ),
            "inspect_balance_command": "agcli balance",
            "inspect_stake_add_command": "agcli stake add --netuid 1 --amount <amount>",
            "inspect_validator_requirements_command": "agcli subnet hyperparams --netuid 1",
            "inspect_owner_param_list_command": "agcli subnet set-param --netuid 1 --param list",
            "inspect_set_param_command": "agcli subnet set-param --netuid 1",
            "inspect_admin_list_command": "agcli admin list",
            "inspect_admin_raw_command": "agcli admin raw --call <sudo-call>",
            "explain_weights_command": "agcli explain weights",
            "explain_commit_reveal_command": "agcli explain commit-reveal",
            "inspect_registration_cost_command": "agcli subnet cost --netuid 1",
            "inspect_register_neuron_command": "agcli subnet register-neuron --netuid 1",
            "inspect_pow_register_command": "agcli subnet pow --netuid 1",
            "inspect_snipe_register_command": "agcli subnet snipe --netuid 1",
            "inspect_health_command": "agcli subnet health --netuid 1",
            "inspect_serve_axon_command": "agcli serve axon --netuid 1 --ip <ip> --port <port>",
            "inspect_serve_axon_tls_command": "agcli serve axon-tls --netuid 1 --ip <ip> --port <port> --cert <cert>",
            "inspect_serve_prometheus_command": "agcli serve prometheus --netuid 1 --ip <ip> --port <port>",
            "inspect_serve_reset_command": "agcli serve reset --netuid 1",
            "inspect_probe_command": "agcli subnet probe --netuid 1",
            "inspect_axon_command": "agcli view axon --netuid 1",
            "inspect_miner_endpoints_command": "agcli view axon --netuid 1",
            "inspect_validator_endpoints_command": "agcli view axon --netuid 1",
            "inspect_watch_command": "agcli subnet watch --netuid 1",
            "inspect_monitor_command": "agcli subnet monitor --netuid 1 --json",
            "adjacent_workflows_note": (
                "If the weights-specific path still looks wrong, pivot to show/metagraph and chain_data plus emissions "
                "for live weights, subnet UIDs/state, pending_commits for operator watch/reveal drift checks, "
                "inspect_neuron_command for per-UID member detail after metagraph/monitor checks, "
                "config_show plus wallet_show plus wallet_current plus wallet_associate plus wallet_derive plus "
                "wallet_sign plus wallet_verify plus balance plus "
                "validators/stake/stake_add/validator_requirements for wallet "
                "selector inspection, wallet inventory plus selected coldkey/hotkey identity confirmation, hotkey "
                "association recovery, manual address derivation checks, signature generation, signature verification, "
                "coldkey funding, "
                "validator readiness, stake top-ups, or validator threshold checks, hyperparams plus "
                "owner_param_list/set_param/admin_list/admin_raw/registration_cost/register_neuron/pow_register/"
                "snipe_register/health for subnet readiness, subnet entry, registration retries, "
                "root-only mutation escape hatches, or mutation discovery, "
                "serve_axon plus serve_axon_tls plus serve_prometheus plus serve_reset plus probe plus "
                "axon/miner_endpoints/validator_endpoints for serve retries, TLS serve recovery, prometheus recovery, "
                "endpoint recovery, or serve/endpoint verification, watch plus monitor for live UID/state drift, "
                "explain_weights/explain_commit_reveal for copy-pasteable concept refreshers, and subnets plus "
                "subnet for available netuid discovery and the current subnet summary."
            ),
            "status_note": (
                "weights status resolves the current hotkey from agcli's global wallet selectors "
                "and inspects pending commits, reveal windows, and commit-reveal settings for "
                "that hotkey on the target subnet."
            ),
            "show_note": (
                "Use weights show when you want the live on-chain weights map; use weights status "
                "when you want commit-reveal state for your hotkey."
            ),
            "pending_commits_note": (
                "Use subnet commits when you need every on-chain pending commit for the subnet, "
                "especially when comparing saved reveal state against live status for one hotkey."
            ),
            "hyperparams_note": (
                "Inspect subnet hyperparams before retrying failed set/reveal flows so "
                "version_key, commit-reveal, and rate-limit assumptions match the subnet."
            ),
            "set_weights_note": (
                "Use direct weights set only when the subnet allows it; otherwise follow "
                "commit-reveal or the saved-state recovery helpers instead of reformatting "
                "commands manually."
            ),
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_with_wallet_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, {"0": "100"}, salt="round-42", wallet="cold", hotkey="miner")
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert helpers["wallet_selection_note"]
        assert helpers["status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 1"
        assert helpers["set"] == "agcli --wallet cold --hotkey-name miner weights set --netuid 1 --weights 0:100"
        assert (
            helpers["commit"]
            == "agcli --wallet cold --hotkey-name miner weights commit --netuid 1 --weights 0:100 --salt round-42"
        )
        assert (
            helpers["reveal"]
            == "agcli --wallet cold --hotkey-name miner weights reveal --netuid 1 --weights 0:100 --salt round-42"
        )
        assert (
            helpers["commit_reveal"]
            == "agcli --wallet cold --hotkey-name miner weights commit-reveal --netuid 1 --weights 0:100"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_serve_prerequisite_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.serve_prerequisite_help(5, wallet="cold", hotkey="miner")
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert helpers["status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 5"
        assert helpers["show"] == "agcli weights show --netuid 5"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 5"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_chain_data_command"] == "agcli subnet show --netuid 5"
        assert helpers["inspect_emissions_command"] == "agcli view emissions --netuid 5"
        assert helpers["inspect_neuron_command"] == "agcli view neuron --netuid 5 --uid 0"
        assert helpers["inspect_validators_command"] == "agcli view validators --netuid 5"
        assert helpers["inspect_stake_command"] == "agcli stake list --netuid 5"
        assert helpers["inspect_stake_add_command"] == "agcli stake add --netuid 5 --amount <amount>"
        assert helpers["inspect_validator_requirements_command"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_owner_param_list_command"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["inspect_set_param_command"] == "agcli subnet set-param --netuid 5"
        assert helpers["inspect_admin_list_command"] == "agcli admin list"
        assert helpers["inspect_admin_raw_command"] == "agcli admin raw --call <sudo-call>"
        assert helpers["inspect_registration_cost_command"] == "agcli subnet cost --netuid 5"
        assert helpers["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 5"
        assert helpers["inspect_pow_register_command"] == "agcli subnet pow --netuid 5"
        assert helpers["inspect_snipe_register_command"] == "agcli subnet snipe --netuid 5"
        assert helpers["inspect_health_command"] == "agcli subnet health --netuid 5"
        assert helpers["inspect_serve_axon_command"] == "agcli serve axon --netuid 5 --ip <ip> --port <port>"
        assert helpers["inspect_probe_command"] == "agcli subnet probe --netuid 5"
        assert helpers["inspect_axon_command"] == "agcli view axon --netuid 5"
        assert helpers["inspect_miner_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["inspect_validator_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["inspect_watch_command"] == "agcli subnet watch --netuid 5"
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 5 --json"
        assert helpers["adjacent_workflows_note"]
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["pending_commits_note"]
        assert helpers["hyperparams_note"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.show_help(5, hotkey_address="5F...", limit=3) == (
            "agcli weights show --netuid 5 --hotkey-address 5F... --limit 3"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_help_with_wallet_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.status_help(4, wallet="cold", hotkey="miner") == (
            "agcli --wallet cold --hotkey-name miner weights status --netuid 4"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_operator_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.operator_workflow_help(1, "0:100", "abc", wallet="cold")
        assert helpers["wallet"] == "cold"
        assert helpers["status"] == "agcli --wallet cold weights status --netuid 1"
        assert helpers["show"] == "agcli weights show --netuid 1"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 1"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 1"
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["pending_commits_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.weights.workflow_help(1, "0:100", salt="abc", wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_rejects_invalid_limit_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="limit must be greater than 0"):
            c.weights.show_help(5, limit=0)

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_rejects_empty_hotkey_address_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey_address cannot be empty"):
            c.weights.show_help(5, hotkey_address="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_serve_prerequisite_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.weights.serve_prerequisite_help(5, hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_inspect_hyperparams_help_alias_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.inspect_hyperparams_help(5) == "agcli subnet hyperparams --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_weights_inspect_version_key_help_old_alias_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.inspect_version_key_help_old(5) == "agcli subnet hyperparams --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_help_with_wallet_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.commit_help(1, "0:100", salt="abc", wallet="cold", hotkey="miner") == (
            "agcli --wallet cold --hotkey-name miner weights commit --netuid 1 --weights 0:100 --salt abc"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_help_with_wallet_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.reveal_help(1, "0:100", "abc", wallet="cold", hotkey="miner") == (
            "agcli --wallet cold --hotkey-name miner weights reveal --netuid 1 --weights 0:100 --salt abc"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_help_with_wallet_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.set_help(1, "0:100", wallet="cold", hotkey="miner") == (
            "agcli --wallet cold --hotkey-name miner weights set --netuid 1 --weights 0:100"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_help_with_wallet_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.commit_reveal_help(1, "0:100", wallet="cold", hotkey="miner") == (
            "agcli --wallet cold --hotkey-name miner weights commit-reveal --netuid 1 --weights 0:100"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.weights.status_help(1, hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.weights.status_help(1, wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_operator_workflow_help_matches_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.operator_workflow_help(1, "0:100", "abc", wallet="cold") == c.weights.workflow_help(
            1, "0:100", "abc", wallet="cold"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_without_wallet_has_no_wallet_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc")
        assert "wallet" not in helpers
        assert "hotkey" not in helpers
        assert "wallet_selection_note" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_weights_serve_prerequisite_help_without_wallet_has_no_wallet_fields_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.serve_prerequisite_help(1)
        assert "wallet" not in helpers
        assert "hotkey" not in helpers
        assert "wallet_selection_note" not in helpers
        assert helpers["status"] == "agcli weights status --netuid 1"
        assert helpers["show"] == "agcli weights show --netuid 1"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_without_filters_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.show_help(1) == "agcli weights show --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_rejects_non_integer_limit_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="limit must be an integer"):
            c.weights.show_help(1, limit=True)

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_exposes_show_and_hyperparams_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc")
        assert helpers["show"] == "agcli weights show --netuid 1"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 1"
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_rejects_empty_hotkey_after_trim_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey_address cannot be empty"):
            c.weights.show_help(1, hotkey_address="  ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.weights.commit_help(1, "0:100", hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.weights.set_help(1, "0:100", wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.weights.reveal_help(1, "0:100", "abc", wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.weights.commit_reveal_help(1, "0:100", hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_serve_prerequisite_help_with_wallet_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.serve_prerequisite_help(5, wallet="cold")
        assert helpers["wallet_selection_note"]
        assert helpers["status"] == "agcli --wallet cold weights status --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_weights_serve_prerequisite_help_with_hotkey_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.serve_prerequisite_help(5, hotkey="miner")
        assert helpers["wallet_selection_note"]
        assert helpers["status"] == "agcli --hotkey-name miner weights status --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_with_wallet_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc", wallet="cold")
        assert helpers["wallet_selection_note"]
        assert helpers["status"] == "agcli --wallet cold weights status --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_with_hotkey_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc", hotkey="miner")
        assert helpers["wallet_selection_note"]
        assert helpers["status"] == "agcli --hotkey-name miner weights status --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_with_wallet_and_hotkey_preserves_unprefixed_show_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc", wallet="cold", hotkey="miner")
        assert helpers["show"] == "agcli weights show --netuid 1"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_rejects_non_string_hotkey_address_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(AttributeError):
            c.weights.show_help(1, hotkey_address=123)  # type: ignore[arg-type]

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_help_with_wallet_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.commit_help(1, "0:100", salt="abc", wallet="cold") == (
            "agcli --wallet cold weights commit --netuid 1 --weights 0:100 --salt abc"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_help_with_hotkey_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.reveal_help(1, "0:100", "abc", hotkey="miner") == (
            "agcli --hotkey-name miner weights reveal --netuid 1 --weights 0:100 --salt abc"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_help_with_wallet_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert (
            c.weights.set_help(1, "0:100", wallet="cold")
            == "agcli --wallet cold weights set --netuid 1 --weights 0:100"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_help_with_hotkey_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.commit_reveal_help(1, "0:100", hotkey="miner") == (
            "agcli --hotkey-name miner weights commit-reveal --netuid 1 --weights 0:100"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_show_and_hyperparams_are_unprefixed_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc", wallet="cold", hotkey="miner")
        assert helpers["show"] == "agcli weights show --netuid 1"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_accepts_hotkey_and_limit_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.show_help(1, hotkey_address="5F...", limit=1) == (
            "agcli weights show --netuid 1 --hotkey-address 5F... --limit 1"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_serve_prerequisite_help_contains_notes_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.serve_prerequisite_help(1)
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["hyperparams_note"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_contains_notes_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc")
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.weights.workflow_help(1, "0:100", salt="abc", hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_operator_workflow_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.weights.operator_workflow_help(1, "0:100", "abc", wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_inspect_version_key_help_aliases_match_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.inspect_version_key_help(1) == c.weights.inspect_hyperparams_help(1)
        assert c.weights.inspect_version_key_help(1) == c.weights.inspect_version_key_help_old(1)

    @patch("taocli.runner.subprocess.run")
    def test_weights_serve_prerequisite_help_matches_expected_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.serve_prerequisite_help(1, wallet="cold", hotkey="miner")
        assert helpers["netuid"] == 1
        assert helpers["status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 1"
        assert helpers["show"] == "agcli weights show --netuid 1"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_rejects_negative_limit_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="limit must be greater than 0"):
            c.weights.show_help(1, limit=-1)

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_help_preserves_unprefixed_form_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.status_help(1) == "agcli weights status --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_show_help_preserves_unprefixed_form_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.show_help(1) == "agcli weights show --netuid 1"

    @patch("taocli.runner.subprocess.run")
    def test_weights_commit_reveal_help_with_wait_and_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.commit_reveal_help(1, "0:100", wait=True, wallet="cold") == (
            "agcli --wallet cold weights commit-reveal --netuid 1 --weights 0:100 --wait"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_reveal_help_with_version_and_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.reveal_help(1, "0:100", "abc", version_key=7, wallet="cold") == (
            "agcli --wallet cold weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_set_help_with_version_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.set_help(1, "0:100", version_key=7, hotkey="miner") == (
            "agcli --hotkey-name miner weights set --netuid 1 --weights 0:100 --version-key 7"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_workflow_help_with_wait_and_wallet_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.workflow_help(1, "0:100", salt="abc", wait=True, wallet="cold", hotkey="miner")
        assert (
            helpers["commit_reveal"]
            == "agcli --wallet cold --hotkey-name miner weights commit-reveal --netuid 1 --weights 0:100 --wait"
        )
        assert helpers["status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 1"

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
        assert helpers["inspect_status_command"] == "agcli weights status --netuid 97"
        assert helpers["inspect_pending_commits_command"] == "agcli subnet commits --netuid 97"
        assert helpers["inspect_version_key_command"] == "agcli subnet hyperparams --netuid 97"
        assert helpers["inspect_metagraph_command"] == "agcli subnet metagraph --netuid 97"
        assert helpers["inspect_chain_data_command"] == "agcli subnet show --netuid 97"
        assert helpers["inspect_subnets_command"] == "agcli subnet list"
        assert helpers["inspect_neuron_command"] == "agcli view neuron --netuid 97 --uid 0"
        assert helpers["inspect_hyperparams_command"] == "agcli subnet hyperparams --netuid 97"
        assert helpers["inspect_validators_command"] == "agcli view validators --netuid 97"
        assert helpers["inspect_stake_command"] == "agcli stake list --netuid 97"
        assert helpers["inspect_config_show_command"] == "agcli config show"
        assert helpers["inspect_wallet_show_command"] == "agcli wallet show --all"
        assert helpers["inspect_wallet_current_command"] == "agcli wallet show"
        assert helpers["inspect_wallet_associate_command"] == "agcli wallet associate-hotkey"
        assert helpers["inspect_wallet_derive_command"] == "agcli wallet derive --input <pubkey-or-mnemonic>"
        assert helpers["inspect_wallet_verify_command"] == (
            "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
        )
        assert helpers["inspect_stake_add_command"] == "agcli stake add --netuid 97 --amount <amount>"
        assert helpers["inspect_validator_requirements_command"] == "agcli subnet hyperparams --netuid 97"
        assert helpers["inspect_registration_cost_command"] == "agcli subnet cost --netuid 97"
        assert helpers["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 97"
        assert helpers["inspect_health_command"] == "agcli subnet health --netuid 97"
        assert helpers["inspect_probe_command"] == "agcli subnet probe --netuid 97"
        assert helpers["inspect_watch_command"] == "agcli subnet watch --netuid 97"
        assert helpers["inspect_axon_command"] == "agcli view axon --netuid 97"
        assert helpers["inspect_miner_endpoints_command"] == "agcli view axon --netuid 97"
        assert helpers["inspect_validator_endpoints_command"] == "agcli view axon --netuid 97"
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 97 --json"
        assert helpers["adjacent_recovery_note"].startswith("If the weights-specific retry path still looks wrong")
        assert "inspect_pending_commits_command" in helpers["adjacent_recovery_note"]
        assert "inspect_metagraph_command" in helpers["adjacent_recovery_note"]
        assert "inspect_neuron_command" in helpers["adjacent_recovery_note"]
        assert "inspect_validators_command" in helpers["adjacent_recovery_note"]
        assert "inspect_config_show_command" in helpers["adjacent_recovery_note"]
        assert "inspect_wallet_show_command" in helpers["adjacent_recovery_note"]
        assert "inspect_wallet_current_command" in helpers["adjacent_recovery_note"]
        assert "inspect_wallet_associate_command" in helpers["adjacent_recovery_note"]
        assert "inspect_wallet_derive_command" in helpers["adjacent_recovery_note"]
        assert "inspect_wallet_sign_command" in helpers["adjacent_recovery_note"]
        assert "inspect_wallet_verify_command" in helpers["adjacent_recovery_note"]
        assert "inspect_hyperparams_command" in helpers["adjacent_recovery_note"]
        assert "inspect_probe_command" in helpers["adjacent_recovery_note"]
        assert "inspect_watch_command" in helpers["adjacent_recovery_note"]
        assert "inspect_monitor_command" in helpers["adjacent_recovery_note"]
        assert "watch plus monitor" in helpers["adjacent_workflows_note"]
        assert (
            "config_show plus wallet_show plus wallet_current plus wallet_associate plus wallet_derive plus "
            "wallet_sign plus wallet_verify plus balance"
            in helpers["adjacent_workflows_note"]
        )
        assert "manual address derivation checks" in helpers["adjacent_workflows_note"]
        assert "signature generation" in helpers["adjacent_workflows_note"]
        assert "signature verification" in helpers["adjacent_workflows_note"]
        assert "hotkey association recovery" in helpers["adjacent_workflows_note"]
        assert "manual address derivation checks" in helpers["adjacent_recovery_note"]
        assert "signature generation" in helpers["adjacent_recovery_note"]
        assert "signature verification" in helpers["adjacent_recovery_note"]
        assert "hotkey association recovery" in helpers["adjacent_recovery_note"]
        assert "inspect_miner_endpoints_command" in helpers["adjacent_recovery_note"]
        assert "inspect_validator_endpoints_command" in helpers["adjacent_recovery_note"]
        assert "inspect_subnets_command" in helpers["adjacent_recovery_note"]
        assert "serve/endpoint verification" in helpers["adjacent_recovery_note"]
        assert helpers["inspect_hyperparams_command"] == helpers["inspect_version_key_command"]
        assert helpers["inspect_hyperparams_command"] == helpers["inspect_validator_requirements_command"]
        assert helpers["preflight_note"].startswith("Inspect weights status and subnet hyperparams")
        assert helpers["pending_commits_note"].startswith("If wallet-specific status")
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
    def test_view_chain_data_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=9)
        assert helpers["subnet"] == "agcli subnet show --netuid 3"
        assert helpers["metagraph"] == "agcli view metagraph --netuid 3"
        assert helpers["neurons"] == "agcli view metagraph --netuid 3"
        assert helpers["neuron"] == "agcli view neuron --netuid 3 --uid 9"
        assert helpers["endpoints"] == "agcli view axon --netuid 3"
        assert helpers["commits"] == "agcli subnet commits --netuid 3"
        assert helpers["probe"] == "agcli subnet probe --netuid 3 --uids 9"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_with_hotkey_keeps_commit_reads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address="5F...")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["neurons"] == "agcli view metagraph --netuid 3"
        assert helpers["commits"] == "agcli subnet commits --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_neuron_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["neurons"] == "agcli view metagraph --netuid 3"
        assert helpers["commits"] == "agcli subnet commits --netuid 3"
        assert helpers["validator_endpoints"] == "agcli view axon --netuid 3"
        assert helpers["miner_endpoints"] == "agcli view axon --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_keeps_owner_param_list_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6, wallet="owner", param="tempo", value="360")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_owner_param_list_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["param_list"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_keeps_owner_param_list_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6)
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["show"] == "agcli subnet show --netuid 6"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["raw"] == "agcli admin raw --call <sudo-call>"
        assert helpers["sudo_note"]
        assert "set" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_command_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6, command="set-tempo", value_flag="--tempo")
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli admin set-tempo --netuid 6 --tempo <value>"
        assert helpers["command"] == "set-tempo"
        assert helpers["value_flag"] == "--tempo"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_value_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6,
            command="set-network-registration",
            value_flag="--allowed",
            value=False,
        )
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["value"] == "false"
        assert helpers["set"] == "agcli admin set-network-registration --netuid 6 --allowed false"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["sudo_note"]

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_sudo_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6,
            command="set-tempo",
            value_flag="--tempo",
            value=12,
            sudo_key=" //Alice ",
        )
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["sudo_key"] == "//Alice"
        assert helpers["set"] == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_keeps_raw_and_notes_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6)
        assert helpers["raw"] == "agcli admin raw --call <sudo-call>"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["sudo_note"]

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_sudo_without_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="sudo_key requires command"):
            c.admin.hyperparameter_workflow_help(6, sudo_key="//Alice")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_value_flag_without_command_via_client_surface_updated(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value_flag requires command"):
            c.admin.hyperparameter_workflow_help(6, value_flag="--tempo")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_value_without_command_via_client_surface_updated(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            c.admin.hyperparameter_workflow_help(6, value=12)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_sudo_key_without_command_via_client_surface_updated(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="sudo_key requires command"):
            c.admin.hyperparameter_workflow_help(6, sudo_key="//Alice")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_with_bool_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-commit-reveal", 6, value_flag="--enabled", value=True)
        assert command == "agcli admin set-commit-reveal --netuid 6 --enabled true"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_rejects_empty_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="command cannot be empty"):
            c.admin.hyperparameter_mutation_help("   ", 6, value_flag="--enabled", value=True)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_rejects_empty_value_flag_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value_flag cannot be empty"):
            c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="   ", value=1)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_rejects_empty_sudo_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="sudo_key cannot be empty"):
            c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=1, sudo_key="   ")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.admin.hyperparameter_mutation_help("set-tempo", 0, value_flag="--tempo", value=1)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_float_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6,
            command="set-adjustment-alpha",
            value_flag="--alpha",
            value=0.5,
        )
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["value"] == "0.5"
        assert helpers["set"] == "agcli admin set-adjustment-alpha --netuid 6 --alpha 0.5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_param_only_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6, param="tempo")
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo"
        assert helpers["param"] == "tempo"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_with_trimmed_wallet_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6, wallet=" owner ")
        assert helpers["wallet"] == "owner"
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_without_wallet_omits_wallet_note_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6)
        assert "wallet_selection_note" not in helpers
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_with_wallet_keeps_wallet_note_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6, wallet="owner")
        assert helpers["wallet_selection_note"]
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_empty_wallet_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.subnet.hyperparameter_workflow_help(6, wallet="")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_empty_param_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="param cannot be empty"):
            c.subnet.hyperparameter_workflow_help(6, param="")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_empty_value_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value cannot be empty"):
            c.subnet.hyperparameter_workflow_help(6, param="tempo", value="")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_keeps_show_get_admin_list_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6)
        assert helpers["show"] == "agcli subnet show --netuid 6"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["mutation_note"]

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_with_value_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6, param="tempo", value="360")
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["value"] == "360"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_alias_matches_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        alias = c.subnet.hyperparameter_workflow_help(6, wallet="owner", param="tempo", value="360")
        plural = c.subnet.hyperparameters_workflow_help(6, wallet="owner", param="tempo", value="360")
        assert alias["owner_param_list"] == plural["owner_param_list"]
        assert alias == plural

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_with_value_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, wallet="owner", param="tempo", value="360")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_param_only_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo")
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo"
        assert helpers["param"] == "tempo"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_with_trimmed_wallet_keeps_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, wallet=" owner ")
        assert helpers["wallet"] == "owner"
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_show_get_admin_list_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["show"] == "agcli subnet show --netuid 6"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_mutation_note_exact_with_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["mutation_note"] == (
            "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
            "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_keeps_mutation_note_exact_with_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6)
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["mutation_note"] == (
            "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
            "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_invalid_netuid_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.subnet.hyperparameter_workflow_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet="cold", hotkey="miner", threads=4)
        assert helpers["registration_cost"] == "agcli subnet cost --netuid 5"
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 5"
        assert helpers["pow_register"] == "agcli --wallet cold --hotkey-name miner subnet pow --netuid 5 --threads 4"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, protocol=4, version=2)
        assert (
            helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080 --protocol 4 --version 2"
        )
        assert helpers["inspect_axon"] == "agcli view axon --netuid 8"
        assert helpers["status_check"] == "agcli view axon --netuid 8"
        assert helpers["registration_check"] == "agcli subnet show --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo", value="360")
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["mutation_note"]
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_with_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6, wallet="owner", param="tempo", value="360")
        assert helpers["wallet"] == "owner"
        assert helpers["wallet_selection_note"]
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_with_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, wallet="owner", param="tempo")
        assert helpers["wallet"] == "owner"
        assert helpers["wallet_selection_note"]
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6 --param tempo"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.subnet.hyperparameter_workflow_help(6, wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.subnet.hyperparameters_workflow_help(6, wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_matches_alias_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.subnet.hyperparameter_workflow_help(
            6, wallet="owner", param="tempo"
        ) == c.subnet.hyperparameters_workflow_help(6, wallet="owner", param="tempo")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_ignores_value_without_param_via_client_surface_with_wallet(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, wallet="owner", value="360")
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert "value" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_wallet_only_via_client_surface_updated(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet="cold")
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --wallet cold subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_hotkey_only_via_client_surface_updated(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, hotkey="miner")
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --hotkey-name miner subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_base_via_client_surface_updated(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["mutation_note"]

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_trimmed_wallet_and_hotkey_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet=" cold ", hotkey=" miner ")
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert helpers["register_neuron"] == "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_with_trimmed_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, wallet=" owner ")
        assert helpers["wallet"] == "owner"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_keeps_mutation_note_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6)
        assert helpers["mutation_note"]
        assert helpers["admin_list"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.subnet.hyperparameter_workflow_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_empty_param_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="param cannot be empty"):
            c.subnet.hyperparameter_workflow_help(6, param="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_rejects_empty_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value cannot be empty"):
            c.subnet.hyperparameter_workflow_help(6, param="tempo", value="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_ignores_value_without_param_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6, wallet="owner", value="360")
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert "value" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_without_overrides_omits_wallet_note_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert "wallet_selection_note" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_without_wallet_omits_wallet_note_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert "wallet_selection_note" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_with_wallet_uses_prefixed_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, wallet="owner")
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_wallet_and_hotkey_keeps_note_exact_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet="cold", hotkey="miner")
        assert helpers["wallet_selection_note"] == (
            "These commands use agcli's global wallet selectors before the subcommand: "
            "--wallet chooses the coldkey and --hotkey-name chooses the hotkey file name."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_mutation_note_exact_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["mutation_note"] == (
            "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
            "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_help_keeps_mutation_note_exact_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_workflow_help(6)
        assert helpers["mutation_note"] == (
            "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
            "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_admin_list_via_client_surface_updated(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["admin_list"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_show_via_client_surface_updated(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_netuid_via_client_surface_updated(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["netuid"] == 6

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_get_via_client_surface_updated(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_param_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo")
        assert helpers["param"] == "tempo"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo"
        assert "value" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6,
            command="set-commit-reveal",
            value_flag="--enabled",
            value=True,
        )
        assert helpers["show"] == "agcli subnet show --netuid 6"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["sudo_note"]
        assert helpers["set"] == "agcli admin set-commit-reveal --netuid 6 --enabled true"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-commit-reveal", 6, value_flag="--enabled", value=True)
        assert command == "agcli admin set-commit-reveal --netuid 6 --enabled true"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_rejects_invalid_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey_address cannot be empty"):
            c.view.chain_data_workflow_help(3, hotkey_address="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.subnet.registration_workflow_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_value_without_flag_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            c.admin.hyperparameter_workflow_help(6, command="set-tempo", value=12)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_empty_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="command cannot be empty"):
            c.admin.hyperparameter_workflow_help(6, command="   ")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_empty_value_flag_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value_flag cannot be empty"):
            c.admin.hyperparameter_workflow_help(6, command="set-tempo", value_flag="   ")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_empty_sudo_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="sudo_key cannot be empty"):
            c.admin.hyperparameter_workflow_help(6, command="set-tempo", sudo_key="   ")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.admin.hyperparameter_workflow_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_base_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6)
        assert helpers == {
            "netuid": 6,
            "show": "agcli subnet show --netuid 6",
            "get": "agcli subnet hyperparams --netuid 6",
            "owner_param_list": "agcli subnet set-param --netuid 6 --param list",
            "admin_list": "agcli admin list",
            "raw": "agcli admin raw --call <sudo-call>",
            "sudo_note": (
                "Use admin list to discover the exact set-* command for root-only knobs, then "
                "run it with --sudo-key. Subnet-owner knobs can usually use subnet set-param instead."
            ),
        }

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_stub_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6, command=" set-tempo ", value_flag=" --tempo ")
        assert helpers["command"] == "set-tempo"
        assert helpers["value_flag"] == "--tempo"
        assert helpers["set"] == "agcli admin set-tempo --netuid 6 --tempo <value>"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_sudo_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6, command="set-tempo", value_flag="--tempo", value=12, sudo_key=" //Alice "
        )
        assert helpers["value"] == "12"
        assert helpers["sudo_key"] == "//Alice"
        assert helpers["set"] == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_bool_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6, command="set-network-registration", value_flag="--allowed", value=False
        )
        assert helpers["value"] == "false"
        assert helpers["set"] == "agcli admin set-network-registration --netuid 6 --allowed false"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_stringifies_float_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6, command="set-adjustment-alpha", value_flag="--alpha", value=0.5
        )
        assert helpers["value"] == "0.5"
        assert helpers["set"] == "agcli admin set-adjustment-alpha --netuid 6 --alpha 0.5"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_value_flag_without_command_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value_flag requires command"):
            c.admin.hyperparameter_workflow_help(6, value_flag="--tempo")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_sudo_key_without_command_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="sudo_key requires command"):
            c.admin.hyperparameter_workflow_help(6, sudo_key="//Alice")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_value_without_command_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            c.admin.hyperparameter_workflow_help(6, value=12)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_rejects_value_without_command_and_flag_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            c.admin.hyperparameter_workflow_help(6, command="set-tempo", value=12)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_trimmed_inputs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6, command=" set-tempo ", value_flag=" --tempo ", value=12, sudo_key=" //Alice "
        )
        assert helpers["command"] == "set-tempo"
        assert helpers["value_flag"] == "--tempo"
        assert helpers["sudo_key"] == "//Alice"
        assert helpers["set"] == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_with_string_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(
            6, command="set-alpha-values", value_flag="--alpha-low", value="0.1"
        )
        assert helpers["value"] == "0.1"
        assert helpers["set"] == "agcli admin set-alpha-values --netuid 6 --alpha-low 0.1"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_ignores_value_without_param_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, value="360")
        assert helpers["set"] == "agcli subnet set-param --netuid 6"
        assert helpers["admin_list"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_rejects_empty_cert_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="cert cannot be empty"):
            c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert="   ")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_includes_tls_and_prometheus_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert="/tmp/cert.pem", prometheus_port=9090)
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090"
        assert helpers["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_prefers_hotkey_filter_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=9, hotkey_address="5F...")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["neuron"] == "agcli view neuron --netuid 3 --uid 9"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_stringifies_float_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-adjustment-alpha", 6, value_flag="--alpha", value=0.5)
        assert command == "agcli admin set-adjustment-alpha --netuid 6 --alpha 0.5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.subnet.registration_workflow_help(5, hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_rejects_empty_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value cannot be empty"):
            c.subnet.hyperparameters_workflow_help(6, param="tempo", value="   ")

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_rejects_invalid_uid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="uid must be greater than or equal to 0"):
            c.view.chain_data_workflow_help(3, uid=-1)

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_rejects_empty_ip_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="ip cannot be empty"):
            c.serve.axon_workflow_help(8, "   ", 8080)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_rejects_empty_param_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="param cannot be empty"):
            c.subnet.hyperparameters_workflow_help(6, param="   ")

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_without_neuron_filter_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert "neuron" not in helpers
        assert helpers["validators"] == "agcli view validators --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_snipe_options_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, max_cost=2.5, max_attempts=8)
        assert helpers["snipe_register"] == "agcli subnet snipe --netuid 5 --max-cost 2.5 --max-attempts 8"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_with_prometheus_version_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, version=2, prometheus_port=9090)
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 2"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_without_sudo_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=12)
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_with_trimmed_param_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param=" tempo ", value=" 12 ")
        assert helpers["param"] == "tempo"
        assert helpers["value"] == "12"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo --value 12"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_with_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address=" 5F... ")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.serve.axon_workflow_help(0, "127.0.0.1", 8080)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_base_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers == {
            "netuid": 6,
            "show": "agcli subnet show --netuid 6",
            "get": "agcli subnet hyperparams --netuid 6",
            "param_list": "agcli subnet set-param --netuid 6 --param list",
            "owner_param_list": "agcli subnet set-param --netuid 6 --param list",
            "set": "agcli subnet set-param --netuid 6",
            "admin_list": "agcli admin list",
            "mutation_note": (
                "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
                "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
            ),
        }

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_base_without_wallet_note_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert "wallet_selection_note" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_base_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert helpers["reset"] == "agcli serve reset --netuid 8"
        assert helpers["probe"] == "agcli subnet probe --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_base_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["subnet"] == "agcli subnet show --netuid 5"
        assert helpers["health"] == "agcli subnet health --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_base_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 3"
        assert helpers["subnet_metagraph_full"] == "agcli subnet metagraph --netuid 3 --full"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_bool_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            "set-network-registration", 6, value_flag="--allowed", value=False
        )
        assert command == "agcli admin set-network-registration --netuid 6 --allowed false"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_tls_with_protocol_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert="/tmp/cert.pem", protocol=4)
        assert helpers["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem --protocol 4"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_wallet_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet="cold")
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --wallet cold subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_probe_unfiltered_for_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address="5F...")
        assert helpers["probe"] == "agcli subnet probe --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_with_trimmed_inputs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            " set-tempo ", 6, value_flag=" --tempo ", value=12, sudo_key=" //Alice "
        )
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_with_tls_and_prometheus_via_client_surface_duplicate(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(
            8, "127.0.0.1", 8080, cert="/tmp/cert.pem", prometheus_port=9090, version=2
        )
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 2"
        assert helpers["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem --version 2"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_hotkey_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, hotkey="miner")
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --hotkey-name miner subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_with_param_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo")
        assert helpers["param"] == "tempo"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_with_uid_and_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=9, hotkey_address=" 5F... ")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["probe"] == "agcli subnet probe --netuid 3 --uids 9"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_rejects_empty_value_flag_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value_flag cannot be empty"):
            c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="", value=1)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_rejects_empty_wallet_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.subnet.registration_workflow_help(5, wallet="")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_with_protocol_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, protocol=4)
        assert helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080 --protocol 4"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.subnet.hyperparameters_workflow_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.view.chain_data_workflow_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_with_version_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, version=2)
        assert helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080 --version 2"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_with_string_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-alpha-values", 6, value_flag="--alpha-low", value="0.1")
        assert command == "agcli admin set-alpha-values --netuid 6 --alpha-low 0.1"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_with_threads_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, threads=2)
        assert helpers["pow_register"] == "agcli subnet pow --netuid 5 --threads 2"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_with_hotkey_does_not_remove_hyperparams_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address="5F...")
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_rejects_empty_command_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="command cannot be empty"):
            c.admin.hyperparameter_mutation_help("", 6, value_flag="--tempo", value=1)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_rejects_empty_param_duplicate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="param cannot be empty"):
            c.subnet.hyperparameters_workflow_help(6, param="")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_rejects_empty_ip_duplicate_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="ip cannot be empty"):
            c.serve.axon_workflow_help(8, "", 8080)

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_with_uid_keeps_hyperparams_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=9)
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_with_false_bool_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-commit-reveal", 6, value_flag="--enabled", value=False)
        assert command == "agcli admin set-commit-reveal --netuid 6 --enabled false"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_health_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet="cold")
        assert helpers["health"] == "agcli subnet health --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_probe_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert helpers["probe"] == "agcli subnet probe --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_validators_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address="5F...")
        assert helpers["validators"] == "agcli view validators --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_admin_list_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo")
        assert helpers["admin_list"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=12)
        assert "--netuid 6" in command

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_reset_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert="/tmp/cert.pem")
        assert helpers["reset"] == "agcli serve reset --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_emissions_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["emissions"] == "agcli view emissions --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_cost_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["registration_cost"] == "agcli subnet cost --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_with_trimmed_sudo_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            "set-tempo", 6, value_flag="--tempo", value=12, sudo_key=" //Alice "
        )
        assert command.endswith("--sudo-key //Alice")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_inspect_axon_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert helpers["inspect_axon"] == "agcli view axon --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_show_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_health_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["health"] == "agcli view health --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_hyperparams_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=12)
        assert command.startswith("agcli admin set-tempo")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert helpers["netuid"] == 8

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["netuid"] == 3

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["netuid"] == 5

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["netuid"] == 6

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_bool_lowercase_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-yuma3", 6, value_flag="--enabled", value=True)
        assert command.endswith("--enabled true")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_port_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert "--port 8080" in helpers["serve_axon"]

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_metagraph_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["metagraph"] == "agcli view metagraph --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_register_neuron_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["register_neuron"] == "agcli subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_get_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_value_flag_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=12)
        assert "--tempo 12" in command

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_ip_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert "--ip 127.0.0.1" in helpers["serve_axon"]

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_subnet_metagraph_full_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["subnet_metagraph_full"] == "agcli subnet metagraph --netuid 3 --full"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_snipe_register_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["snipe_register"] == "agcli subnet snipe --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_param_only_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo")
        assert helpers["param"] == "tempo"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_admin_prefix_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=12)
        assert command.startswith("agcli admin ")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_base_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert helpers["serve_axon"].startswith("agcli serve axon --netuid 8")

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_axon_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["axon"] == "agcli view axon --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_pow_register_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["pow_register"] == "agcli subnet pow --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_string_values_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-alpha-values", 6, value_flag="--alpha-high", value="0.9")
        assert command.endswith("--alpha-high 0.9")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_set_when_value_present_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo", value="12")
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo --value 12"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_probe_with_uid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=4)
        assert helpers["probe"] == "agcli subnet probe --netuid 3 --uids 4"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_prometheus_versionless_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, prometheus_port=9090)
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_float_values_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-adjustment-alpha", 6, value_flag="--alpha", value=0.5)
        assert command.endswith("--alpha 0.5")

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_neuron_with_uid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=4)
        assert helpers["neuron"] == "agcli view neuron --netuid 3 --uid 4"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_trimmed_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet=" cold ")
        assert helpers["wallet"] == "cold"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_trimmed_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(" set-tempo ", 6, value_flag=" --tempo ", value=12)
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_trimmed_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address=" 5F... ")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_trimmed_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, hotkey=" miner ")
        assert helpers["hotkey"] == "miner"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_trimmed_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo", value=" 12 ")
        assert helpers["value"] == "12"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_trimmed_value_flag_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag=" --tempo ", value=12)
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_tls_with_version_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert="/tmp/cert.pem", version=2)
        assert helpers["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem --version 2"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_threads_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, threads=3)
        assert helpers["threads"] == 3

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_param_value_pair_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo", value="12")
        assert helpers["param"] == "tempo"
        assert helpers["value"] == "12"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_protocol_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, protocol=4)
        assert helpers["serve_axon"].endswith("--protocol 4")

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_uid_probe_and_hotkey_axon_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=4, hotkey_address="5F...")
        assert helpers["probe"] == "agcli subnet probe --netuid 3 --uids 4"
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_max_attempts_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, max_attempts=8)
        assert helpers["max_attempts"] == 8

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_max_cost_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, max_cost=2.5)
        assert helpers["max_cost"] == 2.5

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_false_bool_lowercase_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            "set-network-registration", 6, value_flag="--allowed", value=False
        )
        assert command.endswith("--allowed false")

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_tls_without_protocol_or_version_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert="/tmp/cert.pem")
        assert (
            helpers["serve_axon_tls"]
            == "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_hotkey_trimmed_with_uid_probe_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=4, hotkey_address=" 5F... ")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["probe"] == "agcli subnet probe --netuid 3 --uids 4"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_param_only_set_stub_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo")
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_trimmed_sudo_only_when_present_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            "set-tempo", 6, value_flag="--tempo", value=12, sudo_key=" //Alice "
        )
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_prometheus_with_version_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, prometheus_port=9090, version=2)
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 2"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_wallet_hotkey_threads_combo_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet="cold", hotkey="miner", threads=4)
        assert helpers["pow_register"] == ("agcli --wallet cold --hotkey-name miner subnet pow --netuid 5 --threads 4")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_admin_list_when_setting_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo", value="12")
        assert helpers["admin_list"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_all_base_keys_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert set(
            [
                "netuid",
                "metagraph",
                "subnet_metagraph_full",
                "validators",
                "axon",
                "probe",
                "health",
                "emissions",
                "hyperparams",
            ]
        ).issubset(helpers)

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_all_base_keys_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert set(["netuid", "serve_axon", "reset", "inspect_axon", "probe"]).issubset(helpers)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_all_base_keys_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert set(
            [
                "netuid",
                "subnet",
                "hyperparams",
                "registration_cost",
                "health",
                "register_neuron",
                "pow_register",
                "snipe_register",
            ]
        ).issubset(helpers)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_all_base_keys_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert set(["netuid", "show", "get", "admin_list"]).issubset(helpers)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=12)
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_final_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["register_neuron"] == "agcli subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["metagraph"] == "agcli view metagraph --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo", value="12")
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo --value 12"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_false_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            "set-network-registration", 6, value_flag="--allowed", value=False
        )
        assert command == "agcli admin set-network-registration --netuid 6 --allowed false"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_tls_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert="/tmp/cert.pem")
        assert (
            helpers["serve_axon_tls"]
            == "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_hotkey_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address="5F...")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_final_pow_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, threads=4)
        assert helpers["pow_register"] == "agcli subnet pow --netuid 5 --threads 4"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_get_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_sudo_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            "set-tempo", 6, value_flag="--tempo", value=12, sudo_key="//Alice"
        )
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_prometheus_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, prometheus_port=9090)
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_uid_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=4)
        assert helpers["neuron"] == "agcli view neuron --netuid 3 --uid 4"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_final_snipe_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, max_cost=2.5, max_attempts=8)
        assert helpers["snipe_register"] == "agcli subnet snipe --netuid 5 --max-cost 2.5 --max-attempts 8"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_show_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_float_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-adjustment-alpha", 6, value_flag="--alpha", value=0.5)
        assert command == "agcli admin set-adjustment-alpha --netuid 6 --alpha 0.5"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_protocol_version_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, protocol=4, version=2)
        assert (
            helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080 --protocol 4 --version 2"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_uid_hotkey_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=4, hotkey_address="5F...")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["probe"] == "agcli subnet probe --netuid 3 --uids 4"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_param_only_shape_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo")
        assert helpers["param"] == "tempo"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_trimmed_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(" set-tempo ", 6, value_flag=" --tempo ", value=12)
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_trimmed_cert_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, cert=" /tmp/cert.pem ")
        assert (
            helpers["serve_axon_tls"]
            == "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_trimmed_hotkey_shape_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, hotkey_address=" 5F... ")
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_final_trimmed_wallet_hotkey_shape_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5, wallet=" cold ", hotkey=" miner ")
        assert helpers["register_neuron"] == (
            "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 5"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_trimmed_param_value_shape_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param=" tempo ", value=" 12 ")
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo --value 12"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_trimmed_sudo_shape_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            " set-tempo ", 6, value_flag=" --tempo ", value=12, sudo_key=" //Alice "
        )
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_prometheus_version_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080, prometheus_port=9090, version=2)
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 2"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_health_and_emissions_shape_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["health"] == "agcli view health --netuid 3"
        assert helpers["emissions"] == "agcli view emissions --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_final_health_and_cost_shape_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["health"] == "agcli subnet health --netuid 5"
        assert helpers["registration_cost"] == "agcli subnet cost --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_admin_list_shape_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["admin_list"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_bool_shape_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-commit-reveal", 6, value_flag="--enabled", value=True)
        assert command == "agcli admin set-commit-reveal --netuid 6 --enabled true"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_base_keys_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(8, "127.0.0.1", 8080)
        assert helpers["netuid"] == 8
        assert helpers["reset"] == "agcli serve reset --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_base_keys_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3)
        assert helpers["netuid"] == 3
        assert helpers["validators"] == "agcli view validators --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_final_base_keys_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(5)
        assert helpers["netuid"] == 5
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_base_keys_shape_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6)
        assert helpers["netuid"] == 6
        assert helpers["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_base_shape_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help("set-tempo", 6, value_flag="--tempo", value=12)
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_workflow_help_keeps_final_complete_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_workflow_help(
            8, "127.0.0.1", 8080, protocol=4, version=2, cert="/tmp/cert.pem", prometheus_port=9090
        )
        assert (
            helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080 --protocol 4 --version 2"
        )
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 2"
        assert helpers["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem --protocol 4 --version 2"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_workflow_help_keeps_final_complete_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_workflow_help(3, uid=4, hotkey_address="5F...")
        assert helpers["metagraph"] == "agcli view metagraph --netuid 3"
        assert helpers["neuron"] == "agcli view neuron --netuid 3 --uid 4"
        assert helpers["axon"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["probe"] == "agcli subnet probe --netuid 3 --uids 4"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_workflow_help_keeps_final_complete_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_workflow_help(
            5, wallet="cold", hotkey="miner", threads=4, max_cost=2.5, max_attempts=8
        )
        assert helpers["register_neuron"] == (
            "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 5"
        )
        assert helpers["pow_register"] == ("agcli --wallet cold --hotkey-name miner subnet pow --netuid 5 --threads 4")
        assert helpers["snipe_register"] == (
            "agcli --wallet cold --hotkey-name miner subnet snipe --netuid 5 --max-cost 2.5 --max-attempts 8"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_workflow_help_keeps_final_complete_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_workflow_help(6, param="tempo", value="12")
        assert helpers["show"] == "agcli subnet show --netuid 6"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["set"] == "agcli subnet set-param --netuid 6 --param tempo --value 12"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_mutation_help_keeps_final_complete_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        command = c.admin.hyperparameter_mutation_help(
            "set-tempo", 6, value_flag="--tempo", value=12, sudo_key="//Alice"
        )
        assert command == "agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice"

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
            "inspect_version_key_command": "agcli subnet hyperparams --netuid 1",
            "version_key_recovery_note": (
                "Run inspect_version_key_command to inspect the subnet hyperparameters and find the "
                "expected version_key before retrying."
            ),
            "show_command": "agcli weights show --netuid 1",
            "inspect_metagraph_command": "agcli subnet metagraph --netuid 1",
            "inspect_chain_data_command": "agcli subnet show --netuid 1",
            "inspect_subnets_command": "agcli subnet list",
            "inspect_subnet_command": "agcli subnet show --netuid 1",
            "inspect_hyperparams_command": "agcli subnet hyperparams --netuid 1",
            "inspect_emissions_command": "agcli view emissions --netuid 1",
            "inspect_neuron_command": "agcli view neuron --netuid 1 --uid 0",
            "inspect_validators_command": "agcli view validators --netuid 1",
            "inspect_stake_command": "agcli stake list --netuid 1",
            "inspect_config_show_command": "agcli config show",
            "inspect_wallet_show_command": "agcli wallet show --all",
            "inspect_wallet_current_command": "agcli wallet show",
            "inspect_wallet_associate_command": "agcli wallet associate-hotkey",
            "inspect_wallet_derive_command": "agcli wallet derive --input <pubkey-or-mnemonic>",
            "inspect_wallet_sign_command": "agcli wallet sign --message <message>",
            "inspect_wallet_verify_command": (
                "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
            ),
            "inspect_balance_command": "agcli balance",
            "inspect_stake_add_command": "agcli stake add --netuid 1 --amount <amount>",
            "inspect_validator_requirements_command": "agcli subnet hyperparams --netuid 1",
            "inspect_owner_param_list_command": "agcli subnet set-param --netuid 1 --param list",
            "inspect_set_param_command": "agcli subnet set-param --netuid 1",
            "inspect_admin_list_command": "agcli admin list",
            "inspect_admin_raw_command": "agcli admin raw --call <sudo-call>",
            "explain_weights_command": "agcli explain weights",
            "explain_commit_reveal_command": "agcli explain commit-reveal",
            "inspect_registration_cost_command": "agcli subnet cost --netuid 1",
            "inspect_register_neuron_command": "agcli subnet register-neuron --netuid 1",
            "inspect_pow_register_command": "agcli subnet pow --netuid 1",
            "inspect_snipe_register_command": "agcli subnet snipe --netuid 1",
            "inspect_health_command": "agcli subnet health --netuid 1",
            "inspect_serve_axon_command": "agcli serve axon --netuid 1 --ip <ip> --port <port>",
            "inspect_serve_axon_tls_command": "agcli serve axon-tls --netuid 1 --ip <ip> --port <port> --cert <cert>",
            "inspect_serve_prometheus_command": "agcli serve prometheus --netuid 1 --ip <ip> --port <port>",
            "inspect_serve_reset_command": "agcli serve reset --netuid 1",
            "inspect_probe_command": "agcli subnet probe --netuid 1",
            "inspect_axon_command": "agcli view axon --netuid 1",
            "inspect_miner_endpoints_command": "agcli view axon --netuid 1",
            "inspect_validator_endpoints_command": "agcli view axon --netuid 1",
            "inspect_watch_command": "agcli subnet watch --netuid 1",
            "inspect_monitor_command": "agcli subnet monitor --netuid 1 --json",
            "adjacent_workflows_note": (
                "If the weights-specific path still looks wrong, pivot to show/metagraph and chain_data plus emissions "
                "for live weights, subnet UIDs/state, pending_commits for operator watch/reveal drift checks, "
                "inspect_neuron_command for per-UID member detail after metagraph/monitor checks, "
                "config_show plus wallet_show plus wallet_current plus wallet_associate plus wallet_derive plus "
                "wallet_sign plus wallet_verify plus balance plus "
                "validators/stake/stake_add/validator_requirements for wallet "
                "selector inspection, wallet inventory plus selected coldkey/hotkey identity confirmation, hotkey "
                "association recovery, manual address derivation checks, signature generation, signature verification, "
                "coldkey funding, "
                "validator readiness, stake top-ups, or validator threshold checks, hyperparams plus "
                "owner_param_list/set_param/admin_list/admin_raw/registration_cost/register_neuron/pow_register/"
                "snipe_register/health for subnet readiness, subnet entry, registration retries, "
                "root-only mutation escape hatches, or mutation discovery, "
                "serve_axon plus serve_axon_tls plus serve_prometheus plus serve_reset plus probe plus "
                "axon/miner_endpoints/validator_endpoints for serve retries, TLS serve recovery, prometheus recovery, "
                "endpoint recovery, or serve/endpoint verification, watch plus monitor for live UID/state drift, "
                "explain_weights/explain_commit_reveal for copy-pasteable concept refreshers, and subnets plus "
                "subnet for available netuid discovery and the current subnet summary."
            ),
            "adjacent_recovery_note": (
                "If the weights-specific retry path still looks wrong, pivot to show_command for live on-chain "
                "weights, inspect_pending_commits_command for subnet-wide pending commit/watch drift checks, "
                "inspect_metagraph_command, inspect_chain_data_command, inspect_emissions_command, and "
                "inspect_monitor_command for live subnet UIDs/state drift, inspect_neuron_command for per-UID member "
                "detail after metagraph/monitor checks, inspect_config_show_command, "
                "inspect_wallet_show_command, inspect_wallet_current_command, inspect_wallet_associate_command, "
                "inspect_wallet_derive_command, inspect_wallet_sign_command, inspect_wallet_verify_command, "
                "inspect_balance_command, inspect_validators_command, inspect_stake_command, "
                "inspect_stake_add_command, and inspect_validator_requirements_command for wallet selector "
                "inspection, wallet inventory plus selected coldkey/hotkey identity confirmation, hotkey "
                "association recovery, manual address derivation checks, signature generation, "
                "signature verification, coldkey funding, validator readiness, stake top-ups, or "
                "validator threshold checks, "
                "inspect_hyperparams_command plus "
                "inspect_owner_param_list_command, inspect_set_param_command, inspect_admin_list_command, "
                "inspect_admin_raw_command, inspect_registration_cost_command, "
                "inspect_register_neuron_command, inspect_pow_register_command, "
                "inspect_snipe_register_command, and inspect_health_command for subnet readiness, "
                "subnet entry, registration retries, root-only mutation escape hatches, or mutation discovery, "
                "inspect_serve_axon_command plus inspect_serve_axon_tls_command plus "
                "inspect_serve_prometheus_command plus inspect_serve_reset_command plus inspect_probe_command plus "
                "inspect_axon_command, inspect_miner_endpoints_command, and inspect_validator_endpoints_command for "
                "serve retries, TLS serve recovery, prometheus recovery, endpoint recovery, or serve/endpoint "
                "verification, inspect_watch_command plus inspect_monitor_command for live UID/state drift, "
                "explain_weights_command plus explain_commit_reveal_command for copy-pasteable concept refreshers, "
                "inspect_subnets_command for available netuid discovery, and inspect_subnet_command for the current "
                "subnet summary."
            ),
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
            "pending_commit": {
                "index": 1,
                "status": "EXPIRED",
                "commit_block": 100,
                "first_reveal": 110,
                "last_reveal": 130,
            },
            "reveal_window": {"first_block": 110, "last_block": 130},
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
            "pending_commit": {
                "index": 1,
                "status": "EXPIRED",
                "commit_block": 100,
                "first_reveal": 110,
                "last_reveal": 130,
            },
            "reveal_window": {"first_block": 110, "last_block": 130},
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
