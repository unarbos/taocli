"""Tests for the Weights SDK module."""

from __future__ import annotations

import pytest

from pytao.runner import AgcliRunner
from pytao.sdk.weights import Weights


@pytest.fixture
def weights(mock_subprocess):
    return Weights(AgcliRunner())


class TestWeights:
    def test_show(self, weights, mock_subprocess):
        weights.show(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "weights" in cmd and "show" in cmd

    def test_show_with_options(self, weights, mock_subprocess):
        weights.show(1, hotkey_address="5G...", limit=10)
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd and "--limit" in cmd

    def test_set(self, weights, mock_subprocess):
        weights.set(1, "0:100,1:200")
        cmd = mock_subprocess.call_args[0][0]
        assert "set" in cmd and "--weights" in cmd

    def test_set_with_version_key(self, weights, mock_subprocess):
        weights.set(1, "0:100", version_key=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version-key" in cmd

    def test_commit(self, weights, mock_subprocess):
        weights.commit(1, "0:100")
        cmd = mock_subprocess.call_args[0][0]
        assert "commit" in cmd

    def test_commit_with_salt(self, weights, mock_subprocess):
        weights.commit(1, "0:100", salt="abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "--salt" in cmd

    def test_reveal(self, weights, mock_subprocess):
        weights.reveal(1, "0:100", "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "reveal" in cmd and "--salt" in cmd

    def test_status(self, weights, mock_subprocess):
        weights.status(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "status" in cmd

    def test_commit_reveal(self, weights, mock_subprocess):
        weights.commit_reveal(1, "0:100")
        cmd = mock_subprocess.call_args[0][0]
        assert "commit-reveal" in cmd

    def test_commit_reveal_wait(self, weights, mock_subprocess):
        weights.commit_reveal(1, "0:100", wait=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--wait" in cmd
