"""Tests for the Serve SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.serve import Serve


@pytest.fixture
def serve(mock_subprocess):
    return Serve(AgcliRunner())


class TestServe:
    def test_axon(self, serve, mock_subprocess):
        serve.axon(1, "0.0.0.0", 8080)
        cmd = mock_subprocess.call_args[0][0]
        assert "serve" in cmd and "axon" in cmd
        assert "--netuid" in cmd and "--ip" in cmd and "--port" in cmd

    def test_axon_with_protocol(self, serve, mock_subprocess):
        serve.axon(1, "0.0.0.0", 8080, protocol=4)
        cmd = mock_subprocess.call_args[0][0]
        assert "--protocol" in cmd
