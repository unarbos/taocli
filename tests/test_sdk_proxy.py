"""Tests for the Proxy SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.proxy import Proxy


@pytest.fixture
def proxy(mock_subprocess):
    return Proxy(AgcliRunner())


class TestProxy:
    def test_add(self, proxy, mock_subprocess):
        proxy.add("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "proxy" in cmd and "add" in cmd and "--delegate" in cmd

    def test_add_with_type(self, proxy, mock_subprocess):
        proxy.add("5G...", proxy_type="Any")
        cmd = mock_subprocess.call_args[0][0]
        assert "--proxy-type" in cmd

    def test_remove(self, proxy, mock_subprocess):
        proxy.remove("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "proxy" in cmd and "remove" in cmd

    def test_list(self, proxy, mock_subprocess):
        proxy.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "proxy" in cmd and "list" in cmd

    def test_list_with_address(self, proxy, mock_subprocess):
        proxy.list(address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd
