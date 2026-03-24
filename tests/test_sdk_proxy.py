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

    def test_create_pure(self, proxy, mock_subprocess):
        proxy.create_pure()
        cmd = mock_subprocess.call_args[0][0]
        assert "create-pure" in cmd

    def test_create_pure_with_opts(self, proxy, mock_subprocess):
        proxy.create_pure(proxy_type="Any", delay=10, index=0)
        cmd = mock_subprocess.call_args[0][0]
        assert "--proxy-type" in cmd and "--delay" in cmd and "--index" in cmd

    def test_kill_pure(self, proxy, mock_subprocess):
        proxy.kill_pure("5G...", "Any", 0, 100, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "kill-pure" in cmd and "--spawner" in cmd

    def test_announce(self, proxy, mock_subprocess):
        proxy.announce("5G...", "0xabc")
        cmd = mock_subprocess.call_args[0][0]
        assert "announce" in cmd and "--real" in cmd

    def test_proxy_announced(self, proxy, mock_subprocess):
        proxy.proxy_announced("5G...", "5H...", "Balances", "transfer")
        cmd = mock_subprocess.call_args[0][0]
        assert "proxy-announced" in cmd and "--delegate" in cmd

    def test_proxy_announced_with_opts(self, proxy, mock_subprocess):
        proxy.proxy_announced("5G...", "5H...", "Balances", "transfer", proxy_type="Any", args="[]")
        cmd = mock_subprocess.call_args[0][0]
        assert "--proxy-type" in cmd and "--args" in cmd

    def test_reject_announcement(self, proxy, mock_subprocess):
        proxy.reject_announcement("5G...", "0xabc")
        cmd = mock_subprocess.call_args[0][0]
        assert "reject-announcement" in cmd

    def test_list_announcements(self, proxy, mock_subprocess):
        proxy.list_announcements()
        cmd = mock_subprocess.call_args[0][0]
        assert "list-announcements" in cmd

    def test_list_announcements_with_address(self, proxy, mock_subprocess):
        proxy.list_announcements(address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--address" in cmd

    def test_remove_all(self, proxy, mock_subprocess):
        proxy.remove_all()
        cmd = mock_subprocess.call_args[0][0]
        assert "remove-all" in cmd

    def test_remove_announcement(self, proxy, mock_subprocess):
        proxy.remove_announcement("5G...", "0xabc")
        cmd = mock_subprocess.call_args[0][0]
        assert "remove-announcement" in cmd and "--real" in cmd
