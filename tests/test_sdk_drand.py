"""Tests for the Drand SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.drand import Drand


@pytest.fixture
def drand(mock_subprocess):
    return Drand(AgcliRunner())


class TestDrand:
    def test_write_pulse(self, drand, mock_subprocess):
        drand.write_pulse("payload_data", "sig_data")
        cmd = mock_subprocess.call_args[0][0]
        assert "drand" in cmd and "write-pulse" in cmd
        assert "--payload" in cmd and "--signature" in cmd
