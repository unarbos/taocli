"""Tests for the Subnet SDK module."""

from __future__ import annotations

import pytest

from pytao.runner import AgcliRunner
from pytao.sdk.subnet import Subnet


@pytest.fixture
def subnet(mock_subprocess):
    return Subnet(AgcliRunner())


class TestSubnet:
    def test_list(self, subnet, mock_subprocess):
        subnet.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "subnet" in cmd and "list" in cmd

    def test_list_at_block(self, subnet, mock_subprocess):
        subnet.list(at_block=100)
        cmd = mock_subprocess.call_args[0][0]
        assert "--at-block" in cmd

    def test_show(self, subnet, mock_subprocess):
        subnet.show(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "show" in cmd and "--netuid" in cmd

    def test_hyperparams(self, subnet, mock_subprocess):
        subnet.hyperparams(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "hyperparams" in cmd

    def test_metagraph(self, subnet, mock_subprocess):
        subnet.metagraph(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "metagraph" in cmd

    def test_metagraph_full(self, subnet, mock_subprocess):
        subnet.metagraph(1, uid=0, full=True, at_block=100)
        cmd = mock_subprocess.call_args[0][0]
        assert "--uid" in cmd and "--full" in cmd and "--at-block" in cmd

    def test_register(self, subnet, mock_subprocess):
        subnet.register()
        cmd = mock_subprocess.call_args[0][0]
        assert "register" in cmd

    def test_register_neuron(self, subnet, mock_subprocess):
        subnet.register_neuron(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "register-neuron" in cmd

    def test_pow(self, subnet, mock_subprocess):
        subnet.pow(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "pow" in cmd

    def test_pow_threads(self, subnet, mock_subprocess):
        subnet.pow(1, threads=8)
        cmd = mock_subprocess.call_args[0][0]
        assert "--threads" in cmd

    def test_health(self, subnet, mock_subprocess):
        subnet.health(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "health" in cmd

    def test_emissions(self, subnet, mock_subprocess):
        subnet.emissions(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "emissions" in cmd

    def test_cost(self, subnet, mock_subprocess):
        subnet.cost(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "cost" in cmd

    def test_create_cost(self, subnet, mock_subprocess):
        subnet.create_cost()
        cmd = mock_subprocess.call_args[0][0]
        assert "create-cost" in cmd

    def test_liquidity(self, subnet, mock_subprocess):
        subnet.liquidity()
        cmd = mock_subprocess.call_args[0][0]
        assert "liquidity" in cmd

    def test_liquidity_netuid(self, subnet, mock_subprocess):
        subnet.liquidity(netuid=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--netuid" in cmd

    def test_dissolve(self, subnet, mock_subprocess):
        subnet.dissolve(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "dissolve" in cmd

    def test_set_param(self, subnet, mock_subprocess):
        subnet.set_param(1, "tempo", "100")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-param" in cmd and "--param" in cmd

    def test_set_symbol(self, subnet, mock_subprocess):
        subnet.set_symbol(1, "ALPHA")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-symbol" in cmd

    def test_commits(self, subnet, mock_subprocess):
        subnet.commits(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "commits" in cmd

    def test_probe(self, subnet, mock_subprocess):
        subnet.probe(1, uids="0,1,2", timeout_ms=5000)
        cmd = mock_subprocess.call_args[0][0]
        assert "probe" in cmd and "--uids" in cmd

    def test_snipe(self, subnet, mock_subprocess):
        subnet.snipe(1, max_cost=10.0)
        cmd = mock_subprocess.call_args[0][0]
        assert "snipe" in cmd

    def test_trim(self, subnet, mock_subprocess):
        subnet.trim(1, 256)
        cmd = mock_subprocess.call_args[0][0]
        assert "trim" in cmd

    def test_start(self, subnet, mock_subprocess):
        subnet.start(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "start" in cmd

    def test_check_start(self, subnet, mock_subprocess):
        subnet.check_start(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "check-start" in cmd

    def test_emission_split(self, subnet, mock_subprocess):
        subnet.emission_split(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "emission-split" in cmd

    def test_mechanism_count(self, subnet, mock_subprocess):
        subnet.mechanism_count(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "mechanism-count" in cmd

    def test_set_mechanism_count(self, subnet, mock_subprocess):
        subnet.set_mechanism_count(1, 2)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-mechanism-count" in cmd

    def test_set_emission_split(self, subnet, mock_subprocess):
        subnet.set_emission_split(1, "50,50")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-emission-split" in cmd
