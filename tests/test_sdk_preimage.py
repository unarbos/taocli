"""Tests for the Preimage SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.preimage import Preimage


@pytest.fixture
def preimage(mock_subprocess):
    return Preimage(AgcliRunner())


class TestPreimage:
    def test_note(self, preimage, mock_subprocess):
        preimage.note("Balances", "transfer")
        cmd = mock_subprocess.call_args[0][0]
        assert "preimage" in cmd and "note" in cmd
        assert "--pallet" in cmd and "--call" in cmd

    def test_note_with_args(self, preimage, mock_subprocess):
        preimage.note("Balances", "transfer", args='["5G...", 100]')
        cmd = mock_subprocess.call_args[0][0]
        assert "--args" in cmd

    def test_unnote(self, preimage, mock_subprocess):
        preimage.unnote("0xabc123")
        cmd = mock_subprocess.call_args[0][0]
        assert "unnote" in cmd and "--hash" in cmd
