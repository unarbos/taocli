"""Tests for the Delegate SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.delegate import Delegate


@pytest.fixture
def delegate(mock_subprocess):
    return Delegate(AgcliRunner())


class TestDelegate:
    def test_show(self, delegate, mock_subprocess):
        delegate.show("5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "delegate" in cmd and "show" in cmd

    def test_list(self, delegate, mock_subprocess):
        delegate.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "list" in cmd

    def test_decrease_take(self, delegate, mock_subprocess):
        delegate.decrease_take(0.10)
        cmd = mock_subprocess.call_args[0][0]
        assert "decrease-take" in cmd

    def test_decrease_take_with_hotkey(self, delegate, mock_subprocess):
        delegate.decrease_take(0.10, hotkey_address="5G...")
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd

    def test_increase_take(self, delegate, mock_subprocess):
        delegate.increase_take(0.20)
        cmd = mock_subprocess.call_args[0][0]
        assert "increase-take" in cmd
