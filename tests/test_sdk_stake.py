"""Tests for the Stake SDK module."""

from __future__ import annotations

import pytest

from pytao.runner import AgcliRunner
from pytao.sdk.stake import Stake


@pytest.fixture
def stake(mock_subprocess):
    return Stake(AgcliRunner())


class TestStake:
    def test_add(self, stake, mock_subprocess):
        stake.add(10.0, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "stake" in cmd and "add" in cmd
        assert "--amount" in cmd and "10.0" in cmd
        assert "--netuid" in cmd and "1" in cmd

    def test_add_with_options(self, stake, mock_subprocess):
        stake.add(5.0, 2, hotkey_address="5G...", max_slippage=0.01)
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd
        assert "--max-slippage" in cmd

    def test_remove(self, stake, mock_subprocess):
        stake.remove(5.0, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "remove" in cmd

    def test_remove_with_options(self, stake, mock_subprocess):
        stake.remove(5.0, 1, hotkey_address="5G...", max_slippage=0.02)
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd and "--max-slippage" in cmd

    def test_list(self, stake, mock_subprocess):
        stake.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "list" in cmd

    def test_list_with_options(self, stake, mock_subprocess):
        stake.list(address="5G...", at_block=100)
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd and "--at-block" in cmd

    def test_move(self, stake, mock_subprocess):
        stake.move(10.0, 1, 2)
        cmd = mock_subprocess.call_args[0][0]
        assert "move" in cmd and "--from" in cmd and "--to" in cmd

    def test_move_with_hotkey(self, stake, mock_subprocess):
        stake.move(10.0, 1, 2, hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd

    def test_swap(self, stake, mock_subprocess):
        stake.swap(10.0, 1, 2)
        cmd = mock_subprocess.call_args[0][0]
        assert "swap" in cmd

    def test_unstake_all(self, stake, mock_subprocess):
        stake.unstake_all()
        cmd = mock_subprocess.call_args[0][0]
        assert "unstake-all" in cmd

    def test_unstake_all_with_hotkey(self, stake, mock_subprocess):
        stake.unstake_all(hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd

    def test_claim_root(self, stake, mock_subprocess):
        stake.claim_root()
        cmd = mock_subprocess.call_args[0][0]
        assert "claim-root" in cmd

    def test_claim_root_with_netuid(self, stake, mock_subprocess):
        stake.claim_root(netuid=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--netuid" in cmd

    def test_add_limit(self, stake, mock_subprocess):
        stake.add_limit(10.0, 1, 0.5)
        cmd = mock_subprocess.call_args[0][0]
        assert "add-limit" in cmd and "--price" in cmd

    def test_add_limit_partial(self, stake, mock_subprocess):
        stake.add_limit(10.0, 1, 0.5, partial=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--partial" in cmd

    def test_remove_limit(self, stake, mock_subprocess):
        stake.remove_limit(10.0, 1, 0.5)
        cmd = mock_subprocess.call_args[0][0]
        assert "remove-limit" in cmd

    def test_childkey_take(self, stake, mock_subprocess):
        stake.childkey_take(0.18, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "childkey-take" in cmd

    def test_set_children(self, stake, mock_subprocess):
        stake.set_children(1, "0.5:5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-children" in cmd

    def test_recycle_alpha(self, stake, mock_subprocess):
        stake.recycle_alpha(5.0, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "recycle-alpha" in cmd

    def test_burn_alpha(self, stake, mock_subprocess):
        stake.burn_alpha(5.0, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "burn-alpha" in cmd

    def test_swap_limit(self, stake, mock_subprocess):
        stake.swap_limit(10.0, 1, 2, 0.5)
        cmd = mock_subprocess.call_args[0][0]
        assert "swap-limit" in cmd

    def test_swap_limit_partial(self, stake, mock_subprocess):
        stake.swap_limit(10.0, 1, 2, 0.5, partial=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--partial" in cmd

    def test_set_auto(self, stake, mock_subprocess):
        stake.set_auto(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-auto" in cmd

    def test_show_auto(self, stake, mock_subprocess):
        stake.show_auto()
        cmd = mock_subprocess.call_args[0][0]
        assert "show-auto" in cmd

    def test_process_claim(self, stake, mock_subprocess):
        stake.process_claim()
        cmd = mock_subprocess.call_args[0][0]
        assert "process-claim" in cmd

    def test_process_claim_with_options(self, stake, mock_subprocess):
        stake.process_claim(hotkey_address="5G...", netuids="1,2,3")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd and "--netuids" in cmd

    def test_set_claim(self, stake, mock_subprocess):
        stake.set_claim("swap")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-claim" in cmd and "--claim-type" in cmd

    def test_set_claim_with_subnets(self, stake, mock_subprocess):
        stake.set_claim("keep-subnets", subnets="1,2")
        cmd = mock_subprocess.call_args[0][0]
        assert "--subnets" in cmd

    def test_transfer_stake(self, stake, mock_subprocess):
        stake.transfer_stake("5G...", 10.0, 1, 2)
        cmd = mock_subprocess.call_args[0][0]
        assert "transfer-stake" in cmd

    def test_remove_full_limit(self, stake, mock_subprocess):
        stake.remove_full_limit(1, 0.5)
        cmd = mock_subprocess.call_args[0][0]
        assert "remove-full-limit" in cmd

    def test_wizard(self, stake, mock_subprocess):
        stake.wizard()
        cmd = mock_subprocess.call_args[0][0]
        assert "wizard" in cmd

    def test_wizard_with_options(self, stake, mock_subprocess):
        stake.wizard(netuid=1, amount=10.0, hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--netuid" in cmd and "--amount" in cmd and "--hotkey-address" in cmd
