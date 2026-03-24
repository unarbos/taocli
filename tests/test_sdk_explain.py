"""Tests for the Explain SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.explain import Explain


@pytest.fixture
def explain(mock_subprocess):
    return Explain(AgcliRunner())


class TestExplain:
    def test_topic(self, explain, mock_subprocess):
        explain.topic("tempo")
        cmd = mock_subprocess.call_args[0][0]
        assert "explain" in cmd and "--topic" in cmd

    def test_topic_full(self, explain, mock_subprocess):
        explain.topic("weights", full=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "explain" in cmd and "--full" in cmd

    def test_topic_none(self, explain, mock_subprocess):
        explain.topic()
        cmd = mock_subprocess.call_args[0][0]
        assert "explain" in cmd
        assert "--topic" not in cmd

    def test_list_topics(self, explain, mock_subprocess):
        explain.list_topics()
        cmd = mock_subprocess.call_args[0][0]
        assert "explain" in cmd
