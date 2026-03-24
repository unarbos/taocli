"""Tests for the Subscribe SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.subscribe import Subscribe


@pytest.fixture
def subscribe(mock_subprocess):
    return Subscribe(AgcliRunner())


class TestSubscribe:
    def test_blocks(self, subscribe, mock_subprocess):
        subscribe.blocks()
        cmd = mock_subprocess.call_args[0][0]
        assert "subscribe" in cmd and "blocks" in cmd

    def test_events(self, subscribe, mock_subprocess):
        subscribe.events()
        cmd = mock_subprocess.call_args[0][0]
        assert "subscribe" in cmd and "events" in cmd

    def test_events_with_filter(self, subscribe, mock_subprocess):
        subscribe.events(filter="staking")
        cmd = mock_subprocess.call_args[0][0]
        assert "--filter" in cmd

    def test_events_with_netuid(self, subscribe, mock_subprocess):
        subscribe.events(netuid=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--netuid" in cmd

    def test_events_with_account(self, subscribe, mock_subprocess):
        subscribe.events(account="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--account" in cmd
