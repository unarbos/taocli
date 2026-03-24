"""Tests for the SDK base module."""

from __future__ import annotations

from taocli.runner import AgcliRunner
from taocli.sdk.base import SdkModule


class TestSdkModule:
    def test_opt_with_value(self):
        assert SdkModule._opt("--netuid", 1) == ["--netuid", "1"]

    def test_opt_with_none(self):
        assert SdkModule._opt("--netuid", None) == []

    def test_opt_with_string(self):
        assert SdkModule._opt("--address", "5G...") == ["--address", "5G..."]

    def test_flag_true(self):
        assert SdkModule._flag("--yes", True) == ["--yes"]

    def test_flag_false(self):
        assert SdkModule._flag("--yes", False) == []

    def test_run_calls_runner(self, mock_subprocess):
        runner = AgcliRunner()
        mod = SdkModule(runner)
        result = mod._run(["test"])
        assert result == {"ok": True}

    def test_run_raw_calls_runner(self, mock_subprocess):
        from tests.conftest import make_completed_process

        mock_subprocess.return_value = make_completed_process(stdout="raw output\n")
        runner = AgcliRunner()
        mod = SdkModule(runner)
        result = mod._run_raw(["test"])
        assert result == "raw output"
