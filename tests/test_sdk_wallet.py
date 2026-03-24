"""Tests for the Wallet SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.wallet import Wallet


@pytest.fixture
def wallet(mock_subprocess):
    return Wallet(AgcliRunner())


class TestWallet:
    def test_create(self, wallet, mock_subprocess):
        wallet.create()
        cmd = mock_subprocess.call_args[0][0]
        assert "wallet" in cmd and "create" in cmd

    def test_create_with_name(self, wallet, mock_subprocess):
        wallet.create(name="mywallet")
        cmd = mock_subprocess.call_args[0][0]
        assert "--wallet" in cmd and "mywallet" in cmd

    def test_list(self, wallet, mock_subprocess):
        wallet.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "wallet" in cmd and "list" in cmd

    def test_show(self, wallet, mock_subprocess):
        wallet.show()
        cmd = mock_subprocess.call_args[0][0]
        assert "wallet" in cmd and "show" in cmd

    def test_show_with_name(self, wallet, mock_subprocess):
        wallet.show(name="w1")
        cmd = mock_subprocess.call_args[0][0]
        assert "--wallet" in cmd

    def test_import_wallet(self, wallet, mock_subprocess):
        wallet.import_wallet("word1 word2 ... word12")
        cmd = mock_subprocess.call_args[0][0]
        assert "import" in cmd and "--mnemonic" in cmd

    def test_import_with_name(self, wallet, mock_subprocess):
        wallet.import_wallet("words", name="imported")
        cmd = mock_subprocess.call_args[0][0]
        assert "--wallet" in cmd and "imported" in cmd

    def test_regen_coldkey(self, wallet, mock_subprocess):
        wallet.regen_coldkey("words")
        cmd = mock_subprocess.call_args[0][0]
        assert "regen-coldkey" in cmd

    def test_regen_hotkey(self, wallet, mock_subprocess):
        wallet.regen_hotkey("words")
        cmd = mock_subprocess.call_args[0][0]
        assert "regen-hotkey" in cmd

    def test_new_hotkey(self, wallet, mock_subprocess):
        wallet.new_hotkey()
        cmd = mock_subprocess.call_args[0][0]
        assert "new-hotkey" in cmd

    def test_new_hotkey_with_name(self, wallet, mock_subprocess):
        wallet.new_hotkey(name="hk2")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-name" in cmd

    def test_sign(self, wallet, mock_subprocess):
        wallet.sign("hello")
        cmd = mock_subprocess.call_args[0][0]
        assert "sign" in cmd and "--message" in cmd

    def test_verify(self, wallet, mock_subprocess):
        wallet.verify("hello", "0x1234")
        cmd = mock_subprocess.call_args[0][0]
        assert "verify" in cmd and "--signature" in cmd

    def test_verify_with_address(self, wallet, mock_subprocess):
        wallet.verify("msg", "sig", address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd

    def test_derive(self, wallet, mock_subprocess):
        wallet.derive(pubkey="0xabc")
        cmd = mock_subprocess.call_args[0][0]
        assert "derive" in cmd and "--pubkey" in cmd

    def test_derive_mnemonic(self, wallet, mock_subprocess):
        wallet.derive(mnemonic="words")
        cmd = mock_subprocess.call_args[0][0]
        assert "--mnemonic" in cmd

    def test_dev_key(self, wallet, mock_subprocess):
        wallet.dev_key("Bob")
        cmd = mock_subprocess.call_args[0][0]
        assert "dev-key" in cmd and "Bob" in cmd

    def test_associate_hotkey(self, wallet, mock_subprocess):
        wallet.associate_hotkey()
        cmd = mock_subprocess.call_args[0][0]
        assert "associate-hotkey" in cmd

    def test_check_swap(self, wallet, mock_subprocess):
        wallet.check_swap()
        cmd = mock_subprocess.call_args[0][0]
        assert "check-swap" in cmd

    def test_show_mnemonic(self, wallet, mock_subprocess):
        wallet.show_mnemonic()
        cmd = mock_subprocess.call_args[0][0]
        assert "show-mnemonic" in cmd
