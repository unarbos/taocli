"""Tests for the AgcliRunner subprocess wrapper."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from taocli.runner import AgcliError, AgcliRunner
from tests.conftest import make_completed_process


class TestAgcliRunnerInit:
    def test_defaults(self):
        r = AgcliRunner()
        assert r.binary == "agcli"
        assert r.network is None
        assert r.endpoint is None
        assert r.wallet_dir is None
        assert r.wallet is None
        assert r.hotkey_name is None
        assert r.yes is False
        assert r.batch is False
        assert r.output is None
        assert r.password is None
        assert r.proxy is None
        assert r.timeout is None

    def test_custom_init(self):
        r = AgcliRunner(
            binary="/usr/bin/agcli",
            network="test",
            endpoint="ws://localhost:9944",
            wallet_dir="/tmp/wallets",
            wallet="mywallet",
            hotkey_name="myhotkey",
            yes=True,
            batch=True,
            output="json",
            password="secret",
            proxy="5Gx...",
            timeout=30,
        )
        assert r.binary == "/usr/bin/agcli"
        assert r.network == "test"
        assert r.endpoint == "ws://localhost:9944"
        assert r.wallet_dir == "/tmp/wallets"
        assert r.wallet == "mywallet"
        assert r.hotkey_name == "myhotkey"
        assert r.yes is True
        assert r.batch is True
        assert r.output == "json"
        assert r.password == "secret"
        assert r.proxy == "5Gx..."
        assert r.timeout == 30


class TestGlobalArgs:
    def test_no_global_args(self):
        r = AgcliRunner()
        assert r._build_global_args() == []

    def test_all_global_args(self):
        r = AgcliRunner(
            network="finney",
            endpoint="ws://x",
            wallet_dir="/w",
            wallet="w1",
            hotkey_name="h1",
            yes=True,
            batch=True,
            output="json",
            password="pw",
            proxy="5G...",
            timeout=60,
        )
        args = r._build_global_args()
        assert "--network" in args
        assert "finney" in args
        assert "--endpoint" in args
        assert "--wallet-dir" in args
        assert "--wallet" in args
        assert "--hotkey-name" in args
        assert "--yes" in args
        assert "--batch" in args
        assert "--output" in args
        assert "--password" in args
        assert "--proxy" in args
        assert "--timeout" in args
        assert "60" in args


class TestRun:
    def test_run_success(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="ok\n")
        r = AgcliRunner()
        result = r.run(["wallet", "list"])
        assert result.stdout == "ok\n"
        mock_subprocess.assert_called_once()
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[0] == "agcli"
        assert "wallet" in cmd
        assert "list" in cmd

    def test_run_with_global_args(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process()
        r = AgcliRunner(network="test", yes=True)
        r.run(["balance"])
        cmd = mock_subprocess.call_args[0][0]
        assert "--network" in cmd
        assert "test" in cmd
        assert "--yes" in cmd
        assert "balance" in cmd

    def test_run_failure_raises(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=1, stderr="bad argument")
        r = AgcliRunner()
        with pytest.raises(AgcliError) as exc_info:
            r.run(["bad-cmd"])
        assert exc_info.value.returncode == 1
        assert "bad argument" in exc_info.value.stderr

    def test_run_no_check(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=12, stderr="err")
        r = AgcliRunner()
        result = r.run(["bad"], check=False)
        assert result.returncode == 12

    def test_run_binary_not_found(self, mock_subprocess):
        mock_subprocess.side_effect = FileNotFoundError()
        r = AgcliRunner(binary="/nonexistent/agcli")
        with pytest.raises(AgcliError) as exc_info:
            r.run(["version"])
        assert "not found" in str(exc_info.value)
        assert exc_info.value.returncode == -1

    def test_run_timeout(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="agcli", timeout=5)
        r = AgcliRunner()
        with pytest.raises(AgcliError) as exc_info:
            r.run(["long-cmd"], timeout_secs=5)
        assert "timed out" in str(exc_info.value)

    def test_run_passes_timeout(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process()
        r = AgcliRunner()
        r.run(["cmd"], timeout_secs=42)
        assert mock_subprocess.call_args[1]["timeout"] == 42

    def test_run_capture_true(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process()
        r = AgcliRunner()
        r.run(["cmd"], capture=True)
        assert mock_subprocess.call_args[1]["capture_output"] is True

    def test_run_capture_false(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process()
        r = AgcliRunner()
        r.run(["cmd"], capture=False)
        assert mock_subprocess.call_args[1]["capture_output"] is False


class TestRunJson:
    def test_run_json_parses_output(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout='{"balance": 100}')
        r = AgcliRunner()
        result = r.run_json(["balance"])
        assert result == {"balance": 100}
        cmd = mock_subprocess.call_args[0][0]
        assert "--output" in cmd
        assert "json" in cmd
        assert "--batch" in cmd
        assert "--yes" in cmd

    def test_run_json_empty_output(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="")
        r = AgcliRunner()
        result = r.run_json(["balance"])
        assert result is None

    def test_run_json_whitespace_output(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="  \n  ")
        r = AgcliRunner()
        result = r.run_json(["balance"])
        assert result is None

    def test_run_json_with_timeout(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="[]")
        r = AgcliRunner()
        result = r.run_json(["list"], timeout_secs=10)
        assert result == []


class TestFindBinary:
    def test_find_binary_exists(self):
        r = AgcliRunner()
        with patch("taocli.runner.shutil.which", return_value="/usr/bin/agcli"):
            assert r.find_binary() == "/usr/bin/agcli"

    def test_find_binary_missing(self):
        r = AgcliRunner()
        with patch("taocli.runner.shutil.which", return_value=None):
            assert r.find_binary() is None


class TestVersion:
    def test_version(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="agcli 0.1.0\n")
        r = AgcliRunner()
        assert r.version() == "agcli 0.1.0"


class TestAgcliError:
    def test_error_attributes(self):
        err = AgcliError("test error", returncode=12, stderr="details")
        assert str(err) == "test error"
        assert err.returncode == 12
        assert err.stderr == "details"

    def test_error_defaults(self):
        err = AgcliError("msg")
        assert err.returncode == 1
        assert err.stderr == ""
