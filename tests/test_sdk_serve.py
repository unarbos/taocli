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

    def test_axon_with_version(self, serve, mock_subprocess):
        serve.axon(1, "0.0.0.0", 8080, version=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version" in cmd

    def test_reset(self, serve, mock_subprocess):
        serve.reset(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "reset" in cmd and "--netuid" in cmd

    def test_batch_axon(self, serve, mock_subprocess):
        serve.batch_axon("axons.json")
        cmd = mock_subprocess.call_args[0][0]
        assert "batch-axon" in cmd and "--file" in cmd

    def test_prometheus(self, serve, mock_subprocess):
        serve.prometheus(1, "0.0.0.0", 9090)
        cmd = mock_subprocess.call_args[0][0]
        assert "prometheus" in cmd and "--ip" in cmd

    def test_prometheus_with_version(self, serve, mock_subprocess):
        serve.prometheus(1, "0.0.0.0", 9090, version=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version" in cmd

    def test_axon_tls(self, serve, mock_subprocess):
        serve.axon_tls(1, "0.0.0.0", 8080, "/path/cert.pem")
        cmd = mock_subprocess.call_args[0][0]
        assert "axon-tls" in cmd and "--cert" in cmd

    def test_axon_tls_with_opts(self, serve, mock_subprocess):
        serve.axon_tls(1, "0.0.0.0", 8080, "/path/cert.pem", protocol=4, version=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--protocol" in cmd and "--version" in cmd
