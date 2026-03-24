"""Tests for the Contracts SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.contracts import Contracts


@pytest.fixture
def contracts(mock_subprocess):
    return Contracts(AgcliRunner())


class TestContracts:
    def test_upload(self, contracts, mock_subprocess):
        contracts.upload("/path/to/code.wasm")
        cmd = mock_subprocess.call_args[0][0]
        assert "contracts" in cmd and "upload" in cmd and "--code" in cmd

    def test_upload_with_limit(self, contracts, mock_subprocess):
        contracts.upload("/path/to/code.wasm", storage_deposit_limit="1000000")
        cmd = mock_subprocess.call_args[0][0]
        assert "--storage-deposit-limit" in cmd

    def test_instantiate(self, contracts, mock_subprocess):
        contracts.instantiate("0xabc")
        cmd = mock_subprocess.call_args[0][0]
        assert "instantiate" in cmd and "--code-hash" in cmd

    def test_instantiate_with_opts(self, contracts, mock_subprocess):
        contracts.instantiate("0xabc", gas_ref_time=1000, gas_proof_size=500, storage_deposit_limit="100")
        cmd = mock_subprocess.call_args[0][0]
        assert "--gas-ref-time" in cmd and "--gas-proof-size" in cmd

    def test_call(self, contracts, mock_subprocess):
        contracts.call("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "contracts" in cmd and "call" in cmd and "--contract" in cmd

    def test_call_with_opts(self, contracts, mock_subprocess):
        contracts.call("5G...", gas_ref_time=100, gas_proof_size=50, storage_deposit_limit="10")
        cmd = mock_subprocess.call_args[0][0]
        assert "--gas-ref-time" in cmd

    def test_remove_code(self, contracts, mock_subprocess):
        contracts.remove_code("0xabc")
        cmd = mock_subprocess.call_args[0][0]
        assert "remove-code" in cmd and "--code-hash" in cmd
