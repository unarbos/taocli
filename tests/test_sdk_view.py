"""Tests for the View SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.view import View


@pytest.fixture
def view(mock_subprocess):
    return View(AgcliRunner())


class TestView:
    def test_portfolio(self, view, mock_subprocess):
        view.portfolio()
        cmd = mock_subprocess.call_args[0][0]
        assert "view" in cmd and "portfolio" in cmd

    def test_portfolio_with_options(self, view, mock_subprocess):
        view.portfolio(address="5G...", at_block=100)
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd and "--at-block" in cmd

    def test_network(self, view, mock_subprocess):
        view.network()
        cmd = mock_subprocess.call_args[0][0]
        assert "network" in cmd

    def test_dynamic(self, view, mock_subprocess):
        view.dynamic()
        cmd = mock_subprocess.call_args[0][0]
        assert "dynamic" in cmd

    def test_neuron(self, view, mock_subprocess):
        view.neuron(1, 0)
        cmd = mock_subprocess.call_args[0][0]
        assert "neuron" in cmd and "--uid" in cmd

    def test_validators(self, view, mock_subprocess):
        view.validators(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "validators" in cmd

    def test_validators_with_options(self, view, mock_subprocess):
        view.validators(1, limit=50, at_block=100)
        cmd = mock_subprocess.call_args[0][0]
        assert "--limit" in cmd

    def test_account(self, view, mock_subprocess):
        view.account("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "account" in cmd

    def test_history(self, view, mock_subprocess):
        view.history()
        cmd = mock_subprocess.call_args[0][0]
        assert "history" in cmd

    def test_history_options(self, view, mock_subprocess):
        view.history(address="5G...", limit=20)
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd and "--limit" in cmd

    def test_subnet_analytics(self, view, mock_subprocess):
        view.subnet_analytics(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "subnet-analytics" in cmd

    def test_staking_analytics(self, view, mock_subprocess):
        view.staking_analytics()
        cmd = mock_subprocess.call_args[0][0]
        assert "staking-analytics" in cmd

    def test_swap_sim_tao(self, view, mock_subprocess):
        view.swap_sim(1, tao=10.0)
        cmd = mock_subprocess.call_args[0][0]
        assert "swap-sim" in cmd and "--tao" in cmd

    def test_swap_sim_alpha(self, view, mock_subprocess):
        view.swap_sim(1, alpha=10.0)
        cmd = mock_subprocess.call_args[0][0]
        assert "--alpha" in cmd

    def test_nominations(self, view, mock_subprocess):
        view.nominations("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "nominations" in cmd

    def test_metagraph(self, view, mock_subprocess):
        view.metagraph(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "metagraph" in cmd

    def test_metagraph_options(self, view, mock_subprocess):
        view.metagraph(1, since_block=100, limit=50)
        cmd = mock_subprocess.call_args[0][0]
        assert "--since-block" in cmd and "--limit" in cmd

    def test_axon(self, view, mock_subprocess):
        view.axon(1, uid=0)
        cmd = mock_subprocess.call_args[0][0]
        assert "axon" in cmd

    def test_axon_hotkey(self, view, mock_subprocess):
        view.axon(1, hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd

    def test_health(self, view, mock_subprocess):
        view.health(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "health" in cmd

    def test_emissions(self, view, mock_subprocess):
        view.emissions(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "emissions" in cmd

    def test_emissions_limit(self, view, mock_subprocess):
        view.emissions(1, limit=10)
        cmd = mock_subprocess.call_args[0][0]
        assert "--limit" in cmd

    def test_chain_data_workflow_help(self, view):
        helpers = view.chain_data_workflow_help(1)
        assert helpers == {
            "netuid": 1,
            "subnet": "agcli subnet show --netuid 1",
            "metagraph": "agcli view metagraph --netuid 1",
            "neurons": "agcli view metagraph --netuid 1",
            "subnet_metagraph_full": "agcli subnet metagraph --netuid 1 --full",
            "validators": "agcli view validators --netuid 1",
            "endpoints": "agcli view axon --netuid 1",
            "miner_endpoints": "agcli view axon --netuid 1",
            "validator_endpoints": "agcli view axon --netuid 1",
            "axon": "agcli view axon --netuid 1",
            "probe": "agcli subnet probe --netuid 1",
            "commits": "agcli subnet commits --netuid 1",
            "health": "agcli view health --netuid 1",
            "emissions": "agcli view emissions --netuid 1",
            "hyperparams": "agcli subnet hyperparams --netuid 1",
        }

    def test_chain_data_workflow_help_with_uid(self, view):
        helpers = view.chain_data_workflow_help(7, uid=3)
        assert helpers["neuron"] == "agcli view neuron --netuid 7 --uid 3"
        assert helpers["axon"] == "agcli view axon --netuid 7 --uid 3"
        assert helpers["endpoints"] == "agcli view axon --netuid 7"
        assert helpers["miner_endpoints"] == "agcli view axon --netuid 7"
        assert helpers["probe"] == "agcli subnet probe --netuid 7 --uids 3"

    def test_chain_data_workflow_help_includes_subnet_and_endpoint_aliases(self, view):
        helpers = view.chain_data_workflow_help(9)
        assert helpers["subnet"] == "agcli subnet show --netuid 9"
        assert helpers["endpoints"] == "agcli view axon --netuid 9"
        assert helpers["miner_endpoints"] == "agcli view axon --netuid 9"
        assert helpers["validator_endpoints"] == "agcli view axon --netuid 9"
        assert helpers["validators"] == "agcli view validators --netuid 9"
        assert helpers["neurons"] == "agcli view metagraph --netuid 9"
        assert helpers["commits"] == "agcli subnet commits --netuid 9"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 9"

    def test_chain_data_workflow_help_keeps_neuron_and_commit_reads_when_uid_is_set(self, view):
        helpers = view.chain_data_workflow_help(9, uid=4)
        assert helpers["neurons"] == "agcli view metagraph --netuid 9"
        assert helpers["neuron"] == "agcli view neuron --netuid 9 --uid 4"
        assert helpers["commits"] == "agcli subnet commits --netuid 9"
        assert helpers["probe"] == "agcli subnet probe --netuid 9 --uids 4"

    def test_chain_data_workflow_help_keeps_commit_reads_with_hotkey_filter(self, view):
        helpers = view.chain_data_workflow_help(7, hotkey_address="5F...")
        assert helpers["axon"] == "agcli view axon --netuid 7 --hotkey-address 5F..."
        assert helpers["commits"] == "agcli subnet commits --netuid 7"
        assert helpers["neurons"] == "agcli view metagraph --netuid 7"

    def test_chain_data_workflow_help_keeps_endpoint_aliases_with_hotkey_filter(self, view):
        helpers = view.chain_data_workflow_help(7, hotkey_address="5F...")
        assert helpers["axon"] == "agcli view axon --netuid 7 --hotkey-address 5F..."
        assert helpers["endpoints"] == "agcli view axon --netuid 7"
        assert helpers["miner_endpoints"] == "agcli view axon --netuid 7"
        assert helpers["probe"] == "agcli subnet probe --netuid 7"

    def test_chain_data_workflow_help_with_hotkey(self, view):
        helpers = view.chain_data_workflow_help(7, hotkey_address=" 5F... ")
        assert helpers["axon"] == "agcli view axon --netuid 7 --hotkey-address 5F..."

    def test_chain_data_workflow_help_rejects_invalid_netuid(self, view):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            view.chain_data_workflow_help(0)

    def test_chain_data_workflow_help_rejects_boolean_netuid(self, view):
        with pytest.raises(ValueError, match="netuid must be an integer"):
            view.chain_data_workflow_help(True)

    def test_chain_data_workflow_help_rejects_boolean_uid(self, view):
        with pytest.raises(ValueError, match="uid must be an integer"):
            view.chain_data_workflow_help(1, uid=True)

    def test_chain_data_workflow_help_rejects_invalid_uid(self, view):
        with pytest.raises(ValueError, match="uid must be greater than or equal to 0"):
            view.chain_data_workflow_help(1, uid=-1)

    def test_chain_data_workflow_help_rejects_empty_hotkey(self, view):
        with pytest.raises(ValueError, match="hotkey_address cannot be empty"):
            view.chain_data_workflow_help(1, hotkey_address="   ")
