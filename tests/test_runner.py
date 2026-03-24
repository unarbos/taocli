"""Tests for the AgcliRunner subprocess wrapper."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from taocli.runner import (
    AgcliError,
    AgcliRunner,
    _bundled_candidate,
    _ensure_executable,
    find_bundled_agcli_binary,
    resolve_agcli_binary,
)
from tests.conftest import make_completed_process


class TestBundledBinaryResolution:
    def test_bundled_candidate_builds_platform_path(self):
        candidate = str(_bundled_candidate("linux", "x86_64"))
        normalized = candidate.replace("\\", "/")
        assert normalized.endswith("taocli/bin/linux/x86_64/agcli")

    def test_ensure_executable_when_already_executable(self):
        with patch("taocli.runner.os.access", return_value=True):
            assert _ensure_executable("/tmp/agcli") is True

    def test_ensure_executable_adds_user_execute_bit(self):
        with (
            patch("taocli.runner.os.access", side_effect=[False, True]),
            patch("taocli.runner.os.stat") as mock_stat,
            patch("taocli.runner.os.chmod") as mock_chmod,
        ):
            mock_stat.return_value.st_mode = 0o644
            assert _ensure_executable("/tmp/agcli") is True
            mock_chmod.assert_called_once_with("/tmp/agcli", 0o744)

    def test_ensure_executable_returns_false_on_chmod_error(self):
        with (
            patch("taocli.runner.os.access", return_value=False),
            patch("taocli.runner.os.stat") as mock_stat,
            patch("taocli.runner.os.chmod", side_effect=OSError),
        ):
            mock_stat.return_value.st_mode = 0o644
            assert _ensure_executable("/tmp/agcli") is False

    def test_find_bundled_binary_missing_platform(self):
        with (
            patch("taocli.runner.platform.system", return_value="Windows"),
            patch("taocli.runner.platform.machine", return_value="AMD64"),
        ):
            assert find_bundled_agcli_binary() is None

    def test_find_bundled_binary_missing_arch(self):
        with (
            patch("taocli.runner.platform.system", return_value="Linux"),
            patch("taocli.runner.platform.machine", return_value="sparc64"),
        ):
            assert find_bundled_agcli_binary() is None

    def test_find_bundled_binary_missing_file(self):
        fake_candidate = type(
            "FakeCandidate",
            (),
            {
                "is_file": lambda self: False,
                "__str__": lambda self: "/tmp/missing/agcli",
            },
        )()

        with (
            patch("taocli.runner.platform.system", return_value="Linux"),
            patch("taocli.runner.platform.machine", return_value="x86_64"),
            patch("taocli.runner._bundled_candidate", return_value=fake_candidate),
        ):
            assert find_bundled_agcli_binary() is None

    def test_find_bundled_binary_found(self):
        fake_path = "/tmp/taocli/bin/linux/x86_64/agcli"
        fake_candidate = type(
            "FakeCandidate",
            (),
            {
                "is_file": lambda self: True,
                "__str__": lambda self: fake_path,
            },
        )()

        with (
            patch("taocli.runner.platform.system", return_value="Linux"),
            patch("taocli.runner.platform.machine", return_value="AMD64"),
            patch("taocli.runner._bundled_candidate", return_value=fake_candidate),
            patch("taocli.runner._ensure_executable", return_value=True),
        ):
            assert find_bundled_agcli_binary() == fake_path

    def test_find_bundled_binary_found_for_arm64_alias(self):
        fake_path = "/tmp/taocli/bin/darwin/aarch64/agcli"
        fake_candidate = type(
            "FakeCandidate",
            (),
            {
                "is_file": lambda self: True,
                "__str__": lambda self: fake_path,
            },
        )()

        with (
            patch("taocli.runner.platform.system", return_value="Darwin"),
            patch("taocli.runner.platform.machine", return_value="arm64"),
            patch("taocli.runner._bundled_candidate", return_value=fake_candidate),
            patch("taocli.runner._ensure_executable", return_value=True),
        ):
            assert find_bundled_agcli_binary() == fake_path

    def test_find_bundled_binary_found_for_aarch64(self):
        fake_path = "/tmp/taocli/bin/linux/aarch64/agcli"
        fake_candidate = type(
            "FakeCandidate",
            (),
            {
                "is_file": lambda self: True,
                "__str__": lambda self: fake_path,
            },
        )()

        with (
            patch("taocli.runner.platform.system", return_value="Linux"),
            patch("taocli.runner.platform.machine", return_value="aarch64"),
            patch("taocli.runner._bundled_candidate", return_value=fake_candidate),
            patch("taocli.runner._ensure_executable", return_value=True),
        ):
            assert find_bundled_agcli_binary() == fake_path

    def test_find_bundled_binary_not_executable(self):
        fake_path = "/tmp/taocli/bin/linux/x86_64/agcli"
        fake_candidate = type(
            "FakeCandidate",
            (),
            {
                "is_file": lambda self: True,
                "__str__": lambda self: fake_path,
            },
        )()

        with (
            patch("taocli.runner.platform.system", return_value="Linux"),
            patch("taocli.runner.platform.machine", return_value="x86_64"),
            patch("taocli.runner._bundled_candidate", return_value=fake_candidate),
            patch("taocli.runner._ensure_executable", return_value=False),
        ):
            assert find_bundled_agcli_binary() is None

    def test_find_bundled_binary_attempts_to_fix_permissions(self):
        fake_path = "/tmp/taocli/bin/linux/x86_64/agcli"
        fake_candidate = type(
            "FakeCandidate",
            (),
            {
                "is_file": lambda self: True,
                "__str__": lambda self: fake_path,
            },
        )()

        with (
            patch("taocli.runner.platform.system", return_value="Linux"),
            patch("taocli.runner.platform.machine", return_value="x86_64"),
            patch("taocli.runner._bundled_candidate", return_value=fake_candidate),
            patch("taocli.runner._ensure_executable", return_value=True) as mock_ensure,
        ):
            assert find_bundled_agcli_binary() == fake_path
            mock_ensure.assert_called_once_with(fake_path)

    def test_resolve_agcli_binary_prefers_explicit_path(self):
        assert resolve_agcli_binary("/custom/agcli") == "/custom/agcli"

    def test_resolve_agcli_binary_uses_bundled(self):
        with patch("taocli.runner.find_bundled_agcli_binary", return_value="/bundle/agcli"):
            assert resolve_agcli_binary(None) == "/bundle/agcli"

    def test_resolve_agcli_binary_falls_back_to_path(self):
        with patch("taocli.runner.find_bundled_agcli_binary", return_value=None):
            assert resolve_agcli_binary(None) == "agcli"


class TestAgcliRunnerInit:
    def test_defaults(self):
        with patch("taocli.runner.find_bundled_agcli_binary", return_value=None):
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

    def test_defaults_use_bundled_binary_when_present(self):
        with patch("taocli.runner.find_bundled_agcli_binary", return_value="/bundle/agcli"):
            r = AgcliRunner()
        assert r.binary == "/bundle/agcli"

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

    def test_run_success_without_capture(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="ok\n")
        r = AgcliRunner(binary="/custom/agcli")
        result = r.run(["doctor"], capture=False, check=False)
        assert result.stdout == "ok\n"
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[0] == "/custom/agcli"
        assert mock_subprocess.call_args[1]["capture_output"] is False

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
        assert str(exc_info.value) == "agcli exited with code 1: bad argument"

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
        assert "bundled binaries" in str(exc_info.value)
        assert exc_info.value.returncode == -1

    def test_run_timeout(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="agcli", timeout=5)
        r = AgcliRunner()
        with pytest.raises(AgcliError) as exc_info:
            r.run(["long-cmd"], timeout_secs=5)
        assert "timed out" in str(exc_info.value)
        assert "Client(timeout=10)" in str(exc_info.value)

    def test_run_timeout_without_timeout_hint_uses_default(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="agcli", timeout=5)
        r = AgcliRunner()
        with pytest.raises(AgcliError) as exc_info:
            r.run(["long-cmd"])
        assert "Client(timeout=60)" in str(exc_info.value)

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

    def test_run_json_timeout_passed_through(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="[]")
        r = AgcliRunner()
        r.run_json(["list"], timeout_secs=15)
        assert mock_subprocess.call_args[1]["timeout"] == 15

    def test_run_json_preserves_existing_global_flags(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="{}")
        r = AgcliRunner(yes=True, batch=True, output="json")
        r.run_json(["balance"])
        cmd = mock_subprocess.call_args[0][0]
        assert cmd.count("--yes") == 2
        assert cmd.count("--batch") == 2
        assert cmd.count("--output") == 2
        assert cmd.count("json") == 2

    def test_run_json_invalid_json_raises(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="not-json")
        r = AgcliRunner()
        with pytest.raises(ValueError):
            r.run_json(["balance"])


class TestFindBinary:
    def test_find_binary_exists(self):
        with patch("taocli.runner.find_bundled_agcli_binary", return_value=None):
            r = AgcliRunner()
        with patch("taocli.runner.shutil.which", return_value="/usr/bin/agcli") as mock_which:
            assert r.find_binary() == "/usr/bin/agcli"
            mock_which.assert_called_once_with("agcli")

    def test_find_binary_missing(self):
        with patch("taocli.runner.find_bundled_agcli_binary", return_value=None):
            r = AgcliRunner()
        with patch("taocli.runner.shutil.which", return_value=None) as mock_which:
            assert r.find_binary() is None
            mock_which.assert_called_once_with("agcli")

    def test_find_binary_uses_bundled_path(self):
        with patch("taocli.runner.find_bundled_agcli_binary", return_value="/bundle/agcli"):
            r = AgcliRunner()
        with patch("taocli.runner.shutil.which", return_value=None) as mock_which:
            assert r.find_binary() is None
            mock_which.assert_called_once_with("/bundle/agcli")


class TestVersion:
    def test_version(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="agcli 0.1.0\n")
        r = AgcliRunner()
        assert r.version() == "agcli 0.1.0"

    def test_version_uses_runner_binary(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="agcli 0.1.0\n")
        r = AgcliRunner(binary="/custom/agcli")
        r.version()
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[0] == "/custom/agcli"


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
