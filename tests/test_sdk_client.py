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
from tests.test_sdk_weights import (
    DIRECT_SET_READY_STATUS_TEXT,
    EXPIRED_STATUS_TEXT,
    NO_PENDING_STATUS_TEXT,
    READY_STATUS_TEXT,
    WAITING_STATUS_TEXT,
)


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
        assert helpers["normalized_weights"] == "0:100,1:200"
        assert helpers["status"] == "agcli weights status --netuid 1"
        assert helpers["show"] == "agcli weights show --netuid 1"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 1"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 1"
        assert helpers["set"] == "agcli weights set --netuid 1 --weights 0:100,1:200 --version-key 7"
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100,1:200 --version-key 7 --wait"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100,1:200 --salt round-42"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100,1:200 --salt round-42 --version-key 7"
        assert helpers["inspect_localnet_scaffold_command"] == "agcli localnet scaffold"
        assert helpers["inspect_doctor_command"] == "agcli doctor"
        assert helpers["local_validation_tip"] == c.weights._local_validation_tip()
        assert helpers["adjacent_workflows_note"] == c.weights._adjacent_workflows_note()
        assert helpers["status_note"] == c.weights._status_note()
        assert helpers["show_note"] == c.weights._show_note()
        assert helpers["pending_commits_note"] == c.weights._pending_commits_note()
        assert helpers["hyperparams_note"] == c.weights._hyperparams_note()
        assert helpers["set_weights_note"] == c.weights._set_weights_note()
        assert helpers["inspect_metagraph_command"] == "agcli subnet metagraph --netuid 1"
        assert helpers["inspect_chain_data_command"] == "agcli subnet show --netuid 1"
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 1 --json"
        assert helpers["inspect_serve_axon_command"] == "agcli serve axon --netuid 1 --ip <ip> --port <port>"
        assert helpers["explain_commit_reveal_command"] == "agcli explain commit-reveal"
        assert helpers["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 1"
        assert helpers["inspect_hotkey_address_command"] == "agcli view axon --netuid <netuid> --hotkey-address <ss58>"
        assert helpers["inspect_wallet_verify_command"] == (
            "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
        )
        assert len(helpers) >= 60
        assert "wallet" not in helpers
        assert "hotkey" not in helpers

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

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            5,
            wallet="cold",
            hotkey="miner",
            weights={0: 100},
            salt="tempo-5",
            version_key=2,
            status=READY_STATUS_TEXT,
            hyperparams={"weights_version": 2},
            show={0: 100},
            pending_commits={"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        )
        assert helpers["status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 5"
        assert helpers["show"] == "agcli weights show --netuid 5"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 5"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_set_param_command"] == "agcli subnet set-param --netuid 5"
        assert helpers["inspect_admin_list_command"] == "agcli admin list"
        assert helpers["explain_weights_command"] == "agcli explain weights"
        assert helpers["explain_commit_reveal_command"] == "agcli explain commit-reveal"
        assert helpers["inspect_probe_command"] == "agcli subnet probe --netuid 5"
        assert helpers["inspect_serve_axon_command"] == "agcli serve axon --netuid 5 --ip <ip> --port <port>"
        assert (
            helpers["inspect_serve_prometheus_command"] == "agcli serve prometheus --netuid 5 --ip <ip> --port <port>"
        )
        assert helpers["inspect_serve_axon_tls_command"] == (
            "agcli serve axon-tls --netuid 5 --ip <ip> --port <port> --cert <cert>"
        )
        assert helpers["inspect_serve_reset_command"] == "agcli serve reset --netuid 5"
        assert helpers["inspect_watch_command"] == "agcli subnet watch --netuid 5"
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 5 --json"
        assert helpers["inspect_validator_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["inspect_miner_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["adjacent_workflows_note"]
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["pending_commits_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]
        assert helpers["show_command"] == "agcli weights show --netuid 5"
        assert helpers["inspect_chain_data_command"] == "agcli subnet show --netuid 5"
        assert helpers["inspect_subnets_command"] == "agcli subnet list"
        assert helpers["inspect_subnet_command"] == "agcli subnet show --netuid 5"
        assert helpers["inspect_hyperparams_command"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_emissions_command"] == "agcli view emissions --netuid 5"
        assert helpers["inspect_neuron_command"] == "agcli view neuron --netuid 5 --uid 0"
        assert helpers["inspect_validators_command"] == "agcli view validators --netuid 5"
        assert helpers["inspect_stake_command"] == "agcli stake list --netuid 5"
        assert helpers["inspect_config_show_command"] == "agcli config show"
        assert helpers["inspect_config_set_wallet_command"] == "agcli config set --key wallet --value <wallet-name>"
        assert helpers["inspect_config_set_hotkey_command"] == "agcli config set --key hotkey --value <hotkey-name>"
        assert helpers["inspect_wallet_show_command"] == "agcli wallet show --all"
        assert helpers["inspect_wallet_current_command"] == "agcli wallet show"
        assert helpers["inspect_wallet_associate_command"] == "agcli wallet associate-hotkey"
        assert helpers["inspect_wallet_derive_command"] == "agcli wallet derive --input <pubkey-or-mnemonic>"
        assert helpers["inspect_wallet_sign_command"] == "agcli wallet sign --message <message>"
        assert helpers["inspect_wallet_verify_command"] == (
            "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
        )
        assert helpers["inspect_hotkey_address_command"] == "agcli view axon --netuid <netuid> --hotkey-address <ss58>"
        assert helpers["inspect_balance_command"] == "agcli balance"
        assert helpers["inspect_stake_add_command"] == "agcli stake add --netuid 5 --amount <amount>"
        assert helpers["inspect_validator_requirements_command"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_owner_param_list_command"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["inspect_admin_raw_command"] == "agcli admin raw --call <sudo-call>"
        assert helpers["inspect_registration_cost_command"] == "agcli subnet cost --netuid 5"
        assert helpers["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 5"
        assert helpers["inspect_pow_register_command"] == "agcli subnet pow --netuid 5"
        assert helpers["inspect_snipe_register_command"] == "agcli subnet snipe --netuid 5"
        assert helpers["inspect_health_command"] == "agcli subnet health --netuid 5"
        assert helpers["inspect_axon_command"] == "agcli view axon --netuid 5"
        assert helpers["netuid"] == 5
        assert helpers["validation_status"] == "ready"
        assert helpers["validated_reads"] == ["status", "hyperparams", "show", "pending_commits"]
        assert helpers["workflow"]["status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 5"
        assert helpers["status_summary"]["next_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 5 --weights 0:100 --salt tempo-5 --version-key 2"
        )
        assert helpers["next_validation_step"] == (
            "agcli weights reveal --netuid 5 --weights 0:100 --salt tempo-5 --version-key 2"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            6,
            weights={0: 100},
            version_key=4,
            status=DIRECT_SET_READY_STATUS_TEXT,
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert helpers["status"] == "agcli weights status --netuid 6"
        assert helpers["show"] == "agcli weights show --netuid 6"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 6"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["inspect_set_param_command"] == "agcli subnet set-param --netuid 6"
        assert helpers["inspect_admin_list_command"] == "agcli admin list"
        assert helpers["explain_weights_command"] == "agcli explain weights"
        assert helpers["explain_commit_reveal_command"] == "agcli explain commit-reveal"
        assert helpers["inspect_probe_command"] == "agcli subnet probe --netuid 6"
        assert helpers["inspect_serve_axon_command"] == "agcli serve axon --netuid 6 --ip <ip> --port <port>"
        assert (
            helpers["inspect_serve_prometheus_command"] == "agcli serve prometheus --netuid 6 --ip <ip> --port <port>"
        )
        assert helpers["inspect_serve_axon_tls_command"] == (
            "agcli serve axon-tls --netuid 6 --ip <ip> --port <port> --cert <cert>"
        )
        assert helpers["inspect_serve_reset_command"] == "agcli serve reset --netuid 6"
        assert helpers["inspect_watch_command"] == "agcli subnet watch --netuid 6"
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 6 --json"
        assert helpers["inspect_validator_endpoints_command"] == "agcli view axon --netuid 6"
        assert helpers["inspect_miner_endpoints_command"] == "agcli view axon --netuid 6"
        assert helpers["adjacent_workflows_note"]
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["pending_commits_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]
        assert helpers["show_command"] == "agcli weights show --netuid 6"
        assert helpers["inspect_chain_data_command"] == "agcli subnet show --netuid 6"
        assert helpers["inspect_subnets_command"] == "agcli subnet list"
        assert helpers["inspect_subnet_command"] == "agcli subnet show --netuid 6"
        assert helpers["inspect_hyperparams_command"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["inspect_emissions_command"] == "agcli view emissions --netuid 6"
        assert helpers["inspect_neuron_command"] == "agcli view neuron --netuid 6 --uid 0"
        assert helpers["inspect_validators_command"] == "agcli view validators --netuid 6"
        assert helpers["inspect_stake_command"] == "agcli stake list --netuid 6"
        assert helpers["inspect_config_show_command"] == "agcli config show"
        assert helpers["inspect_config_set_wallet_command"] == "agcli config set --key wallet --value <wallet-name>"
        assert helpers["inspect_config_set_hotkey_command"] == "agcli config set --key hotkey --value <hotkey-name>"
        assert helpers["inspect_wallet_show_command"] == "agcli wallet show --all"
        assert helpers["inspect_wallet_current_command"] == "agcli wallet show"
        assert helpers["inspect_wallet_associate_command"] == "agcli wallet associate-hotkey"
        assert helpers["inspect_wallet_derive_command"] == "agcli wallet derive --input <pubkey-or-mnemonic>"
        assert helpers["inspect_wallet_sign_command"] == "agcli wallet sign --message <message>"
        assert helpers["inspect_wallet_verify_command"] == (
            "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
        )
        assert helpers["inspect_hotkey_address_command"] == "agcli view axon --netuid <netuid> --hotkey-address <ss58>"
        assert helpers["inspect_balance_command"] == "agcli balance"
        assert helpers["inspect_stake_add_command"] == "agcli stake add --netuid 6 --amount <amount>"
        assert helpers["inspect_validator_requirements_command"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["inspect_owner_param_list_command"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["inspect_admin_raw_command"] == "agcli admin raw --call <sudo-call>"
        assert helpers["inspect_registration_cost_command"] == "agcli subnet cost --netuid 6"
        assert helpers["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 6"
        assert helpers["inspect_pow_register_command"] == "agcli subnet pow --netuid 6"
        assert helpers["inspect_snipe_register_command"] == "agcli subnet snipe --netuid 6"
        assert helpers["inspect_health_command"] == "agcli subnet health --netuid 6"
        assert helpers["inspect_axon_command"] == "agcli view axon --netuid 6"
        assert helpers["workflow"]["set"] == "agcli weights set --netuid 6 --weights 0:100 --version-key 4"
        assert helpers["workflow"]["status"] == "agcli weights status --netuid 6"
        assert helpers["workflow"]["show"] == "agcli weights show --netuid 6"
        assert helpers["workflow"]["pending_commits"] == "agcli subnet commits --netuid 6"
        assert helpers["workflow"]["hyperparams"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["workflow"]["inspect_set_param_command"] == "agcli subnet set-param --netuid 6"
        assert helpers["workflow"]["inspect_admin_list_command"] == "agcli admin list"
        assert helpers["workflow"]["explain_weights_command"] == "agcli explain weights"
        assert helpers["workflow"]["explain_commit_reveal_command"] == "agcli explain commit-reveal"
        assert helpers["workflow"]["inspect_probe_command"] == "agcli subnet probe --netuid 6"
        assert (
            helpers["workflow"]["inspect_serve_axon_command"] == "agcli serve axon --netuid 6 --ip <ip> --port <port>"
        )
        assert (
            helpers["workflow"]["inspect_serve_prometheus_command"]
            == "agcli serve prometheus --netuid 6 --ip <ip> --port <port>"
        )
        assert helpers["workflow"]["inspect_serve_axon_tls_command"] == (
            "agcli serve axon-tls --netuid 6 --ip <ip> --port <port> --cert <cert>"
        )
        assert helpers["workflow"]["inspect_serve_reset_command"] == "agcli serve reset --netuid 6"
        assert helpers["workflow"]["inspect_watch_command"] == "agcli subnet watch --netuid 6"
        assert helpers["workflow"]["inspect_monitor_command"] == "agcli subnet monitor --netuid 6 --json"
        assert helpers["workflow"]["inspect_validator_endpoints_command"] == "agcli view axon --netuid 6"
        assert helpers["workflow"]["inspect_miner_endpoints_command"] == "agcli view axon --netuid 6"
        assert helpers["workflow"]["adjacent_workflows_note"]
        assert helpers["workflow"]["status_note"]
        assert helpers["workflow"]["show_note"]
        assert helpers["workflow"]["pending_commits_note"]
        assert helpers["workflow"]["hyperparams_note"]
        assert helpers["workflow"]["set_weights_note"]
        assert helpers["workflow"]["show_command"] == "agcli weights show --netuid 6"
        assert helpers["workflow"]["inspect_chain_data_command"] == "agcli subnet show --netuid 6"
        assert helpers["workflow"]["inspect_subnets_command"] == "agcli subnet list"
        assert helpers["workflow"]["inspect_subnet_command"] == "agcli subnet show --netuid 6"
        assert helpers["workflow"]["inspect_hyperparams_command"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["workflow"]["inspect_emissions_command"] == "agcli view emissions --netuid 6"
        assert helpers["workflow"]["inspect_neuron_command"] == "agcli view neuron --netuid 6 --uid 0"
        assert helpers["workflow"]["inspect_validators_command"] == "agcli view validators --netuid 6"
        assert helpers["workflow"]["inspect_stake_command"] == "agcli stake list --netuid 6"
        assert helpers["workflow"]["inspect_config_show_command"] == "agcli config show"
        assert (
            helpers["workflow"]["inspect_config_set_wallet_command"]
            == "agcli config set --key wallet --value <wallet-name>"
        )
        assert (
            helpers["workflow"]["inspect_config_set_hotkey_command"]
            == "agcli config set --key hotkey --value <hotkey-name>"
        )
        assert helpers["workflow"]["inspect_wallet_show_command"] == "agcli wallet show --all"
        assert helpers["workflow"]["inspect_wallet_current_command"] == "agcli wallet show"
        assert helpers["workflow"]["inspect_wallet_associate_command"] == "agcli wallet associate-hotkey"
        assert (
            helpers["workflow"]["inspect_wallet_derive_command"] == "agcli wallet derive --input <pubkey-or-mnemonic>"
        )
        assert helpers["workflow"]["inspect_wallet_sign_command"] == "agcli wallet sign --message <message>"
        assert helpers["workflow"]["inspect_wallet_verify_command"] == (
            "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
        )
        assert (
            helpers["workflow"]["inspect_hotkey_address_command"]
            == "agcli view axon --netuid <netuid> --hotkey-address <ss58>"
        )
        assert helpers["workflow"]["inspect_balance_command"] == "agcli balance"
        assert helpers["workflow"]["inspect_stake_add_command"] == "agcli stake add --netuid 6 --amount <amount>"
        assert helpers["workflow"]["inspect_validator_requirements_command"] == "agcli subnet hyperparams --netuid 6"
        assert (
            helpers["workflow"]["inspect_owner_param_list_command"] == "agcli subnet set-param --netuid 6 --param list"
        )
        assert helpers["workflow"]["inspect_admin_raw_command"] == "agcli admin raw --call <sudo-call>"
        assert helpers["workflow"]["inspect_registration_cost_command"] == "agcli subnet cost --netuid 6"
        assert helpers["workflow"]["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 6"
        assert helpers["workflow"]["inspect_pow_register_command"] == "agcli subnet pow --netuid 6"
        assert helpers["workflow"]["inspect_snipe_register_command"] == "agcli subnet snipe --netuid 6"
        assert helpers["workflow"]["inspect_health_command"] == "agcli subnet health --netuid 6"
        assert helpers["workflow"]["inspect_axon_command"] == "agcli view axon --netuid 6"
        assert helpers["validation_status"] == "ready"
        assert helpers["workflow"]["set"] == "agcli weights set --netuid 6 --weights 0:100 --version-key 4"
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights set --netuid 6 --weights 0:100 --version-key 4"
        assert helpers["next_validation_step"] == "agcli weights set --netuid 6 --weights 0:100 --version-key 4"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.weights.weights_validation_text(7, status=READY_STATUS_TEXT, show={0: 100})
        assert text == (
            "Weights verification on subnet 7 has reads status, show; still missing hyperparams, pending_commits."
        )
        assert c.weights.validation_text(7, status=READY_STATUS_TEXT, show={0: 100}) == text
        assert c.weights.operator_validation_text(7, status=READY_STATUS_TEXT, show={0: 100}) == text
        assert c.weights.operator_workflow_validation_text(7, status=READY_STATUS_TEXT, show={0: 100}) == text

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.weights.weights_snapshot_text(7, status=READY_STATUS_TEXT, hyperparams={"tempo": 360})
        assert c.weights.snapshot_text(7, status=READY_STATUS_TEXT, hyperparams={"tempo": 360}) == text
        assert c.weights.operator_snapshot_text(7, status=READY_STATUS_TEXT, hyperparams={"tempo": 360}) == text
        assert (
            c.weights.operator_workflow_snapshot_text(7, status=READY_STATUS_TEXT, hyperparams={"tempo": 360}) == text
        )
        assert text == (
            "Weights verification on subnet 7 has reads status, hyperparams; still missing show, pending_commits. "
            "Next: agcli weights show --netuid 7"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_missing_reads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(4)
        assert helpers["validated_reads"] == []
        assert helpers["validation_status"] == "missing"
        assert helpers["next_validation_step"] == "agcli weights status --netuid 4"
        assert c.weights.validation_help(4) == helpers
        assert c.weights.operator_validation_help(4) == helpers
        assert c.weights.operator_workflow_validation_help(4) == helpers
        snapshot = c.weights.weights_snapshot_help(4)
        assert c.weights.snapshot_help(4) == snapshot
        assert c.weights.operator_snapshot_help(4) == snapshot
        assert c.weights.operator_workflow_snapshot_help(4) == snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_wait_path_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status=NO_PENDING_STATUS_TEXT,
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert (
            c.weights.validation_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status=NO_PENDING_STATUS_TEXT,
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == helpers
        )
        assert (
            c.weights.operator_validation_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status=NO_PENDING_STATUS_TEXT,
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == helpers
        )
        assert (
            c.weights.operator_workflow_validation_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status=NO_PENDING_STATUS_TEXT,
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == helpers
        )
        snapshot = c.weights.weights_snapshot_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status=NO_PENDING_STATUS_TEXT,
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert (
            c.weights.snapshot_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status=NO_PENDING_STATUS_TEXT,
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == snapshot
        )
        assert (
            c.weights.operator_snapshot_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status=NO_PENDING_STATUS_TEXT,
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == snapshot
        )
        assert (
            c.weights.operator_workflow_snapshot_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status=NO_PENDING_STATUS_TEXT,
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == snapshot
        )
        assert helpers["recommended_command"] == (
            "agcli weights commit-reveal --netuid 9 --weights 0:100 --version-key 4 --wait"
        )
        assert helpers["next_validation_step"] == (
            "agcli weights commit-reveal --netuid 9 --weights 0:100 --version-key 4 --wait"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_partial_reads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(8, status=READY_STATUS_TEXT, show={0: 100})
        assert helpers["validation_status"] == "partial"
        assert helpers["validated_reads"] == ["status", "show"]
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_without_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(10, weights={0: 100}, salt="tempo-10", version_key=5)
        assert helpers["validation_status"] == "missing"
        assert helpers["workflow"]["commit"] == "agcli weights commit --netuid 10 --weights 0:100 --salt tempo-10"
        assert helpers["next_validation_step"] == "agcli weights status --netuid 10"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_bad_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.weights_validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_blank_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.weights.weights_snapshot_help(8, wallet="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_blank_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.weights.weights_snapshot_help(8, hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_blank_salt_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="salt cannot be empty"):
            c.weights.weights_validation_help(8, weights={0: 100}, salt="   ")

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_blank_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(8, status="   ", show={0: 100})
        assert helpers["validation_status"] == "partial"
        assert helpers["validated_reads"] == ["show"]
        assert helpers["next_validation_step"] == "agcli weights status --netuid 8"
        assert c.weights.validation_help(8, status="   ", show={0: 100}) == helpers
        assert c.weights.operator_validation_help(8, status="   ", show={0: 100}) == helpers
        assert c.weights.operator_workflow_validation_help(8, status="   ", show={0: 100}) == helpers

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_bad_status_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.weights_validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_missing_block_status_mapping_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.weights_validation_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_non_bool_commit_reveal_status_mapping_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status commit_reveal_enabled must be a boolean"):
            c.weights.weights_validation_help(
                8,
                status={"block": 1, "commit_reveal_enabled": "yes", "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_missing_reveal_period_status_mapping_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status reveal_period_epochs must be an integer"):
            c.weights.weights_validation_help(
                8,
                status={"block": 1, "commit_reveal_enabled": True, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_accepts_summary_mapping_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            8,
            weights={0: 100},
            salt="tempo-8",
            version_key=3,
            status={
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
                        "hash": "0x1212",
                    }
                ],
            },
            hyperparams={"weights_version": 3},
            show={0: 100},
            pending_commits={"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        )
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )
        assert helpers["next_validation_step"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_accepts_pending_commits_key_status_mapping_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            8,
            status={
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "pending_commits": [{"status": "READY TO REVEAL", "commit_block": 100}],
            },
            hyperparams={"weights_version": 3},
            show={0: 100},
            pending_commits={"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        )
        assert helpers["status_summary"]["pending_commits"] == 1
        assert helpers["validation_status"] == "ready"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_accepts_blank_non_status_inputs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(8, show="   ", hyperparams="   ", pending_commits="   ")
        assert helpers["validation_status"] == "missing"
        assert helpers["validated_reads"] == []

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_uses_summary_mapping_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            8,
            weights={0: 100},
            salt="tempo-8",
            version_key=3,
            status={
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
                        "hash": "0x1212",
                    }
                ],
            },
            hyperparams={"weights_version": 3},
            show={0: 100},
            pending_commits={"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        )
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )
        assert helpers["next_validation_step"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_without_status_via_client_surface_matches_aliases(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        snapshot = c.weights.weights_snapshot_help(10, weights={0: 100}, salt="tempo-10", version_key=5)
        assert c.weights.snapshot_help(10, weights={0: 100}, salt="tempo-10", version_key=5) == snapshot
        assert c.weights.operator_snapshot_help(10, weights={0: 100}, salt="tempo-10", version_key=5) == snapshot
        assert (
            c.weights.operator_workflow_snapshot_help(10, weights={0: 100}, salt="tempo-10", version_key=5) == snapshot
        )
        assert snapshot["workflow"]["commit"] == "agcli weights commit --netuid 10 --weights 0:100 --salt tempo-10"
        assert snapshot["next_validation_step"] == "agcli weights status --netuid 10"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_accepts_waiting_summary_mapping_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            5,
            weights={0: 100},
            salt="tempo-5",
            version_key=2,
            status={
                "block": 100,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 2,
                "commits": [
                    {
                        "status": "WAITING (10 blocks until reveal window)",
                        "commit_block": 90,
                        "first_reveal": 110,
                        "last_reveal": 120,
                        "blocks_until_action": 10,
                        "hash": "0x3434",
                    }
                ],
            },
            show={0: 100},
        )
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["ready_command"] == (
            "agcli weights reveal --netuid 5 --weights 0:100 --salt tempo-5 --version-key 2"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_status_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        result = c.weights.validation_help(8, status="   ", show={0: 100})
        assert c.weights.operator_validation_help(8, status="   ", show={0: 100}) == result
        assert c.weights.operator_workflow_validation_help(8, status="   ", show={0: 100}) == result

    @patch("taocli.runner.subprocess.run")
    def test_weights_text_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.weights.validation_text(
            7, status=READY_STATUS_TEXT, show={0: 100}
        ) == c.weights.weights_validation_text(
            7,
            status=READY_STATUS_TEXT,
            show={0: 100},
        )
        assert c.weights.operator_validation_text(
            7, status=READY_STATUS_TEXT, show={0: 100}
        ) == c.weights.weights_validation_text(
            7,
            status=READY_STATUS_TEXT,
            show={0: 100},
        )
        assert c.weights.operator_workflow_validation_text(
            7,
            status=READY_STATUS_TEXT,
            show={0: 100},
        ) == c.weights.weights_validation_text(7, status=READY_STATUS_TEXT, show={0: 100})
        assert c.weights.snapshot_text(
            7, status=READY_STATUS_TEXT, hyperparams={"tempo": 360}
        ) == c.weights.weights_snapshot_text(
            7,
            status=READY_STATUS_TEXT,
            hyperparams={"tempo": 360},
        )
        assert c.weights.operator_snapshot_text(
            7,
            status=READY_STATUS_TEXT,
            hyperparams={"tempo": 360},
        ) == c.weights.weights_snapshot_text(7, status=READY_STATUS_TEXT, hyperparams={"tempo": 360})
        assert c.weights.operator_workflow_snapshot_text(
            7,
            status=READY_STATUS_TEXT,
            hyperparams={"tempo": 360},
        ) == c.weights.weights_snapshot_text(7, status=READY_STATUS_TEXT, hyperparams={"tempo": 360})

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_primary_and_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-8",
            "version_key": 3,
            "status": READY_STATUS_TEXT,
            "hyperparams": {"weights_version": 3},
            "show": {0: 100},
            "pending_commits": {"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        }
        primary = c.weights.weights_validation_help(8, **kwargs)
        assert c.weights.validation_help(8, **kwargs) == primary
        assert c.weights.operator_validation_help(8, **kwargs) == primary
        assert c.weights.operator_workflow_validation_help(8, **kwargs) == primary
        primary_snapshot = c.weights.weights_snapshot_help(8, **kwargs)
        assert c.weights.snapshot_help(8, **kwargs) == primary_snapshot
        assert c.weights.operator_snapshot_help(8, **kwargs) == primary_snapshot
        assert c.weights.operator_workflow_snapshot_help(8, **kwargs) == primary_snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_selected_workflow_commands_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(6)
        assert helpers["status"] == "agcli weights status --netuid 6"
        assert helpers["show"] == "agcli weights show --netuid 6"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_selected_workflow_commands_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(6)
        assert helpers["status"] == "agcli weights status --netuid 6"
        assert helpers["show"] == "agcli weights show --netuid 6"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_non_status_inputs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(8, show="   ", hyperparams="   ", pending_commits="   ")
        assert helpers["validation_status"] == "missing"
        assert helpers["validated_reads"] == []

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_copies_next_action_subset_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            8,
            weights={0: 100},
            salt="tempo-8",
            version_key=3,
            status=READY_STATUS_TEXT,
            hyperparams={"weights_version": 3},
            show={0: 100},
            pending_commits={"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        )
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )
        assert helpers["reason"] == "A pending commit is ready to reveal now."
        assert helpers["next_step"] == "Run recommended_command now to reveal the pending commit."

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_primary_and_aliases_wait_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-9",
            "version_key": 4,
            "wait": True,
            "status": NO_PENDING_STATUS_TEXT,
            "hyperparams": {"weights_version": 4},
            "show": {0: 100},
            "pending_commits": {"commits": []},
        }
        primary = c.weights.weights_validation_help(9, **kwargs)
        assert c.weights.validation_help(9, **kwargs) == primary
        assert c.weights.operator_validation_help(9, **kwargs) == primary
        assert c.weights.operator_workflow_validation_help(9, **kwargs) == primary
        primary_snapshot = c.weights.weights_snapshot_help(9, **kwargs)
        assert c.weights.snapshot_help(9, **kwargs) == primary_snapshot
        assert c.weights.operator_snapshot_help(9, **kwargs) == primary_snapshot
        assert c.weights.operator_workflow_snapshot_help(9, **kwargs) == primary_snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_summary_mapping_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-8",
            "version_key": 3,
            "status": {
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
                        "hash": "0x1212",
                    }
                ],
            },
            "hyperparams": {"weights_version": 3},
            "show": {0: 100},
            "pending_commits": {"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        }
        primary = c.weights.weights_validation_help(8, **kwargs)
        assert c.weights.validation_help(8, **kwargs) == primary
        assert c.weights.operator_validation_help(8, **kwargs) == primary
        assert c.weights.operator_workflow_validation_help(8, **kwargs) == primary
        primary_snapshot = c.weights.weights_snapshot_help(8, **kwargs)
        assert c.weights.snapshot_help(8, **kwargs) == primary_snapshot
        assert c.weights.operator_snapshot_help(8, **kwargs) == primary_snapshot
        assert c.weights.operator_workflow_snapshot_help(8, **kwargs) == primary_snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_waiting_mapping_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-5",
            "version_key": 2,
            "status": {
                "block": 100,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 2,
                "commits": [
                    {
                        "status": "WAITING (10 blocks until reveal window)",
                        "commit_block": 90,
                        "first_reveal": 110,
                        "last_reveal": 120,
                        "blocks_until_action": 10,
                        "hash": "0x3434",
                    }
                ],
            },
            "show": {0: 100},
        }
        primary = c.weights.weights_validation_help(5, **kwargs)
        assert c.weights.validation_help(5, **kwargs) == primary
        assert c.weights.operator_validation_help(5, **kwargs) == primary
        assert c.weights.operator_workflow_validation_help(5, **kwargs) == primary
        primary_snapshot = c.weights.weights_snapshot_help(5, **kwargs)
        assert c.weights.snapshot_help(5, **kwargs) == primary_snapshot
        assert c.weights.operator_snapshot_help(5, **kwargs) == primary_snapshot
        assert c.weights.operator_workflow_snapshot_help(5, **kwargs) == primary_snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_blank_status_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        snapshot = c.weights.weights_snapshot_help(8, status="   ", show={0: 100})
        assert c.weights.snapshot_help(8, status="   ", show={0: 100}) == snapshot
        assert c.weights.operator_snapshot_help(8, status="   ", show={0: 100}) == snapshot
        assert c.weights.operator_workflow_snapshot_help(8, status="   ", show={0: 100}) == snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_accepts_pending_commits_key_mapping_aliases_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "status": {
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "pending_commits": [{"status": "READY TO REVEAL", "commit_block": 100}],
            },
            "hyperparams": {"weights_version": 3},
            "show": {0: 100},
            "pending_commits": {"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        }
        primary = c.weights.weights_validation_help(8, **kwargs)
        assert c.weights.validation_help(8, **kwargs) == primary
        assert c.weights.operator_validation_help(8, **kwargs) == primary
        assert c.weights.operator_workflow_validation_help(8, **kwargs) == primary
        primary_snapshot = c.weights.weights_snapshot_help(8, **kwargs)
        assert c.weights.snapshot_help(8, **kwargs) == primary_snapshot
        assert c.weights.operator_snapshot_help(8, **kwargs) == primary_snapshot
        assert c.weights.operator_workflow_snapshot_help(8, **kwargs) == primary_snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_bad_status_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.weights_snapshot_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_bad_status_text_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_workflow_validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_bad_status_text_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.snapshot_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_snapshot_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_workflow_snapshot_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_summary_mapping_text_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        summary_text = c.weights.weights_validation_text(
            8,
            status={
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
                        "hash": "0x1212",
                    }
                ],
            },
            show={0: 100},
        )
        assert (
            c.weights.validation_text(
                8,
                status={
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
                            "hash": "0x1212",
                        }
                    ],
                },
                show={0: 100},
            )
            == summary_text
        )
        assert (
            c.weights.operator_validation_text(
                8,
                status={
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
                            "hash": "0x1212",
                        }
                    ],
                },
                show={0: 100},
            )
            == summary_text
        )
        assert (
            c.weights.operator_workflow_validation_text(
                8,
                status={
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
                            "hash": "0x1212",
                        }
                    ],
                },
                show={0: 100},
            )
            == summary_text
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_summary_mapping_text_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        snapshot_text = c.weights.weights_snapshot_text(
            8,
            status={
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
                        "hash": "0x1212",
                    }
                ],
            },
            show={0: 100},
        )
        assert (
            c.weights.snapshot_text(
                8,
                status={
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
                            "hash": "0x1212",
                        }
                    ],
                },
                show={0: 100},
            )
            == snapshot_text
        )
        assert (
            c.weights.operator_snapshot_text(
                8,
                status={
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
                            "hash": "0x1212",
                        }
                    ],
                },
                show={0: 100},
            )
            == snapshot_text
        )
        assert (
            c.weights.operator_workflow_snapshot_text(
                8,
                status={
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
                            "hash": "0x1212",
                        }
                    ],
                },
                show={0: 100},
            )
            == snapshot_text
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_selected_workflow_commands_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        primary = c.weights.weights_snapshot_help(6)
        assert c.weights.snapshot_help(6) == primary
        assert c.weights.operator_snapshot_help(6) == primary
        assert c.weights.operator_workflow_snapshot_help(6) == primary

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_selected_workflow_commands_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        primary = c.weights.weights_validation_help(6)
        assert c.weights.validation_help(6) == primary
        assert c.weights.operator_validation_help(6) == primary
        assert c.weights.operator_workflow_validation_help(6) == primary

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_blank_non_status_inputs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ")
        assert helpers["validation_status"] == "missing"
        assert helpers["validated_reads"] == []
        assert c.weights.snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ") == helpers
        assert c.weights.operator_snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ") == helpers
        assert (
            c.weights.operator_workflow_snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ")
            == helpers
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_non_status_inputs_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        primary = c.weights.weights_validation_help(8, show="   ", hyperparams="   ", pending_commits="   ")
        assert c.weights.validation_help(8, show="   ", hyperparams="   ", pending_commits="   ") == primary
        assert c.weights.operator_validation_help(8, show="   ", hyperparams="   ", pending_commits="   ") == primary
        assert (
            c.weights.operator_workflow_validation_help(8, show="   ", hyperparams="   ", pending_commits="   ")
            == primary
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_bad_status_text_selected_aliases_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.snapshot_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_snapshot_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_workflow_snapshot_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_bad_status_text_validation_aliases_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")
        with pytest.raises(ValueError, match="weights status output must be a mapping or recognizable status text"):
            c.weights.operator_workflow_validation_help(8, status="Weight Commit Status — SN8\n  Hotkey: only")

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_summary_mapping_missing_block_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.weights_snapshot_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_summary_mapping_non_bool_commit_reveal_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status commit_reveal_enabled must be a boolean"):
            c.weights.weights_snapshot_help(
                8,
                status={"block": 1, "commit_reveal_enabled": "yes", "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_summary_mapping_missing_reveal_period_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status reveal_period_epochs must be an integer"):
            c.weights.weights_snapshot_help(
                8,
                status={"block": 1, "commit_reveal_enabled": True, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_rejects_summary_mapping_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.snapshot_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.operator_snapshot_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.operator_workflow_snapshot_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_rejects_summary_mapping_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.validation_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.operator_validation_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )
        with pytest.raises(ValueError, match="status block must be an integer"):
            c.weights.operator_workflow_validation_help(
                8,
                status={"commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
                show={0: 100},
            )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_wait_mapping_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-5",
            "version_key": 2,
            "status": {
                "block": 100,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 2,
                "commits": [
                    {
                        "status": "WAITING (10 blocks until reveal window)",
                        "commit_block": 90,
                        "first_reveal": 110,
                        "last_reveal": 120,
                        "blocks_until_action": 10,
                        "hash": "0x3434",
                    }
                ],
            },
            "show": {0: 100},
        }
        primary = c.weights.weights_snapshot_help(5, **kwargs)
        assert c.weights.snapshot_help(5, **kwargs) == primary
        assert c.weights.operator_snapshot_help(5, **kwargs) == primary
        assert c.weights.operator_workflow_snapshot_help(5, **kwargs) == primary

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_status_summary_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-8",
            "version_key": 3,
            "status": READY_STATUS_TEXT,
            "hyperparams": {"weights_version": 3},
            "show": {0: 100},
            "pending_commits": {"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        }
        snapshot = c.weights.weights_snapshot_help(8, **kwargs)
        assert snapshot["recommended_command"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )
        assert c.weights.snapshot_help(8, **kwargs) == snapshot
        assert c.weights.operator_snapshot_help(8, **kwargs) == snapshot
        assert c.weights.operator_workflow_snapshot_help(8, **kwargs) == snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_ready_direct_set_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "version_key": 4,
            "status": DIRECT_SET_READY_STATUS_TEXT,
            "hyperparams": {"weights_version": 4},
            "show": {0: 100},
            "pending_commits": {"commits": []},
        }
        primary = c.weights.weights_validation_help(6, **kwargs)
        assert c.weights.validation_help(6, **kwargs) == primary
        assert c.weights.operator_validation_help(6, **kwargs) == primary
        assert c.weights.operator_workflow_validation_help(6, **kwargs) == primary
        primary_snapshot = c.weights.weights_snapshot_help(6, **kwargs)
        assert c.weights.snapshot_help(6, **kwargs) == primary_snapshot
        assert c.weights.operator_snapshot_help(6, **kwargs) == primary_snapshot
        assert c.weights.operator_workflow_snapshot_help(6, **kwargs) == primary_snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_status_aliases_snapshot_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        snapshot = c.weights.weights_snapshot_help(8, status="   ", show={0: 100})
        assert snapshot["validation_status"] == "partial"
        assert snapshot["validated_reads"] == ["show"]
        assert c.weights.snapshot_help(8, status="   ", show={0: 100}) == snapshot
        assert c.weights.operator_snapshot_help(8, status="   ", show={0: 100}) == snapshot
        assert c.weights.operator_workflow_snapshot_help(8, status="   ", show={0: 100}) == snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_status_text_alias_validation_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        primary = c.weights.weights_validation_help(8, status="   ", show={0: 100})
        assert c.weights.validation_help(8, status="   ", show={0: 100}) == primary
        assert c.weights.operator_validation_help(8, status="   ", show={0: 100}) == primary
        assert c.weights.operator_workflow_validation_help(8, status="   ", show={0: 100}) == primary

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_blank_non_status_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        primary = c.weights.weights_snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ")
        assert c.weights.snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ") == primary
        assert c.weights.operator_snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ") == primary
        assert (
            c.weights.operator_workflow_snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ")
            == primary
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_non_status_aliases_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        validation_text = c.weights.weights_validation_text(8, show="   ")
        assert c.weights.validation_text(8, show="   ") == validation_text
        assert c.weights.operator_validation_text(8, show="   ") == validation_text
        assert c.weights.operator_workflow_validation_text(8, show="   ") == validation_text
        snapshot_text = c.weights.weights_snapshot_text(8, show="   ")
        assert c.weights.snapshot_text(8, show="   ") == snapshot_text
        assert c.weights.operator_snapshot_text(8, show="   ") == snapshot_text
        assert c.weights.operator_workflow_snapshot_text(8, show="   ") == snapshot_text

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_status_summary_selected_commands_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            8,
            weights={0: 100},
            salt="tempo-8",
            version_key=3,
            status=READY_STATUS_TEXT,
            hyperparams={"weights_version": 3},
            show={0: 100},
            pending_commits={"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        )
        assert helpers["status"] == "agcli weights status --netuid 8"
        assert helpers["show"] == "agcli weights show --netuid 8"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 8"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_wait_status_summary_selected_commands_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status=NO_PENDING_STATUS_TEXT,
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert helpers["recommended_command"] == (
            "agcli weights commit-reveal --netuid 9 --weights 0:100 --version-key 4 --wait"
        )
        assert helpers["next_validation_step"] == (
            "agcli weights commit-reveal --netuid 9 --weights 0:100 --version-key 4 --wait"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_wait_status_summary_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-9",
            "version_key": 4,
            "wait": True,
            "status": NO_PENDING_STATUS_TEXT,
            "hyperparams": {"weights_version": 4},
            "show": {0: 100},
            "pending_commits": {"commits": []},
        }
        snapshot = c.weights.weights_snapshot_help(9, **kwargs)
        assert c.weights.snapshot_help(9, **kwargs) == snapshot
        assert c.weights.operator_snapshot_help(9, **kwargs) == snapshot
        assert c.weights.operator_workflow_snapshot_help(9, **kwargs) == snapshot

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_selected_adjacent_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(5, wallet="cold", hotkey="miner")
        assert helpers["inspect_set_param_command"] == "agcli subnet set-param --netuid 5"
        assert helpers["inspect_admin_list_command"] == "agcli admin list"
        assert helpers["inspect_probe_command"] == "agcli subnet probe --netuid 5"
        assert helpers["inspect_serve_axon_command"] == "agcli serve axon --netuid 5 --ip <ip> --port <port>"
        assert (
            helpers["inspect_serve_prometheus_command"] == "agcli serve prometheus --netuid 5 --ip <ip> --port <port>"
        )
        assert helpers["inspect_serve_axon_tls_command"] == (
            "agcli serve axon-tls --netuid 5 --ip <ip> --port <port> --cert <cert>"
        )
        assert helpers["inspect_serve_reset_command"] == "agcli serve reset --netuid 5"
        assert helpers["inspect_watch_command"] == "agcli subnet watch --netuid 5"
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 5 --json"
        assert helpers["inspect_validator_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["inspect_miner_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["adjacent_workflows_note"]
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["pending_commits_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]
        assert helpers["show_command"] == "agcli weights show --netuid 5"
        assert helpers["inspect_chain_data_command"] == "agcli subnet show --netuid 5"
        assert helpers["inspect_subnets_command"] == "agcli subnet list"
        assert helpers["inspect_subnet_command"] == "agcli subnet show --netuid 5"
        assert helpers["inspect_hyperparams_command"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_emissions_command"] == "agcli view emissions --netuid 5"
        assert helpers["inspect_neuron_command"] == "agcli view neuron --netuid 5 --uid 0"
        assert helpers["inspect_validators_command"] == "agcli view validators --netuid 5"
        assert helpers["inspect_stake_command"] == "agcli stake list --netuid 5"
        assert helpers["inspect_config_show_command"] == "agcli config show"
        assert helpers["inspect_config_set_wallet_command"] == "agcli config set --key wallet --value <wallet-name>"
        assert helpers["inspect_config_set_hotkey_command"] == "agcli config set --key hotkey --value <hotkey-name>"
        assert helpers["inspect_wallet_show_command"] == "agcli wallet show --all"
        assert helpers["inspect_wallet_current_command"] == "agcli wallet show"
        assert helpers["inspect_wallet_associate_command"] == "agcli wallet associate-hotkey"
        assert helpers["inspect_wallet_derive_command"] == "agcli wallet derive --input <pubkey-or-mnemonic>"
        assert helpers["inspect_wallet_sign_command"] == "agcli wallet sign --message <message>"
        assert helpers["inspect_wallet_verify_command"] == (
            "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
        )
        assert helpers["inspect_hotkey_address_command"] == "agcli view axon --netuid <netuid> --hotkey-address <ss58>"
        assert helpers["inspect_balance_command"] == "agcli balance"
        assert helpers["inspect_stake_add_command"] == "agcli stake add --netuid 5 --amount <amount>"
        assert helpers["inspect_validator_requirements_command"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_owner_param_list_command"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["inspect_admin_raw_command"] == "agcli admin raw --call <sudo-call>"
        assert helpers["inspect_registration_cost_command"] == "agcli subnet cost --netuid 5"
        assert helpers["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 5"
        assert helpers["inspect_pow_register_command"] == "agcli subnet pow --netuid 5"
        assert helpers["inspect_snipe_register_command"] == "agcli subnet snipe --netuid 5"
        assert helpers["inspect_health_command"] == "agcli subnet health --netuid 5"
        assert helpers["inspect_axon_command"] == "agcli view axon --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_selected_adjacent_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(5, wallet="cold", hotkey="miner")
        assert helpers["inspect_set_param_command"] == "agcli subnet set-param --netuid 5"
        assert helpers["inspect_admin_list_command"] == "agcli admin list"
        assert helpers["inspect_probe_command"] == "agcli subnet probe --netuid 5"
        assert helpers["inspect_serve_axon_command"] == "agcli serve axon --netuid 5 --ip <ip> --port <port>"
        assert (
            helpers["inspect_serve_prometheus_command"] == "agcli serve prometheus --netuid 5 --ip <ip> --port <port>"
        )
        assert helpers["inspect_serve_axon_tls_command"] == (
            "agcli serve axon-tls --netuid 5 --ip <ip> --port <port> --cert <cert>"
        )
        assert helpers["inspect_serve_reset_command"] == "agcli serve reset --netuid 5"
        assert helpers["inspect_watch_command"] == "agcli subnet watch --netuid 5"
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 5 --json"
        assert helpers["inspect_validator_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["inspect_miner_endpoints_command"] == "agcli view axon --netuid 5"
        assert helpers["adjacent_workflows_note"]
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["pending_commits_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]
        assert helpers["show_command"] == "agcli weights show --netuid 5"
        assert helpers["inspect_chain_data_command"] == "agcli subnet show --netuid 5"
        assert helpers["inspect_subnets_command"] == "agcli subnet list"
        assert helpers["inspect_subnet_command"] == "agcli subnet show --netuid 5"
        assert helpers["inspect_hyperparams_command"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_emissions_command"] == "agcli view emissions --netuid 5"
        assert helpers["inspect_neuron_command"] == "agcli view neuron --netuid 5 --uid 0"
        assert helpers["inspect_validators_command"] == "agcli view validators --netuid 5"
        assert helpers["inspect_stake_command"] == "agcli stake list --netuid 5"
        assert helpers["inspect_config_show_command"] == "agcli config show"
        assert helpers["inspect_config_set_wallet_command"] == "agcli config set --key wallet --value <wallet-name>"
        assert helpers["inspect_config_set_hotkey_command"] == "agcli config set --key hotkey --value <hotkey-name>"
        assert helpers["inspect_wallet_show_command"] == "agcli wallet show --all"
        assert helpers["inspect_wallet_current_command"] == "agcli wallet show"
        assert helpers["inspect_wallet_associate_command"] == "agcli wallet associate-hotkey"
        assert helpers["inspect_wallet_derive_command"] == "agcli wallet derive --input <pubkey-or-mnemonic>"
        assert helpers["inspect_wallet_sign_command"] == "agcli wallet sign --message <message>"
        assert helpers["inspect_wallet_verify_command"] == (
            "agcli wallet verify --message <message> --signature <signature> --signer <ss58>"
        )
        assert helpers["inspect_hotkey_address_command"] == "agcli view axon --netuid <netuid> --hotkey-address <ss58>"
        assert helpers["inspect_balance_command"] == "agcli balance"
        assert helpers["inspect_stake_add_command"] == "agcli stake add --netuid 5 --amount <amount>"
        assert helpers["inspect_validator_requirements_command"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["inspect_owner_param_list_command"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["inspect_admin_raw_command"] == "agcli admin raw --call <sudo-call>"
        assert helpers["inspect_registration_cost_command"] == "agcli subnet cost --netuid 5"
        assert helpers["inspect_register_neuron_command"] == "agcli subnet register-neuron --netuid 5"
        assert helpers["inspect_pow_register_command"] == "agcli subnet pow --netuid 5"
        assert helpers["inspect_snipe_register_command"] == "agcli subnet snipe --netuid 5"
        assert helpers["inspect_health_command"] == "agcli subnet health --netuid 5"
        assert helpers["inspect_axon_command"] == "agcli view axon --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_status_summary_text_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        validation_text = c.weights.weights_validation_text(
            8,
            status=READY_STATUS_TEXT,
            hyperparams={"weights_version": 3},
        )
        assert (
            c.weights.validation_text(8, status=READY_STATUS_TEXT, hyperparams={"weights_version": 3})
            == validation_text
        )
        assert (
            c.weights.operator_validation_text(
                8,
                status=READY_STATUS_TEXT,
                hyperparams={"weights_version": 3},
            )
            == validation_text
        )
        assert (
            c.weights.operator_workflow_validation_text(
                8,
                status=READY_STATUS_TEXT,
                hyperparams={"weights_version": 3},
            )
            == validation_text
        )
        snapshot_text = c.weights.weights_snapshot_text(
            8,
            status=READY_STATUS_TEXT,
            hyperparams={"weights_version": 3},
        )
        assert c.weights.snapshot_text(8, status=READY_STATUS_TEXT, hyperparams={"weights_version": 3}) == snapshot_text
        assert (
            c.weights.operator_snapshot_text(
                8,
                status=READY_STATUS_TEXT,
                hyperparams={"weights_version": 3},
            )
            == snapshot_text
        )
        assert (
            c.weights.operator_workflow_snapshot_text(
                8,
                status=READY_STATUS_TEXT,
                hyperparams={"weights_version": 3},
            )
            == snapshot_text
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_with_blank_status_and_wait_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status="   ",
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert helpers["validation_status"] == "partial"
        assert helpers["validated_reads"] == ["hyperparams", "show", "pending_commits"]
        assert helpers["next_validation_step"] == "agcli weights status --netuid 9"

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_with_blank_status_and_wait_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status="   ",
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert helpers["validation_status"] == "partial"
        assert helpers["validated_reads"] == ["hyperparams", "show", "pending_commits"]
        assert helpers["next_validation_step"] == "agcli weights status --netuid 9"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_status_and_wait_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        primary = c.weights.weights_validation_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status="   ",
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert (
            c.weights.validation_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status="   ",
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == primary
        )
        assert (
            c.weights.operator_validation_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status="   ",
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == primary
        )
        assert (
            c.weights.operator_workflow_validation_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status="   ",
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == primary
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_snapshot_help_blank_status_and_wait_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        primary = c.weights.weights_snapshot_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status="   ",
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert (
            c.weights.snapshot_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status="   ",
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == primary
        )
        assert (
            c.weights.operator_snapshot_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status="   ",
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == primary
        )
        assert (
            c.weights.operator_workflow_snapshot_help(
                9,
                weights={0: 100},
                salt="tempo-9",
                version_key=4,
                wait=True,
                status="   ",
                hyperparams={"weights_version": 4},
                show={0: 100},
                pending_commits={"commits": []},
            )
            == primary
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_selected_commands_and_notes_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(5, wallet="cold", hotkey="miner")
        assert helpers["status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 5"
        assert helpers["show"] == "agcli weights show --netuid 5"
        assert helpers["pending_commits"] == "agcli subnet commits --netuid 5"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["show_command"] == "agcli weights show --netuid 5"
        assert helpers["adjacent_workflows_note"]
        assert helpers["status_note"]
        assert helpers["show_note"]
        assert helpers["pending_commits_note"]
        assert helpers["hyperparams_note"]
        assert helpers["set_weights_note"]

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_status_summary_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            8,
            weights={0: 100},
            salt="tempo-8",
            version_key=3,
            status=READY_STATUS_TEXT,
            hyperparams={"weights_version": 3},
            show={0: 100},
            pending_commits={"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        )
        assert helpers["status_summary"]["next_action"] == "REVEAL"
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )
        assert helpers["reason"] == "A pending commit is ready to reveal now."
        assert helpers["next_step"] == "Run recommended_command now to reveal the pending commit."

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_wait_status_summary_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            5,
            weights={0: 100},
            salt="tempo-5",
            version_key=2,
            status={
                "block": 100,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 2,
                "commits": [
                    {
                        "status": "WAITING (10 blocks until reveal window)",
                        "commit_block": 90,
                        "first_reveal": 110,
                        "last_reveal": 120,
                        "blocks_until_action": 10,
                        "hash": "0x3434",
                    }
                ],
            },
            show={0: 100},
        )
        assert helpers["status_summary"]["next_action"] == "WAIT"
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["ready_command"] == (
            "agcli weights reveal --netuid 5 --weights 0:100 --salt tempo-5 --version-key 2"
        )
        assert helpers["timing_note"] == "Wait about 10 more blocks, then check status again."

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_direct_set_status_summary_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            6,
            weights={0: 100},
            version_key=4,
            status=DIRECT_SET_READY_STATUS_TEXT,
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights set --netuid 6 --weights 0:100 --version-key 4"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_no_pending_wait_summary_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(
            9,
            weights={0: 100},
            salt="tempo-9",
            version_key=4,
            wait=True,
            status=NO_PENDING_STATUS_TEXT,
            hyperparams={"weights_version": 4},
            show={0: 100},
            pending_commits={"commits": []},
        )
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == (
            "agcli weights commit-reveal --netuid 9 --weights 0:100 --version-key 4 --wait"
        )
        assert helpers["next_validation_step"] == (
            "agcli weights commit-reveal --netuid 9 --weights 0:100 --version-key 4 --wait"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_status_summary_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(8, status="   ", show={0: 100})
        assert "status_summary" not in helpers
        assert "recommended_action" not in helpers
        assert helpers["next_validation_step"] == "agcli weights status --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_blank_non_status_summary_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_snapshot_help(8, show="   ", hyperparams="   ", pending_commits="   ")
        assert "status_summary" not in helpers
        assert "recommended_action" not in helpers
        assert helpers["next_validation_step"] == "agcli weights status --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_summary_fields_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        kwargs = {
            "weights": {0: 100},
            "salt": "tempo-8",
            "version_key": 3,
            "status": READY_STATUS_TEXT,
            "hyperparams": {"weights_version": 3},
            "show": {0: 100},
            "pending_commits": {"commits": [{"hash": "0x1212", "status": "READY TO REVEAL"}]},
        }
        primary = c.weights.weights_snapshot_help(8, **kwargs)
        assert c.weights.snapshot_help(8, **kwargs) == primary
        assert c.weights.operator_snapshot_help(8, **kwargs) == primary
        assert c.weights.operator_workflow_snapshot_help(8, **kwargs) == primary

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_uses_mapping_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            8,
            weights={0: 100},
            salt="tempo-8",
            version_key=3,
            status={
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
                        "hash": "0x1212",
                    }
                ],
            },
            hyperparams={"weights_version": 3},
            show={0: 100},
            pending_commits=[{"hash": "0x1212"}],
        )
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )
        assert helpers["next_validation_step"] == (
            "agcli weights reveal --netuid 8 --weights 0:100 --salt tempo-8 --version-key 3"
        )

    @patch("taocli.runner.subprocess.run")
    def test_weights_validation_help_keeps_prefixed_workflow_commands_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.weights_validation_help(
            5,
            wallet="cold",
            hotkey="validator",
            weights={0: 100},
            salt="tempo-5",
            version_key=2,
        )
        assert helpers["workflow"]["status"] == "agcli --wallet cold --hotkey-name validator weights status --netuid 5"
        assert helpers["workflow"]["set"] == (
            "agcli --wallet cold --hotkey-name validator weights set --netuid 5 --weights 0:100 --version-key 2"
        )
        assert helpers["workflow"]["commit_reveal"] == (
            "agcli --wallet cold --hotkey-name validator weights commit-reveal --netuid 5 "
            "--weights 0:100 --version-key 2"
        )
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
            "inspect_localnet_scaffold_command": "agcli localnet scaffold",
            "inspect_doctor_command": "agcli doctor",
            "local_validation_tip": c.weights._local_validation_tip(),
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
            "config_show plus config_set_wallet plus config_set_hotkey plus wallet_show plus wallet_current plus "
            "wallet_associate plus wallet_derive plus wallet_sign plus wallet_verify plus hotkey_address plus balance"
            in helpers["adjacent_workflows_note"]
        )
        assert "hotkey-address confirmation" in helpers["adjacent_workflows_note"]
        assert "inspect_config_set_wallet_command" in helpers["adjacent_recovery_note"]
        assert "inspect_config_set_hotkey_command" in helpers["adjacent_recovery_note"]
        assert "inspect_hotkey_address_command" in helpers["adjacent_recovery_note"]
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
    def test_weights_troubleshoot_unrevealed_commit_help_preserves_raw_status_text_via_client_surface(
        self, mock_run, tmp_path
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        state_path = tmp_path / "weights-state.json"
        c.weights.save_commit_reveal_state_help(state_path, 97, "0:100", "abc", version_key=6)
        status_text = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   125
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  Pending commits: 1

  [1] Hash:    0x1212
      Commit:  block 100
      Reveal:  blocks 120..130
      Status:  READY TO REVEAL (5 blocks remaining)
"""
        helpers = c.weights.troubleshoot_unrevealed_commit_help(state_path, status=status_text)
        assert helpers["raw_status"] == status_text.strip()
        assert helpers["status_summary"]["next_action"] == "REVEAL"

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
        assert helpers["scope"] == "uid"
        assert helpers["uid"] == 9
        assert helpers["summary"] == (
            "Start with the SN3 metagraph, then inspect UID 9 directly with neuron, axon, and probe reads."
        )
        assert helpers["recommended_order"] == ["subnet", "metagraph", "validators", "axon", "probe", "hyperparams"]
        assert helpers["primary_read"] == "agcli view neuron --netuid 3 --uid 9"
        assert helpers["endpoint_check"] == "agcli view axon --netuid 3 --uid 9"
        assert helpers["reachability_check"] == "agcli subnet probe --netuid 3 --uids 9"
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
        assert helpers["scope"] == "hotkey"
        assert helpers["hotkey_address"] == "5F..."
        assert helpers["filter_note"] == (
            "Hotkey focus narrows view axon only; keep metagraph and probe subnet-wide unless you also know the UID."
        )
        assert helpers["endpoint_check"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
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
        assert helpers["scope"] == "wallet_and_hotkey"
        assert helpers["summary"] == "Check subnet 5 readiness, then register hotkey miner from wallet cold."
        assert helpers["recommended_order"] == [
            "subnet",
            "registration_cost",
            "health",
            "register_neuron",
            "post_registration_check",
        ]
        assert helpers["registration_cost"] == "agcli subnet cost --netuid 5"
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 5"
        assert helpers["pow_register"] == "agcli --wallet cold --hotkey-name miner subnet pow --netuid 5 --threads 4"
        assert (
            helpers["primary_register"] == "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 5"
        )
        assert helpers["post_registration_check"] == "agcli subnet metagraph --netuid 5 --full"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_validation_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_validation_help(5, hotkey="miner", subnet={"netuid": 5}, health={"ok": True})
        assert helpers["scope"] == "hotkey"
        assert helpers["validated_reads"] == ["subnet", "health"]
        assert helpers["missing_reads"] == ["registration_cost"]
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet cost --netuid 5"
        assert helpers["workflow"]["register_neuron"] == "agcli --hotkey-name miner subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_snapshot_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_snapshot_help(
            5,
            wallet="cold",
            hotkey="miner",
            subnet={"netuid": 5},
            registration_cost={"tao": 1.0},
            health={"ok": True},
            registration_proof={"uid": 2},
        )
        assert helpers["validation_status"] == "registered"
        assert helpers["confirmed_registered"] is True
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["workflow"]["scope"] == "wallet_and_hotkey"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_validation_help_without_payloads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_validation_help(5)
        assert helpers["validation_status"] == "missing"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 5"
        assert helpers["workflow"]["primary_register"] == "agcli subnet register-neuron --netuid 5"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_validation_help_treats_blank_payload_as_missing_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_validation_help(5, subnet="  ", registration_cost={"tao": 1.0})
        assert helpers["validated_reads"] == ["registration_cost"]
        assert helpers["missing_reads"] == ["subnet", "health"]

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_snapshot_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.registration_snapshot_text(5, subnet={"netuid": 5}, health={"ok": True})
        assert text == (
            "Registration on subnet 5 has preflight reads subnet, health; still missing registration_cost. "
            "Next: agcli subnet cost --netuid 5"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_validation_help_rejects_boolean_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be an integer"):
            c.subnet.registration_validation_help(True)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_snapshot_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.subnet.registration_snapshot_help(5, hotkey="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_validation_help_embeds_workflow_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_validation_help(5, wallet="cold", registration_proof={"uid": 4})
        assert helpers["workflow"]["scope"] == "wallet"
        assert helpers["workflow"]["summary"] == "Check subnet 5 readiness, then register from wallet cold."
        assert helpers["confirmed_registered"] is True

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_validation_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.registration_validation_text(5, subnet={"netuid": 5})
        assert text == "Registration on subnet 5 has preflight reads subnet; still missing registration_cost, health."

    @patch("taocli.runner.subprocess.run")
    def test_subnet_registration_snapshot_help_preserves_workflow_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.registration_snapshot_help(5, hotkey="miner", registration_cost={"tao": 1.0})
        assert helpers["workflow"]["post_registration_check"] == "agcli subnet metagraph --netuid 5 --full"
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 5"

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
    def test_serve_axon_validation_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(
            8,
            "127.0.0.1",
            8080,
            registration_check={"netuid": 8},
            probe={"ok": True},
        )
        assert helpers["scope"] == "subnet"
        assert helpers["validated_reads"] == ["registration_check", "probe"]
        assert helpers["missing_reads"] == ["axon"]
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli view axon --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_snapshot_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_snapshot_help(8, "127.0.0.1", 8080, hotkey="miner", axon={"uid": 1})
        assert helpers["workflow"]["scope"] == "hotkey"
        assert helpers["validation_status"] == "partial"
        assert helpers["validated_reads"] == ["axon"]
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_without_payloads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(8, "127.0.0.1", 8080)
        assert helpers["validation_status"] == "missing"
        assert helpers["missing_reads"] == ["registration_check", "axon", "probe"]

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_treats_blank_payload_as_missing_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(8, "127.0.0.1", 8080, registration_check="  ", axon={"uid": 1})
        assert helpers["validated_reads"] == ["axon"]
        assert helpers["missing_reads"] == ["registration_check", "probe"]

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_embeds_workflow_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(
            8,
            "127.0.0.1",
            8080,
            wallet="cold",
            registration_check={"netuid": 8},
        )
        assert helpers["workflow"]["serve_axon"] == (
            "agcli --wallet cold serve axon --netuid 8 --ip 127.0.0.1 --port 8080"
        )
        assert helpers["workflow"]["scope"] == "wallet"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_snapshot_help_preserves_workflow_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_snapshot_help(8, "127.0.0.1", 8080, prometheus_port=9090, probe={"ok": True})
        assert helpers["workflow"]["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090"
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_rejects_boolean_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be an integer"):
            c.serve.axon_validation_help(True, "127.0.0.1", 8080)

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_snapshot_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            c.serve.axon_snapshot_help(8, "127.0.0.1", 8080, hotkey="   ")

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
        assert helpers["netuid"] == 6
        assert helpers["scope"] == "subnet_admin"
        assert helpers["show"] == "agcli subnet show --netuid 6"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 6 --param list"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["raw"] == "agcli admin raw --call <sudo-call>"
        assert helpers["sudo_note"] == (
            "Use admin list to discover the exact set-* command for root-only knobs, then "
            "run it with --sudo-key. Subnet-owner knobs can usually use subnet set-param instead."
        )
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]
        assert helpers["primary_read"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["mutation_check"] == "agcli admin list"
        assert "set" not in helpers
        assert helpers["summary"]

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
    def test_subnet_hyperparameter_validation_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, subnet={"netuid": 6}, hyperparams={"tempo": 360})
        assert helpers["validated_reads"] == ["subnet", "hyperparams"]
        assert helpers["missing_reads"] == ["param_list"]
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_alias_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_snapshot_help(
            6,
            wallet="owner",
            param="tempo",
            value="360",
            subnet={"netuid": 6},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == (
            "agcli --wallet owner subnet set-param --netuid 6 --param tempo --value 360"
        )
        assert helpers["workflow"] == c.subnet.hyperparameter_workflow_help(
            6, wallet="owner", param="tempo", value="360"
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(
            6,
            command="set-tempo",
            value_flag="--tempo",
            value=12,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["scope"] == "subnet_admin"
        assert helpers["validation_status"] == "ready_to_mutate"
        assert helpers["next_validation_step"] == "agcli admin set-tempo --netuid 6 --tempo 12"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_text_alias_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameters_snapshot_text(
            6,
            command="set-network-registration",
            value_flag="--allowed",
            value=False,
            show={"netuid": 6},
            get={"allowed": False},
            owner_param_list=["network_registration_allowed"],
            admin_list=["set-network-registration"],
        )
        assert text.endswith("Next: agcli admin set-network-registration --netuid 6 --allowed false")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_rejects_empty_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="command cannot be empty"):
            c.admin.hyperparameter_validation_help(6, command="   ")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_snapshot_text_rejects_empty_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value cannot be empty"):
            c.subnet.hyperparameters_snapshot_text(6, param="tempo", value="   ")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_without_reads_uses_show_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(6, command="set-tempo", value_flag="--tempo")
        assert helpers["validation_status"] == "missing"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_validation_text_alias_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.hyperparameters_validation_text(6, param_list=["tempo"])
        assert text == "Hyperparameter reads for subnet 6 have param_list; still missing subnet, hyperparams."

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_preserves_workflow_copy_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(6)
        helpers["workflow"]["show"] = "mutated"
        assert c.admin.hyperparameter_workflow_help(6)["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_preserves_workflow_copy_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(6)
        helpers["workflow"]["show"] = "mutated"
        assert c.subnet.hyperparameter_workflow_help(6)["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_recommended_order_is_copy_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6)
        helpers["recommended_order"].append("oops")
        assert c.admin.hyperparameter_workflow_help(6)["recommended_order"] == [
            "show",
            "get",
            "owner_param_list",
            "admin_list",
            "set",
        ]

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_validation_help_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.subnet.hyperparameters_validation_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameters_snapshot_help_alias_rejects_invalid_netuid_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.admin.hyperparameters_snapshot_help(0)

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_text_ready_to_mutate_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameter_validation_text(
            6,
            command="set-tempo",
            value_flag="--tempo",
            value=12,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text == "Admin hyperparameter reads for subnet 6 are ready and the mutation command is prepared."

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_text_ready_with_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.hyperparameter_snapshot_text(
            6,
            wallet="owner",
            param="tempo",
            value="360",
            subnet={"netuid": 6},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text.endswith("Next: agcli --wallet owner subnet set-param --netuid 6 --param tempo --value 360")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_without_command_points_to_raw_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_without_reads_points_to_show_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, param="tempo")
        assert helpers["validation_status"] == "missing"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_ready_without_value_points_to_param_command_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(
            6,
            wallet="owner",
            param="tempo",
            subnet={"netuid": 6},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli --wallet owner subnet set-param --netuid 6 --param tempo"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameters_validation_text_alias_partial_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameters_validation_text(6, admin_list=["set-tempo"])
        assert (
            text
            == "Admin hyperparameter reads for subnet 6 have admin_list; still missing show, get, owner_param_list."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_alias_matches_direct_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.subnet.hyperparameters_snapshot_help(6, wallet="owner") == c.subnet.hyperparameter_snapshot_help(
            6, wallet="owner"
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_alias_matches_direct_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.admin.hyperparameters_validation_help(
            6, admin_list=["set-tempo"]
        ) == c.admin.hyperparameter_validation_help(6, admin_list=["set-tempo"])

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_with_value_without_param_keeps_base_set_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(
            6,
            wallet="owner",
            value="360",
            subnet={"netuid": 6},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6"
        assert helpers["next_validation_step"] == "agcli --wallet owner subnet set-param --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_text_with_sudo_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameter_snapshot_text(
            6,
            command="set-tempo",
            value_flag="--tempo",
            value=12,
            sudo_key="//Alice",
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text.endswith("Next: agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_only_param_list_points_to_show_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, param_list=["tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_with_only_admin_list_points_to_show_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(6, admin_list=["set-tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_show_get_admin_points_to_owner_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6, show={"netuid": 6}, get={"tempo": 12}, admin_list=["set-tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_text_missing_everything_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.hyperparameter_validation_text(6)
        assert text == "Hyperparameter reads for subnet 6 still need subnet, hyperparams, and param_list output."

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_text_missing_everything_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameter_validation_text(6)
        assert text == (
            "Admin hyperparameter reads for subnet 6 still need show, get, owner_param_list, and admin_list output."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_includes_workflow_commands_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(6, wallet="owner", param="tempo")
        assert helpers["show"] == "agcli subnet show --netuid 6"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 6 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 6 --param tempo"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_includes_summary_fields_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(6)
        assert helpers["summary"]
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]
        assert helpers["primary_read"] == "agcli subnet hyperparams --netuid 6"
        assert helpers["mutation_check"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_with_trimmed_inputs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(6, wallet=" owner ", param=" tempo ", value=" 360 ")
        assert helpers["workflow"]["wallet"] == "owner"
        assert helpers["workflow"]["param"] == "tempo"
        assert helpers["workflow"]["value"] == "360"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_trimmed_inputs_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6,
            command=" set-tempo ",
            value_flag=" --tempo ",
            value=12,
            sudo_key=" //Alice ",
        )
        assert helpers["workflow"]["command"] == "set-tempo"
        assert helpers["workflow"]["value_flag"] == "--tempo"
        assert helpers["workflow"]["sudo_key"] == "//Alice"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_workflow_alias_still_matches_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.subnet.hyperparameters_workflow_help(
            6, wallet="owner", param="tempo", value="360"
        ) == c.subnet.hyperparameter_workflow_help(6, wallet="owner", param="tempo", value="360")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_text_alias_missing_everything_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameters_snapshot_text(6)
        assert text == (
            "Admin hyperparameter reads for subnet 6 still need show, get, owner_param_list, and admin_list output. "
            "Next: agcli subnet show --netuid 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_snapshot_text_alias_missing_everything_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.hyperparameters_snapshot_text(6)
        assert text == (
            "Hyperparameter reads for subnet 6 still need subnet, hyperparams, and param_list output. "
            "Next: agcli subnet show --netuid 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_summary_for_partial_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(6, show={"netuid": 6}, admin_list=["set-tempo"])
        assert helpers["validation_summary"] == (
            "Admin hyperparameter reads for subnet 6 have show, admin_list; still missing get, owner_param_list."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_summary_for_partial_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, subnet={"netuid": 6})
        assert helpers["validation_summary"] == (
            "Hyperparameter reads for subnet 6 have subnet; still missing hyperparams, param_list."
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_summary_for_ready_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(
            6,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_summary"] == (
            "Admin hyperparameter reads for subnet 6 are ready: show, get, "
            "owner_param_list, and admin_list output are present."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_summary_for_ready_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(
            6,
            subnet={"netuid": 6},
            hyperparams={"tempo": 12},
            param_list=["tempo"],
        )
        assert helpers["validation_summary"] == (
            "Hyperparameter reads for subnet 6 are ready: subnet, hyperparams, and param_list output are present."
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_summary_for_ready_to_mutate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(
            6,
            command="set-tempo",
            value_flag="--tempo",
            value=12,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert (
            helpers["validation_summary"]
            == "Admin hyperparameter reads for subnet 6 are ready and the mutation command is prepared."
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameters_validation_help_alias_with_string_payloads_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameters_validation_help(
            6, show="show", get="get", owner_param_list="owner", admin_list="admin"
        )
        assert helpers["validation_status"] == "ready"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameters_validation_help_alias_with_string_payloads_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameters_validation_help(6, subnet="show", hyperparams="get", param_list="list")
        assert helpers["validation_status"] == "ready"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_empty_string_admin_list_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6, show={"netuid": 6}, get={"tempo": 12}, owner_param_list=["tempo"], admin_list=""
        )
        assert helpers["missing_reads"] == ["admin_list"]
        assert helpers["next_validation_step"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_whitespace_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(
            6, subnet={"netuid": 6}, hyperparams={"tempo": 12}, param_list="   "
        )
        assert helpers["missing_reads"] == ["param_list"]
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_bool_value_ready_to_mutate_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6,
            command="set-commit-reveal",
            value_flag="--enabled",
            value=True,
            show={"netuid": 6},
            get={"enabled": True},
            owner_param_list=["commit_reveal"],
            admin_list=["set-commit-reveal"],
        )
        assert helpers["next_validation_step"] == "agcli admin set-commit-reveal --netuid 6 --enabled true"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_with_ready_reads_no_param_uses_base_set_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(
            6,
            subnet={"netuid": 6},
            hyperparams={"tempo": 12},
            param_list=["tempo"],
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_with_only_show_points_to_get_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(6, show={"netuid": 6})
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_only_subnet_points_to_get_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, subnet={"netuid": 6})
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_text_with_command_only_no_reads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameter_snapshot_text(6, command="set-tempo", value_flag="--tempo")
        assert text == (
            "Admin hyperparameter reads for subnet 6 still need show, get, owner_param_list, and admin_list output. "
            "Next: agcli subnet show --netuid 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_text_with_partial_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.hyperparameter_snapshot_text(6, wallet="owner", subnet={"netuid": 6})
        assert text == (
            "Hyperparameter reads for subnet 6 have subnet; still missing hyperparams, param_list. "
            "Next: agcli subnet hyperparams --netuid 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_with_only_admin_list_points_to_show_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(6, admin_list=["set-tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_only_param_list_points_to_show_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, param_list=["tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_with_show_get_owner_points_to_admin_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(
            6, show={"netuid": 6}, get={"tempo": 12}, owner_param_list=["tempo"]
        )
        assert helpers["next_validation_step"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_subnet_get_points_to_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, subnet={"netuid": 6}, hyperparams={"tempo": 12})
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_with_string_payloads_and_no_command_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(
            6, show="show", get="get", owner_param_list="owner", admin_list="admin"
        )
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_string_payloads_and_param_value_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(
            6,
            param="tempo",
            value="360",
            subnet="show",
            hyperparams="get",
            param_list="list",
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_alias_matches_direct_again_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.admin.hyperparameters_validation_help(6, show={"netuid": 6}) == c.admin.hyperparameter_validation_help(
            6, show={"netuid": 6}
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_alias_matches_direct_again_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.subnet.hyperparameters_validation_help(
            6, subnet={"netuid": 6}
        ) == c.subnet.hyperparameter_validation_help(6, subnet={"netuid": 6})

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_rejects_sudo_without_command_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="sudo_key requires command"):
            c.admin.hyperparameter_snapshot_help(6, sudo_key="//Alice")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.subnet.hyperparameter_snapshot_help(6, wallet="")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_rejects_value_without_command_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            c.admin.hyperparameter_validation_help(6, value=12)

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_rejects_empty_param_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="param cannot be empty"):
            c.subnet.hyperparameter_validation_help(6, param="")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_rejects_value_flag_without_command_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value_flag requires command"):
            c.admin.hyperparameter_snapshot_help(6, value_flag="--tempo")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_rejects_empty_value_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="value cannot be empty"):
            c.subnet.hyperparameter_snapshot_help(6, param="tempo", value="")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_ready_reads_and_bool_value_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6,
            command="set-network-registration",
            value_flag="--allowed",
            value=False,
            show={"netuid": 6},
            get={"allowed": False},
            owner_param_list=["network_registration_allowed"],
            admin_list=["set-network-registration"],
        )
        assert helpers["next_validation_step"] == "agcli admin set-network-registration --netuid 6 --allowed false"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_with_ready_reads_and_value_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(
            6,
            param="tempo",
            value="360",
            subnet={"netuid": 6},
            hyperparams={"tempo": 12},
            param_list=["tempo"],
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_summary_mentions_root_only_knobs_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert "root-only knobs" in c.admin.hyperparameter_workflow_help(6)["summary"]

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_truthy_scalars_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, subnet=1, hyperparams=2, param_list=3)
        assert helpers["validation_status"] == "ready"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_with_truthy_scalars_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(6, show=1, get=2, owner_param_list=3, admin_list=4)
        assert helpers["validation_status"] == "ready"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_ready_no_param_uses_base_set_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(
            6,
            subnet={"netuid": 6},
            hyperparams={"tempo": 12},
            param_list=["tempo"],
        )
        assert helpers["set"] == "agcli subnet set-param --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_ready_to_mutate_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6,
            command="set-tempo",
            value_flag="--tempo",
            value=12,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_status"] == "ready_to_mutate"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_ready_without_value_summary_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.subnet.hyperparameter_validation_text(
            6,
            param="tempo",
            subnet={"netuid": 6},
            hyperparams={"tempo": 12},
            param_list=["tempo"],
        )
        assert (
            text
            == "Hyperparameter reads for subnet 6 are ready: subnet, hyperparams, and param_list output are present."
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_ready_without_command_summary_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameter_validation_text(
            6,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text == (
            "Admin hyperparameter reads for subnet 6 are ready: show, get, "
            "owner_param_list, and admin_list output are present."
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_workflow_copy_via_client_surface_again(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(6)
        helpers["workflow"]["show"] = "changed"
        assert c.subnet.hyperparameter_workflow_help(6)["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_workflow_copy_via_client_surface_again(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(6)
        helpers["workflow"]["show"] = "changed"
        assert c.admin.hyperparameter_workflow_help(6)["show"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_alias_matches_direct_again_again_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.subnet.hyperparameters_validation_help(
            6, param_list=["tempo"]
        ) == c.subnet.hyperparameter_validation_help(6, param_list=["tempo"])

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_text_ready_to_mutate_with_sudo_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.admin.hyperparameter_snapshot_text(
            6,
            command="set-tempo",
            value_flag="--tempo",
            value=12,
            sudo_key="//Alice",
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text.endswith("Next: agcli admin set-tempo --netuid 6 --tempo 12 --sudo-key //Alice")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_text_missing_everything_via_client_surface_duplicate(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.subnet.hyperparameter_snapshot_text(6) == (
            "Hyperparameter reads for subnet 6 still need subnet, hyperparams, and param_list output. "
            "Next: agcli subnet show --netuid 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_text_missing_everything_via_client_surface_duplicate(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert c.admin.hyperparameter_snapshot_text(6) == (
            "Admin hyperparameter reads for subnet 6 still need show, get, owner_param_list, and admin_list output. "
            "Next: agcli subnet show --netuid 6"
        )

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_show_get_param_list_ready_points_to_set_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(
            6, subnet={"netuid": 6}, hyperparams={"tempo": 12}, param_list=["tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_with_show_get_owner_admin_ready_points_to_raw_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(
            6,
            show={"netuid": 6},
            get={"tempo": 12},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_with_only_hyperparams_and_param_list_points_to_show_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(6, hyperparams={"tempo": 12}, param_list=["tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_only_get_and_admin_list_points_to_show_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(6, get={"tempo": 12}, admin_list=["set-tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_with_subnet_and_get_points_to_param_list_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(6, subnet={"netuid": 6}, hyperparams={"tempo": 12})
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param list"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_show_get_owner_points_to_admin_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6, show={"netuid": 6}, get={"tempo": 12}, owner_param_list=["tempo"]
        )
        assert helpers["next_validation_step"] == "agcli admin list"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_with_value_without_param_keeps_base_set_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(
            6,
            value="360",
            subnet={"netuid": 6},
            hyperparams={"tempo": 12},
            param_list=["tempo"],
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_snapshot_help_with_string_payloads_no_command_points_to_raw_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_snapshot_help(
            6, show="show", get="get", owner_param_list="owner", admin_list="admin"
        )
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_with_string_payloads_param_value_points_to_set_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(
            6,
            param="tempo",
            value="360",
            subnet="show",
            hyperparams="get",
            param_list="list",
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 6 --param tempo --value 360"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_rejects_empty_sudo_key_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="sudo_key cannot be empty"):
            c.admin.hyperparameter_validation_help(6, command="set-tempo", value_flag="--tempo", sudo_key="")

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_rejects_empty_wallet_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            c.subnet.hyperparameter_validation_help(6, wallet="")

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_summary_fields_present_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6)
        assert helpers["scope"] == "subnet_admin"
        assert helpers["summary"]
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]
        assert helpers["primary_read"] == helpers["get"]
        assert helpers["mutation_check"] == helpers["admin_list"]

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_validation_help_workflow_contains_wallet_note_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_validation_help(6, wallet="owner")
        assert helpers["workflow"]["wallet_selection_note"]
        assert helpers["workflow"]["wallet"] == "owner"

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_validation_help_workflow_contains_raw_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_validation_help(6)
        assert helpers["workflow"]["raw"] == "agcli admin raw --call <sudo-call>"

    @patch("taocli.runner.subprocess.run")
    def test_subnet_hyperparameter_snapshot_help_workflow_embeds_wallet_note_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.subnet.hyperparameter_snapshot_help(6, wallet="owner")
        assert helpers["workflow"]["wallet_selection_note"]
        assert helpers["wallet_selection_note"]

    @patch("taocli.runner.subprocess.run")
    def test_admin_hyperparameter_workflow_help_without_command_has_no_set_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.admin.hyperparameter_workflow_help(6)
        assert "set" not in helpers

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
    def test_view_chain_data_validation_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_validation_help(3, uid=9, metagraph={"uids": [9]}, axon=[{"uid": 9}])
        assert helpers["scope"] == "uid"
        assert helpers["validated_reads"] == ["metagraph", "axon"]
        assert helpers["missing_reads"] == ["probe"]
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet probe --netuid 3 --uids 9"
        assert helpers["workflow"]["primary_read"] == "agcli view neuron --netuid 3 --uid 9"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_snapshot_help(3, hotkey_address="5F...", metagraph={"uids": [1]})
        assert helpers["scope"] == "hotkey"
        assert helpers["validation_status"] == "partial"
        assert helpers["validation_summary"] == "Validated metagraph output for SN3; still missing axon, probe."
        assert helpers["next_validation_step"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["endpoint_check"] == "agcli view axon --netuid 3 --hotkey-address 5F..."

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert (
            c.view.chain_data_snapshot_text(3, metagraph={"uids": [1]}, axon={"uid": 1}, probe={"ok": True})
            == "Metagraph, axon, and probe output are all present for SN3. Next: agcli subnet hyperparams --netuid 3"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert (
            c.view.chain_data_validation_text(3, hotkey_address="5F...", metagraph={"uids": [1]})
            == "Validated metagraph output for SN3; still missing axon, probe."
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_preserves_filter_note_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_snapshot_help(3, uid=9, hotkey_address="5F...", metagraph={"uids": [9]})
        assert helpers["filter_note"] == (
            "view axon is filtered by hotkey_address while subnet probe stays filtered by uid, "
            "because probe only accepts UID selectors."
        )
        assert helpers["next_validation_step"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["reachability_check"] == "agcli subnet probe --netuid 3 --uids 9"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_help_rejects_invalid_uid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="uid must be greater than or equal to 0"):
            c.view.chain_data_validation_help(3, uid=-1)

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_rejects_empty_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey_address cannot be empty"):
            c.view.chain_data_snapshot_help(3, hotkey_address="   ")

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_text_rejects_invalid_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            c.view.chain_data_snapshot_text(0)

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_text_rejects_invalid_hotkey_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="hotkey_address cannot be empty"):
            c.view.chain_data_validation_text(3, hotkey_address="   ")

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_help_treats_blank_string_payload_as_missing(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_validation_help(3, metagraph="  ", probe={"ok": True})
        assert helpers["validated_reads"] == ["probe"]
        assert helpers["missing_reads"] == ["metagraph", "axon"]
        assert helpers["next_validation_step"] == "agcli view metagraph --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_with_complete_payloads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_snapshot_help(3, metagraph={"uids": [1]}, axon={"uid": 1}, probe={"ok": True})
        assert helpers["validation_status"] == "ready"
        assert helpers["missing_reads"] == []
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 3"
        assert helpers["validation_summary"] == "Metagraph, axon, and probe output are all present for SN3."

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_help_without_payloads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_validation_help(3)
        assert helpers["validation_status"] == "missing"
        assert helpers["validated_reads"] == []
        assert helpers["missing_reads"] == ["metagraph", "axon", "probe"]
        assert helpers["next_validation_step"] == "agcli view metagraph --netuid 3"
        assert helpers["validation_summary"] == "No metagraph, axon, or probe output has been supplied yet for SN3."

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_preserves_workflow_aliases_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_snapshot_help(3, metagraph={"uids": [1]})
        assert helpers["subnet"] == "agcli subnet show --netuid 3"
        assert helpers["metagraph"] == "agcli view metagraph --netuid 3"
        assert helpers["endpoints"] == "agcli view axon --netuid 3"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 3"
        assert helpers["workflow"]["summary"] == helpers["summary"]
        assert helpers["workflow"]["recommended_order"] == helpers["recommended_order"]

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_help_embeds_workflow_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_validation_help(3, hotkey_address="5F...", metagraph={"uids": [1]})
        assert helpers["workflow"]["endpoint_check"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["workflow"]["reachability_check"] == "agcli subnet probe --netuid 3"
        assert helpers["workflow"]["scope"] == "hotkey"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_text_uses_missing_probe_step_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        expected = (
            "Validated metagraph, axon output for SN3; still missing probe. "
            "Next: agcli subnet probe --netuid 3 --uids 4"
        )
        assert c.view.chain_data_snapshot_text(3, uid=4, metagraph={"uids": [4]}, axon={"uid": 4}) == expected

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_text_with_complete_payloads_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert (
            c.view.chain_data_validation_text(3, metagraph={"uids": [1]}, axon={"uid": 1}, probe={"ok": True})
            == "Metagraph, axon, and probe output are all present for SN3."
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_embeds_validation_lists_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_snapshot_help(3, probe={"ok": True})
        assert helpers["validated_reads"] == ["probe"]
        assert helpers["missing_reads"] == ["metagraph", "axon"]
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli view metagraph --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_keeps_validation_and_workflow_summary_distinct(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_snapshot_help(3, probe={"ok": True})
        assert helpers["summary"] == (
            "Start with subnet and metagraph reads for SN3, then inspect axon and probe output "
            "to confirm live endpoints."
        )
        assert helpers["validation_summary"] == "Validated probe output for SN3; still missing metagraph, axon."

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_help_with_complete_payloads_keeps_workflow(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_validation_help(3, metagraph={"uids": [1]}, axon={"uid": 1}, probe={"ok": True})
        assert helpers["validation_status"] == "ready"
        assert helpers["workflow"]["hyperparams"] == "agcli subnet hyperparams --netuid 3"
        assert helpers["workflow"]["primary_read"] == "agcli view metagraph --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_help_with_uid_and_hotkey_complete_payloads(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_snapshot_help(
            3,
            uid=9,
            hotkey_address="5F...",
            metagraph={"uids": [9]},
            axon={"uid": 9},
            probe={"ok": True},
        )
        assert helpers["scope"] == "uid+hotkey"
        assert helpers["validation_status"] == "ready"
        assert helpers["endpoint_check"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["reachability_check"] == "agcli subnet probe --netuid 3 --uids 9"
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_help_with_only_axon_payload_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.view.chain_data_validation_help(3, hotkey_address="5F...", axon={"uid": 1})
        assert helpers["validated_reads"] == ["axon"]
        assert helpers["missing_reads"] == ["metagraph", "probe"]
        assert helpers["next_validation_step"] == "agcli view metagraph --netuid 3"

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_snapshot_text_with_only_probe_payload_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        assert (
            c.view.chain_data_snapshot_text(3, probe={"ok": True})
            == "Validated probe output for SN3; still missing metagraph, axon. Next: agcli view metagraph --netuid 3"
        )

    @patch("taocli.runner.subprocess.run")
    def test_view_chain_data_validation_help_rejects_boolean_netuid_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        with pytest.raises(ValueError, match="netuid must be an integer"):
            c.view.chain_data_validation_help(True)

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
        assert helpers["scope"] == "uid+hotkey"
        assert helpers["uid"] == 4
        assert helpers["hotkey_address"] == "5F..."
        assert helpers["summary"] == (
            "Start with the SN3 metagraph, then inspect UID 4 and hotkey 5F...; "
            "axon is filtered by hotkey while probe stays UID-scoped."
        )
        assert helpers["filter_note"] == (
            "view axon is filtered by hotkey_address while subnet probe stays filtered by uid, "
            "because probe only accepts UID selectors."
        )
        assert helpers["primary_read"] == "agcli view neuron --netuid 3 --uid 4"
        assert helpers["endpoint_check"] == "agcli view axon --netuid 3 --hotkey-address 5F..."
        assert helpers["reachability_check"] == "agcli subnet probe --netuid 3 --uids 4"
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
        assert helpers["scope"] == "subnet"
        assert helpers["primary_serve"] == helpers["serve_axon"]
        assert helpers["endpoint_check"] == helpers["inspect_axon"]
        assert helpers["reachability_check"] == helpers["probe"]
        assert helpers["recommended_order"] == [
            "registration_check",
            "serve_axon",
            "endpoint_check",
            "reachability_check",
            "weights_status",
        ]
        assert helpers["summary"] == (
            "Serve SN8 127.0.0.1:8080 on subnet 8, then verify registration, endpoint metadata, and reachability."
        )

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_snapshot_help_keeps_final_complete_shape_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_snapshot_help(
            8,
            "127.0.0.1",
            8080,
            protocol=4,
            version=2,
            cert="/tmp/cert.pem",
            prometheus_port=9090,
            registration_check={"netuid": 8},
            axon={"ip": "127.0.0.1"},
            probe={"ok": True},
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["validated_reads"] == ["registration_check", "axon", "probe"]
        assert helpers["missing_reads"] == []
        assert helpers["next_validation_step"] == "agcli weights status --netuid 8"
        assert helpers["workflow"]["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem --protocol 4 --version 2"
        )
        assert helpers["workflow"]["serve_prometheus"] == (
            "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 2"
        )
        assert helpers["workflow"]["summary"] == (
            "Serve SN8 127.0.0.1:8080 on subnet 8, then verify registration, endpoint metadata, and reachability."
        )

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.serve.axon_validation_text(8, "127.0.0.1", 8080, registration_check={"netuid": 8})
        assert text == "Serve verification on subnet 8 has reads registration_check; still missing axon, probe."

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_snapshot_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        text = c.serve.axon_snapshot_text(8, "127.0.0.1", 8080, probe={"ok": True})
        assert text == (
            "Serve verification on subnet 8 has reads probe; still missing registration_check, axon. "
            "Next: agcli subnet show --netuid 8"
        )

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_with_complete_payloads_keeps_workflow_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(
            8,
            "127.0.0.1",
            8080,
            wallet="cold",
            hotkey="miner",
            registration_check={"netuid": 8},
            axon={"uid": 1},
            probe={"ok": True},
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["workflow"]["scope"] == "wallet_and_hotkey"
        assert helpers["workflow"]["summary"] == (
            "Serve SN8 127.0.0.1:8080 on subnet 8 for hotkey miner from wallet cold, then verify "
            "registration, endpoint metadata, and reachability."
        )
        assert helpers["workflow"]["primary_serve"] == (
            "agcli --wallet cold --hotkey-name miner serve axon --netuid 8 --ip 127.0.0.1 --port 8080"
        )
        assert helpers["workflow"]["endpoint_check"] == "agcli view axon --netuid 8"
        assert helpers["workflow"]["reachability_check"] == "agcli subnet probe --netuid 8"
        assert helpers["workflow"]["recommended_order"] == [
            "registration_check",
            "serve_axon",
            "endpoint_check",
            "reachability_check",
            "weights_status",
        ]
        assert helpers["next_validation_step"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 8"

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_with_hotkey_scope_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(8, "127.0.0.1", 8080, hotkey="miner", axon={"uid": 1})
        assert helpers["scope"] == "hotkey"
        assert helpers["workflow"]["scope"] == "hotkey"
        assert helpers["workflow"]["summary"] == (
            "Serve SN8 127.0.0.1:8080 on subnet 8 for hotkey miner, then verify registration, "
            "endpoint metadata, and reachability."
        )

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_with_wallet_scope_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(8, "127.0.0.1", 8080, wallet="cold", registration_check={"netuid": 8})
        assert helpers["scope"] == "wallet"
        assert helpers["workflow"]["summary"] == (
            "Serve SN8 127.0.0.1:8080 on subnet 8 from wallet cold, then verify registration, "
            "endpoint metadata, and reachability."
        )

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_snapshot_help_preserves_summary_vs_validation_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_snapshot_help(8, "127.0.0.1", 8080, probe={"ok": True})
        assert helpers["summary"] == (
            "Serve SN8 127.0.0.1:8080 on subnet 8, then verify registration, endpoint metadata, and reachability."
        )
        assert helpers["validation_summary"] == (
            "Serve verification on subnet 8 has reads probe; still missing registration_check, axon."
        )
        assert helpers["workflow"]["summary"] == helpers["summary"]

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_with_prometheus_and_tls_workflow_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(
            8,
            "127.0.0.1",
            8080,
            cert="/tmp/cert.pem",
            prometheus_port=9090,
            registration_check={"netuid": 8},
        )
        assert helpers["workflow"]["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090"
        assert helpers["workflow"]["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem"
        )
        assert helpers["missing_reads"] == ["axon", "probe"]

    @patch("taocli.runner.subprocess.run")
    def test_serve_axon_validation_help_complete_payloads_next_step_uses_prefixed_weights_status_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.serve.axon_validation_help(
            8,
            "127.0.0.1",
            8080,
            wallet="cold",
            hotkey="miner",
            registration_check={"netuid": 8},
            axon={"uid": 1},
            probe={"ok": True},
        )
        assert helpers["next_validation_step"] == ("agcli --wallet cold --hotkey-name miner weights status --netuid 8")

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
        assert flow["normalized_weights"] == workflow["normalized_weights"]
        assert flow["commit"] == workflow["commit"]
        assert flow["reveal"] == workflow["reveal"]
        assert flow["status"] == workflow["status"]
        assert flow["inspect_localnet_scaffold_command"] == c.weights.inspect_localnet_scaffold_help()
        assert flow["inspect_doctor_command"] == c.weights.inspect_doctor_help()
        assert flow["local_validation_tip"] == c.weights._local_validation_tip()

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
            "inspect_localnet_scaffold_command": "agcli localnet scaffold",
            "inspect_doctor_command": "agcli doctor",
            "local_validation_tip": c.weights._local_validation_tip(),
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
            "inspect_localnet_scaffold_command": "agcli localnet scaffold",
            "inspect_doctor_command": "agcli doctor",
            "local_validation_tip": c.weights._local_validation_tip(),
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
    def test_weights_troubleshoot_mechanism_help_preserves_raw_status_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        status_text = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   125
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  Pending commits: 1

  [1] Hash:    0x1212
      Commit:  block 100
      Reveal:  blocks 120..130
      Status:  READY TO REVEAL (5 blocks remaining)
"""
        helpers = c.weights.troubleshoot_mechanism_help(1, 4, "RevealTooEarly", status=status_text)
        assert helpers["raw_status"] == status_text.strip()
        assert helpers["status_summary"]["next_action"] == "REVEAL"

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
    def test_weights_troubleshoot_timelocked_help_preserves_raw_status_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        status_text = """Weight Commit Status — SN9
  Hotkey:          5GrwvaEF5zXb26Fz9rcQpDWS57CtE
  Current block:   140
  Commit-reveal:   ENABLED
  Reveal period:   4 epochs

  Pending commits: 1

  [1] Hash:    0x5656
      Commit:  block 100
      Reveal:  blocks 110..130
      Status:  EXPIRED
"""
        helpers = c.weights.troubleshoot_timelocked_help(7, "ExpiredWeightCommit", status=status_text)
        assert helpers["raw_status"] == status_text.strip()
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"

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
        assert helpers["error"] == "IncorrectCommitRevealVersion"
        assert helpers["likely_cause"] == "The subnet expects a different version_key than the one provided."
        assert helpers["next_step"] == "Inspect the subnet hyperparameters, then retry with the matching version_key."
        assert helpers["status"] == "agcli weights status --netuid 1"
        assert helpers["normalized_weights"] == "0:100"
        assert helpers["set"] == "agcli weights set --netuid 1 --weights 0:100 --version-key 7"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7"
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100 --version-key 7"
        assert helpers["inspect_version_key_command"] == "agcli subnet hyperparams --netuid 1"
        assert helpers["version_key_recovery_note"] == (
            "Run inspect_version_key_command to inspect the subnet hyperparameters and find the expected version_key before retrying."
        )
        assert helpers["inspect_localnet_scaffold_command"] == "agcli localnet scaffold"
        assert helpers["inspect_doctor_command"] == "agcli doctor"
        assert helpers["local_validation_tip"] == c.weights._local_validation_tip()
        assert helpers["adjacent_workflows_note"] == c.weights._adjacent_workflows_note()
        assert helpers["adjacent_recovery_note"] == c.weights._adjacent_recovery_note()
        assert helpers["inspect_monitor_command"] == "agcli subnet monitor --netuid 1 --json"
        assert helpers["inspect_health_command"] == "agcli subnet health --netuid 1"
        assert helpers["inspect_wallet_current_command"] == "agcli wallet show"
        assert len(helpers) >= 60

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
        assert summary["status"] == "agcli weights status --netuid 5"
        assert summary["current_block"] == 125
        assert summary["commit_reveal_enabled"] is True
        assert summary["reveal_period_epochs"] == 3
        assert summary["pending_commits"] == 1
        assert summary["pending_statuses"] == ["READY TO REVEAL (5 blocks remaining)"]
        assert summary["next_action"] == "REVEAL"
        assert summary["recommended_action"] == "REVEAL"
        assert summary["recommended_command"] == "agcli weights status --netuid 5"
        assert summary["blocks_until_action"] == 5
        assert summary["pending_commit"] == {
            "index": 1,
            "status": "READY TO REVEAL (5 blocks remaining)",
            "commit_block": 100,
            "first_reveal": 120,
            "last_reveal": 130,
            "blocks_until_action": 5,
        }
        assert summary["reveal_window"] == {"first_block": 120, "last_block": 130}
        assert summary["next_step"] == (
            "Recover the original weights and salt, then rerun recommended_command to build the reveal command."
        )
        assert summary["reason"] == (
            "A pending commit is ready to reveal now; provide the original weights and salt "
            "to build the reveal command."
        )
        assert summary["commit_windows"] == [summary["pending_commit"]]

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
            "next_step": "Run recommended_command to start a fresh commit-reveal weights update.",
            "local_validation_tip": c.weights._local_validation_tip(),
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_action_help_preserves_next_step_via_client_surface(self, mock_run) -> None:
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
        assert helpers["next_step"] == "Run recommended_command to start a fresh commit-reveal weights update."
        assert helpers["reason"] == "No commit is pending and this subnet uses commit-reveal."
        assert helpers["recommended_command"] == (
            "agcli weights commit-reveal --netuid 3 --weights 0:100 --version-key 9 --wait"
        )
        assert helpers["normalized_weights"] == "0:100"

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_action_help_preserves_raw_status_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.next_action_help(5, READY_STATUS_TEXT, "0:100", salt="abc", version_key=7)

        assert helpers["raw_status"] == READY_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "REVEAL"

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_mechanism_action_help_preserves_raw_status_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.next_mechanism_action_help(5, 4, NO_PENDING_STATUS_TEXT, "0:100", hash_value="11" * 32)

        assert helpers["raw_status"] == NO_PENDING_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_timelocked_action_help_preserves_raw_status_text_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.next_timelocked_action_help(9, EXPIRED_STATUS_TEXT, "0:100", round=42, salt="abc")

        assert helpers["raw_status"] == EXPIRED_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_action_help_omits_raw_status_for_json_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.next_action_help(
            1,
            {
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                    }
                ],
            },
            "0:100",
            salt="abc",
        )

        assert "raw_status" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_mechanism_action_help_omits_raw_status_for_json_status_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.next_mechanism_action_help(
            5,
            4,
            {
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                    }
                ],
            },
            "0:100",
            salt="abc",
        )

        assert "raw_status" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_weights_next_timelocked_action_help_omits_raw_status_for_json_status_via_client_surface(
        self, mock_run
    ) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        helpers = c.weights.next_timelocked_action_help(
            9,
            {
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 110,
                        "last_reveal": 130,
                        "status": "EXPIRED",
                    }
                ],
            },
            "0:100",
            round=42,
            salt="abc",
        )

        assert "raw_status" not in helpers

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_runbook_help_strips_text_raw_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        runbook = c.weights.status_runbook_help(5, "\n" + READY_STATUS_TEXT + "\n")

        assert runbook["raw_status"] == READY_STATUS_TEXT.strip()
        assert runbook["summary"]["next_action"] == "REVEAL"

    @patch("taocli.runner.subprocess.run")
    def test_weights_status_summary_help_keeps_text_summary_surface_clean_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process()
        c = Client()
        summary = c.weights.status_summary_help(READY_STATUS_TEXT)

        assert "raw_status" not in summary
        assert summary["next_action"] == "REVEAL"
        assert summary["pending_commits"] == 1

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_text_strips_raw_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="\n" + EXPIRED_STATUS_TEXT + "\n")
        c = Client()
        helpers = c.weights.diagnose_text(9, "ExpiredWeightCommit")

        assert helpers["raw_status"] == EXPIRED_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_mechanism_text_strips_raw_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="\n" + READY_STATUS_TEXT + "\n")
        c = Client()
        helpers = c.weights.diagnose_mechanism_text(5, 4, "RevealTooEarly", "0:100", salt="abc", version_key=7)

        assert helpers["raw_status"] == READY_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "REVEAL"

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_timelocked_text_strips_raw_status_via_client_surface(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(stdout="\n" + WAITING_STATUS_TEXT + "\n")
        c = Client()
        helpers = c.weights.diagnose_timelocked_text(8, "RevealTooEarly")

        assert helpers["raw_status"] == WAITING_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "WAIT"

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
            "next_step": "Run recommended_command to submit a fresh weights update.",
            "local_validation_tip": c.weights._local_validation_tip(),
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
            "next_step": "Prepare a fresh weights payload, then rerun recommended_command to build the retry command.",
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
            "local_validation_tip": c.weights._local_validation_tip(),
        }

    @patch("taocli.runner.subprocess.run")
    def test_weights_diagnose_via_client_surface_uses_status_guidance_next_step(self, mock_run) -> None:
        mock_run.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        c = Client()
        helpers = c.weights.diagnose(7, "ExpiredWeightCommit")
        assert helpers["next_step"] == (
            "Prepare a fresh weights payload, then rerun recommended_command to build the retry command."
        )
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["reason"] == "A previous pending commit expired, so fresh weights are required."
        assert helpers["recommended_command"] == "agcli weights status --netuid 7"
        assert helpers["pending_commit"]["status"] == "EXPIRED"
        assert helpers["reveal_window"] == {"first_block": 110, "last_block": 130}

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
