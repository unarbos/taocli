"""Tests for the Crowdloan SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.crowdloan import Crowdloan


@pytest.fixture
def crowdloan(mock_subprocess):
    return Crowdloan(AgcliRunner())


class TestCrowdloan:
    def test_create(self, crowdloan, mock_subprocess):
        crowdloan.create("100", "1", "1000", 999)
        cmd = mock_subprocess.call_args[0][0]
        assert "crowdloan" in cmd and "create" in cmd
        assert "--deposit" in cmd and "--cap" in cmd

    def test_create_with_target(self, crowdloan, mock_subprocess):
        crowdloan.create("100", "1", "1000", 999, target="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--target" in cmd

    def test_contribute(self, crowdloan, mock_subprocess):
        crowdloan.contribute("1", "50")
        cmd = mock_subprocess.call_args[0][0]
        assert "contribute" in cmd and "--amount" in cmd

    def test_withdraw(self, crowdloan, mock_subprocess):
        crowdloan.withdraw("1")
        cmd = mock_subprocess.call_args[0][0]
        assert "withdraw" in cmd

    def test_finalize(self, crowdloan, mock_subprocess):
        crowdloan.finalize("1")
        cmd = mock_subprocess.call_args[0][0]
        assert "finalize" in cmd

    def test_refund(self, crowdloan, mock_subprocess):
        crowdloan.refund("1")
        cmd = mock_subprocess.call_args[0][0]
        assert "refund" in cmd

    def test_dissolve(self, crowdloan, mock_subprocess):
        crowdloan.dissolve("1")
        cmd = mock_subprocess.call_args[0][0]
        assert "dissolve" in cmd

    def test_update_cap(self, crowdloan, mock_subprocess):
        crowdloan.update_cap("1", "2000")
        cmd = mock_subprocess.call_args[0][0]
        assert "update-cap" in cmd and "--cap" in cmd

    def test_update_end(self, crowdloan, mock_subprocess):
        crowdloan.update_end("1", 1500)
        cmd = mock_subprocess.call_args[0][0]
        assert "update-end" in cmd and "--end-block" in cmd

    def test_update_min_contribution(self, crowdloan, mock_subprocess):
        crowdloan.update_min_contribution("1", "5")
        cmd = mock_subprocess.call_args[0][0]
        assert "update-min-contribution" in cmd

    def test_list(self, crowdloan, mock_subprocess):
        crowdloan.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "crowdloan" in cmd and "list" in cmd

    def test_info(self, crowdloan, mock_subprocess):
        crowdloan.info("1")
        cmd = mock_subprocess.call_args[0][0]
        assert "info" in cmd

    def test_contributors(self, crowdloan, mock_subprocess):
        crowdloan.contributors("1")
        cmd = mock_subprocess.call_args[0][0]
        assert "contributors" in cmd
