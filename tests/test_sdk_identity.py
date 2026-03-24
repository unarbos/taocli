"""Tests for the Identity SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.identity import Identity


@pytest.fixture
def identity(mock_subprocess):
    return Identity(AgcliRunner())


class TestIdentity:
    def test_set(self, identity, mock_subprocess):
        identity.set(name="mynet")
        cmd = mock_subprocess.call_args[0][0]
        assert "identity" in cmd and "set" in cmd and "--name" in cmd

    def test_set_all_options(self, identity, mock_subprocess):
        identity.set(name="mynet", url="https://example.com", description="desc")
        cmd = mock_subprocess.call_args[0][0]
        assert "--name" in cmd and "--url" in cmd and "--description" in cmd

    def test_get(self, identity, mock_subprocess):
        identity.get()
        cmd = mock_subprocess.call_args[0][0]
        assert "identity" in cmd and "get" in cmd

    def test_get_with_address(self, identity, mock_subprocess):
        identity.get(address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd

    def test_set_subnet(self, identity, mock_subprocess):
        identity.set_subnet(netuid=1, name="My Subnet")
        cmd = mock_subprocess.call_args[0][0]
        assert "identity" in cmd and "set-subnet" in cmd
        assert "--netuid" in cmd and "--name" in cmd

    def test_set_subnet_all_options(self, identity, mock_subprocess):
        identity.set_subnet(netuid=1, name="SN", github="https://github.com/x", url="https://x.com")
        cmd = mock_subprocess.call_args[0][0]
        assert "--netuid" in cmd and "--name" in cmd and "--github" in cmd and "--url" in cmd

    def test_remove(self, identity, mock_subprocess):
        identity.remove()
        cmd = mock_subprocess.call_args[0][0]
        assert "identity" in cmd and "remove" in cmd
