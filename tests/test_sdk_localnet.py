"""Tests for the Localnet SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.localnet import Localnet


@pytest.fixture
def localnet(mock_subprocess):
    return Localnet(AgcliRunner())


class TestLocalnet:
    def test_start(self, localnet, mock_subprocess):
        localnet.start()
        cmd = mock_subprocess.call_args[0][0]
        assert "localnet" in cmd and "start" in cmd

    def test_start_with_opts(self, localnet, mock_subprocess):
        localnet.start(image="myimage", container="mycontainer", port=9944, timeout=60)
        cmd = mock_subprocess.call_args[0][0]
        assert "--image" in cmd and "--container" in cmd and "--port" in cmd

    def test_start_no_wait(self, localnet, mock_subprocess):
        localnet.start(wait=False)
        cmd = mock_subprocess.call_args[0][0]
        assert "--wait" not in cmd

    def test_stop(self, localnet, mock_subprocess):
        localnet.stop()
        cmd = mock_subprocess.call_args[0][0]
        assert "stop" in cmd

    def test_stop_with_container(self, localnet, mock_subprocess):
        localnet.stop(container="mycontainer")
        cmd = mock_subprocess.call_args[0][0]
        assert "--container" in cmd

    def test_status(self, localnet, mock_subprocess):
        localnet.status()
        cmd = mock_subprocess.call_args[0][0]
        assert "status" in cmd

    def test_status_with_opts(self, localnet, mock_subprocess):
        localnet.status(container="c", port=9944)
        cmd = mock_subprocess.call_args[0][0]
        assert "--container" in cmd and "--port" in cmd

    def test_reset(self, localnet, mock_subprocess):
        localnet.reset()
        cmd = mock_subprocess.call_args[0][0]
        assert "reset" in cmd

    def test_reset_with_opts(self, localnet, mock_subprocess):
        localnet.reset(image="i", container="c", port=9944, timeout=60)
        cmd = mock_subprocess.call_args[0][0]
        assert "--image" in cmd and "--timeout" in cmd

    def test_logs(self, localnet, mock_subprocess):
        localnet.logs()
        cmd = mock_subprocess.call_args[0][0]
        assert "logs" in cmd

    def test_logs_with_opts(self, localnet, mock_subprocess):
        localnet.logs(container="c", tail=50)
        cmd = mock_subprocess.call_args[0][0]
        assert "--container" in cmd and "--tail" in cmd

    def test_scaffold(self, localnet, mock_subprocess):
        localnet.scaffold()
        cmd = mock_subprocess.call_args[0][0]
        assert "scaffold" in cmd

    def test_scaffold_with_opts(self, localnet, mock_subprocess):
        localnet.scaffold(config="c.json", image="i", port=9944, no_start=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--config" in cmd and "--no-start" in cmd
