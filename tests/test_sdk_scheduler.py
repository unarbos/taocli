"""Tests for the Scheduler SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.scheduler import Scheduler


@pytest.fixture
def scheduler(mock_subprocess):
    return Scheduler(AgcliRunner())


class TestScheduler:
    def test_schedule(self, scheduler, mock_subprocess):
        scheduler.schedule(1000, "Balances", "transfer")
        cmd = mock_subprocess.call_args[0][0]
        assert "scheduler" in cmd and "schedule" in cmd
        assert "--when" in cmd and "--pallet" in cmd

    def test_schedule_with_opts(self, scheduler, mock_subprocess):
        scheduler.schedule(1000, "Balances", "transfer", args="[]", priority=128, repeat_every=10, repeat_count=5)
        cmd = mock_subprocess.call_args[0][0]
        assert "--args" in cmd and "--priority" in cmd
        assert "--repeat-every" in cmd and "--repeat-count" in cmd

    def test_schedule_named(self, scheduler, mock_subprocess):
        scheduler.schedule_named("my-job", 1000, "Balances", "transfer")
        cmd = mock_subprocess.call_args[0][0]
        assert "schedule-named" in cmd and "--id" in cmd

    def test_schedule_named_with_opts(self, scheduler, mock_subprocess):
        scheduler.schedule_named(
            "my-job", 1000, "Balances", "transfer", args="[]", priority=64, repeat_every=5, repeat_count=3
        )
        cmd = mock_subprocess.call_args[0][0]
        assert "--args" in cmd and "--priority" in cmd

    def test_cancel(self, scheduler, mock_subprocess):
        scheduler.cancel(1000, 0)
        cmd = mock_subprocess.call_args[0][0]
        assert "cancel" in cmd and "--when" in cmd and "--index" in cmd

    def test_cancel_named(self, scheduler, mock_subprocess):
        scheduler.cancel_named("my-job")
        cmd = mock_subprocess.call_args[0][0]
        assert "cancel-named" in cmd and "--id" in cmd
