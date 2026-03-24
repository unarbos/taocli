"""Tests for the Block SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.block import Block


@pytest.fixture
def block(mock_subprocess):
    return Block(AgcliRunner())


class TestBlock:
    def test_info(self, block, mock_subprocess):
        block.info(100)
        cmd = mock_subprocess.call_args[0][0]
        assert "block" in cmd and "info" in cmd and "--number" in cmd

    def test_latest(self, block, mock_subprocess):
        block.latest()
        cmd = mock_subprocess.call_args[0][0]
        assert "block" in cmd and "latest" in cmd

    def test_range(self, block, mock_subprocess):
        block.range(100, 200)
        cmd = mock_subprocess.call_args[0][0]
        assert "block" in cmd and "range" in cmd
        assert "--from" in cmd and "--to" in cmd
