"""Tests for the Diff SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.diff import Diff


@pytest.fixture
def diff(mock_subprocess):
    return Diff(AgcliRunner())


class TestDiff:
    def test_portfolio(self, diff, mock_subprocess):
        diff.portfolio("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "diff" in cmd and "portfolio" in cmd and "--address" in cmd

    def test_portfolio_with_blocks(self, diff, mock_subprocess):
        diff.portfolio("5G...", block1=100, block2=200)
        cmd = mock_subprocess.call_args[0][0]
        assert "--block1" in cmd and "--block2" in cmd

    def test_subnet(self, diff, mock_subprocess):
        diff.subnet(1, 100, 200)
        cmd = mock_subprocess.call_args[0][0]
        assert "subnet" in cmd and "--netuid" in cmd

    def test_network(self, diff, mock_subprocess):
        diff.network(100, 200)
        cmd = mock_subprocess.call_args[0][0]
        assert "network" in cmd and "--block1" in cmd

    def test_metagraph(self, diff, mock_subprocess):
        diff.metagraph(1, 100, 200)
        cmd = mock_subprocess.call_args[0][0]
        assert "metagraph" in cmd and "--netuid" in cmd
