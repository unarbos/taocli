"""Tests for the CLI pass-through layer."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from pytao.cli.main import COMMAND_GROUPS, main
from pytao.runner import AgcliError
from tests.conftest import make_completed_process

# Reference the module object for patching (not the click command)
_cli_main_module = sys.modules["pytao.cli.main"]


@pytest.fixture
def cli_runner():
    return CliRunner()


class TestCLIHelp:
    def test_no_args_shows_help(self, cli_runner):
        result = cli_runner.invoke(main, [])
        assert result.exit_code == 0
        assert "pytao" in result.output
        assert "Available commands" in result.output

    def test_help_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "pytao" in result.output

    def test_version_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "pytao" in result.output

    def test_available_commands_listed(self, cli_runner):
        result = cli_runner.invoke(main, [])
        for cmd in ["wallet", "stake", "transfer", "subnet", "balance", "weights", "view"]:
            assert cmd in result.output


class TestCLIPassThrough:
    @patch.object(_cli_main_module, "AgcliRunner")
    def test_passthrough_wallet_list(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="wallet list\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "list"])
        assert result.exit_code == 0
        assert "wallet list" in result.output
        mock_instance.run.assert_called_once()
        args = mock_instance.run.call_args
        assert list(args[0][0]) == ["wallet", "list"]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_passthrough_with_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "add", "--amount", "10", "--netuid", "1"])
        assert result.exit_code == 0
        args = list(mock_instance.run.call_args[0][0])
        assert "stake" in args
        assert "add" in args
        assert "--amount" in args
        assert "10" in args

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_passthrough_nonzero_exit(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(returncode=1, stderr="error msg\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["bad-command"])
        assert result.exit_code == 1

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_passthrough_stderr(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="", stderr="warning\n", returncode=0)
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["doctor"])
        assert result.exit_code == 0

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_passthrough_agcli_error(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = AgcliError("binary not found", returncode=-1)
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "list"])
        assert result.exit_code == 1
        assert "Error" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_custom_binary(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        cli_runner.invoke(main, ["--agcli-binary", "/custom/agcli", "doctor"])
        mock_cls.assert_called_once_with(binary="/custom/agcli")


class TestCommandGroups:
    def test_command_groups_not_empty(self):
        assert len(COMMAND_GROUPS) > 30

    def test_key_groups_present(self):
        for grp in [
            "wallet",
            "stake",
            "transfer",
            "subnet",
            "weights",
            "view",
            "root",
            "delegate",
            "identity",
            "balance",
            "config",
            "admin",
        ]:
            assert grp in COMMAND_GROUPS
