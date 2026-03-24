"""Tests for the Utils SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.utils import Utils


@pytest.fixture
def utils(mock_subprocess):
    return Utils(AgcliRunner())


class TestUtils:
    def test_convert(self, utils, mock_subprocess):
        utils.convert("1000000000")
        cmd = mock_subprocess.call_args[0][0]
        assert "utils" in cmd and "convert" in cmd and "--value" in cmd

    def test_convert_with_units(self, utils, mock_subprocess):
        utils.convert("1.0", from_unit="tao", to_unit="rao")
        cmd = mock_subprocess.call_args[0][0]
        assert "--from" in cmd and "--to" in cmd

    def test_latency(self, utils, mock_subprocess):
        utils.latency()
        cmd = mock_subprocess.call_args[0][0]
        assert "utils" in cmd and "latency" in cmd
