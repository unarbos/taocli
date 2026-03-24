"""Tests for the Commitment SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.commitment import Commitment


@pytest.fixture
def commitment(mock_subprocess):
    return Commitment(AgcliRunner())


class TestCommitment:
    def test_set(self, commitment, mock_subprocess):
        commitment.set(1, "my_endpoint_data")
        cmd = mock_subprocess.call_args[0][0]
        assert "commitment" in cmd and "set" in cmd
        assert "--netuid" in cmd and "--data" in cmd

    def test_get(self, commitment, mock_subprocess):
        commitment.get(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "commitment" in cmd and "get" in cmd

    def test_get_with_address(self, commitment, mock_subprocess):
        commitment.get(1, address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd

    def test_list(self, commitment, mock_subprocess):
        commitment.list(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "commitment" in cmd and "list" in cmd
