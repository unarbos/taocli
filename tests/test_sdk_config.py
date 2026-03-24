"""Tests for the Config SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.config import Config


@pytest.fixture
def config(mock_subprocess):
    return Config(AgcliRunner())


class TestConfig:
    def test_get(self, config, mock_subprocess):
        config.get("network")
        cmd = mock_subprocess.call_args[0][0]
        assert "config" in cmd and "get" in cmd and "--key" in cmd

    def test_set(self, config, mock_subprocess):
        config.set("network", "finney")
        cmd = mock_subprocess.call_args[0][0]
        assert "config" in cmd and "set" in cmd and "--key" in cmd and "--value" in cmd

    def test_list(self, config, mock_subprocess):
        config.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "config" in cmd and "list" in cmd

    def test_reset(self, config, mock_subprocess):
        config.reset()
        cmd = mock_subprocess.call_args[0][0]
        assert "config" in cmd and "reset" in cmd

    def test_path(self, config, mock_subprocess):
        config.path()
        cmd = mock_subprocess.call_args[0][0]
        assert "config" in cmd and "path" in cmd

    def test_cache_clear(self, config, mock_subprocess):
        config.cache_clear()
        cmd = mock_subprocess.call_args[0][0]
        assert "config" in cmd and "cache-clear" in cmd

    def test_cache_info(self, config, mock_subprocess):
        config.cache_info()
        cmd = mock_subprocess.call_args[0][0]
        assert "config" in cmd and "cache-info" in cmd
