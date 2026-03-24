"""Tests for the Root SDK module."""

from __future__ import annotations

import pytest

from pytao.runner import AgcliRunner
from pytao.sdk.root import Root


@pytest.fixture
def root(mock_subprocess):
    return Root(AgcliRunner())


class TestRoot:
    def test_register(self, root, mock_subprocess):
        root.register()
        cmd = mock_subprocess.call_args[0][0]
        assert "root" in cmd and "register" in cmd

    def test_weights(self, root, mock_subprocess):
        root.weights("1:100,2:200")
        cmd = mock_subprocess.call_args[0][0]
        assert "weights" in cmd and "--weights" in cmd
