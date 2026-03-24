"""Cross-cutting tests for error handling, return value parsing, and edge cases.

Exercises error paths and JSON parsing across SDK modules to ensure
AgcliError propagates correctly and return values are handled.
"""

from __future__ import annotations

import json
import subprocess
from unittest.mock import patch

import pytest

from taocli.runner import AgcliError, AgcliRunner
from taocli.sdk.base import SdkModule
from taocli.sdk.client import Client
from taocli.sdk.stake import Stake
from taocli.sdk.transfer import Transfer
from taocli.sdk.view import View
from taocli.sdk.wallet import Wallet
from taocli.sdk.weights import Weights
from tests.conftest import make_completed_process

# ---------------------------------------------------------------------------
# 1. AgcliError propagation through SDK modules
# ---------------------------------------------------------------------------


class TestSdkErrorPropagation:
    """Verify that AgcliError from the runner surfaces through SDK wrappers."""

    def test_sdk_run_propagates_nonzero_exit(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=1, stderr="insufficient balance")
        runner = AgcliRunner()
        mod = SdkModule(runner)
        with pytest.raises(AgcliError) as exc_info:
            mod._run(["transfer", "--dest", "5G...", "--amount", "999"])
        assert exc_info.value.returncode == 1
        assert "insufficient balance" in exc_info.value.stderr

    def test_sdk_run_raw_propagates_error(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=2, stderr="wallet locked")
        runner = AgcliRunner()
        mod = SdkModule(runner)
        with pytest.raises(AgcliError) as exc_info:
            mod._run_raw(["wallet", "show"])
        assert exc_info.value.returncode == 2

    def test_wallet_create_propagates_error(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=1, stderr="wallet already exists")
        w = Wallet(AgcliRunner())
        with pytest.raises(AgcliError) as exc_info:
            w.create(name="existing")
        assert "wallet already exists" in exc_info.value.stderr

    def test_transfer_propagates_error(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=1, stderr="invalid address format")
        xfer = Transfer(AgcliRunner())
        with pytest.raises(AgcliError):
            xfer.transfer("bad-addr", 10.0)

    def test_stake_add_propagates_error(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=1, stderr="not enough free balance")
        s = Stake(AgcliRunner())
        with pytest.raises(AgcliError) as exc_info:
            s.add(999.0, 1)
        assert "not enough free balance" in exc_info.value.stderr

    def test_weights_set_propagates_error(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(returncode=1, stderr="version key mismatch")
        w = Weights(AgcliRunner())
        with pytest.raises(AgcliError):
            w.set(1, "0:0.5,1:0.5")


# ---------------------------------------------------------------------------
# 2. Timeout propagation through SDK modules
# ---------------------------------------------------------------------------


class TestSdkTimeout:
    """Verify that subprocess timeouts propagate as AgcliError."""

    def test_sdk_run_timeout(self, mock_subprocess):
        mock_subprocess.side_effect = subprocess.TimeoutExpired(cmd="agcli", timeout=5)
        runner = AgcliRunner()
        mod = SdkModule(runner)
        with pytest.raises(AgcliError) as exc_info:
            mod._run(["view", "network"], timeout_secs=5)
        assert "timed out" in str(exc_info.value)

    def test_client_balance_timeout(self):
        with patch("taocli.runner.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="agcli", timeout=10)
            c = Client(timeout=10)
            with pytest.raises(AgcliError) as exc_info:
                c.balance()
            assert "timed out" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. Binary-not-found propagation
# ---------------------------------------------------------------------------


class TestBinaryNotFound:
    def test_sdk_module_binary_not_found(self, mock_subprocess):
        mock_subprocess.side_effect = FileNotFoundError()
        runner = AgcliRunner(binary="/nonexistent/agcli")
        mod = SdkModule(runner)
        with pytest.raises(AgcliError) as exc_info:
            mod._run(["balance"])
        assert "not found" in str(exc_info.value)
        assert exc_info.value.returncode == -1

    def test_client_binary_not_found(self):
        with patch("taocli.runner.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            c = Client(binary="/bad/path")
            with pytest.raises(AgcliError) as exc_info:
                c.balance()
            assert "not found" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 4. Return value parsing — JSON responses
# ---------------------------------------------------------------------------


class TestReturnValueParsing:
    """Verify that SDK methods return properly parsed JSON."""

    def test_balance_returns_parsed_dict(self):
        with patch("taocli.runner.subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(stdout='{"free": "123.456", "staked": "78.9"}')
            c = Client()
            result = c.balance()
            assert result == {"free": "123.456", "staked": "78.9"}

    def test_balance_returns_none_on_empty(self):
        with patch("taocli.runner.subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(stdout="")
            c = Client()
            assert c.balance() is None

    def test_view_returns_list(self, mock_subprocess):
        payload = [{"netuid": 1, "name": "root"}, {"netuid": 2, "name": "alpha"}]
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(payload))
        v = View(AgcliRunner())
        result = v.network()
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["netuid"] == 1

    def test_wallet_list_returns_array(self, mock_subprocess):
        payload = [{"name": "default", "hotkeys": ["default"]}]
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(payload))
        w = Wallet(AgcliRunner())
        result = w.list()
        assert isinstance(result, list)
        assert result[0]["name"] == "default"

    def test_stake_list_returns_parsed(self, mock_subprocess):
        payload = {"stakes": [{"amount": "10.0", "netuid": 1}]}
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(payload))
        s = Stake(AgcliRunner())
        result = s.list()
        assert result["stakes"][0]["amount"] == "10.0"

    def test_run_json_parses_nested_json(self, mock_subprocess):
        payload = {"data": {"inner": [1, 2, 3]}, "ok": True}
        mock_subprocess.return_value = make_completed_process(stdout=json.dumps(payload))
        runner = AgcliRunner()
        result = runner.run_json(["test"])
        assert result["data"]["inner"] == [1, 2, 3]

    def test_run_json_handles_whitespace_only(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="   \n\t  \n")
        runner = AgcliRunner()
        assert runner.run_json(["test"]) is None

    def test_run_json_raises_on_malformed_json(self, mock_subprocess):
        mock_subprocess.return_value = make_completed_process(stdout="{not valid json")
        runner = AgcliRunner()
        with pytest.raises(json.JSONDecodeError):
            runner.run_json(["test"])


# ---------------------------------------------------------------------------
# 5. Client-level convenience method edge cases
# ---------------------------------------------------------------------------


class TestClientEdgeCases:
    def test_doctor_strips_output(self):
        with patch("taocli.runner.subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(stdout="  All checks passed  \n\n")
            c = Client()
            assert c.doctor() == "All checks passed"

    def test_version_strips_output(self):
        with patch("taocli.runner.subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(stdout="agcli 1.2.3\n")
            c = Client()
            assert c.version() == "agcli 1.2.3"

    def test_balance_at_block_zero(self):
        with patch("taocli.runner.subprocess.run") as mock_run:
            mock_run.return_value = make_completed_process(stdout='{"free": 0}')
            c = Client()
            c.balance(at_block=0)
            cmd = mock_run.call_args[0][0]
            assert "--at-block" in cmd
            assert "0" in cmd


# ---------------------------------------------------------------------------
# 6. SdkModule _opt/_flag edge cases
# ---------------------------------------------------------------------------


class TestOptFlagEdgeCases:
    def test_opt_with_zero_value(self):
        assert SdkModule._opt("--amount", 0) == ["--amount", "0"]

    def test_opt_with_empty_string(self):
        assert SdkModule._opt("--name", "") == ["--name", ""]

    def test_opt_with_float(self):
        assert SdkModule._opt("--amount", 1.5) == ["--amount", "1.5"]

    def test_opt_with_bool_true(self):
        # bool True is not None, so it should work
        assert SdkModule._opt("--flag", True) == ["--flag", "True"]

    def test_flag_with_truthy_values(self):
        # Only True should produce the flag
        assert SdkModule._flag("--yes", True) == ["--yes"]
        assert SdkModule._flag("--yes", False) == []


# ---------------------------------------------------------------------------
# 7. AgcliError construction edge cases
# ---------------------------------------------------------------------------


class TestAgcliErrorEdgeCases:
    def test_error_str_includes_message(self):
        err = AgcliError("something went wrong", returncode=42, stderr="details here")
        assert "something went wrong" in str(err)

    def test_error_with_empty_stderr(self):
        err = AgcliError("fail")
        assert err.stderr == ""
        assert err.returncode == 1

    def test_error_is_exception(self):
        assert issubclass(AgcliError, Exception)

    def test_error_can_be_caught_as_exception(self):
        with pytest.raises(AgcliError):
            raise AgcliError("test")
