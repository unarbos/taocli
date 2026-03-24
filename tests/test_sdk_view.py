"""Tests for the View SDK module."""

from __future__ import annotations

import pytest

from pytao.runner import AgcliRunner
from pytao.sdk.view import View


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
