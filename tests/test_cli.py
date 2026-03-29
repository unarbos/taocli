"""Tests for the CLI pass-through layer."""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, call, patch

import click
import pytest
from click.testing import CliRunner

from taocli.cli.main import COMMAND_GROUPS, main, normalize_passthrough_args, unsupported_alias_message
from taocli.runner import AgcliError
from tests.conftest import make_completed_process

# Reference the module object for patching (not the click command)
_cli_main_module = sys.modules["taocli.cli.main"]


@pytest.fixture
def cli_runner():
    return CliRunner()


class TestCLIHelp:
    def test_no_args_shows_help(self, cli_runner):
        result = cli_runner.invoke(main, [])
        assert result.exit_code == 0
        assert "taocli" in result.output
        assert "Available commands" in result.output

    def test_help_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "taocli" in result.output

    def test_version_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "taocli" in result.output

    def test_available_commands_listed(self, cli_runner):
        result = cli_runner.invoke(main, [])
        for cmd in ["wallet", "stake", "transfer", "subnet", "balance", "weights", "view"]:
            assert cmd in result.output

    def test_help_mentions_bundled_binary(self, cli_runner):
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "bundled agcli binary" in result.output
        assert "agcli/releases" in result.output

    def test_help_mentions_tao_cli_distribution(self, cli_runner):
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "tao-cli" in result.output

    def test_help_mentions_localnet_scaffold_for_validation(self, cli_runner):
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "taocli localnet scaffold" in result.output
        assert "taocli doctor" in result.output
        assert "taocli weights status --netuid <netuid>" in result.output

    def test_no_args_mentions_btcli_aliases(self, cli_runner):
        result = cli_runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Compatibility aliases for btcli users" in result.output
        assert "subnets -> subnet" in result.output
        assert "sudo -> admin" in result.output
        assert "axon -> serve" in result.output
        assert "crowd -> crowdloan" in result.output

    def test_btcli_alias_help_is_explained(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "--help"])
        assert result.exit_code == 0
        assert "Compatibility aliases" in result.output
        assert "taocli subnets list" in result.output


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
    def test_btcli_subnets_alias_rewrites_to_subnet(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":2}]\n'),
            make_completed_process(stdout='[]\n'),
            make_completed_process(stdout='{"block":0}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "list", "--output", "json"])
        assert result.exit_code == 0
        assert '"subnets": {"2": {' in result.output
        assert '"subnet_name": ""' in result.output
        assert '"price": 0.0' in result.output
        assert mock_instance.run.call_args_list == [
            ((["subnet", "list", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "network", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_enriches_price_from_swap_sim(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":1,"name":"apex"}]\n'),
            make_completed_process(
                stdout='[{"netuid":1,"name":"apex","tao_in":{"rao":10000000000},"alpha_in":{"raw":10000000000},"alpha_out":{"raw":1000000000},"price":0.0,"tao_in_emission":0,"tempo":100,"blocks_since_last_step":58}]\n'
            ),
            make_completed_process(stdout='{"block":77017}\n'),
            make_completed_process(stdout='{"netuid":1,"current_price":1e-09}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--network", "local", "--json-output"])

        assert result.exit_code == 0
        assert '"price": 1e-09' in result.output
        assert '"market_cap": 1.1000000000000001e-08' in result.output
        assert mock_instance.run.call_args_list == [
            ((["subnet", "list", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "network", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "swap-sim", "--netuid", "1", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_keeps_swap_sim_price_over_ratio_fallback(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":1,"name":"apex"}]\n'),
            make_completed_process(
                stdout='[{"netuid":1,"name":"apex","tao_in":{"rao":10000000000},"alpha_in":{"raw":10000000000},"alpha_out":{"raw":1000000000},"price":0.0,"tao_in_emission":0,"tempo":100,"blocks_since_last_step":58}]\n'
            ),
            make_completed_process(stdout='{"block":77017}\n'),
            make_completed_process(stdout='{"netuid":1,"current_price":1e-09}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output"])

        assert result.exit_code == 0
        assert '"price": 1e-09' in result.output
        assert '"market_cap": 1.1000000000000001e-08' in result.output
        assert '"liquidity": {"tao_in": 10.0, "alpha_in": 10.0}' in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_does_not_pass_at_block_to_swap_sim(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":1}]\n'),
            make_completed_process(stdout='[{"netuid":1,"tao_in":{"rao":1000000000},"alpha_in":{"raw":1000000000},"alpha_out":{"raw":0},"price":0.0,"tao_in_emission":0,"tempo":10,"blocks_since_last_step":1}]\n'),
            make_completed_process(stdout='{"block":100}\n'),
            make_completed_process(stdout='{"netuid":1,"current_price":0.5}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output", "--at-block", "123"])

        assert result.exit_code == 0
        assert '"price": 0.5' in result.output
        assert mock_instance.run.call_args_list == [
            ((["subnet", "list", "--output", "json", "--at-block", "123"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--at-block", "123", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "network", "--at-block", "123", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "swap-sim", "--netuid", "1", "--output", "json"],), {"check": False, "capture": True}),
        ]


    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_uses_btcli_style_schema_and_extra_queries(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout=(
                    '[{"netuid":0,"name":"root","tempo":100},'
                    '{"netuid":2,"name":"omron","tempo":10}]\n'
                )
            ),
            make_completed_process(
                stdout=(
                    '[{"netuid":0,"name":"root","tempo":100,"tao_in":{"rao":0},"alpha_in":{"raw":0},'
                    '"alpha_out":{"raw":0},"tao_in_emission":0,"blocks_since_last_step":77},'
                    '{"netuid":2,"name":"omron","tempo":10,"tao_in":{"rao":1000299848938},'
                    '"alpha_in":{"raw":999700240945},"alpha_out":{"raw":0},'
                    '"price":1.000599787,"tao_in_emission":0,"blocks_since_last_step":9}]\n'
                )
            ),
            make_completed_process(stdout='{"block":72801}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--network", "local", "--json-output"])

        assert result.exit_code == 0
        assert '"total_netuids": 2' in result.output
        assert '"total_rate": 2.000599787' in result.output
        assert '"total_tao_emitted": 1000.299848938' in result.output
        assert '"subnets": {"0": {' in result.output
        assert '"subnet_name": "root"' in result.output
        assert '"subnet_name": "omron"' in result.output
        assert '"market_cap": 1000.2998481534157' in result.output
        assert '"liquidity": {"tao_in": 1000.299848938, "alpha_in": 999.700240945}' in result.output
        assert '"tempo": {"blocks_since_last_step": 9, "sn_tempo": 10}' in result.output
        assert '"emission_percentage": 1.37401938014313' in result.output
        assert mock_instance.run.call_args_list == [
            ((["subnet", "list", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "network", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    def test_btcli_subnets_list_json_flag_normalizes_to_output_json(self):
        assert normalize_passthrough_args(["subnets", "list", "--json-output", "--network", "local"]) == [
            "subnet",
            "list",
            "--output",
            "json",
            "--network",
            "local",
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_preserves_at_block_for_extra_queries(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[]\n'),
            make_completed_process(stdout='[]\n'),
            make_completed_process(stdout='{"block":100}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output", "--at-block", "123"])

        assert result.exit_code == 0
        assert mock_instance.run.call_args_list == [
            ((["subnet", "list", "--output", "json", "--at-block", "123"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--at-block", "123", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "network", "--at-block", "123", "--output", "json"],), {"check": False, "capture": True}),
        ]
        assert '"total_netuids": 0' in result.output
        assert '"subnets": {}' in result.output
        assert '"emission_percentage": 0.0' in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_text_output_does_not_trigger_extra_queries(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='plain text\n')
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list"])

        assert result.exit_code == 0
        assert result.output == 'plain text\n'
        mock_instance.run.assert_called_once_with(["subnet", "list"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_falls_back_when_list_is_not_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='not-json\n')
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output"])

        assert result.exit_code == 0
        assert result.output == 'not-json\n'
        mock_instance.run.assert_called_once_with(["subnet", "list", "--output", "json"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_ignores_bad_extra_query_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":2,"name":"omron"}]\n'),
            make_completed_process(stdout='not-json\n'),
            make_completed_process(stdout='also-not-json\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output"])

        assert result.exit_code == 0
        assert '"subnets": {"2": {' in result.output
        assert '"subnet_name": "omron"' in result.output
        assert '"total_tao_emitted": 0.0' in result.output
        assert '"emission_percentage": 0.0' in result.output
        assert len(mock_instance.run.call_args_list) == 3

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_prefers_dynamic_name_and_price(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":2,"name":"stale"}]\n'),
            make_completed_process(
                stdout='[{"netuid":2,"name":"fresh","tao_in":{"rao":2000000000},"alpha_in":{"raw":1000000000},"alpha_out":{"raw":500000000},"price":{"tao":2.0},"tao_in_emission":{"rao":100000000},"tempo":12,"blocks_since_last_step":3}]\n'
            ),
            make_completed_process(stdout='{"block":50}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output"])

        assert result.exit_code == 0
        assert '"subnet_name": "fresh"' in result.output
        assert '"price": 2.0' in result.output
        assert '"supply": 1.5' in result.output
        assert '"market_cap": 3.0' in result.output
        assert '"emission": 0.1' in result.output
        assert '"tempo": {"blocks_since_last_step": 3, "sn_tempo": 12}' in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_sets_root_defaults(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":0,"name":"root"}]\n'),
            make_completed_process(stdout='[{"netuid":0,"name":"root","tempo":100}]\n'),
            make_completed_process(stdout='{"block":10}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output"])

        assert result.exit_code == 0
        assert '"subnets": {"0": {"netuid": 0, "subnet_name": "root", "price": 1.0' in result.output
        assert '"liquidity": {"tao_in": null, "alpha_in": null}' in result.output
        assert '"alpha_out": null' in result.output
        assert '"tempo": {"blocks_since_last_step": null, "sn_tempo": null}' in result.output
        assert '"total_rate": 1.0' in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_list_json_output_sorts_root_then_market_cap(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='[{"netuid":2},{"netuid":0},{"netuid":1}]\n'),
            make_completed_process(
                stdout=(
                    '[{"netuid":2,"name":"two","tao_in":{"rao":4000000000},"alpha_in":{"raw":2000000000},"alpha_out":{"raw":0},"price":{"tao":2.0},"tao_in_emission":0,"tempo":10,"blocks_since_last_step":1},'
                    '{"netuid":0,"name":"root","tempo":100},'
                    '{"netuid":1,"name":"one","tao_in":{"rao":1000000000},"alpha_in":{"raw":1000000000},"alpha_out":{"raw":0},"price":{"tao":0.5},"tao_in_emission":0,"tempo":10,"blocks_since_last_step":1}]\n'
                )
            ),
            make_completed_process(stdout='{"block":100}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "list", "--json-output"])

        assert result.exit_code == 0
        assert result.output.index('"0": {') < result.output.index('"2": {') < result.output.index('"1": {')

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_alias_rewrites_to_subnet_hyperparams(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tempo":10}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--output", "json"])
        assert result.exit_code == 0
        assert '"hyperparameter": "tempo"' in result.output
        assert '"normalized_value": 10' in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_json_normalizes_hyperparams_schema(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout=(
                '{"netuid":2,"tempo":10,"max_weights_limit":65535,"commit_reveal_weights_interval":1,'
                '"min_burn":{"rao":500000,"tao":0.0005},"weights_version":0,'
                '"alpha_high":60000,"alpha_low":1000,"alpha_sigmoid_steepness":32768,'
                '"bonds_reset_enabled":true,"subnet_is_active":true,"transfers_enabled":false,'
                '"user_liquidity_enabled":true,"yuma3_enabled":1}\n'
            )
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--json-output"])
        assert result.exit_code == 0
        assert '"hyperparameter": "tempo"' in result.output
        assert '"hyperparameter": "max_weight_limit"' in result.output
        assert '"hyperparameter": "commit_reveal_period"' in result.output
        assert '"hyperparameter": "alpha_high"' in result.output
        assert '"hyperparameter": "alpha_low"' in result.output
        assert '"hyperparameter": "alpha_sigmoid_steepness"' in result.output
        assert '"hyperparameter": "bonds_reset_enabled"' in result.output
        assert '"hyperparameter": "subnet_is_active"' in result.output
        assert '"hyperparameter": "transfers_enabled"' in result.output
        assert '"hyperparameter": "user_liquidity_enabled"' in result.output
        assert '"hyperparameter": "yuma_version"' in result.output
        assert '"normalized_value": "1"' in result.output
        assert '"normalized_value": "0.9155413138"' in result.output
        assert '"normalized_value": "0.0152590219"' in result.output
        assert '"normalized_value": "0.5000076295"' in result.output
        assert '"normalized_value": {"rao": 500000, "tao": 0.0005}' in result.output
        assert '"owner_settable": true' in result.output
        assert '"owner_settable": false' in result.output
        assert '"docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#commitrevealperiod"' in result.output
        assert '"docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#yuma3"' in result.output
        assert '"netuid"' not in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

        assert result.output.count('"hyperparameter":') == 13

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_json_leaves_unexpected_payload_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[{"tempo": 10}]\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '[{"tempo": 10}]'
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_text_output_normalizes_from_json_payload(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout=(
                '{"netuid":2,"tempo":10,"max_weights_limit":65535,'
                '"commit_reveal_weights_interval":1,'
                '"min_burn":{"rao":500000,"tao":0.0005},"weights_version":0,'
                '"user_liquidity_enabled":true,"yuma3_enabled":1}\n'
            )
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2"])
        assert result.exit_code == 0
        assert "Subnet Hyperparameters" in result.output
        assert "NETUID: 2 (omron) - Network: local" in result.output
        assert "HYPERPARAMETER" in result.output
        assert "commit_reveal_period" in result.output
        assert "0.000500000 τ" in result.output
        assert "COMPLICATED (Owner/Sudo)" in result.output
        assert "Tip: Use btcli sudo set --param <name> --value <value> to modify hyperparameters." in result.output
        assert "Tip: To set custom hyperparameters not in this list, use the exact parameter name from the chain metadata." in result.output
        assert "Example: btcli sudo set --netuid 2 --param custom_param_name --value 123" in result.output
        assert "For detailed documentation, visit: https://docs.bittensor.com" in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_text_output_falls_back_when_json_parse_fails(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Hyperparameters for SN2\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2"])
        assert result.exit_code == 0
        assert result.output == "Hyperparameters for SN2\n"
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_text_output_keeps_explicit_non_json_passthrough(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tempo":10}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--output", "table"])
        assert result.exit_code == 0
        assert result.output == '{"tempo":10}\n'
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "table"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_json_normalizes_burn_value_and_normalized_value(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"min_burn":{"rao":500000,"tao":0.0005}}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--json-output"])
        assert result.exit_code == 0
        assert '"hyperparameter": "min_burn"' in result.output
        assert '"value": 500000' in result.output
        assert '"normalized_value": {"rao": 500000, "tao": 0.0005}' in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_json_reuses_explicit_json_output_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tempo":10}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--output", "json"])
        assert result.exit_code == 0
        assert '"hyperparameter": "tempo"' in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_prompt_flag_text_path_still_forces_json_runner_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tempo":10}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--prompt"])
        assert result.exit_code == 0
        assert "Subnet Hyperparameters" in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_no_prompt_flag_text_path_still_forces_json_runner_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tempo":10}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--no-prompt"])
        assert result.exit_code == 0
        assert "Subnet Hyperparameters" in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--yes", "--output", "json"],
            check=False,
            capture=True,
        )


    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_output_json_flag_normalizes_schema(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tempo":10}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--output", "json"])
        assert result.exit_code == 0
        assert '"hyperparameter": "tempo"' in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_sudo_get_non_json_output_is_not_normalized(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tempo":10}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["sudo", "get", "--netuid", "2", "--output", "table"])
        assert result.exit_code == 0
        assert result.output == '{"tempo":10}\n'
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "table"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_axon_reset_alias_rewrites_to_serve_reset(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="reset\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["axon", "reset", "--netuid", "1"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(["serve", "reset", "--netuid", "1"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_axon_set_normalizes_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "axon",
                "set",
                "--netuid",
                "1",
                "--ip",
                "1.2.3.4",
                "--port",
                "8091",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "serve",
                "axon",
                "--netuid",
                "1",
                "--ip",
                "1.2.3.4",
                "--port",
                "8091",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_axon_reset_normalizes_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "axon",
                "reset",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "serve",
                "reset",
                "--netuid",
                "1",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_axon_set_rejects_unsupported_wait_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["axon", "set", "--wait-for-inclusion"])
        assert result.exit_code == 1
        assert "axon set flag '--wait-for-inclusion'" in result.output
        assert "not implemented in taocli yet" in result.output

    def test_btcli_axon_set_rejects_unsupported_ip_type_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["axon", "set", "--ip-type", "6"])
        assert result.exit_code == 1
        assert "axon set flag '--ip-type'" in result.output
        assert "IP family selection" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_update_cap_rewrites_to_variant(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="updated\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["crowd", "update", "--crowdloan-id", "7", "--cap", "42"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["crowdloan", "update-cap", "--crowdloan-id", "7", "--cap", "42"],
            check=False,
            capture=True,
        )

    def test_btcli_crowd_update_requires_field_selector(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "update", "--crowdloan-id", "7"])
        assert result.exit_code == 2
        assert "needs one of --cap, --end/--end-block, or --min-contribution" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_list_maps_json_output_and_no_prompt(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"items": []}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["crowd", "list", "--json-output", "--no-prompt"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["crowdloan", "list", "--output", "json", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_info_maps_wallet_flags_and_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"success": false}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "crowd",
                "info",
                "--crowdloan-id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "crowdloan",
                "info",
                "--crowdloan-id",
                "7",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_contributors_maps_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"success": true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["crowd", "contributors", "--crowdloan-id", "7", "--json-output"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["crowdloan", "contributors", "--crowdloan-id", "7", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_create_maps_wallet_target_and_json_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"created": true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "crowd",
                "create",
                "--deposit",
                "10",
                "--min-contribution",
                "1",
                "--cap",
                "1000",
                "--end-block",
                "500",
                "--target-address",
                "5target",
                "--proxy",
                "5proxy",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "crowdloan",
                "create",
                "--deposit",
                "10",
                "--min-contribution",
                "1",
                "--cap",
                "1000",
                "--end-block",
                "500",
                "--target",
                "5target",
                "--proxy",
                "5proxy",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_contribute_maps_id_wallet_and_json_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok": true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "crowd",
                "contribute",
                "--id",
                "7",
                "--amount",
                "12.5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "crowdloan",
                "contribute",
                "--crowdloan-id",
                "7",
                "--amount",
                "12.5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_refund_maps_id_wallet_and_json_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok": true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "crowd",
                "refund",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "crowdloan",
                "refund",
                "--crowdloan-id",
                "7",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_withdraw_maps_id_wallet_and_json_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok": true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "crowd",
                "withdraw",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "crowdloan",
                "withdraw",
                "--crowdloan-id",
                "7",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_finalize_maps_id_wallet_and_json_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok": true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "crowd",
                "finalize",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "crowdloan",
                "finalize",
                "--crowdloan-id",
                "7",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_dissolve_maps_id_wallet_and_json_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok": true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "crowd",
                "dissolve",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "crowdloan",
                "dissolve",
                "--crowdloan-id",
                "7",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_crowd_list_empty_text_is_normalized_to_btcli_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No crowdloans found.\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["crowd", "list", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == (
            '{"success": true, "error": null, "data": {"crowdloans": [], "total_count": 0, '
            '"total_raised": 0, "total_cap": 0, "total_contributors": 0}}'
        )

    def test_btcli_crowd_list_rejects_unsupported_status_filter(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "list", "--status", "active"])
        assert result.exit_code == 1
        assert "crowd list flag '--status'" in result.output

    def test_btcli_crowd_info_rejects_show_contributors_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "info", "--show-contributors"])
        assert result.exit_code == 1
        assert "crowd info flag '--show-contributors'" in result.output
        assert "crowd contributors" in result.output

    def test_btcli_crowd_contributors_rejects_quiet_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "contributors", "--quiet"])
        assert result.exit_code == 1
        assert "crowd contributors flag '--quiet'" in result.output

    def test_btcli_crowd_create_rejects_unsupported_duration_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "create", "--duration", "100"])
        assert result.exit_code == 1
        assert "crowd create flag '--duration'" in result.output
        assert "absolute --end-block" in result.output

    def test_btcli_crowd_contribute_rejects_unsupported_wait_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "contribute", "--wait-for-inclusion"])
        assert result.exit_code == 1
        assert "crowd contribute flag '--wait-for-inclusion'" in result.output

    def test_btcli_crowd_refund_rejects_unsupported_quiet_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "refund", "--quiet"])
        assert result.exit_code == 1
        assert "crowd refund flag '--quiet'" in result.output

    def test_btcli_crowd_finalize_rejects_unsupported_wait_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "finalize", "--wait-for-finalization"])
        assert result.exit_code == 1
        assert "crowd finalize flag '--wait-for-finalization'" in result.output

    def test_btcli_crowd_dissolve_rejects_unsupported_quiet_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["crowd", "dissolve", "--quiet"])
        assert result.exit_code == 1
        assert "crowd dissolve flag '--quiet'" in result.output

    def test_unsupported_btcli_governance_alias_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["sudo", "senate"])
        assert result.exit_code == 2
        assert "use btcli for governance reads" in result.output

    def test_unsupported_btcli_view_dashboard_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["view", "dashboard"])
        assert result.exit_code == 2
        assert "btcli-compatible `view dashboard` is not implemented in taocli/agcli yet" in result.output
        assert "view network" in result.output
        assert "view portfolio" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_config_get_alias_rewrites_to_config_show(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="current config\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["config", "get"])
        assert result.exit_code == 0
        assert result.output == "current config\n"
        mock_instance.run.assert_called_once_with(["config", "show"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_config_get_alias_drops_prompt_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["config", "get", "--prompt"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(["config", "show"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_config_get_alias_maps_no_prompt_to_yes(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["config", "get", "--no-prompt"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(["config", "show", "--yes"], check=False, capture=True)

    def test_btcli_config_get_rejects_json_output_like_btcli(self, cli_runner):
        result = cli_runner.invoke(main, ["config", "get", "--json-output"])
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output

    @pytest.mark.parametrize(
        "subcommand",
        ["set", "clear", "proxies", "add-proxy", "remove-proxy", "update-proxy", "clear-proxies"],
    )
    def test_unsupported_btcli_config_surfaces_fail_cleanly(self, cli_runner, subcommand):
        result = cli_runner.invoke(main, ["config", subcommand])
        assert result.exit_code == 2
        assert "btcli-compatible `config" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_rao_rewrites_output_like_btcli(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "1000000000"])
        assert result.exit_code == 0
        assert result.output == "1000000000ρ = τ1.000000\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_tao_rewrites_output_like_btcli(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--tao", "1.5"])
        assert result.exit_code == 0
        assert result.output == "τ1.5 = 1500000000ρ\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_handles_both_rao_and_tao_like_btcli(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "1", "--tao", "1"])
        assert result.exit_code == 0
        assert result.output == "1ρ = τ0.000000\nτ1 = 1000000000ρ\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_passthrough_when_not_using_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--amount", "2"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(["utils", "convert", "--amount", "2"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_falls_back_when_value_is_invalid(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="fallback\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--tao", "not-a-number"])
        assert result.exit_code == 0
        assert result.output == "fallback\n"
        mock_instance.run.assert_called_once_with(
            ["utils", "convert", "--amount", "not-a-number", "--to-rao"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_passthrough_when_extra_flags_present(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "5", "--output", "json"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["utils", "convert", "--amount", "5", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_passthrough_when_json_output_requested_indirectly(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "5", "--output", "json"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["utils", "convert", "--amount", "5", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_normalizes_agcli_stdout_when_passthrough_runs(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="1000000000 RAO = 1.000000000 TAO\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "1000000000", "--output", "table"])
        assert result.exit_code == 0
        assert result.output == "1000000000ρ = τ1.000000\n"
        mock_instance.run.assert_called_once_with(
            ["utils", "convert", "--amount", "1000000000", "--output", "table"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_stdout_passthrough_for_unexpected_shape(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="unexpected\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "1000000000", "--output", "table"])
        assert result.exit_code == 0
        assert result.output == "unexpected\n"
        mock_instance.run.assert_called_once_with(
            ["utils", "convert", "--amount", "1000000000", "--output", "table"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_normalizes_tao_stdout_when_passthrough_runs(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="1.5 TAO = 1500000000 RAO\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--tao", "1.5", "--output", "table"])
        assert result.exit_code == 0
        assert result.output == "τ1.5 = 1500000000ρ\n"
        mock_instance.run.assert_called_once_with(
            ["utils", "convert", "--amount", "1.5", "--to-rao", "--output", "table"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_handles_multiple_btcli_flags_in_order(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "1", "--tao", "2.5"])
        assert result.exit_code == 0
        assert result.output == "1ρ = τ0.000000\nτ2.5 = 2500000000ρ\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_handles_decimal_with_trailing_zero(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--tao", "1.0"])
        assert result.exit_code == 0
        assert result.output == "τ1.0 = 1000000000ρ\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_handles_zero_rao(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "0"])
        assert result.exit_code == 0
        assert result.output == "0ρ = τ0.000000\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_handles_zero_tao(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--tao", "0"])
        assert result.exit_code == 0
        assert result.output == "τ0 = 0ρ\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_handles_negative_tao_via_builtin_format(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--tao", "-1.5"])
        assert result.exit_code == 0
        assert result.output == "τ-1.5 = -1500000000ρ\n"
        mock_instance.run.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_convert_handles_negative_rao_via_builtin_format(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "convert", "--rao", "-1"])
        assert result.exit_code == 0
        assert result.output == "-1ρ = τ-0.000000\n"
        mock_instance.run.assert_not_called()

    def test_btcli_utils_convert_without_amount_matches_btcli_message(self, cli_runner):
        result = cli_runner.invoke(main, ["utils", "convert"])
        assert result.exit_code == 0
        assert result.stderr == "❌ Specify `--rao` and/or `--tao`.\n"
        assert result.output == result.stderr

    def test_btcli_utils_convert_rejects_json_output_like_btcli(self, cli_runner):
        result = cli_runner.invoke(main, ["utils", "convert", "--json-output"])
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_utils_latency_network_rewrites_to_extra(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="latency\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["utils", "latency", "--network", "ws://127.0.0.1:9944"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["utils", "latency", "--extra", "ws://127.0.0.1:9944"], check=False, capture=True
        )

    def test_btcli_utils_latency_rejects_json_output_like_btcli(self, cli_runner):
        result = cli_runner.invoke(main, ["utils", "latency", "--json-output"])
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_proxy_create_rewrites_to_create_pure(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="created\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "proxy",
                "create",
                "--proxy-type",
                "Any",
                "--delay",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "proxy",
                "create-pure",
                "--proxy-type",
                "any",
                "--delay",
                "5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "32",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_proxy_add_rewrites_supported_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="added\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "proxy",
                "add",
                "--delegate",
                "5abc",
                "--proxy-type",
                "SmallTransfer",
                "--delay",
                "3",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "proxy",
                "add",
                "--delegate",
                "5abc",
                "--proxy-type",
                "small_transfer",
                "--delay",
                "3",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_proxy_remove_all_rewrites_to_remove_all(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="removed\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["proxy", "remove", "--all", "--wallet-name", "alice", "--no-prompt"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["proxy", "remove-all", "--wallet", "alice", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_proxy_kill_rewrites_to_kill_pure(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="killed\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "proxy",
                "kill",
                "--height",
                "10",
                "--ext-index",
                "2",
                "--spawner",
                "5spawn",
                "--proxy-type",
                "RootWeights",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "proxy",
                "kill-pure",
                "--height",
                "10",
                "--ext-index",
                "2",
                "--spawner",
                "5spawn",
                "--proxy-type",
                "root_weights",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_proxy_execute_fails_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["proxy", "execute", "--call-hash", "0x1234"])
        assert result.exit_code == 2
        assert "proxy execute" in result.output
        assert "call-hash/call-hex" in result.output

    def test_btcli_liquidity_list_fails_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["liquidity", "list", "--netuid", "1"])
        assert result.exit_code == 2
        assert "liquidity list" in result.output
        assert "not a matching liquidity list command" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_liquidity_add_normalizes_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "liquidity",
                "add",
                "--netuid",
                "2",
                "--liquidity",
                "1.5",
                "--price-low",
                "100",
                "--price-high",
                "200",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "liquidity",
                "add",
                "--netuid",
                "2",
                "--amount",
                "1500000000",
                "--price-low",
                "100",
                "--price-high",
                "200",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_liquidity_modify_normalizes_liquidity_delta(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "liquidity",
                "modify",
                "--netuid",
                "2",
                "--position-id",
                "7",
                "--liquidity-delta",
                "0.25",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "liquidity",
                "modify",
                "--netuid",
                "2",
                "--position-id",
                "7",
                "--delta",
                "250000000",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_liquidity_remove_normalizes_wallet_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "liquidity",
                "remove",
                "--netuid",
                "2",
                "--position-id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "liquidity",
                "remove",
                "--netuid",
                "2",
                "--position-id",
                "7",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_liquidity_add_rejects_proxy_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["liquidity", "add", "--proxy", "5abc"])
        assert result.exit_code == 1
        assert "liquidity add" in result.output
        assert "proxy execution path" in result.output

    def test_btcli_liquidity_remove_rejects_all_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["liquidity", "remove", "--all"])
        assert result.exit_code == 1
        assert "liquidity remove" in result.output
        assert "explicit --position-id" in result.output

    def test_btcli_liquidity_modify_rejects_invalid_liquidity_delta(self, cli_runner):
        result = cli_runner.invoke(main, ["liquidity", "modify", "--liquidity-delta", "not-a-number"])
        assert result.exit_code == 1
        assert "Invalid btcli liquidity amount 'not-a-number'" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_dry_run_banner_is_reordered_after_leading_summary_line(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout=(
                "Adding liquidity on SN2: range [0.100000, 10.000000] (ticks [-23027, 23027]), amount=2 RAO\n"
                '{"dry_run":true,"signer":"5abc","call_data_hex":"0x1234","call_data_len":2}\n'
                "Liquidity added on SN2: 2 RAO in range [0.100000, 10.000000].\n"
                "  Tx: dry-run\n"
            ),
            stderr='[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n',
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["liquidity", "add", "--netuid", "2", "--amount", "2", "--output", "json"])
        assert result.exit_code == 0
        assert result.stderr == ""
        assert result.stdout == (
            "Adding liquidity on SN2: range [0.100000, 10.000000] (ticks [-23027, 23027]), amount=2 RAO\n"
            '[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n'
            '{"dry_run":true,"signer":"5abc","call_data_hex":"0x1234","call_data_len":2}\n'
            "Liquidity added on SN2: 2 RAO in range [0.100000, 10.000000].\n"
            "  Tx: dry-run\n"
        )
        assert result.output == result.stdout

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_dry_run_banner_stays_separate_when_stdout_is_only_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"dry_run":true,"signer":"5abc","call_data_hex":"0x1234","call_data_len":2}\n',
            stderr='[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n',
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["liquidity", "add", "--netuid", "2", "--amount", "2", "--output", "json"])
        assert result.exit_code == 0
        assert result.stderr == "[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n"
        assert result.stdout == '{"dry_run":true,"signer":"5abc","call_data_hex":"0x1234","call_data_len":2}\n'
        assert result.output == (
            '{"dry_run":true,"signer":"5abc","call_data_hex":"0x1234","call_data_len":2}\n'
            '[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n'
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_non_matching_stdout_stderr_order_is_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"ok":true}\n',
            stderr='warning\n',
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["liquidity", "add", "--netuid", "2", "--amount", "2", "--output", "json"])
        assert result.exit_code == 0
        assert result.stdout == '{"ok":true}\n'
        assert result.stderr == 'warning\n'
        assert result.output == '{"ok":true}\nwarning\n'

        mock_instance.run.return_value = make_completed_process(
            stdout='plain text\n',
            stderr='[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n',
        )
        result = cli_runner.invoke(main, ["liquidity", "add", "--netuid", "2", "--amount", "2", "--output", "json"])
        assert result.exit_code == 0
        assert result.stdout == 'plain text\n'
        assert result.stderr == '[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n'
        assert result.output == 'plain text\n[dry-run] Transaction would be submitted by 5abc (2 bytes call data)\n'

        mock_instance.run.assert_called_with(
            ["liquidity", "add", "--netuid", "2", "--amount", "2", "--output", "json"],
            check=False,
            capture=True,
        )

    def test_btcli_proxy_create_rejects_unsupported_wait_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["proxy", "create", "--wait-for-inclusion"])
        assert result.exit_code == 1
        assert "wait-for-inclusion" in result.output
        assert "not implemented in taocli yet" in result.output

    def test_btcli_proxy_create_rejects_unsupported_wait_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["proxy", "create", "--wait-for-inclusion"])
        assert result.exit_code == 1
        assert "wait-for-inclusion" in result.output
        assert "not implemented in taocli yet" in result.output

    def test_btcli_proxy_rejects_unsupported_proxy_type(self, cli_runner):
        result = cli_runner.invoke(main, ["proxy", "add", "--proxy-type", "NonFungible"])
        assert result.exit_code == 1
        assert "proxy type 'NonFungible'" in result.output

    def test_btcli_proxy_remove_all_rejects_delegate_specific_flags(self, cli_runner):
        result = cli_runner.invoke(main, ["proxy", "remove", "--all", "--delegate", "5abc"])
        assert result.exit_code == 1
        assert "remove --all" in result.output
        assert "--delegate" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_get_identity_alias_passes_through(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "get-identity", "--netuid", "1", "--output", "json"])
        assert result.exit_code == 0
        assert result.output.strip() == "{}"
        mock_instance.run.assert_called_once_with(
            ["subnet", "get-identity", "--netuid", "1", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_set_identity_alias_maps_supported_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "set-identity",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--subnet-name",
                "MySubnet",
                "--github-repo",
                "https://github.com/example/repo",
                "--subnet-url",
                "https://example.com",
                "--json-output",
                "--no-prompt",
            ],
        )

        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "identity",
                "set-subnet",
                "--netuid",
                "1",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "miner",
                "--name",
                "MySubnet",
                "--github",
                "https://github.com/example/repo",
                "--url",
                "https://example.com",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_subnets_set_identity_json_output_conflicts_with_default_prompt(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "set-identity", "--netuid", "1", "--json-output"])
        assert result.exit_code == 1
        assert "Cannot specify both '--json-output' and '--prompt'" in result.output

    def test_btcli_subnets_set_identity_rejects_unsupported_subnet_contact_field(self, cli_runner):
        result = cli_runner.invoke(
            main,
            ["subnets", "set-identity", "--netuid", "1", "--subnet-name", "test", "--subnet-contact", "team@example.com"],
        )
        assert result.exit_code == 1
        assert "subnets set-identity" in result.output
        assert "subnet-contact metadata" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_set_identity_missing_name_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --name <NAME>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "set-identity", "--netuid", "1", "--no-prompt"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(
            ["identity", "set-subnet", "--netuid", "1", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_alias_maps_json_output_and_no_prompt(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"netuid":2,"name":"fresh","tempo":12,"burn":{"rao":123000},"owner":"5owner"}\n'),
            make_completed_process(stdout='[{"netuid":2,"name":"fresh","tao_in":{"rao":2000000000},"alpha_in":{"raw":1000000000},"tao_in_emission":{"rao":100000000},"tempo":12,"blocks_since_last_step":3}]\n'),
            make_completed_process(stdout='{"netuid":2,"neurons":[{"uid":0,"stake_tao":1.5,"dividends":0.25,"incentive":0.5,"emission":0.125,"hotkey":"5hot","coldkey":"5owner"}]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "show", "--netuid", "2", "--json-output", "--no-prompt"])
        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "netuid": 2,
            "mechanism_id": 0,
            "mechanism_count": 1,
            "name": ": fresh",
            "owner": "5owner",
            "owner_identity": "",
            "rate": 0.0,
            "emission": 0.1,
            "tao_pool": 2.0,
            "alpha_pool": 1.0,
            "tempo": {"block_since_last_step": 3, "tempo": 12},
            "registration_cost": 0.000123,
            "uids": [
                {
                    "uid": 0,
                    "stake": 1.5,
                    "alpha_stake": 1.5,
                    "tao_stake": 0.0,
                    "dividends": 0.25,
                    "incentive": 0.5,
                    "emissions": 0.125,
                    "hotkey": "5hot",
                    "coldkey": "5owner",
                    "identity": "[dark_sea_green3](*Owner controlled)[/dark_sea_green3]",
                    "claim_type": None,
                    "claim_type_subnets": None,
                }
            ],
        }
        assert mock_instance.run.call_args_list == [
            call(["subnet", "show", "--netuid", "2", "--output", "json", "--yes"], check=False, capture=True),
            call(["view", "dynamic", "--output", "json"], check=False, capture=True),
            call(["view", "metagraph", "--netuid", "2", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_json_output_falls_back_when_extra_queries_fail(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"netuid":2,"name":"fresh","tempo":12,"burn":{"rao":123000},"owner":"5owner"}\n'),
            make_completed_process(stdout='not-json\n'),
            make_completed_process(stdout='also-not-json\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "show", "--netuid", "2", "--json-output", "--no-prompt"])
        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "netuid": 2,
            "mechanism_id": 0,
            "mechanism_count": 1,
            "name": ": fresh",
            "owner": "5owner",
            "owner_identity": "",
            "rate": 0.0,
            "emission": 0.0,
            "tao_pool": 0.0,
            "alpha_pool": 0.0,
            "tempo": {"block_since_last_step": None, "tempo": 12},
            "registration_cost": 0.000123,
            "uids": [],
        }

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_json_output_leaves_non_json_stdout_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='subnet 2\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "show", "--netuid", "2", "--json-output", "--no-prompt"])
        assert result.exit_code == 0
        assert result.output == 'subnet 2\n'
        mock_instance.run.assert_called_once_with(
            ["subnet", "show", "--netuid", "2", "--output", "json", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_text_output_renders_btcli_style_summary(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"netuid":2,"name":"fresh","tempo":12,"burn":{"rao":123000},"owner":"5owner"}\n'),
            make_completed_process(stdout='[{"netuid":2,"name":"fresh","tao_in":{"rao":2000000000},"alpha_in":{"raw":1000000000},"tao_in_emission":{"rao":100000000},"tempo":12,"blocks_since_last_step":3}]\n'),
            make_completed_process(stdout='{"netuid":2,"neurons":[{"uid":0,"stake_tao":1.5,"dividends":0.25,"incentive":0.5,"emission":0.125,"hotkey":"5hot","coldkey":"5owner"}]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "show", "--network", "local", "--netuid", "2", "--no-prompt"])
        assert result.exit_code == 0
        assert "Warning: Verify your local subtensor is running on port 9944." in result.output
        assert "Subnet 2: fresh" in result.output
        assert "Mechanism 0/1" in result.output
        assert "UID | Stake | Alpha stake | TAO stake | Dividends | Incentive | Emissions | Hotkey | Coldkey | Identity" in result.output
        assert "0 | 1.5000 | 1.5000 | 0.0000 | 0.2500 | 0.5000 | 0.1250 | 5hot | 5owner | [dark_sea_green3](*Owner controlled)[/dark_sea_green3]" in result.output
        assert "Owner: 5owner" in result.output
        assert "Rate: 0.0000" in result.output
        assert "Emission: 0.1000" in result.output
        assert "TAO Pool: τ 2.0000" in result.output
        assert "Alpha Pool: α 1.0000" in result.output
        assert "Tempo: 12 (3 blocks ago)" in result.output
        assert "Registration cost: τ 0.000123" in result.output
        assert "Neurons: 1" in result.output
        assert mock_instance.run.call_args_list == [
            call(["subnet", "show", "--network", "local", "--netuid", "2", "--yes", "--output", "json"], check=False, capture=True),
            call(["view", "dynamic", "--network", "local", "--output", "json"], check=False, capture=True),
            call(["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_text_output_falls_back_when_primary_stdout_is_not_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='subnet summary\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "show", "--netuid", "2", "--no-prompt"])
        assert result.exit_code == 0
        assert result.output == 'subnet summary\n'
        mock_instance.run.assert_called_once_with(
            ["subnet", "show", "--netuid", "2", "--yes", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_json_output_preserves_context_flags_on_extra_queries(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"netuid":4,"name":"ctx","tempo":9,"burn":{"rao":500000},"owner":"5ctx"}\n'),
            make_completed_process(stdout='[]\n'),
            make_completed_process(stdout='{"netuid":4,"neurons":[]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["subnets", "show", "--network", "local", "--at-block", "123", "--netuid", "4", "--json-output", "--no-prompt"],
        )
        assert result.exit_code == 0
        assert mock_instance.run.call_args_list == [
            call(["subnet", "show", "--network", "local", "--at-block", "123", "--netuid", "4", "--output", "json", "--yes"], check=False, capture=True),
            call(["view", "dynamic", "--network", "local", "--at-block", "123", "--output", "json"], check=False, capture=True),
            call(["view", "metagraph", "--netuid", "4", "--network", "local", "--at-block", "123", "--output", "json"], check=False, capture=True),
        ]


    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_json_output_uses_zero_defaults_for_missing_optional_fields(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"netuid":7,"owner":"5owner"}\n'),
            make_completed_process(stdout='[{"netuid":7}]\n'),
            make_completed_process(stdout='{"netuid":7,"neurons":[{"uid":1,"hotkey":"5hot","coldkey":"5cold"}]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "show", "--netuid", "7", "--json-output", "--no-prompt"])
        assert result.exit_code == 0
        assert json.loads(result.output) == {
            "netuid": 7,
            "mechanism_id": 0,
            "mechanism_count": 1,
            "name": "",
            "owner": "5owner",
            "owner_identity": "",
            "rate": 0.0,
            "emission": 0.0,
            "tao_pool": 0.0,
            "alpha_pool": 0.0,
            "tempo": {"block_since_last_step": None, "tempo": None},
            "registration_cost": 0.0,
            "uids": [
                {
                    "uid": 1,
                    "stake": 0.0,
                    "alpha_stake": 0.0,
                    "tao_stake": 0.0,
                    "dividends": 0.0,
                    "incentive": 0.0,
                    "emissions": 0.0,
                    "hotkey": "5hot",
                    "coldkey": "5cold",
                    "identity": "",
                    "claim_type": None,
                    "claim_type_subnets": None,
                }
            ],
        }

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_set_symbol_alias_maps_positional_symbol_and_wallet_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "set-symbol",
                "--netuid",
                "2",
                "シ",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "set-symbol",
                "--netuid",
                "2",
                "--symbol",
                "シ",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_subnets_check_start_rejects_json_output_like_btcli(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "check-start", "--netuid", "5", "--json-output"])
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_check_start_alias_maps_no_prompt_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"can_start":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "check-start", "--netuid", "5", "--no-prompt"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"can_start":true}'
        mock_instance.run.assert_called_once_with(
            ["subnet", "check-start", "--netuid", "5", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_check_start_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "check-start"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(
            ["subnet", "check-start"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_check_start_success_rewrites_btcli_style_text(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout="SN1 is already active (emissions running)\n"),
            make_completed_process(
                stdout='[{"netuid":1,"network_registered_at":0}]\n'
            ),
            make_completed_process(stdout='{"block":178913}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "check-start", "--network", "local", "--netuid", "1", "--no-prompt"])

        assert result.exit_code == 0
        assert result.output == (
            "Warning: Verify your local subtensor is running on port 9944.\n\n"
            "Subnet 1:\n"
            "Registered at: 0\n"
            "Current block: 178913\n"
            "Minimum start block: 0\n"
            "Emission schedule can be started\n"
        )
        assert mock_instance.run.call_args_list == [
            call(["subnet", "check-start", "--network", "local", "--netuid", "1", "--yes"], check=False, capture=True),
            call(["view", "dynamic", "--network", "local", "--output", "json"], check=False, capture=True),
            call(["view", "network", "--network", "local", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_check_start_success_falls_back_when_auxiliary_reads_fail(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout="SN2 is already active (emissions running)\n"),
            make_completed_process(stdout="not-json\n"),
            make_completed_process(stdout="also-not-json\n"),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "check-start", "--netuid", "2", "--no-prompt"])

        assert result.exit_code == 0
        assert result.output == "SN2 is already active (emissions running)\n"
        assert mock_instance.run.call_args_list == [
            call(["subnet", "check-start", "--netuid", "2", "--yes"], check=False, capture=True),
            call(["view", "dynamic", "--output", "json"], check=False, capture=True),
            call(["view", "network", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_check_start_success_preserves_context_flags_on_auxiliary_reads(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout="SN4 is already active (emissions running)\n"),
            make_completed_process(stdout='[{"netuid":4,"network_registered_at":12}]\n'),
            make_completed_process(stdout='{"block":456}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            ["subnets", "check-start", "--network", "local", "--at-block", "123", "--netuid", "4", "--no-prompt"],
        )

        assert result.exit_code == 0
        assert result.output == (
            "Warning: Verify your local subtensor is running on port 9944.\n\n"
            "Subnet 4:\n"
            "Registered at: 12\n"
            "Current block: 456\n"
            "Minimum start block: 12\n"
            "Emission schedule can be started\n"
        )
        assert mock_instance.run.call_args_list == [
            call(["subnet", "check-start", "--network", "local", "--at-block", "123", "--netuid", "4", "--yes"], check=False, capture=True),
            call(["view", "dynamic", "--network", "local", "--at-block", "123", "--output", "json"], check=False, capture=True),
            call(["view", "network", "--network", "local", "--at-block", "123", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_create_alias_maps_identity_and_wallet_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"created":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "create",
                "--subnet-name",
                "test-subnet",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--proxy",
                "5proxy",
                "--repo",
                "https://github.com/unarbos/test-subnet",
                "--subnet-contact",
                "ops@example.com",
                "--url",
                "https://example.com",
                "--discord-handle",
                "discord.gg/example",
                "--description",
                "test subnet",
                "--additional-info",
                "extra context",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"created":true}'
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "register-with-identity",
                "--name",
                "test-subnet",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--proxy",
                "5proxy",
                "--github",
                "https://github.com/unarbos/test-subnet",
                "--contact",
                "ops@example.com",
                "--url",
                "https://example.com",
                "--discord",
                "discord.gg/example",
                "--description",
                "test subnet",
                "--additional",
                "extra context",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_alias_maps_wallet_json_prompt_and_proxy_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"started":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "start",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--proxy",
                "5proxy",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"started":true}'
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "start",
                "--netuid",
                "5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--proxy",
                "5proxy",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_count_alias_maps_json_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"count":2}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["subnets", "mechanisms", "count", "--netuid", "5", "--json-output", "--no-prompt"],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"count":2}'
        mock_instance.run.assert_called_once_with(
            ["subnet", "mechanism-count", "--netuid", "5", "--output", "json", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_set_alias_maps_wallet_count_json_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "mechanisms",
                "set",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--mech-count",
                "3",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"ok":true}'
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "set-mechanism-count",
                "--netuid",
                "5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--count",
                "3",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_emissions_alias_maps_json_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"split":[50,50]}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["subnets", "mechanisms", "emissions", "--netuid", "5", "--json-output", "--no-prompt"],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"split":[50,50]}'
        mock_instance.run.assert_called_once_with(
            ["subnet", "emission-split", "--netuid", "5", "--output", "json", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_split_emissions_alias_maps_wallet_split_json_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "mechanisms",
                "split-emissions",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--split",
                "60,40",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"ok":true}'
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "set-emission-split",
                "--netuid",
                "5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--weights",
                "60,40",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_count_success_rewrites_btcli_style_text(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"count":1}\n')
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "count", "--network", "local", "--netuid", "1", "--no-prompt"])

        assert result.exit_code == 0
        assert result.output == (
            "Warning: Verify your local subtensor is running on port 9944.\n\n"
            "Subnet 1 currently has 1 mechanism.\n"
            "(Tip: 1 mechanism means there are no mechanisms beyond the main subnet)\n"
        )
        mock_instance.run.assert_called_once_with(
            ["subnet", "mechanism-count", "--network", "local", "--netuid", "1", "--yes", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_emissions_success_rewrites_btcli_style_text(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"configured":false,"message":"No emission split configured (using default)","netuid":1}\n'),
            make_completed_process(stdout='{"count":1}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "emissions", "--network", "local", "--netuid", "1", "--no-prompt"])

        assert result.exit_code == 0
        assert result.output == (
            "Warning: Verify your local subtensor is running on port 9944.\n\n"
            "Subnet 1 only has the primary mechanism (mechanism 0). No emission split to display.\n"
        )
        assert mock_instance.run.call_args_list == [
            call(["subnet", "emission-split", "--network", "local", "--netuid", "1", "--yes", "--output", "json"], check=False, capture=True),
            call(["subnet", "mechanism-count", "--netuid", "1", "--network", "local", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_count_success_falls_back_when_stdout_is_not_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="SN1 mechanism count: 1\n")
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "count", "--netuid", "1", "--no-prompt"])

        assert result.exit_code == 0
        assert result.output == "SN1 mechanism count: 1\n"
        mock_instance.run.assert_called_once_with(
            ["subnet", "mechanism-count", "--netuid", "1", "--yes", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_emissions_success_falls_back_when_payload_and_count_lookup_do_not_help(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"weights":[100]}\n'),
            make_completed_process(stdout='not-json\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "emissions", "--netuid", "1", "--no-prompt"])

        assert result.exit_code == 0
        assert result.output == '{"weights":[100]}\n'
        assert mock_instance.run.call_args_list == [
            call(["subnet", "emission-split", "--netuid", "1", "--yes", "--output", "json"], check=False, capture=True),
            call(["subnet", "mechanism-count", "--netuid", "1", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_emissions_success_uses_count_lookup_without_local_warning(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"configured":false,"message":"No emission split configured (using default)","netuid":7}\n'),
            make_completed_process(stdout='{"count":1}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "emissions", "--netuid", "7", "--no-prompt"])

        assert result.exit_code == 0
        assert result.output == "Subnet 7 only has the primary mechanism (mechanism 0). No emission split to display.\n"
        assert mock_instance.run.call_args_list == [
            call(["subnet", "emission-split", "--netuid", "7", "--yes", "--output", "json"], check=False, capture=True),
            call(["subnet", "mechanism-count", "--netuid", "7", "--output", "json"], check=False, capture=True),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_emissions_success_preserves_context_flags_on_count_lookup(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(stdout='{"configured":false,"message":"No emission split configured (using default)","netuid":4}\n'),
            make_completed_process(stdout='{"count":1}\n'),
        ]
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "emissions", "--network", "local", "--at-block", "123", "--netuid", "4", "--no-prompt"])

        assert result.exit_code == 0
        assert mock_instance.run.call_args_list == [
            call(["subnet", "emission-split", "--network", "local", "--at-block", "123", "--netuid", "4", "--yes", "--output", "json"], check=False, capture=True),
            call(["subnet", "mechanism-count", "--netuid", "4", "--network", "local", "--at-block", "123", "--output", "json"], check=False, capture=True),
        ]
        assert "Subnet 4 only has the primary mechanism" in result.output

    def test_btcli_subnets_create_rejects_unsupported_logo_url_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--logo-url", "https://example.com/logo.png"])
        assert result.exit_code == 1
        assert "subnets create flag '--logo-url'" in result.output
        assert "logo URL metadata" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_create_missing_name_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --name <NAME>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "create"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["subnet", "register-with-identity"], check=False, capture=True)

    def test_btcli_subnets_create_requires_subnet_name(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--subnet-name' requires a value" in result.output

    def test_btcli_subnets_create_json_output_conflicts_with_default_prompt(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--json-output"])
        assert result.exit_code == 1
        assert "Cannot specify both '--json-output' and '--prompt'" in result.output


    def test_btcli_subnets_create_requires_proxy_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--proxy"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--proxy' requires a value" in result.output

    def test_btcli_subnets_create_rejects_mev_protection_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--mev-protection"])
        assert result.exit_code == 1
        assert "subnets create flag '--mev-protection'" in result.output
        assert "MEV-protection toggles" in result.output

    def test_btcli_subnets_create_rejects_announce_only_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--announce-only"])
        assert result.exit_code == 1
        assert "subnets create flag '--announce-only'" in result.output
        assert "announce-only proxy submission" in result.output

    def test_btcli_subnets_create_rejects_verbose_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--verbose"])
        assert result.exit_code == 1
        assert "subnets create flag '--verbose'" in result.output
        assert "verbose-mode output expansion" in result.output

    def test_btcli_subnets_create_rejects_no_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--no"])
        assert result.exit_code == 1
        assert "subnets create flag '--no'" in result.output
        assert "automatic-decline prompts" in result.output

    def test_btcli_subnets_create_rejects_quiet_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--quiet"])
        assert result.exit_code == 1
        assert "subnets create flag '--quiet'" in result.output
        assert "quiet-mode output suppression" in result.output

    def test_btcli_subnets_create_rejects_no_mev_protection_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--no-mev-protection"])
        assert result.exit_code == 1
        assert "subnets create flag '--no-mev-protection'" in result.output
        assert "MEV-protection toggles" in result.output

    def test_btcli_subnets_create_rejects_no_announce_only_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--no-announce-only"])
        assert result.exit_code == 1
        assert "subnets create flag '--no-announce-only'" in result.output
        assert "announce-only proxy submission" in result.output

    def test_btcli_subnets_create_requires_subnet_name_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--subnet-name' requires a value" in result.output

    def test_btcli_subnets_create_requires_repo_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--repo"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--repo' requires a value" in result.output

    def test_btcli_subnets_create_requires_url_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--url"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--url' requires a value" in result.output

    def test_btcli_subnets_create_requires_description_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--description"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--description' requires a value" in result.output

    def test_btcli_subnets_create_requires_additional_info_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--additional-info"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--additional-info' requires a value" in result.output

    def test_btcli_subnets_create_requires_wallet_name_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--wallet-name"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--wallet-name' requires a value" in result.output

    def test_btcli_subnets_create_requires_hotkey_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--hotkey"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--hotkey' requires a value" in result.output

    def test_btcli_subnets_create_requires_wallet_path_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--wallet-path"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--wallet-path' requires a value" in result.output

    def test_btcli_subnets_create_requires_subnet_contact_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--subnet-contact"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--subnet-contact' requires a value" in result.output

    def test_btcli_subnets_create_requires_discord_handle_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--discord-handle"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--discord-handle' requires a value" in result.output

    def test_btcli_subnets_create_requires_github_repo_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--github-repo"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--github-repo' requires a value" in result.output

    def test_btcli_subnets_create_requires_subnet_url_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--subnet-url"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--subnet-url' requires a value" in result.output

    def test_btcli_subnets_create_rejects_logo_url_without_value_too(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--logo-url"])
        assert result.exit_code == 1
        assert "subnets create flag '--logo-url'" in result.output
        assert "logo URL metadata" in result.output

    def test_btcli_subnets_create_requires_json_output_still_needs_subnet_name(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--json-output", "--no-prompt", "--subnet-name"])
        assert result.exit_code == 1
        assert "subnets create" in result.output
        assert "flag '--subnet-name' requires a value" in result.output

    def test_btcli_subnets_create_json_output_no_prompt_missing_name_rewrites_to_wallet_prompt_abort(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--json-output", "--no-prompt"])
        assert result.exit_code == 1
        assert "Cannot specify both '--json-output' and '--prompt'" not in result.output
        assert "agcli binary not found" in result.output

    def test_btcli_subnets_create_rejects_logo_url_even_with_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "create", "--subnet-name", "test", "--logo-url", "logo"])
        assert result.exit_code == 1
        assert "subnets create flag '--logo-url'" in result.output

    def test_btcli_subnets_start_rejects_json_output_like_btcli(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "start", "--netuid", "5", "--json-output"])
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_alias_maps_wallet_and_prompt_and_proxy_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='started\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "start",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--proxy",
                "5proxy",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output == 'started\n'
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "start",
                "--netuid",
                "5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--proxy",
                "5proxy",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_preserves_native_json_output_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tx_hash":"0xabc"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "start", "--netuid", "5", "--output", "json", "--no-prompt"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"tx_hash":"0xabc"}'
        mock_instance.run.assert_called_once_with(
            ["subnet", "start", "--netuid", "5", "--output", "json", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_json_output_rejection_wins_over_no_prompt(self, mock_cls, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "start", "--netuid", "5", "--json-output", "--no-prompt"])
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output
        mock_cls.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_json_output_rejection_happens_before_wallet_flag_mapping(self, mock_cls, cli_runner):
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "start",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--proxy",
                "5proxy",
                "--json-output",
            ],
        )
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output
        mock_cls.assert_not_called()

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_accepts_native_output_json_without_btcli_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"tx_hash":"0xdef"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "start",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--output",
                "json",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"tx_hash":"0xdef"}'
        mock_instance.run.assert_called_once_with(
            ["subnet", "start", "--netuid", "5", "--wallet", "alice", "--output", "json", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_alias_maps_wallet_json_prompt_and_proxy_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"started":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "start",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--proxy",
                "5proxy",
                "--output",
                "json",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"started":true}'
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "start",
                "--netuid",
                "5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--proxy",
                "5proxy",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )
    def test_btcli_subnets_start_rejects_announce_only_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "start", "--netuid", "5", "--announce-only"])
        assert result.exit_code == 1
        assert "subnets start flag '--announce-only'" in result.output
        assert "announce-only proxy submission" in result.output

    def test_btcli_subnets_start_requires_proxy_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "start", "--netuid", "5", "--proxy"])
        assert result.exit_code == 1
        assert "subnets start" in result.output
        assert "flag '--proxy' requires a value" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "start"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "start"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_missing_wallet_rewrites_to_btcli_error(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "Wallet 'alice' not found in /tmp/notreal.\n"
                "  Create one with: agcli wallet create --name alice\n"
                "  List existing:   agcli wallet list\n"
                "  To use a different wallet directory set AGCLI_WALLET_DIR.\n"
            ),
            returncode=1,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "start",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/notreal",
                "--hotkey",
                "default",
            ],
        )

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "❌ Error: Wallet does not exist. \n"
            "Please verify your wallet information: Wallet (Name: 'alice', Hotkey: 'default',\n"
            "Path: '/tmp/notreal')\n"
        )
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "start",
                "--netuid",
                "1",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/notreal",
                "--hotkey-name",
                "default",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_password_prompt_failure_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "Cannot prompt for coldkey password: stdin is not a TTY (non-interactive).\n"
                "Use AGCLI_PASSWORD / AGCLI_COLDKEY_PASSWORD or pass --password in batch mode.\n"
            ),
            returncode=1,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "start", "--netuid", "1"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (which you used to create the subnet) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(
            ["subnet", "start", "--netuid", "1"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_password_prompt_failure_preserves_explicit_wallet_path(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "Cannot prompt for coldkey password: stdin is not a TTY (non-interactive).\n"
                "Use AGCLI_PASSWORD / AGCLI_COLDKEY_PASSWORD or pass --password in batch mode.\n"
            ),
            returncode=1,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "start",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
            ],
        )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert "Cannot prompt for coldkey password: stdin is not a TTY" in result.stderr
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "start",
                "--netuid",
                "1",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_password_batch_failure_rewrites_to_not_owner_for_non_owner_wallet(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stderr=(
                    "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD.\n"
                ),
                returncode=1,
            ),
            make_completed_process(stdout='{"netuid":1,"owner":"5owner"}\n'),
        ]
        mock_cls.return_value = mock_instance

        with patch.object(_cli_main_module, "_btcli_wallet_coldkey_ss58", return_value="5alice"):
            result = cli_runner.invoke(
                main,
                [
                    "subnets",
                    "start",
                    "--network",
                    "local",
                    "--netuid",
                    "1",
                    "--wallet-name",
                    "alice",
                    "--wallet-path",
                    "/tmp/wallets",
                    "--hotkey",
                    "default",
                ],
            )

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "❌ This wallet doesn't own the specified subnet.\n"
        assert mock_instance.run.call_args_list == [
            call(
                [
                    "subnet",
                    "start",
                    "--network",
                    "local",
                    "--netuid",
                    "1",
                    "--wallet",
                    "alice",
                    "--wallet-dir",
                    "/tmp/wallets",
                    "--hotkey-name",
                    "default",
                ],
                check=False,
                capture=True,
            ),
            call(
                [
                    "subnet",
                    "show",
                    "--network",
                    "local",
                    "--netuid",
                    "1",
                    "--output",
                    "json",
                ],
                check=False,
                capture=True,
            ),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_start_password_batch_failure_preserves_original_error_for_owner_wallet(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stderr=(
                    "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD.\n"
                ),
                returncode=1,
            ),
            make_completed_process(stdout='{"netuid":1,"owner":"5alice"}\n'),
        ]
        mock_cls.return_value = mock_instance

        with patch.object(_cli_main_module, "_btcli_wallet_coldkey_ss58", return_value="5alice"):
            result = cli_runner.invoke(
                main,
                [
                    "subnets",
                    "start",
                    "--network",
                    "local",
                    "--netuid",
                    "1",
                    "--wallet-name",
                    "alice",
                    "--wallet-path",
                    "/tmp/wallets",
                ],
            )

        assert result.exit_code == 1
        assert result.stdout == ""
        assert result.stderr == (
            "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD.\n"
        )
        assert mock_instance.run.call_args_list == [
            call(
                [
                    "subnet",
                    "start",
                    "--network",
                    "local",
                    "--netuid",
                    "1",
                    "--wallet",
                    "alice",
                    "--wallet-dir",
                    "/tmp/wallets",
                ],
                check=False,
                capture=True,
            ),
            call(
                [
                    "subnet",
                    "show",
                    "--network",
                    "local",
                    "--netuid",
                    "1",
                    "--output",
                    "json",
                ],
                check=False,
                capture=True,
            ),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_show_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "show"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "show"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_count_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "count"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "mechanism-count"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_set_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
                "  --count <COUNT>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "set"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "set-mechanism-count"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_emissions_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "emissions"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "emission-split"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_mechanisms_split_emissions_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
                "  --weights <WEIGHTS>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "mechanisms", "split-emissions"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "set-emission-split"], check=False, capture=True)

    def test_btcli_subnets_mechanisms_count_rejects_quiet_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "mechanisms", "count", "--netuid", "5", "--quiet"])
        assert result.exit_code == 1
        assert "subnets mechanisms count flag '--quiet'" in result.output
        assert "quiet-mode output suppression" in result.output

    def test_btcli_subnets_mechanisms_set_rejects_announce_only_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "mechanisms", "set", "--netuid", "5", "--announce-only"])
        assert result.exit_code == 1
        assert "subnets mechanisms set flag '--announce-only'" in result.output
        assert "announce-only proxy submission" in result.output

    def test_btcli_subnets_mechanisms_set_requires_count_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "mechanisms", "set", "--netuid", "5", "--count"])
        assert result.exit_code == 1
        assert "subnets mechanisms set" in result.output
        assert "flag '--count' requires a value" in result.output

    def test_btcli_subnets_mechanisms_set_rejects_proxy_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "mechanisms", "set", "--netuid", "5", "--proxy"])
        assert result.exit_code == 1
        assert "subnets mechanisms set flag '--proxy'" in result.output
        assert "proxy execution" in result.output

    def test_btcli_subnets_mechanisms_emissions_rejects_verbose_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "mechanisms", "emissions", "--netuid", "5", "--verbose"])
        assert result.exit_code == 1
        assert "subnets mechanisms emissions flag '--verbose'" in result.output
        assert "verbose-mode output expansion" in result.output

    def test_btcli_subnets_mechanisms_split_emissions_rejects_wait_for_inclusion_flag(self, cli_runner):
        result = cli_runner.invoke(
            main,
            ["subnets", "mechanisms", "split-emissions", "--netuid", "5", "--wait-for-inclusion"],
        )
        assert result.exit_code == 1
        assert "subnets mechanisms split-emissions flag '--wait-for-inclusion'" in result.output
        assert "wait-for-inclusion toggles" in result.output

    def test_btcli_subnets_mechanisms_split_emissions_requires_split_value(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "mechanisms", "split-emissions", "--netuid", "5", "--split"])
        assert result.exit_code == 1
        assert "subnets mechanisms split-emissions" in result.output
        assert "flag '--split' requires a value" in result.output

    def test_btcli_subnets_show_rejects_unsupported_mechid_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "show", "--netuid", "2", "--mechid", "1"])
        assert result.exit_code == 1
        assert "subnets show flag '--mechid'" in result.output
        assert "mechanism-id filtering" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_set_symbol_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "set-symbol", "シ"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(
            ["subnet", "set-symbol", "--symbol", "シ"], check=False, capture=True
        )

    def test_btcli_subnets_set_symbol_rejects_proxy_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "set-symbol", "--netuid", "2", "シ", "--proxy", "5abc"])
        assert result.exit_code == 1
        assert "subnets set-symbol flag '--proxy'" in result.output
        assert "proxy execution" in result.output

    def test_btcli_subnets_set_symbol_requires_symbol(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "set-symbol", "--netuid", "2", "--json-output"])
        assert result.exit_code == 1
        assert "requires a subnet symbol" in result.output

    def test_btcli_subnets_set_symbol_rejects_duplicate_symbol_sources(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "set-symbol", "--netuid", "2", "--symbol", "A", "B"])
        assert result.exit_code == 1
        assert "accepts a single symbol value" in result.output

    def test_btcli_subnets_show_rejects_sort_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "show", "--netuid", "2", "--sort", "name"])
        assert result.exit_code == 1
        assert "subnets show flag '--sort'" in result.output
        assert "sorting controls" in result.output

    def test_btcli_subnets_price_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "price", "--netuid", "2"])
        assert result.exit_code == 2
        assert "subnets price" in result.output
        assert "no matching `subnet price` command" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_rewrites_to_balance(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":0,"balance_tao":0.0}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert result.output.strip() == (
            '{"balances": {"Provided Address 1": '
            '{"coldkey": "5abc", "free": 0.0, "staked": 0.0, "total": 0.0}}, '
            '"totals": {"free": 0.0, "staked": 0.0, "total": 0.0}}'
        )
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_renders_btcli_style_text_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":0,"balance_tao":0.0}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--network", "local", "--address", "5abc"])
        assert result.exit_code == 0
        assert "Warning: Verify your local subtensor is running on port 9944." in result.output
        assert "Wallet Coldkey Balance" in result.output
        assert "Network: local" in result.output
        assert "Wallet Name | Coldkey Address | Free Balance | Staked | Total Balance" in result.output
        assert "Provided Address 1 | 5abc | 0.000000000 τ | 0.000000000 τ | 0.000000000 τ" in result.output
        assert "Total Balance |  | 0.000000000 τ | 0.000000000 τ | 0.000000000 τ" in result.output
        mock_instance.run.assert_called_once_with(
            ["balance", "--network", "local", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_leaves_non_json_stdout_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Free balance: 0.0000 τ\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc"])
        assert result.exit_code == 0
        assert result.output == "Free balance: 0.0000 τ\n"
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_leaves_unexpected_json_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"balance_tao": 0.0}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"balance_tao": 0.0}'
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_maps_ss58_flag_to_address(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":0,"balance_tao":0.0}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--ss58", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert '"Provided Address 1"' in result.output
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_maps_json_output_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":0,"balance_tao":0.0}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"totals"' in result.output
        assert "Wallet Coldkey Balance" not in result.output
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_text_output_uses_custom_endpoint_as_chain_context(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":0,"balance_tao":0.0}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--endpoint", "ws://127.0.0.1:9944", "--address", "5abc"])
        assert result.exit_code == 0
        assert "Warning: Verify your local subtensor is running on port 9944." in result.output
        assert "Network: custom" in result.output
        mock_instance.run.assert_called_once_with(
            ["balance", "--endpoint", "ws://127.0.0.1:9944", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_text_output_omits_local_warning_for_non_local_network(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":0,"balance_tao":0.0}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--network", "finney", "--address", "5abc"])
        assert result.exit_code == 0
        assert "Warning: Verify your local subtensor is running on port 9944." not in result.output
        assert "Network: finney" in result.output
        mock_instance.run.assert_called_once_with(
            ["balance", "--network", "finney", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_text_output_falls_back_when_json_parse_fails(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Address: 5abc\nBalance: 0.000000000 τ\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc"])
        assert result.exit_code == 0
        assert result.output == "Address: 5abc\nBalance: 0.000000000 τ\n"
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_text_output_falls_back_for_unexpected_json_shape(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"balance_tao":0.0}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"balance_tao":0.0}'
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_text_output_forces_json_even_with_explicit_table_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":0,"balance_tao":0.0}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc", "--output", "table"])
        assert result.exit_code == 0
        assert "Wallet Coldkey Balance" in result.output
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "table"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_text_output_preserves_numeric_balance(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","balance_rao":1250000000,"balance_tao":1.25}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc"])
        assert result.exit_code == 0
        assert "Provided Address 1 | 5abc | 1.250000000 τ | 0.000000000 τ | 1.250000000 τ" in result.output
        assert "Total Balance |  | 1.250000000 τ | 0.000000000 τ | 1.250000000 τ" in result.output
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_maps_no_prompt_to_yes(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc", "--no-prompt"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--yes", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_drops_prompt_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "balance", "--address", "5abc", "--prompt"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["balance", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_balance_alias_maps_wallet_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "balance",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["balance", "--wallet", "alice", "--wallet-dir", "/tmp/wallets", "--hotkey-name", "default", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_list_alias_wraps_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[{"name":"alice","coldkey":"5abc"}]\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "list", "--wallet-path", "/tmp/wallets", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"wallets": [{"name": "alice", "coldkey": "5abc"}]}'
        mock_instance.run.assert_called_once_with(
            ["wallet", "list", "--wallet-dir", "/tmp/wallets", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_list_alias_enriches_json_output_from_wallet_files(self, mock_cls, cli_runner, tmp_path):
        wallet_dir = tmp_path / "wallets"
        hotkeys_dir = wallet_dir / "alice" / "hotkeys"
        hotkeys_dir.mkdir(parents=True)
        coldkey_payload = {
            "accountId": "0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d",
            "ss58Address": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "publicKey": "0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d",
        }
        (wallet_dir / "alice" / "coldkeypub.txt").write_text(json.dumps(coldkey_payload))
        (hotkeys_dir / "defaultpub.txt").write_text(json.dumps(coldkey_payload))

        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[{"name":"alice","coldkey":"5abc"}]\n')
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["wallet", "list", "--wallet-path", str(wallet_dir), "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == (
            '{"wallets": [{"name": "alice", "ss58_address": '
            '"5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY", '
            '"hotkeys": [{"name": "default", "ss58_address": '
            '"5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"}]}]}'
        )
        mock_instance.run.assert_called_once_with(
            ["wallet", "list", "--wallet-dir", str(wallet_dir), "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_list_alias_rewrites_non_empty_text_output(self, mock_cls, cli_runner, tmp_path):
        wallet_dir = tmp_path / "wallets"
        hotkeys_dir = wallet_dir / "alice" / "hotkeys"
        hotkeys_dir.mkdir(parents=True)
        coldkey_payload = {
            "accountId": "0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d",
            "ss58Address": "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            "publicKey": "0xd43593c715fdd31c61141abd04a99fd6822c8558854ccde39a5684e7a56da27d",
        }
        (wallet_dir / "alice" / "coldkeypub.txt").write_text(json.dumps(coldkey_payload))
        (hotkeys_dir / "defaultpub.txt").write_text(json.dumps(coldkey_payload))

        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout=f"Wallets in {wallet_dir}:\n  alice (5Grw...utQY)\n")
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["wallet", "list", "--wallet-path", str(wallet_dir)])
        assert result.exit_code == 0
        assert result.output == (
            "Wallets\n"
            "└── Coldkey alice  ss58_address 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n"
            "    └── Hotkey default  ss58_address \n"
            "        5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n"
        )
        mock_instance.run.assert_called_once_with(
            ["wallet", "list", "--wallet-dir", str(wallet_dir)], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_list_alias_rewrites_empty_text_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No wallets found in /tmp/wallets\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "list", "--wallet-path", "/tmp/wallets"])
        assert result.exit_code == 0
        assert result.output == "❌ No wallets found in dir: /tmp/wallets\n\nWallets\n└── No wallets found.\n"
        mock_instance.run.assert_called_once_with(
            ["wallet", "list", "--wallet-dir", "/tmp/wallets"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_get_identity_alias_rewrites_to_identity_show(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"address": "5abc"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "get-identity", "--ss58", "5abc", "--output", "json"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["identity", "show", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_get_identity_empty_json_passthrough(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "get-identity", "--ss58", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert result.output.strip() == "{}"
        mock_instance.run.assert_called_once_with(
            ["identity", "show", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_get_identity_empty_text_output_with_network_rewrite(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No identity found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "get-identity", "--ss58", "5abc", "--network", "local"])
        assert result.exit_code == 0
        assert result.output == "❌ Existing identity not found for 5abc on Network: local, Chain: ws://127.0.0.1:9944\n"
        mock_instance.run.assert_called_once_with(
            ["identity", "show", "--address", "5abc", "--network", "local"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_get_identity_empty_text_output_with_endpoint_rewrite(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No identity found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["wallet", "get-identity", "--ss58", "5abc", "--endpoint", "ws://node.example:9944"],
        )
        assert result.exit_code == 0
        assert result.output == "❌ Existing identity not found for 5abc on Network: custom, Chain: ws://node.example:9944\n"
        mock_instance.run.assert_called_once_with(
            ["identity", "show", "--address", "5abc", "--endpoint", "ws://node.example:9944"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_get_identity_empty_text_output_without_context_rewrite(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No identity found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "get-identity", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "❌ Existing identity not found for 5abc on Network: custom\n"
        mock_instance.run.assert_called_once_with(
            ["identity", "show", "--address", "5abc"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_swap_check_alias_rewrites_to_wallet_check_swap(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[]\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "swap-check", "--address", "5abc", "--output", "json"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["wallet", "check-swap", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_swap_check_text_output_normalizes_no_pending_message(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","swap_scheduled":false}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "swap-check", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "No pending swap announcement found for coldkey: 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["wallet", "check-swap", "--address", "5abc"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_swap_check_json_output_keeps_agcli_payload(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"address":"5abc","swap_scheduled":false}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "swap-check", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output == '{"address":"5abc","swap_scheduled":false}\n'
        mock_instance.run.assert_called_once_with(
            ["wallet", "check-swap", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_swap_check_text_output_normalizes_native_text_message(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='No coldkey swap scheduled for 5abc\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "swap-check", "--address", "5abc"])
        assert result.exit_code == 0
        assert result.output == "No pending swap announcement found for coldkey: 5abc\n"

    def test_btcli_wallet_swap_check_rejects_all_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "swap-check", "--all"])
        assert result.exit_code == 1
        assert "wallet swap-check" in result.output
        assert "all-announcements view" in result.output

    def test_btcli_wallet_swap_check_rejects_quiet_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "swap-check", "--quiet"])
        assert result.exit_code == 1
        assert "wallet swap-check" in result.output
        assert "quiet-mode output suppression" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_swap_check_missing_address_stderr_is_normalized(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(returncode=1, stderr="wallet or address is required\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "swap-check"])
        assert result.exit_code == 0
        assert result.output == (
            "Enter wallet name or SS58 address (leave blank to show all pending announcements):\n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["wallet", "check-swap"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_rewrites_to_view_portfolio_and_wraps_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":123000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":42}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--network", "local", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == (
            '{"wallet": "5abc", "network": "local", "subnets": [{"netuid": 2, "tempo": 10, '
            '"neurons": [{"coldkey": "5abc", "hotkey": "default", "uid": 0, "active": false, '
            '"stake": 0.0, "rank": 0.0, "trust": 0.0, "consensus": 0.0, "incentive": 0.0, '
            '"dividends": 0.0, "emission": 0, "validator_trust": 0.0, "validator_permit": true, '
            '"last_update": 42, "axon": null, "hotkey_ss58": "5hot"}], "name": "omron", '
            '"symbol": "β"}], "total_balance": 123.0}'
        )
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_uses_wallet_name_and_metagraph_when_available(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5abc","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":99}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["wallet", "overview", "--wallet-name", "alice", "--network", "local", "--json-output"],
        )
        assert result.exit_code == 0
        assert '"wallet": "alice|5abc"' in result.output
        assert '"coldkey": "alice"' in result.output
        assert '"hotkey": "default"' in result.output
        assert '"network": "local"' in result.output
        assert '"subnets": [{"netuid": 2' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_filters_metagraph_to_requested_wallet_hotkey(self, mock_cls, cli_runner, tmp_path):
        wallet_dir = tmp_path / "wallets"
        hotkeys_dir = wallet_dir / "alice" / "hotkeys"
        hotkeys_dir.mkdir(parents=True)
        (hotkeys_dir / "defaultpub.txt").write_text('{"ss58Address":"5hot-default"}')
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot-default","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":99},{"uid":1,"active":false,"coldkey":"5abc","hotkey":"5other-hotkey","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":100}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                str(wallet_dir),
                "--hotkey",
                "default",
                "--network",
                "local",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        assert '"uid": 0' in result.output
        assert '"uid": 1' not in result.output
        assert '"hotkey_ss58": "5hot-default"' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", str(wallet_dir), "--hotkey-name", "default", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_keeps_all_coldkey_matches_when_wallet_hotkey_file_missing(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot-default","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":99},{"uid":1,"active":false,"coldkey":"5abc","hotkey":"5other-hotkey","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":100}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/missing-wallet-dir",
                "--hotkey",
                "default",
                "--network",
                "local",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        assert result.output.count('"uid":') == 2
        assert '"uid": 0' in result.output
        assert '"uid": 1' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", "/tmp/missing-wallet-dir", "--hotkey-name", "default", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_falls_back_to_positions_when_requested_hotkey_has_no_metagraph_match(self, mock_cls, cli_runner, tmp_path):
        wallet_dir = tmp_path / "wallets"
        hotkeys_dir = wallet_dir / "alice" / "hotkeys"
        hotkeys_dir.mkdir(parents=True)
        (hotkeys_dir / "defaultpub.txt").write_text('{"ss58Address":"5hot-default"}')
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":1,"active":false,"coldkey":"5abc","hotkey":"5other-hotkey","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":100}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                str(wallet_dir),
                "--hotkey",
                "default",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        assert '"subnets": [{"netuid": 2, "amount": {"rao": 500000000}}]' in result.output
        assert '"uid": 1' not in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", str(wallet_dir), "--hotkey-name", "default", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_uses_coldkey_self_hotkey_when_wallet_file_matches_coldkey(self, mock_cls, cli_runner, tmp_path):
        wallet_dir = tmp_path / "wallets"
        hotkeys_dir = wallet_dir / "alice" / "hotkeys"
        hotkeys_dir.mkdir(parents=True)
        (hotkeys_dir / "defaultpub.txt").write_text('{"ss58Address":"5abc"}')
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5abc","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":99},{"uid":1,"active":false,"coldkey":"5abc","hotkey":"5other-hotkey","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":100}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                str(wallet_dir),
                "--hotkey",
                "default",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        assert result.output.count('"uid":') == 1
        assert '"uid": 0' in result.output
        assert '"uid": 1' not in result.output
        assert '"hotkey_ss58": "5abc"' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", str(wallet_dir), "--hotkey-name", "default", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_filters_metagraph_to_requested_wallet_hotkey(self, mock_cls, cli_runner, tmp_path):
        wallet_dir = tmp_path / "wallets"
        hotkeys_dir = wallet_dir / "alice" / "hotkeys"
        hotkeys_dir.mkdir(parents=True)
        (hotkeys_dir / "defaultpub.txt").write_text('{"ss58Address":"5hot-default"}')
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":123000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot-default","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":42},{"uid":1,"active":false,"coldkey":"5abc","hotkey":"5other-hotkey","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":43}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                str(wallet_dir),
                "--hotkey",
                "default",
                "--network",
                "local",
            ],
        )
        assert result.exit_code == 0
        assert "uid=0" in result.output
        assert "uid=1" not in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", str(wallet_dir), "--hotkey-name", "default", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_keeps_all_matches_when_wallet_hotkey_file_missing(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":123000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot-default","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":42},{"uid":1,"active":false,"coldkey":"5abc","hotkey":"5other-hotkey","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":43}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["wallet", "overview", "--wallet-name", "alice", "--wallet-path", "/tmp/missing-wallet-dir", "--hotkey", "default"],
        )
        assert result.exit_code == 0
        assert result.output.count("uid=") == 2
        assert "uid=0" in result.output
        assert "uid=1" in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", "/tmp/missing-wallet-dir", "--hotkey-name", "default", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_falls_back_to_positions_when_requested_hotkey_has_no_metagraph_match(self, mock_cls, cli_runner, tmp_path):
        wallet_dir = tmp_path / "wallets"
        hotkeys_dir = wallet_dir / "alice" / "hotkeys"
        hotkeys_dir.mkdir(parents=True)
        (hotkeys_dir / "defaultpub.txt").write_text('{"ss58Address":"5hot-default"}')
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":1,"active":false,"coldkey":"5abc","hotkey":"5other-hotkey","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":43}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                str(wallet_dir),
                "--hotkey",
                "default",
            ],
        )
        assert result.exit_code == 0
        assert result.output == (
            "Wallet\n"
            "\n"
            "alice : 5abc\n"
            "Network: custom\n"
            "Subnet: 2\n"
            "\n"
            "Wallet free balance: 1.0000 τ\n"
        )
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", str(wallet_dir), "--hotkey-name", "default", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_renders_btcli_shaped_summary_from_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":123000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":42}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--network", "local"])
        assert result.exit_code == 0
        assert result.output == (
            "Wallet\n"
            "\n"
            "5abc : 5abc\n"
            "Network: local\n"
            "Subnet: 2: omron β\n"
            "  5abc/default uid=0 stake=0.000000000 τ active=False validator_permit=True\n"
            "\n"
            "Wallet free balance: 123.0000 τ\n"
        )
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_falls_back_to_agcli_text_when_stdout_is_not_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Portfolio for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "Portfolio for 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["view", "portfolio", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_falls_back_to_positions_when_metagraph_is_not_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(stdout='not-json\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"subnets": [{"netuid": 2, "amount": {"rao": 500000000}}]' in result.output
        assert '"network": "custom"' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_falls_back_to_positions_when_subnet_has_no_matching_neurons(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(stdout='{"netuid":2,"neurons":[]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"subnets": [{"netuid": 2, "amount": {"rao": 500000000}}]' in result.output
        assert '"positions"' not in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_uses_enriched_empty_subnet_list_when_positions_are_empty(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(stdout='{"netuid":2,"neurons":[]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"subnets": []' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_skips_extra_queries_when_portfolio_has_no_coldkey(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"free_balance":{"rao":123000000000},"total_staked":{"rao":0},"positions":[]}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"wallet": "5abc", "network": "custom", "subnets": [], "total_balance": 123.0}'
        mock_instance.run.assert_called_once_with(
            ["view", "portfolio", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_leaves_unexpected_json_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"balance_tao": 1.0}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"balance_tao": 1.0}'
        mock_instance.run.assert_called_once_with(
            ["view", "portfolio", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_falls_back_to_positions_when_no_matching_neurons(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":1,"active":false,"coldkey":"5other","hotkey":"5hot","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":false,"last_update":7}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"subnets": [{"netuid": 2, "amount": {"rao": 500000000}}]' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_ignores_bad_dynamic_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='not-json\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"subnets": [{"netuid": 2, "amount": {"rao": 500000000}}]' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_keeps_positions_when_dynamic_empty(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='[]\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"subnets": [{"netuid": 2, "amount": {"rao": 500000000}}]' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_uses_dynamic_symbol_over_subnet_show_symbol_style(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":12}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"symbol": "β"' in result.output
        assert '"symbol": "α2"' not in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_does_not_query_root_metagraph(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":0,"name":"root","symbol":"Τ","tempo":100},{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(stdout='{"netuid":2,"neurons":[]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]
        assert '"subnets": []' in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_uses_requested_network_in_output_even_without_metagraph(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='not-json\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--wallet-name", "alice", "--network", "local", "--json-output"])
        assert result.exit_code == 0
        assert '"wallet": "alice|5abc"' in result.output
        assert '"network": "local"' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_rewrites_missing_wallet_error(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            returncode=1,
            stderr=(
                "Could not resolve coldkey address from wallet 'alice' in /tmp/wallets.\n"
                "  Tip: pass --address <ss58> explicitly, or create a wallet with: agcli wallet create\n"
            ),
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["wallet", "overview", "--wallet-name", "alice", "--wallet-path", "/tmp/wallets"],
        )
        assert result.exit_code == 0
        assert "Wallet does not exist" in result.output
        assert "Could not resolve coldkey address" not in result.output
        assert "Wallet (Name: 'alice', Hotkey: 'default'" in result.output
        mock_instance.run.assert_called_once_with(
            ["view", "portfolio", "--wallet", "alice", "--wallet-dir", "/tmp/wallets", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_suppresses_missing_wallet_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            returncode=1,
            stderr=(
                "Could not resolve coldkey address from wallet 'alice' in /tmp/wallets.\n"
                "  Tip: pass --address <ss58> explicitly, or create a wallet with: agcli wallet create\n"
            ),
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        assert result.output == ""
        mock_instance.run.assert_called_once_with(
            [
                "view",
                "portfolio",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_overview_alias_rejects_unsupported_all_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "overview", "--all"])
        assert result.exit_code == 1
        assert "wallet overview flag '--all' is not implemented in taocli yet" in result.output

    def test_btcli_wallet_overview_alias_rejects_sorting_flags(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "overview", "--sort-by", "name"])
        assert result.exit_code == 1
        assert "wallet overview flag '--sort-by' is not implemented in taocli yet" in result.output

    def test_btcli_wallet_overview_alias_rejects_netuids_flags(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "overview", "--netuids", "1,2"])
        assert result.exit_code == 1
        assert "wallet overview flag '--netuids' is not implemented in taocli yet" in result.output

    def test_btcli_wallet_overview_alias_rejects_short_all_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "overview", "-a"])
        assert result.exit_code == 1
        assert "wallet overview flag '-a' is not implemented in taocli yet" in result.output

    def test_btcli_wallet_overview_alias_rejects_short_netuids_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "overview", "-n", "1"])
        assert result.exit_code == 1
        assert "wallet overview flag '-n' is not implemented in taocli yet" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_maps_wallet_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":0},"total_staked":{"rao":0},"positions":[]}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--no-prompt",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--wallet-dir", "/tmp/wallets", "--hotkey-name", "default", "--yes", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_alias_drops_prompt_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Portfolio\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--prompt"])
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["view", "portfolio", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_renders_btcli_shaped_summary_from_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":123000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(
                stdout='{"netuid":2,"neurons":[{"uid":0,"active":false,"coldkey":"5abc","hotkey":"5hot","stake_tao":0.0,"rank":0.0,"trust":0.0,"consensus":0.0,"incentive":0.0,"dividends":0.0,"emission":0.0,"validator_trust":0.0,"validator_permit":true,"last_update":42}]}\n'
            ),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--network", "local"])
        assert result.exit_code == 0
        assert result.output == (
            "Wallet\n"
            "\n"
            "5abc : 5abc\n"
            "Network: local\n"
            "Subnet: 2: omron β\n"
            "  5abc/default uid=0 stake=0.000000000 τ active=False validator_permit=True\n"
            "\n"
            "Wallet free balance: 123.0000 τ\n"
        )
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--network", "local", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_falls_back_to_agcli_text_when_stdout_is_not_json(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Portfolio for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "Portfolio for 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["view", "portfolio", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_uses_wallet_name_and_address_in_header(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[]\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--wallet-name", "alice"])
        assert result.exit_code == 0
        assert result.output == (
            "Wallet\n"
            "\n"
            "alice : 5abc\n"
            "Network: custom\n"
            "\n"
            "Wallet free balance: 2.0000 τ\n"
        )
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_uses_positions_when_metagraph_has_no_match(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='[{"netuid":2,"name":"omron","symbol":"β","tempo":10}]\n'),
            make_completed_process(stdout='{"netuid":2,"neurons":[]}\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == (
            "Wallet\n"
            "\n"
            "5abc : 5abc\n"
            "Network: custom\n"
            "Subnet: 2\n"
            "\n"
            "Wallet free balance: 1.0000 τ\n"
        )
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "metagraph", "--netuid", "2", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_text_skips_dynamic_queries_without_coldkey(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"free_balance":{"rao":123000000000},"total_staked":{"rao":0},"positions":[]}\n'
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == (
            "Wallet\n"
            "\n"
            "5abc : 5abc\n"
            "Network: custom\n"
            "\n"
            "Wallet free balance: 123.0000 τ\n"
        )
        mock_instance.run.assert_called_once_with(
            ["view", "portfolio", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_json_uses_coldkey_when_address_missing(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5fromwallet","free_balance":{"rao":2000000000},"total_staked":{"rao":0},"positions":[]}\n'
            ),
            make_completed_process(stdout='[]\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--wallet-name", "alice", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == (
            '{"wallet": "alice|5fromwallet", "network": "custom", "subnets": [], "total_balance": 2.0}'
        )
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--wallet", "alice", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_overview_json_preserves_positions(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.side_effect = [
            make_completed_process(
                stdout='{"coldkey_ss58":"5abc","free_balance":{"rao":1000000000},"total_staked":{"rao":500000000},"positions":[{"netuid":2,"amount":{"rao":500000000}}]}\n'
            ),
            make_completed_process(stdout='not-json\n'),
        ]
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["wallet", "overview", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"positions"' not in result.output
        assert '"subnets": [{"netuid": 2, "amount": {"rao": 500000000}}]' in result.output
        assert mock_instance.run.call_args_list == [
            ((["view", "portfolio", "--address", "5abc", "--output", "json"],), {"check": False, "capture": True}),
            ((["view", "dynamic", "--output", "json"],), {"check": False, "capture": True}),
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_maps_ss58_and_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[]\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output == ""
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_rewrites_empty_text_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No stakes found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "No stakes found for coldkey ss58: (5abc)\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--address", "5abc"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_adds_local_warning_for_network_local(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No stakes found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--network", "local", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "Warning: Verify your local subtensor is running on port 9944.\n\nNo stakes found for coldkey ss58: (5abc)\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--network", "local", "--address", "5abc"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_adds_local_warning_for_explicit_endpoint(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No stakes found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            ["stake", "list", "--endpoint", "ws://127.0.0.1:9944", "--ss58", "5abc"],
        )
        assert result.exit_code == 0
        assert result.output == "Warning: Verify your local subtensor is running on port 9944.\n\nNo stakes found for coldkey ss58: (5abc)\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--endpoint", "ws://127.0.0.1:9944", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_falls_back_when_requested_address_missing(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No stakes found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--wallet-name", "alice"])
        assert result.exit_code == 0
        assert result.output == "No stakes found for coldkey ss58: 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--wallet", "alice"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_native_stake_list_text_output_is_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No stakes found for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--address", "5abc"])
        assert result.exit_code == 0
        assert result.output == "No stakes found for 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--address", "5abc"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_native_stake_list_json_output_is_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[]\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--address", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert result.output.strip() == "[]"
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_keeps_non_empty_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[{"hotkey":"5hk"}]\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '[{"hotkey":"5hk"}]'
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_leaves_unexpected_json_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"count": 0}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "list", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"count": 0}'
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--address", "5abc", "--output", "json"], check=False, capture=True
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_list_alias_maps_wallet_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "list",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["stake", "list", "--wallet", "alice", "--wallet-dir", "/tmp/wallets", "--hotkey-name", "default", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_add_alias_maps_wallet_period_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "add",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "add",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-address",
                "default",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "32",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_add_alias_maps_hotkey_ss58_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "add",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--hotkey-ss58-address",
                "5Fhotkey",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["stake", "add", "--amount", "10", "--netuid", "1", "--hotkey-address", "5Fhotkey"],
            check=False,
            capture=True,
        )

    def test_btcli_stake_add_rejects_all_netuids_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "add", "--all-netuids"])
        assert result.exit_code == 1
        assert "stake add" in result.output
        assert "--all-netuids" in result.output
        assert "single --netuid" in result.output

    def test_btcli_stake_add_rejects_tolerance_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "add", "--tolerance", "0.5"])
        assert result.exit_code == 1
        assert "stake add" in result.output
        assert "--tolerance" in result.output
        assert "safe-staking tolerance controls" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_add_no_arg_error_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --amount <AMOUNT>\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "add"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert "Safe staking: enabled (from config)." in result.stderr
        assert "Enter the netuid to use. Leave blank for all netuids:" in result.stderr
        assert result.stderr.endswith("Aborted.\n")
        mock_instance.run.assert_called_once_with(["stake", "add"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_add_netuid_only_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --amount <AMOUNT>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "add", "--netuid", "1"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert "Enter the wallet name (default):" in result.stderr
        assert result.stderr.endswith("Aborted.\n")
        mock_instance.run.assert_called_once_with(["stake", "add", "--netuid", "1"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_remove_alias_maps_wallet_period_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "remove",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--era",
                "24",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "remove",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-address",
                "default",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "24",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_remove_alias_maps_hotkey_ss58_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "remove",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--hotkey-ss58-address",
                "5Fhotkey",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            ["stake", "remove", "--amount", "10", "--netuid", "1", "--hotkey-address", "5Fhotkey"],
            check=False,
            capture=True,
        )

    def test_btcli_stake_remove_rejects_unstake_all_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "remove", "--unstake-all"])
        assert result.exit_code == 1
        assert "stake remove" in result.output
        assert "--unstake-all" in result.output
        assert "stake unstake-all" in result.output

    def test_btcli_stake_remove_rejects_interactive_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "remove", "--interactive"])
        assert result.exit_code == 1
        assert "stake remove" in result.output
        assert "--interactive" in result.output
        assert "interactive unstake selector" in result.output

    def test_btcli_stake_remove_rejects_tolerance_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "remove", "--tolerance", "0.5"])
        assert result.exit_code == 1
        assert result.exit_code == 1
        assert "stake remove" in result.output
        assert "--tolerance" in result.output
        assert "safe-staking tolerance controls" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_remove_no_arg_error_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --amount <AMOUNT>\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "remove"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert "Safe staking: enabled (from config)." in result.stderr
        assert "Enter the netuid to use. Leave blank for all netuids:" in result.stderr
        assert result.stderr.endswith("Aborted.\n")
        mock_instance.run.assert_called_once_with(["stake", "remove"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_remove_netuid_only_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --amount <AMOUNT>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "remove", "--netuid", "1"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert "Enter the wallet name (default):" in result.stderr
        assert result.stderr.endswith("Aborted.\n")
        mock_instance.run.assert_called_once_with(["stake", "remove", "--netuid", "1"], check=False, capture=True)

    def test_normalize_passthrough_args_maps_btcli_stake_add_hotkey_aliases(self):
        assert normalize_passthrough_args(["stake", "add", "--hotkey", "5Fhotkey"]) == [
            "stake",
            "add",
            "--hotkey-address",
            "5Fhotkey",
        ]
        assert normalize_passthrough_args(["stake", "add", "--hotkey-ss58-address", "5Fhotkey"]) == [
            "stake",
            "add",
            "--hotkey-address",
            "5Fhotkey",
        ]

    def test_normalize_passthrough_args_maps_btcli_stake_remove_hotkey_aliases(self):
        assert normalize_passthrough_args(["stake", "remove", "--hotkey", "5Fhotkey"]) == [
            "stake",
            "remove",
            "--hotkey-address",
            "5Fhotkey",
        ]
        assert normalize_passthrough_args(["stake", "remove", "--hotkey-ss58-address", "5Fhotkey"]) == [
            "stake",
            "remove",
            "--hotkey-address",
            "5Fhotkey",
        ]

    def test_normalize_passthrough_args_rejects_btcli_stake_add_unsupported_flags(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all-netuids'"):
            normalize_passthrough_args(["stake", "add", "--all-netuids"])
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--tolerance'"):
            normalize_passthrough_args(["stake", "add", "--tolerance", "0.5"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_unsupported_flags(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--unstake-all'"):
            normalize_passthrough_args(["stake", "remove", "--unstake-all"])
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--interactive'"):
            normalize_passthrough_args(["stake", "remove", "--interactive"])

    def test_normalize_passthrough_args_leaves_native_stake_add_remove_flags_unchanged(self):
        assert normalize_passthrough_args(["stake", "add", "--max-slippage", "2.0"]) == [
            "stake",
            "add",
            "--max-slippage",
            "2.0",
        ]
        assert normalize_passthrough_args(["stake", "remove", "--max-slippage", "2.0"]) == [
            "stake",
            "remove",
            "--max-slippage",
            "2.0",
        ]

    def test_normalize_passthrough_args_preserves_stake_add_remove_when_no_btcli_flags_present(self):
        assert normalize_passthrough_args(["stake", "add", "--amount", "10", "--netuid", "1"]) == [
            "stake",
            "add",
            "--amount",
            "10",
            "--netuid",
            "1",
        ]
        assert normalize_passthrough_args(["stake", "remove", "--amount", "10", "--netuid", "1"]) == [
            "stake",
            "remove",
            "--amount",
            "10",
            "--netuid",
            "1",
        ]

    def test_normalize_passthrough_args_rejects_btcli_stake_add_prompt_only_flags(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--quiet'"):
            normalize_passthrough_args(["stake", "add", "--quiet"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_prompt_only_flags(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--verbose'"):
            normalize_passthrough_args(["stake", "remove", "--verbose"])

    def test_normalize_passthrough_args_maps_btcli_stake_add_no_prompt_and_json(self):
        assert normalize_passthrough_args(["stake", "add", "--json-output", "--no-prompt"]) == [
            "stake",
            "add",
            "--output",
            "json",
            "--yes",
        ]

    def test_normalize_passthrough_args_maps_btcli_stake_remove_no_prompt_and_json(self):
        assert normalize_passthrough_args(["stake", "remove", "--json-output", "--no-prompt"]) == [
            "stake",
            "remove",
            "--output",
            "json",
            "--yes",
        ]

    def test_normalize_passthrough_args_maps_btcli_stake_add_period_aliases(self):
        assert normalize_passthrough_args(["stake", "add", "--period", "32"]) == [
            "stake",
            "add",
            "--mortality-blocks",
            "32",
        ]

    def test_normalize_passthrough_args_maps_btcli_stake_remove_era_aliases(self):
        assert normalize_passthrough_args(["stake", "remove", "--era", "24"]) == [
            "stake",
            "remove",
            "--mortality-blocks",
            "24",
        ]

    def test_normalize_passthrough_args_rejects_btcli_stake_add_all_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all'"):
            normalize_passthrough_args(["stake", "add", "--all"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_all_hotkeys_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--all-hotkeys'"):
            normalize_passthrough_args(["stake", "remove", "--all-hotkeys"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_unstake_all_alpha_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--unstake-all-alpha'"):
            normalize_passthrough_args(["stake", "remove", "--unstake-all-alpha"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_mev_protection_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--mev-protection'"):
            normalize_passthrough_args(["stake", "add", "--mev-protection"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_mev_protection_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--mev-protection'"):
            normalize_passthrough_args(["stake", "remove", "--mev-protection"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_allow_partial_stake_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--allow-partial-stake'"):
            normalize_passthrough_args(["stake", "add", "--allow-partial-stake"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_allow_partial_stake_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--allow-partial-stake'"):
            normalize_passthrough_args(["stake", "remove", "--allow-partial-stake"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_proxy_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--proxy'"):
            normalize_passthrough_args(["stake", "add", "--proxy", "5proxy"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_proxy_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--proxy'"):
            normalize_passthrough_args(["stake", "remove", "--proxy", "5proxy"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_announce_only_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--announce-only'"):
            normalize_passthrough_args(["stake", "add", "--announce-only"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_announce_only_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--announce-only'"):
            normalize_passthrough_args(["stake", "remove", "--announce-only"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_include_hotkeys_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--include-hotkeys'"):
            normalize_passthrough_args(["stake", "add", "--include-hotkeys", "a,b"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_exclude_hotkeys_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--exclude-hotkeys'"):
            normalize_passthrough_args(["stake", "remove", "--exclude-hotkeys", "a,b"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_all_tokens_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all-tokens'"):
            normalize_passthrough_args(["stake", "add", "--all-tokens"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_all_netuids_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--all-netuids'"):
            normalize_passthrough_args(["stake", "remove", "--all-netuids"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_no_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--no'"):
            normalize_passthrough_args(["stake", "remove", "--no"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_no_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--no'"):
            normalize_passthrough_args(["stake", "add", "--no"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_quiet_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--quiet'"):
            normalize_passthrough_args(["stake", "remove", "--quiet"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_verbose_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--verbose'"):
            normalize_passthrough_args(["stake", "add", "--verbose"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_safe_staking_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--safe-staking'"):
            normalize_passthrough_args(["stake", "add", "--safe-staking"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_safe_staking_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--safe-staking'"):
            normalize_passthrough_args(["stake", "remove", "--safe-staking"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_verbose_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--verbose'"):
            normalize_passthrough_args(["stake", "remove", "--verbose"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_quiet_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--quiet'"):
            normalize_passthrough_args(["stake", "add", "--quiet"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_tolerance_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--tolerance'"):
            normalize_passthrough_args(["stake", "remove", "--tolerance", "0.5"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_tolerance_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--tolerance'"):
            normalize_passthrough_args(["stake", "add", "--tolerance", "0.5"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_interactive_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--interactive'"):
            normalize_passthrough_args(["stake", "remove", "--interactive"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_all_hotkeys_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all-hotkeys'"):
            normalize_passthrough_args(["stake", "add", "--all-hotkeys"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_include_hotkeys_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--include-hotkeys'"):
            normalize_passthrough_args(["stake", "remove", "--include-hotkeys", "a,b"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_all_netuids_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all-netuids'"):
            normalize_passthrough_args(["stake", "add", "--all-netuids"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_all_hotkeys_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--all-hotkeys'"):
            normalize_passthrough_args(["stake", "remove", "--all-hotkeys"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_exclude_hotkeys_flag(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--exclude-hotkeys'"):
            normalize_passthrough_args(["stake", "add", "--exclude-hotkeys", "a,b"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_no_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--no'"):
            normalize_passthrough_args(["stake", "remove", "--no"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_no_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--no'"):
            normalize_passthrough_args(["stake", "add", "--no"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_quiet_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--quiet'"):
            normalize_passthrough_args(["stake", "remove", "--quiet"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_verbose_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--verbose'"):
            normalize_passthrough_args(["stake", "add", "--verbose"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_safe_staking_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--safe-staking'"):
            normalize_passthrough_args(["stake", "remove", "--safe-staking"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_safe_staking_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--safe-staking'"):
            normalize_passthrough_args(["stake", "add", "--safe-staking"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_verbose_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--verbose'"):
            normalize_passthrough_args(["stake", "remove", "--verbose"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_quiet_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--quiet'"):
            normalize_passthrough_args(["stake", "add", "--quiet"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_tolerance_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--tolerance'"):
            normalize_passthrough_args(["stake", "remove", "--tolerance", "0.5"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_tolerance_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--tolerance'"):
            normalize_passthrough_args(["stake", "add", "--tolerance", "0.5"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_interactive_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--interactive'"):
            normalize_passthrough_args(["stake", "remove", "--interactive"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_all_hotkeys_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all-hotkeys'"):
            normalize_passthrough_args(["stake", "add", "--all-hotkeys"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_include_hotkeys_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--include-hotkeys'"):
            normalize_passthrough_args(["stake", "remove", "--include-hotkeys", "a,b"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_all_netuids_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all-netuids'"):
            normalize_passthrough_args(["stake", "add", "--all-netuids"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_all_hotkeys_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--all-hotkeys'"):
            normalize_passthrough_args(["stake", "remove", "--all-hotkeys"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_exclude_hotkeys_flag_2(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--exclude-hotkeys'"):
            normalize_passthrough_args(["stake", "add", "--exclude-hotkeys", "a,b"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_no_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--no'"):
            normalize_passthrough_args(["stake", "remove", "--no"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_no_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--no'"):
            normalize_passthrough_args(["stake", "add", "--no"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_quiet_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--quiet'"):
            normalize_passthrough_args(["stake", "remove", "--quiet"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_verbose_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--verbose'"):
            normalize_passthrough_args(["stake", "add", "--verbose"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_safe_staking_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--safe-staking'"):
            normalize_passthrough_args(["stake", "remove", "--safe-staking"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_safe_staking_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--safe-staking'"):
            normalize_passthrough_args(["stake", "add", "--safe-staking"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_verbose_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--verbose'"):
            normalize_passthrough_args(["stake", "remove", "--verbose"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_quiet_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--quiet'"):
            normalize_passthrough_args(["stake", "add", "--quiet"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_tolerance_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--tolerance'"):
            normalize_passthrough_args(["stake", "remove", "--tolerance", "0.5"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_tolerance_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--tolerance'"):
            normalize_passthrough_args(["stake", "add", "--tolerance", "0.5"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_interactive_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--interactive'"):
            normalize_passthrough_args(["stake", "remove", "--interactive"])

    def test_normalize_passthrough_args_rejects_btcli_stake_add_all_hotkeys_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake add` flag '--all-hotkeys'"):
            normalize_passthrough_args(["stake", "add", "--all-hotkeys"])

    def test_normalize_passthrough_args_rejects_btcli_stake_remove_include_hotkeys_flag_3(self):
        with pytest.raises(click.ClickException, match=r"`stake remove` flag '--include-hotkeys'"):
            normalize_passthrough_args(["stake", "remove", "--include-hotkeys", "a,b"])

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_transfer_alias_rewrites_to_transfer_stake_and_maps_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "transfer",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--dest",
                "5dest",
                "--amount",
                "10",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "transfer-stake",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--dest",
                "5dest",
                "--amount",
                "10",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-address",
                "5hotkey",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "32",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_move_alias_maps_period_and_prompt_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "move",
                "--from",
                "5src",
                "--to",
                "5dst",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--amount",
                "10",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--prompt",
                "--era",
                "24",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "move",
                "--from",
                "5src",
                "--to",
                "5dst",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--amount",
                "10",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--mortality-blocks",
                "24",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_move_no_arg_error_rewrites_to_confirmation_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --from <FROM>\n"
                "  --to <TO>\n"
                "  --origin-netuid <ORIGIN_NETUID>\n"
                "  --dest-netuid <DEST_NETUID>\n"
                "  --amount <AMOUNT>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "move"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "This transaction will move stake to another hotkey while keeping the same coldkey ownership. Do you wish to continue?  [y/n] (n):\n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "move"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_transfer_no_arg_error_rewrites_to_confirmation_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --origin-netuid <ORIGIN_NETUID>\n"
                "  --dest-netuid <DEST_NETUID>\n"
                "  --dest <DEST>\n"
                "  --amount <AMOUNT>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "transfer"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "This transaction will transfer ownership from one coldkey to another, in subnets which have enabled it. You should ensure that the destination coldkey is not a validator hotkey before continuing. Do you wish to continue? [y/n] (n):\n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "transfer-stake"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_transfer_stake_no_arg_error_rewrites_to_confirmation_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --origin-netuid <ORIGIN_NETUID>\n"
                "  --dest-netuid <DEST_NETUID>\n"
                "  --dest <DEST>\n"
                "  --amount <AMOUNT>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "transfer-stake"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "This transaction will transfer ownership from one coldkey to another, in subnets which have enabled it. You should ensure that the destination coldkey is not a validator hotkey before continuing. Do you wish to continue? [y/n] (n):\n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "transfer-stake"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_transfer_alias_rewrites_to_transfer_stake_and_maps_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "transfer",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--dest",
                "5dest",
                "--amount",
                "10",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "transfer-stake",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--dest",
                "5dest",
                "--amount",
                "10",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-address",
                "5hotkey",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "32",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_wizard_alias_maps_wallet_flags_and_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "wizard",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "wizard",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_wizard_no_tao_output_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout=(
                "=== Staking Wizard ===\n\n"
                "Wallet: default (5G9Z...ceZW)\n"
                "Balance: 0.000000000 τ\n\n"
                "You need TAO to stake. Transfer some TAO to your coldkey first.\n"
            )
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "wizard"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "wizard"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_wizard_preserves_nonmatching_stdout(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Wizard complete\n")
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "wizard"])

        assert result.exit_code == 0
        assert result.stdout == "Wizard complete\n"
        assert result.stderr == ""
        mock_instance.run.assert_called_once_with(["stake", "wizard"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_swap_maps_hotkey_address_and_period_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "swap",
                "--netuid",
                "2",
                "--amount",
                "10",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "swap",
                "--netuid",
                "2",
                "--amount",
                "10",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-address",
                "5hotkey",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "32",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_stake_swap_rejects_unsupported_safe_staking_flags(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "swap", "--safe-staking"])
        assert result.exit_code == 1
        assert "stake swap` flag '--safe-staking'" in result.output
        assert "safe-staking mode toggles" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_swap_no_arg_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --origin-netuid <ORIGIN_NETUID>\n"
                "  --dest-netuid <DEST_NETUID>\n"
                "  --amount <AMOUNT>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "swap"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "This command moves stake from one subnet to another subnet while keeping the same coldkey-hotkey pair.\n"
            "Safe staking: enabled (from config).\n"
            "Rate tolerance: 0.005 (0.5%) by default. Set this using `btcli config set` or `--tolerance` flag\n"
            "Partial staking: disabled (from config).\n"
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "swap"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_maps_btcli_read_flags_and_shapes_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout="No auto-stake destinations set for 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n"
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "auto",
                "--ss58",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert '"0": {"subnet_name": "root", "status": "default", "destination": null, "identity": null}' in result.output
        assert '"1": {"subnet_name": "apex", "status": "default", "destination": null, "identity": null}' in result.output
        assert '"2": {"subnet_name": "omron", "status": "default", "destination": null, "identity": null}' in result.output
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "show-auto",
                "--address",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_shapes_empty_text_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout="No auto-stake destinations set for 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n"
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "auto",
                "--ss58",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
        )
        assert result.exit_code == 0
        assert "Auto Stake Destinations for 5Grwva...HGKutQY" in result.output
        assert "Network: custom" in result.output
        assert "Coldkey: 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY" in result.output
        assert "NETUID  SUBNET  STATUS   DESTINATION HOTKEY   IDENTITY" in result.output
        assert "0       root    Default" in result.output
        assert "1       apex    Default" in result.output
        assert "2       omron   Default" in result.output
        assert "Total subnets: 3  Custom destinations: 0" in result.output
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "show-auto",
                "--address",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_adds_local_warning_and_network_context(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout="No auto-stake destinations set for 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n"
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "auto",
                "--network",
                "local",
                "--ss58",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
        )
        assert result.exit_code == 0
        assert result.output.startswith("Warning: Verify your local subtensor is running on port 9944.\n\n")
        assert "Auto Stake Destinations for 5Grwva...HGKutQY" in result.output
        assert "Network: local" in result.output
        assert "Coldkey: 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY" in result.output
        assert "Total subnets: 3  Custom destinations: 0" in result.output
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "show-auto",
                "--network",
                "local",
                "--address",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_adds_local_warning_for_explicit_endpoint(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout="No auto-stake destinations set for 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n"
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "auto",
                "--endpoint",
                "ws://127.0.0.1:9944",
                "--ss58",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
        )
        assert result.exit_code == 0
        assert result.output.startswith("Warning: Verify your local subtensor is running on port 9944.\n\n")
        assert "Network: custom" in result.output
        assert "Auto Stake Destinations for 5Grwva...HGKutQY" in result.output
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "show-auto",
                "--endpoint",
                "ws://127.0.0.1:9944",
                "--address",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_omits_local_warning_for_non_local_network(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout="No auto-stake destinations set for 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n"
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "auto",
                "--network",
                "finney",
                "--ss58",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
        )
        assert result.exit_code == 0
        assert "Warning: Verify your local subtensor is running on port 9944." not in result.output
        assert "Network: finney" in result.output
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "show-auto",
                "--network",
                "finney",
                "--address",
                "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_non_empty_text_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Configured destinations\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "Configured destinations\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_native_stake_show_auto_text_output_is_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "show-auto", "--address", "5abc"])
        assert result.exit_code == 0
        assert result.output == "No auto-stake destinations set for 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_native_stake_show_auto_json_output_is_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"configured":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "show-auto", "--address", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"configured":true}'
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_unexpected_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"configured":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"configured":true}'
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_json_output_stays_default_shape_on_local_network(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--network", "local", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert '"0": {"subnet_name": "root", "status": "default", "destination": null, "identity": null}' in result.output
        assert '"1": {"subnet_name": "apex", "status": "default", "destination": null, "identity": null}' in result.output
        assert '"2": {"subnet_name": "omron", "status": "default", "destination": null, "identity": null}' in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--network", "local", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_falls_back_to_truncated_stdout_address(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5Grw...utQY\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto"])
        assert result.exit_code == 0
        assert "Auto Stake Destinations for 5Grw...utQY" in result.output
        assert "Coldkey: 5Grw...utQY" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_falls_back_to_custom_network_without_context(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "Network: custom" in result.output
        assert "Warning: Verify your local subtensor is running on port 9944." not in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_maps_output_json_flag(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert '"0": {"subnet_name": "root", "status": "default", "destination": null, "identity": null}' in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_maps_address_flag_directly(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--address", "5abc"])
        assert result.exit_code == 0
        assert "Coldkey: 5abc" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_maps_ss58_flag_in_text_mode(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "Coldkey: 5abc" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_maps_no_prompt_to_yes_in_text_mode(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--no-prompt"])
        assert result.exit_code == 0
        assert "Coldkey: 5abc" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_maps_wallet_flags_without_ss58(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--wallet-name", "alice", "--wallet-path", "/tmp/wallets"])
        assert result.exit_code == 0
        assert "Coldkey: 5abc" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--wallet", "alice", "--wallet-dir", "/tmp/wallets"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_leaves_non_empty_json_array_payload_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='[{"netuid":1}]\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '[{"netuid":1}]'
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_leaves_non_matching_text_stdout_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="Already configured\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == "Already configured\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_ignores_non_btcli_show_auto_path(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "show-auto", "--address", "5abc"])
        assert result.exit_code == 0
        assert result.output == "No auto-stake destinations set for 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_handles_short_address_without_truncation(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5short\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5short"])
        assert result.exit_code == 0
        assert "Auto Stake Destinations for 5short" in result.output
        assert "Coldkey: 5short" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5short"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_existing_ellipsis_address(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abcd...xyz123\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto"])
        assert result.exit_code == 0
        assert "Auto Stake Destinations for 5abcd...xyz123" in result.output
        assert "Coldkey: 5abcd...xyz123" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_json_passthrough_for_non_default_dict(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"custom": {"destination": "5hk"}}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"custom": {"destination": "5hk"}}'
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_maps_no_prompt_to_yes_in_json_mode(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--json-output", "--no-prompt"])
        assert result.exit_code == 0
        assert '"0": {"subnet_name": "root", "status": "default", "destination": null, "identity": null}' in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json", "--yes"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_native_json_request_when_output_json_used(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert '"0": {"subnet_name": "root", "status": "default", "destination": null, "identity": null}' in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_output_unchanged_when_json_parse_not_needed(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "show-auto", "--address", "5abc", "--output", "json"])
        assert result.exit_code == 0
        assert result.output == "No auto-stake destinations set for 5abc\n"
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_preserves_json_passthrough_for_scalar_payload(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='42\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc", "--json-output"])
        assert result.exit_code == 0
        assert result.output.strip() == '42'
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_preserves_text_passthrough_for_json_blob_without_default_shape(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"foo":"bar"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output.strip() == '{"foo":"bar"}'
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_warning_off_for_non_local_endpoint(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--endpoint", "wss://example.com", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "Warning: Verify your local subtensor is running on port 9944." not in result.output
        assert "Network: custom" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--endpoint", "wss://example.com", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_handles_localnet_network_name(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--network", "localnet", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "Warning: Verify your local subtensor is running on port 9944." in result.output
        assert "Network: localnet" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--network", "localnet", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_json_default_shape_when_stdout_address_is_truncated(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5Grw...utQY\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--json-output"])
        assert result.exit_code == 0
        assert '"0": {"subnet_name": "root", "status": "default", "destination": null, "identity": null}' in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--output", "json"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_text_passthrough_for_empty_stdout(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output == ""
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_json_default_shape_keeps_null_identity(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--json-output", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert '"identity": null' in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--output", "json", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_json_default_shape_keeps_null_destination(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--json-output", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert '"destination": null' in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--output", "json", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_text_shape_has_combined_summary_line(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "Total subnets: 3  Custom destinations: 0" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_text_shape_uses_truncated_header_not_full_address(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"])
        assert result.exit_code == 0
        assert "Auto Stake Destinations for 5Grwva...HGKutQY" in result.output
        assert "Auto Stake Destinations for 5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY" not in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5GrwvaEF5zXb26Fz9rcQpDWS57CtERHpNehXCPcNoHGKutQY"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_json_shape_without_network_metadata(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--json-output", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "Network:" not in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--output", "json", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_text_shape_without_destination_placeholder_dash_column(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "0       root    Default  -" not in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_text_shape_with_destination_hotkey_identity_header(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "DESTINATION HOTKEY   IDENTITY" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_warning_prefix_with_blank_line(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--network", "local", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert result.output.startswith("Warning: Verify your local subtensor is running on port 9944.\n\nAuto Stake Destinations")
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--network", "local", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_auto_alias_keeps_custom_network_name_for_non_local_endpoint(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="No auto-stake destinations set for 5abc\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["stake", "auto", "--endpoint", "wss://remote", "--ss58", "5abc"])
        assert result.exit_code == 0
        assert "Network: custom" in result.output
        mock_instance.run.assert_called_once_with(
            ["stake", "show-auto", "--endpoint", "wss://remote", "--address", "5abc"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_set_auto_maps_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "set-auto",
                "--netuid",
                "7",
                "--hotkey",
                "5hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "set-auto",
                "--netuid",
                "7",
                "--hotkey-address",
                "5hotkey",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "32",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_stake_set_auto_rejects_proxy_only_flags(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "set-auto", "--proxy"])
        assert result.exit_code == 1
        assert "stake set-auto` flag '--proxy'" in result.output
        assert "proxy execution path" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_set_auto_missing_netuid_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "set-auto"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Safe staking: enabled (from config).\n"
            "Enter the wallet name (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "set-auto"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_set_auto_password_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr="Cannot prompt for coldkey password: stdin is not a TTY\n",
            returncode=1,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            ["stake", "set-auto", "--netuid", "7", "--wallet-name", "alice", "--hotkey", "5hotkey"],
        )

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Safe staking: enabled (from config).\n"
            "Enter the wallet name (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(
            ["stake", "set-auto", "--netuid", "7", "--wallet", "alice", "--hotkey-address", "5hotkey"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_set_claim_maps_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "set-claim",
                "Manual",
                "--netuids",
                "1,2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "set-claim",
                "--claim-type",
                "manual",
                "--subnets",
                "1,2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_process_claim_maps_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "stake",
                "process-claim",
                "--netuid",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "process-claim",
                "--netuids",
                "7",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_set_claim_no_arg_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --claim-type <CLAIM_TYPE>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "set-claim"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "set-claim"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_process_claim_password_prompt_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "Error: Cannot prompt for coldkey password: stdin is not a TTY (non-interactive). Set AGCLI_PASSWORD or pass --password. For scripts/agents/CI, use --batch together with AGCLI_PASSWORD so missing inputs fail fast.\n"
            ),
            returncode=1,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "process-claim"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(["stake", "process-claim"], check=False, capture=True)

    def test_btcli_stake_child_get_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "child", "get"])
        assert result.exit_code == 2
        assert "btcli-compatible `stake child get` is not implemented" in result.output

    def test_btcli_stake_child_revoke_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "child", "revoke"])
        assert result.exit_code == 2
        assert "btcli-compatible `stake child revoke` is not implemented" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_child_set_maps_btcli_flags_and_pairs(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            [
                "stake",
                "child",
                "set",
                "--netuid",
                "1",
                "--children",
                "5child1",
                "--children",
                "5child2",
                "--proportions",
                "0.3",
                "--proportions",
                "0.7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5parent",
                "--json-output",
                "--no-prompt",
            ],
        )

        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "set-children",
                "--netuid",
                "1",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-address",
                "5parent",
                "--output",
                "json",
                "--yes",
                "--children",
                "0.3:5child1,0.7:5child2",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_stake_child_set_rejects_unsupported_all_netuids(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "child", "set", "--all-netuids"])
        assert result.exit_code == 1
        assert "stake child set` flag '--all-netuids'" in result.output

    def test_btcli_stake_child_set_requires_matching_children_and_proportions(self, cli_runner):
        result = cli_runner.invoke(
            main,
            ["stake", "child", "set", "--children", "5child1", "--proportions", "0.3", "--proportions", "0.7"],
        )
        assert result.exit_code == 2
        assert "requires the same number of --children and --proportions values" in result.output

    def test_btcli_stake_child_set_requires_explicit_proportions(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "child", "set", "--children", "5child1"])
        assert result.exit_code == 2
        assert "interactive proportion prompting is not implemented" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_child_set_missing_args_rewrite_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
                "  --children <CHILDREN>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "child", "set"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Enter the netuid to use. Leave blank for all netuids: \nAborted.\n"
        mock_instance.run.assert_called_once_with(["stake", "set-children"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_child_set_password_prompt_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout=(
                "Error: Cannot prompt for coldkey password: stdin is not a TTY (non-interactive). "
                "Set AGCLI_PASSWORD or pass --password. For scripts/agents/CI, use --batch together with AGCLI_PASSWORD so missing inputs fail fast.\n"
            ),
            returncode=1,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            [
                "stake",
                "child",
                "set",
                "--netuid",
                "1",
                "--children",
                "5child1",
                "--proportions",
                "1.0",
            ],
        )

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(
            ["stake", "set-children", "--netuid", "1", "--children", "1.0:5child1"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_child_take_maps_btcli_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            [
                "stake",
                "child",
                "take",
                "--netuid",
                "7",
                "--take",
                "0.12",
                "--child-hotkey-ss58",
                "5child",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--json-output",
                "--no-prompt",
            ],
        )

        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "stake",
                "childkey-take",
                "--netuid",
                "7",
                "--take",
                "0.12",
                "--hotkey-address",
                "5child",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_stake_child_take_read_mode_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "child", "take", "--netuid", "1"])
        assert result.exit_code == 2
        assert "read mode is not implemented" in result.output

    def test_btcli_stake_child_take_rejects_unsupported_all_netuids(self, cli_runner):
        result = cli_runner.invoke(main, ["stake", "child", "take", "--all-netuids", "--take", "0.12"])
        assert result.exit_code == 1
        assert "stake child take` flag '--all-netuids'" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_stake_child_take_password_prompt_error_rewrites_to_wallet_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "Error: Cannot prompt for coldkey password: stdin is not a TTY (non-interactive). Set AGCLI_PASSWORD or pass --password. For scripts/agents/CI, use --batch together with AGCLI_PASSWORD so missing inputs fail fast.\n"
            ),
            returncode=1,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["stake", "child", "take", "--netuid", "1", "--take", "0.12"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(
            ["stake", "childkey-take", "--netuid", "1", "--take", "0.12"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_register_alias_maps_wallet_period_and_json_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"status":"ok"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "register",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--period",
                "64",
                "--no-prompt",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        assert result.output.strip() == '{"status":"ok"}'
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "register-neuron",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--mortality-blocks",
                "64",
                "--yes",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_pow_register_alias_maps_processors_and_wallet_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "pow-register",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--processors",
                "8",
                "--prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "pow",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--threads",
                "8",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_hyperparameters_json_normalizes_hyperparams_schema(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout=(
                '{"netuid":2,"tempo":10,"max_weights_limit":65535,"commit_reveal_weights_interval":1,'
                '"min_burn":{"rao":500000,"tao":0.0005},"weights_version":0,'
                '"alpha_high":60000,"alpha_low":1000,"alpha_sigmoid_steepness":32768,'
                '"bonds_reset_enabled":true,"subnet_is_active":true,"transfers_enabled":false,'
                '"user_liquidity_enabled":true,"yuma3_enabled":1}\n'
            )
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "hyperparameters", "--netuid", "2", "--json-output"])
        assert result.exit_code == 0
        assert '"hyperparameter": "tempo"' in result.output
        assert '"hyperparameter": "max_weight_limit"' in result.output
        assert '"hyperparameter": "commit_reveal_period"' in result.output
        assert '"hyperparameter": "alpha_high"' in result.output
        assert '"hyperparameter": "alpha_low"' in result.output
        assert '"hyperparameter": "alpha_sigmoid_steepness"' in result.output
        assert '"hyperparameter": "bonds_reset_enabled"' in result.output
        assert '"hyperparameter": "subnet_is_active"' in result.output
        assert '"hyperparameter": "transfers_enabled"' in result.output
        assert '"hyperparameter": "user_liquidity_enabled"' in result.output
        assert '"hyperparameter": "yuma_version"' in result.output
        assert '"normalized_value": {"rao": 500000, "tao": 0.0005}' in result.output
        assert '"owner_settable": true' in result.output
        assert '"docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#commitrevealperiod"' in result.output
        assert '"docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#yuma3"' in result.output
        assert '"netuid"' not in result.output
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )

        assert result.output.count('"hyperparameter":') == 13

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_hyperparameters_text_output_normalizes_from_json_payload(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout=(
                '{"netuid":2,"tempo":10,"max_weights_limit":65535,'
                '"commit_reveal_weights_interval":1,'
                '"min_burn":{"rao":500000,"tao":0.0005},"weights_version":0,'
                '"user_liquidity_enabled":true,"yuma3_enabled":1}\n'
            )
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(main, ["subnets", "hyperparameters", "--netuid", "2"])
        assert result.exit_code == 0
        assert "Subnet Hyperparameters" in result.output
        assert "NETUID: 2 (omron) - Network: local" in result.output
        assert "HYPERPARAMETER" in result.output
        assert "commit_reveal_period" in result.output
        assert "0.000500000 τ" in result.output
        assert "COMPLICATED (Owner/Sudo)" in result.output
        assert "No (Root Only)" in result.output
        assert "Yes" in result.output
        assert "Tip: Use btcli sudo set --param <name> --value <value> to modify hyperparameters." in result.output
        assert "Tip: To set custom hyperparameters not in this list, use the exact parameter name from the chain metadata." in result.output
        assert "Example: btcli sudo set --netuid 2 --param custom_param_name --value 123" in result.output
        assert "The parameter name must match exactly as defined in the chain's AdminUtils pallet metadata." in result.output
        assert "For detailed documentation, visit: https://docs.bittensor.com" in result.output
        assert "(unknown)" not in result.output
        assert result.output.count("Tip:") == 3
        assert result.output.count("Example:") == 1
        assert result.output.count("COMPLICATED (Owner/Sudo)") == 1
        assert result.output.count("user_liquidity_enabled") == 1
        assert result.output.count("yuma_version") == 1
        assert result.output.endswith("For detailed documentation, visit: https://docs.bittensor.com\n")
        assert result.output.index("user_liquidity_enabled") < result.output.index("weights_version")
        assert result.output.index("weights_version") < result.output.index("yuma_version")
        mock_instance.run.assert_called_once_with(
            ["subnet", "hyperparams", "--netuid", "2", "--output", "json"],
            check=False,
            capture=True,
        )


    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_burn_cost_alias_rewrites_json_output_shape(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"cost_rao":1501041712970,"cost_tao":1501.04171297}\n'
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "burn-cost", "--json-output", "--network", "local"])

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_burn_cost_alias_rewrites_json_output_shape(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"cost_rao":1501041712970,"cost_tao":1501.04171297}\n'
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "burn-cost", "--json-output", "--network", "local"])

        assert result.exit_code == 0
        assert result.output == '{"burn_cost": {"rao": 1501041712970, "tao": 1501.04171297}, "error": ""}\n'
        mock_instance.run.assert_called_once_with(
            ["subnet", "create-cost", "--json-output", "--network", "local"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_burn_cost_output_json_passthrough_also_normalizes(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stdout='{"cost_rao":1501041712970,"cost_tao":1501.04171297}\n'
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "burn-cost", "--output", "json", "--network", "local"])

        assert result.exit_code == 0
        assert result.output == '{"burn_cost": {"rao": 1501041712970, "tao": 1501.04171297}, "error": ""}\n'
        mock_instance.run.assert_called_once_with(
            ["subnet", "create-cost", "--output", "json", "--network", "local"],
            check=False,
            capture=True,
        )

    def test_btcli_subnets_burn_cost_alias_maps_known_alias(self):
        assert normalize_passthrough_args(["subnets", "burn-cost", "--json-output", "--network", "local"]) == [
            "subnet",
            "create-cost",
            "--json-output",
            "--network",
            "local",
        ]

    def test_btcli_subnets_register_alias_rejects_announce_only_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "register", "--netuid", "2", "--announce-only"])
        assert result.exit_code == 1
        assert (
            "btcli-compatible subnets register flag '--announce-only' is not implemented in taocli yet"
            in result.output
        )

    def test_btcli_subnets_pow_register_alias_rejects_cuda_flags(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "pow-register", "--netuid", "2", "--cuda"])
        assert result.exit_code == 1
        assert "btcli-compatible subnets pow-register flag '--cuda' is not implemented in taocli yet" in result.output

    def test_btcli_subnets_pow_register_alias_rejects_json_output_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["subnets", "pow-register", "--netuid", "2", "--json-output"])
        assert result.exit_code == 2
        assert "No such option: --json-output" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_register_alias_rewrites_missing_wallet_error(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            returncode=1,
            stderr=(
                "Could not resolve coldkey address from wallet 'alice' in /tmp/wallets.\n"
                "  Tip: pass --address <ss58> explicitly, or create a wallet with: agcli wallet create\n"
            ),
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "register",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert "Wallet does not exist" in result.output
        assert "Hotkey: 'miner'" in result.output
        assert "Could not resolve coldkey address" not in result.output
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "register-neuron",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "miner",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_register_alias_suppresses_missing_wallet_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            returncode=1,
            stderr=(
                "Could not resolve coldkey address from wallet 'alice' in /tmp/wallets.\n"
                "  Tip: pass --address <ss58> explicitly, or create a wallet with: agcli wallet create\n"
            ),
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "register",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert result.output == ""
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "register-neuron",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "miner",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_register_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "register"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "register-neuron"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_pow_register_missing_netuid_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            stderr=(
                "error: the following required arguments were not provided:\n"
                "  --netuid <NETUID>\n"
            ),
            returncode=2,
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "pow-register"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == "Netuid: Aborted.\n"
        mock_instance.run.assert_called_once_with(["subnet", "pow"], check=False, capture=True)

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_pow_register_alias_rewrites_missing_wallet_error(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            returncode=1,
            stderr=(
                "Wallet 'alice' not found in /tmp/wallets.\n"
                "  Create one with: agcli wallet create --name alice\n"
                "  List existing:   agcli wallet list\n"
                "  To use a different wallet directory set AGCLI_WALLET_DIR.\n"
            ),
        )
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "subnets",
                "pow-register",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        assert "Wallet does not exist" in result.output
        assert "Hotkey: 'default'" in result.output
        assert "Wallet 'alice' not found" not in result.output
        mock_instance.run.assert_called_once_with(
            [
                "subnet",
                "pow",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_register_no_wallet_password_failure_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            returncode=1,
            stderr=(
                "Cannot prompt for coldkey password: stdin is not a TTY (non-interactive). "
                "Set AGCLI_PASSWORD or pass --password. For scripts/agents/CI, use --batch together with "
                "AGCLI_PASSWORD so missing inputs fail fast."
            ),
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "register", "--netuid", "2"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(
            ["subnet", "register-neuron", "--netuid", "2"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_subnets_pow_register_no_wallet_password_failure_rewrites_to_prompt_abort(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(
            returncode=1,
            stderr=(
                "Cannot prompt for coldkey password: stdin is not a TTY (non-interactive). "
                "Set AGCLI_PASSWORD or pass --password. For scripts/agents/CI, use --batch together with "
                "AGCLI_PASSWORD so missing inputs fail fast."
            ),
        )
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(main, ["subnets", "pow-register", "--netuid", "2"])

        assert result.exit_code == 0
        assert result.stdout == ""
        assert result.stderr == (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
        mock_instance.run.assert_called_once_with(
            ["subnet", "pow", "--netuid", "2"],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_set_identity_alias_maps_supported_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance

        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "set-identity",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--id-name",
                "alice validator",
                "--web-url",
                "https://example.com",
                "--image-url",
                "https://example.com/image.png",
                "--description",
                "validator",
                "--github",
                "unarbos/taocli",
                "--json-output",
                "--no-prompt",
            ],
        )

        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "identity",
                "set",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--name",
                "alice validator",
                "--url",
                "https://example.com",
                "--image",
                "https://example.com/image.png",
                "--description",
                "validator",
                "--github",
                "unarbos/taocli",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_set_identity_alias_rejects_unsupported_hotkey_target(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "set-identity", "--hotkey", "miner"])
        assert result.exit_code == 1
        assert "wallet set-identity" in result.output
        assert "hotkey-identity target semantics" in result.output

    def test_btcli_wallet_set_identity_alias_rejects_unsupported_discord_field(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "set-identity", "--discord", "arbos"])
        assert result.exit_code == 1
        assert "wallet set-identity" in result.output
        assert "discord field" in result.output

    def test_unsupported_btcli_wallet_swap_hotkey_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "swap-hotkey"])
        assert result.exit_code == 2
        assert "use `taocli swap hotkey --new-hotkey ...` or btcli" in result.output

    def test_unsupported_btcli_wallet_swap_coldkey_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "swap-coldkey"])
        assert result.exit_code == 2
        assert "use `taocli swap coldkey --new-coldkey ...` or btcli" in result.output

    def test_unsupported_btcli_wallet_new_coldkey_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "new-coldkey"])
        assert result.exit_code == 2
        assert "not implemented in taocli/agcli yet" in result.output
        assert "wallet create" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_new_hotkey_alias_maps_wallet_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "new-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "wallet",
                "new-hotkey",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--name",
                "miner",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_new_hotkey_alias_rejects_unsupported_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "new-hotkey", "--n-words", "24"])
        assert result.exit_code == 1
        assert "wallet new-hotkey" in result.output
        assert "mnemonic word-count selection" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_create_alias_maps_wallet_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "create",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "wallet",
                "create",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "miner",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_create_alias_rejects_unsupported_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "create", "--use-password"])
        assert result.exit_code == 1
        assert "wallet create" in result.output
        assert "password-protection toggles" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_associate_hotkey_alias_maps_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="ok\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "associate-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "wallet",
                "associate-hotkey",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-address",
                "5hotkey",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_associate_hotkey_alias_rejects_unsupported_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "associate-hotkey", "--announce-only"])
        assert result.exit_code == 1
        assert "wallet associate-hotkey" in result.output
        assert "announce-only proxy submission" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_regen_coldkey_alias_maps_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"wallet":"alice"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "regen-coldkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--mnemonic",
                "horse cart dog",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "wallet",
                "regen-coldkey",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "miner",
                "--mnemonic",
                "horse cart dog",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_regen_coldkey_alias_rejects_unsupported_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "regen-coldkey", "--seed", "0x1234"])
        assert result.exit_code == 1
        assert "wallet regen-coldkey" in result.output
        assert "raw seed input" in result.output

    def test_unsupported_btcli_wallet_regen_coldkeypub_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "regen-coldkeypub"])
        assert result.exit_code == 2
        assert "not implemented in taocli/agcli yet" in result.output
        assert "no matching `wallet regen-coldkeypub` subcommand" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_regen_hotkey_alias_maps_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"hotkey":"miner"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "regen-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--mnemonic",
                "horse cart dog",
                "--json-output",
                "--no-prompt",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "wallet",
                "regen-hotkey",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--name",
                "miner",
                "--mnemonic",
                "horse cart dog",
                "--output",
                "json",
                "--yes",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_regen_hotkey_alias_rejects_unsupported_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "regen-hotkey", "--json", "/tmp/key.json"])
        assert result.exit_code == 1
        assert "wallet regen-hotkey" in result.output
        assert "JSON key-backup restoration" in result.output

    def test_unsupported_btcli_wallet_regen_hotkeypub_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "regen-hotkeypub"])
        assert result.exit_code == 2
        assert "not implemented in taocli/agcli yet" in result.output
        assert "no matching `wallet regen-hotkeypub` subcommand" in result.output

    def test_unsupported_btcli_wallet_faucet_errors_cleanly(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "faucet"])
        assert result.exit_code == 2
        assert "not implemented in taocli/agcli yet" in result.output
        assert "no matching `wallet faucet` or top-level `faucet` command" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_transfer_alias_maps_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"ok":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "transfer",
                "--destination",
                "5dest",
                "--amount",
                "1.5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "transfer",
                "--dest",
                "5dest",
                "--amount",
                "1.5",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "miner",
                "--output",
                "json",
                "--yes",
                "--mortality-blocks",
                "32",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_transfer_alias_rejects_unsupported_all_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "transfer", "--all"])
        assert result.exit_code == 1
        assert "wallet transfer" in result.output
        assert "transfer-all" in result.output

    def test_btcli_wallet_transfer_alias_rejects_proxy_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "transfer", "--proxy", "5abc"])
        assert result.exit_code == 1
        assert "wallet transfer" in result.output
        assert "proxy execution" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_sign_alias_maps_flags(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"signature":"0xabc"}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "sign",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--message",
                "hello",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "wallet",
                "sign",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "miner",
                "--message",
                "hello",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_sign_alias_rejects_unsupported_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "sign", "--use-hotkey"])
        assert result.exit_code == 1
        assert "wallet sign" in result.output
        assert "signs with the coldkey only" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_wallet_verify_alias_maps_address_and_json_output(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout='{"valid":true}\n')
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "wallet",
                "verify",
                "--message",
                "hello",
                "--signature",
                "0xabc",
                "--address",
                "5signer",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "wallet",
                "verify",
                "--message",
                "hello",
                "--signature",
                "0xabc",
                "--signer",
                "5signer",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_wallet_verify_alias_rejects_public_key_flag(self, cli_runner):
        result = cli_runner.invoke(main, ["wallet", "verify", "-p", "0x1234"])
        assert result.exit_code == 1
        assert "wallet verify" in result.output
        assert "raw public key" in result.output

    def test_normalize_passthrough_args_maps_wallet_compatibility_slice(self):
        assert normalize_passthrough_args(
            [
                "wallet",
                "new-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "new-hotkey",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--name",
            "miner",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "create",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "create",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "associate-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "associate-hotkey",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "5hotkey",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "regen-coldkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--mnemonic",
                "horse cart dog",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "regen-coldkey",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--mnemonic",
            "horse cart dog",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "regen-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--mnemonic",
                "horse cart dog",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "regen-hotkey",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--name",
            "miner",
            "--mnemonic",
            "horse cart dog",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "sign",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--message",
                "hello",
                "--json-output",
            ]
        ) == [
            "wallet",
            "sign",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--message",
            "hello",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "verify",
                "--message",
                "hello",
                "--signature",
                "0xabc",
                "--address",
                "5signer",
                "--json-output",
            ]
        ) == [
            "wallet",
            "verify",
            "--message",
            "hello",
            "--signature",
            "0xabc",
            "--signer",
            "5signer",
            "--output",
            "json",
        ]
        with pytest.raises(click.ClickException, match="wallet new-hotkey"):
            normalize_passthrough_args(["wallet", "new-hotkey", "--n-words", "24"])
        with pytest.raises(click.ClickException, match="wallet create"):
            normalize_passthrough_args(["wallet", "create", "--use-password"])
        with pytest.raises(click.ClickException, match="wallet associate-hotkey"):
            normalize_passthrough_args(["wallet", "associate-hotkey", "--announce-only"])
        with pytest.raises(click.ClickException, match="wallet regen-coldkey"):
            normalize_passthrough_args(["wallet", "regen-coldkey", "--seed", "0x1234"])
        assert normalize_passthrough_args(
            [
                "wallet",
                "transfer",
                "--destination",
                "5dest",
                "--amount",
                "1.5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "transfer",
            "--dest",
            "5dest",
            "--amount",
            "1.5",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "set-identity",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--id-name",
                "alice validator",
                "--web-url",
                "https://example.com",
                "--image-url",
                "https://example.com/image.png",
                "--description",
                "validator",
                "--github",
                "unarbos/taocli",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "identity",
            "set",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--name",
            "alice validator",
            "--url",
            "https://example.com",
            "--image",
            "https://example.com/image.png",
            "--description",
            "validator",
            "--github",
            "unarbos/taocli",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.ClickException, match="wallet regen-hotkey"):
            normalize_passthrough_args(["wallet", "regen-hotkey", "--json", "/tmp/key.json"])
        with pytest.raises(click.ClickException, match="wallet transfer"):
            normalize_passthrough_args(["wallet", "transfer", "--all"])
        with pytest.raises(click.ClickException, match="wallet set-identity"):
            normalize_passthrough_args(["wallet", "set-identity", "--hotkey", "miner"])
        with pytest.raises(click.ClickException, match="wallet sign"):
            normalize_passthrough_args(["wallet", "sign", "--use-hotkey"])
        with pytest.raises(click.ClickException, match="wallet verify"):
            normalize_passthrough_args(["wallet", "verify", "-p", "0x1234"])
        assert unsupported_alias_message(["wallet", "regen-coldkeypub"], ["wallet", "regen-coldkeypub"])
        assert unsupported_alias_message(["wallet", "regen-hotkeypub"], ["wallet", "regen-hotkeypub"])
        assert unsupported_alias_message(["wallet", "faucet"], ["wallet", "faucet"])
        assert unsupported_alias_message(["subnets", "price"], ["subnet", "price"])

    def test_normalize_passthrough_args_maps_known_aliases(self):
        assert normalize_passthrough_args(["subnets", "hyperparameters", "--netuid", "1"]) == [
            "subnet",
            "hyperparams",
            "--netuid",
            "1",
        ]
        assert normalize_passthrough_args(["wallet", "balance", "--address", "5abc"]) == [
            "balance",
            "--address",
            "5abc",
        ]
        assert normalize_passthrough_args(["wallet", "balance", "--ss58", "5abc", "--json-output"]) == [
            "balance",
            "--address",
            "5abc",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "balance",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--no-prompt",
            ]
        ) == [
            "balance",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--yes",
        ]
        assert normalize_passthrough_args(["wallet", "balance", "--address", "5abc", "--prompt"]) == [
            "balance",
            "--address",
            "5abc",
        ]
        assert normalize_passthrough_args(["wallet", "balance", "--ss58-address", "5abc"]) == [
            "balance",
            "--address",
            "5abc",
        ]
        assert normalize_passthrough_args(["wallet", "balance", "--coldkey-ss58", "5abc"]) == [
            "balance",
            "--address",
            "5abc",
        ]
        assert normalize_passthrough_args(["wallet", "balance", "--key", "5abc"]) == [
            "balance",
            "--address",
            "5abc",
        ]
        assert normalize_passthrough_args(["wallet", "list", "--wallet-path", "/tmp/wallets", "--json-output"]) == [
            "wallet",
            "list",
            "--wallet-dir",
            "/tmp/wallets",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(["wallet", "get-identity", "--ss58", "5abc"]) == [
            "identity",
            "show",
            "--address",
            "5abc",
        ]
        assert normalize_passthrough_args(["wallet", "swap-check", "--address", "5abc"]) == [
            "wallet",
            "check-swap",
            "--address",
            "5abc",
        ]
        assert normalize_passthrough_args(["wallet", "swap-check", "--ss58", "5abc", "--json-output"]) == [
            "wallet",
            "check-swap",
            "--address",
            "5abc",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(["wallet", "overview", "--ss58", "5abc", "--json-output"]) == [
            "view",
            "portfolio",
            "--address",
            "5abc",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(["wallet", "transfer", "--destination", "5dest", "--amount", "1.5"]) == [
            "transfer",
            "--dest",
            "5dest",
            "--amount",
            "1.5",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "overview",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--no-prompt",
            ]
        ) == [
            "view",
            "portfolio",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--yes",
        ]
        assert normalize_passthrough_args(["wallet", "swap-hotkey", "--netuid", "1"]) == [
            "wallet",
            "swap-hotkey",
            "--netuid",
            "1",
        ]
        assert normalize_passthrough_args(["wallet", "swap-coldkey", "announce"]) == [
            "wallet",
            "swap-coldkey",
            "announce",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "new-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "new-hotkey",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--name",
            "miner",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "create",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "create",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "associate-hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "wallet",
            "associate-hotkey",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "5hotkey",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "sign",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--message",
                "hello",
                "--json-output",
            ]
        ) == [
            "wallet",
            "sign",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--message",
            "hello",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(
            [
                "wallet",
                "verify",
                "--message",
                "hello",
                "--signature",
                "0xabc",
                "--address",
                "5signer",
                "--json-output",
            ]
        ) == [
            "wallet",
            "verify",
            "--message",
            "hello",
            "--signature",
            "0xabc",
            "--signer",
            "5signer",
            "--output",
            "json",
        ]
        with pytest.raises(click.ClickException, match="wallet new-hotkey"):
            normalize_passthrough_args(["wallet", "new-hotkey", "--n-words", "24"])
        with pytest.raises(click.ClickException, match="wallet create"):
            normalize_passthrough_args(["wallet", "create", "--use-password"])
        with pytest.raises(click.ClickException, match="wallet associate-hotkey"):
            normalize_passthrough_args(["wallet", "associate-hotkey", "--announce-only"])
        with pytest.raises(click.ClickException, match="wallet sign"):
            normalize_passthrough_args(["wallet", "sign", "--use-hotkey"])
        with pytest.raises(click.ClickException, match="wallet verify"):
            normalize_passthrough_args(["wallet", "verify", "-p", "0x1234"])
        assert normalize_passthrough_args(["utils", "convert", "--rao", "1000000000"]) == [
            "utils",
            "convert",
            "--amount",
            "1000000000",
        ]
        assert normalize_passthrough_args(["utils", "convert", "--tao", "1.5"]) == [
            "utils",
            "convert",
            "--amount",
            "1.5",
            "--to-rao",
        ]
        assert normalize_passthrough_args(["utils", "latency", "--network", "ws://127.0.0.1:9944"]) == [
            "utils",
            "latency",
            "--extra",
            "ws://127.0.0.1:9944",
        ]
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(["utils", "convert", "--json-output"])
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(["utils", "latency", "--json-output"])
        assert normalize_passthrough_args(["stake", "list", "--ss58", "5abc", "--json-output"]) == [
            "stake",
            "list",
            "--address",
            "5abc",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "add",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "add",
            "--amount",
            "10",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "default",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "remove",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "remove",
            "--amount",
            "10",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "default",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "move",
                "--amount",
                "10",
                "--origin-netuid",
                "1",
                "--destination-netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "move",
            "--amount",
            "10",
            "--origin-netuid",
            "1",
            "--destination-netuid",
            "2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "transfer",
                "--amount",
                "10",
                "--origin-netuid",
                "1",
                "--destination-netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "transfer-stake",
            "--amount",
            "10",
            "--origin-netuid",
            "1",
            "--destination-netuid",
            "2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "5hotkey",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "wizard",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "wizard",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "set-claim",
                "alpha",
                "--netuids",
                "1,2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "set-claim",
            "--claim-type",
            "alpha",
            "--subnets",
            "1,2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "process-claim",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "process-claim",
            "--netuids",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "child",
                "set",
                "--netuid",
                "1",
                "--children",
                "5child1",
                "--children",
                "5child2",
                "--proportions",
                "0.3",
                "--proportions",
                "0.7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5parent",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "set-children",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "5parent",
            "--output",
            "json",
            "--yes",
            "--children",
            "0.3:5child1,0.7:5child2",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "child",
                "take",
                "--netuid",
                "7",
                "--take",
                "0.12",
                "--child-hotkey-ss58",
                "5child",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "childkey-take",
            "--netuid",
            "7",
            "--take",
            "0.12",
            "--hotkey-address",
            "5child",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.UsageError, match="interactive proportion prompting"):
            normalize_passthrough_args(["stake", "child", "set", "--children", "5child1"])
        with pytest.raises(click.UsageError, match="read mode is not implemented"):
            normalize_passthrough_args(["stake", "child", "take", "--netuid", "1"])
        assert normalize_passthrough_args(
            [
                "stake",
                "auto",
                "--ss58",
                "5abc",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "show-auto",
            "--address",
            "5abc",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "set-auto",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "set-auto",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "5hotkey",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        with pytest.raises(click.ClickException, match="stake set-auto"):
            normalize_passthrough_args(["stake", "set-auto", "--proxy"])
        with pytest.raises(click.ClickException, match="stake swap"):
            normalize_passthrough_args(["stake", "swap", "--safe-staking"])
        with pytest.raises(click.UsageError, match="stake child get"):
            normalize_passthrough_args(["stake", "child", "get"])
        assert normalize_passthrough_args(
            [
                "axon",
                "set",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "1",
            ]
        ) == [
            "serve",
            "axon",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
            "1",
        ]
        with pytest.raises(click.ClickException, match="axon set"):
            normalize_passthrough_args(["axon", "set", "--wait-for-inclusion"])
        with pytest.raises(click.ClickException, match="axon set"):
            normalize_passthrough_args(["axon", "set", "--ip-type", "6"])
        assert normalize_passthrough_args(
            [
                "subnets",
                "register",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
                "--netuid",
                "2",
            ]
        ) == [
            "subnet",
            "register-neuron",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
            "--netuid",
            "2",
        ]
        assert normalize_passthrough_args(["subnets", "get-identity", "--netuid", "1"]) == [
            "subnet",
            "get-identity",
            "--netuid",
            "1",
        ]
        assert normalize_passthrough_args(
            ["subnets", "show", "--netuid", "2", "--json-output", "--no-prompt"]
        ) == [
            "subnet",
            "show",
            "--netuid",
            "2",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "subnets",
                "set-symbol",
                "--netuid",
                "2",
                "シ",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "subnet",
            "set-symbol",
            "--netuid",
            "2",
            "--symbol",
            "シ",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(["subnets", "check-start", "--netuid", "5", "--json-output", "--no-prompt"])
        assert normalize_passthrough_args(
            [
                "subnets",
                "create",
                "--subnet-name",
                "test-subnet",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--proxy",
                "5proxy",
                "--repo",
                "https://github.com/unarbos/test-subnet",
                "--subnet-contact",
                "ops@example.com",
                "--url",
                "https://example.com",
                "--discord-handle",
                "discord.gg/example",
                "--description",
                "test subnet",
                "--additional-info",
                "extra context",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "subnet",
            "register-with-identity",
            "--name",
            "test-subnet",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--proxy",
            "5proxy",
            "--github",
            "https://github.com/unarbos/test-subnet",
            "--contact",
            "ops@example.com",
            "--url",
            "https://example.com",
            "--discord",
            "discord.gg/example",
            "--description",
            "test subnet",
            "--additional",
            "extra context",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "subnets",
                "pow-register",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--no-prompt",
                "--processors",
                "4",
                "--netuid",
                "2",
            ]
        ) == [
            "subnet",
            "pow",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--yes",
            "--threads",
            "4",
            "--netuid",
            "2",
        ]
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(["subnets", "pow-register", "--netuid", "2", "--json-output"])
        with pytest.raises(click.ClickException, match="subnets show flag '--mechid'"):
            normalize_passthrough_args(["subnets", "show", "--netuid", "2", "--mechid", "1"])
        with pytest.raises(click.ClickException, match="subnets create flag '--logo-url'"):
            normalize_passthrough_args(["subnets", "create", "--subnet-name", "test", "--logo-url", "logo"])
        assert normalize_passthrough_args(["subnets", "create"]) == [
            "subnet",
            "register-with-identity",
        ]
        with pytest.raises(click.ClickException, match="Cannot specify both '--json-output' and '--prompt'"):
            normalize_passthrough_args(["subnets", "create", "--json-output"])
        with pytest.raises(click.ClickException, match="btcli-compatible `subnets create` flag '--proxy' requires a value"):
            normalize_passthrough_args(["subnets", "create", "--subnet-name", "test", "--proxy"])
        with pytest.raises(click.ClickException, match="subnets create flag '--mev-protection'"):
            normalize_passthrough_args(["subnets", "create", "--subnet-name", "test", "--mev-protection"])
        assert normalize_passthrough_args(
            [
                "subnets",
                "set-identity",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--subnet-name",
                "MySubnet",
                "--github-repo",
                "https://github.com/example/repo",
                "--subnet-url",
                "https://example.com",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "identity",
            "set-subnet",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--name",
            "MySubnet",
            "--github",
            "https://github.com/example/repo",
            "--url",
            "https://example.com",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.ClickException, match="Cannot specify both '--json-output' and '--prompt'"):
            normalize_passthrough_args(["subnets", "set-identity", "--netuid", "1", "--json-output"])
        with pytest.raises(click.ClickException, match="subnets set-identity flag '--subnet-contact'"):
            normalize_passthrough_args(
                ["subnets", "set-identity", "--netuid", "1", "--subnet-name", "test", "--subnet-contact", "team@example.com"]
            )
        with pytest.raises(click.ClickException, match="btcli-compatible `subnets set-identity` flag '--proxy' requires a value"):
            normalize_passthrough_args(["subnets", "set-identity", "--netuid", "1", "--subnet-name", "test", "--proxy"])
        with pytest.raises(click.ClickException, match="subnets set-symbol flag '--proxy'"):
            normalize_passthrough_args(["subnets", "set-symbol", "--netuid", "2", "シ", "--proxy", "5abc"])
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(
                [
                    "subnets",
                    "start",
                    "--netuid",
                    "2",
                    "--wallet-name",
                    "alice",
                    "--wallet-path",
                    "/tmp/wallets",
                    "--hotkey",
                    "miner",
                    "--proxy",
                    "5proxy",
                    "--json-output",
                    "--no-prompt",
                ]
            )
        assert normalize_passthrough_args(
            [
                "subnets",
                "start",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--proxy",
                "5proxy",
                "--no-prompt",
            ]
        ) == [
            "subnet",
            "start",
            "--netuid",
            "2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--proxy",
            "5proxy",
            "--yes",
        ]
        assert normalize_passthrough_args(
            ["subnets", "mechanisms", "count", "--netuid", "5", "--json-output", "--no-prompt"]
        ) == [
            "subnet",
            "mechanism-count",
            "--netuid",
            "5",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "subnets",
                "mechanisms",
                "set",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--mech-count",
                "3",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "subnet",
            "set-mechanism-count",
            "--netuid",
            "5",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--count",
            "3",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            ["subnets", "mechanisms", "emissions", "--netuid", "5", "--json-output", "--no-prompt"]
        ) == [
            "subnet",
            "emission-split",
            "--netuid",
            "5",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "subnets",
                "mechanisms",
                "split-emissions",
                "--netuid",
                "5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--split",
                "60,40",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "subnet",
            "set-emission-split",
            "--netuid",
            "5",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--weights",
            "60,40",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.ClickException, match="subnets start flag '--announce-only'"):
            normalize_passthrough_args(["subnets", "start", "--netuid", "2", "--announce-only"])
        with pytest.raises(click.ClickException, match="btcli-compatible `subnets start` flag '--proxy' requires a value"):
            normalize_passthrough_args(["subnets", "start", "--netuid", "2", "--proxy"])
        with pytest.raises(click.ClickException, match="subnets mechanisms count flag '--quiet'"):
            normalize_passthrough_args(["subnets", "mechanisms", "count", "--netuid", "5", "--quiet"])
        with pytest.raises(click.ClickException, match="subnets mechanisms set flag '--announce-only'"):
            normalize_passthrough_args(["subnets", "mechanisms", "set", "--netuid", "5", "--announce-only"])
        with pytest.raises(click.ClickException, match="btcli-compatible `subnets mechanisms set` flag '--count' requires a value"):
            normalize_passthrough_args(["subnets", "mechanisms", "set", "--netuid", "5", "--count"])
        with pytest.raises(click.ClickException, match="subnets mechanisms set flag '--proxy'"):
            normalize_passthrough_args(["subnets", "mechanisms", "set", "--netuid", "5", "--proxy"])
        with pytest.raises(click.ClickException, match="subnets mechanisms emissions flag '--verbose'"):
            normalize_passthrough_args(["subnets", "mechanisms", "emissions", "--netuid", "5", "--verbose"])
        with pytest.raises(click.ClickException, match="subnets mechanisms split-emissions flag '--wait-for-inclusion'"):
            normalize_passthrough_args(["subnets", "mechanisms", "split-emissions", "--netuid", "5", "--wait-for-inclusion"])
        with pytest.raises(click.ClickException, match="btcli-compatible `subnets mechanisms split-emissions` flag '--split' requires a value"):
            normalize_passthrough_args(["subnets", "mechanisms", "split-emissions", "--netuid", "5", "--split"])
        assert normalize_passthrough_args(["subnets", "set-symbol", "シ", "--json-output"]) == [
            "subnet",
            "set-symbol",
            "--symbol",
            "シ",
            "--output",
            "json",
        ]
        with pytest.raises(click.ClickException, match="requires a subnet symbol"):
            normalize_passthrough_args(["subnets", "set-symbol", "--netuid", "2", "--json-output"])
        with pytest.raises(click.ClickException, match="accepts a single symbol value"):
            normalize_passthrough_args(["subnets", "set-symbol", "--netuid", "2", "--symbol", "A", "B"])
        with pytest.raises(click.ClickException, match="subnets show flag '--sort'"):
            normalize_passthrough_args(["subnets", "show", "--netuid", "2", "--sort", "name"])
        assert normalize_passthrough_args(["sudo", "trim", "--netuid", "1", "--max", "64"]) == [
            "subnet",
            "trim",
            "--netuid",
            "1",
            "--max",
            "64",
        ]
        assert normalize_passthrough_args(["sudo", "trim", "--netuid", "1", "--max", "64"]) == [
            "subnet",
            "trim",
            "--netuid",
            "1",
            "--max",
            "64",
        ]
        assert normalize_passthrough_args(["crowd", "update", "--crowdloan-id", "7", "--end", "99"]) == [
            "crowdloan",
            "update-end",
            "--crowdloan-id",
            "7",
            "--end",
            "99",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "list",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "list",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "info",
                "--crowdloan-id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "info",
            "--crowdloan-id",
            "7",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "contributors",
                "--crowdloan-id",
                "7",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "contributors",
            "--crowdloan-id",
            "7",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "create",
                "--deposit",
                "10",
                "--min-contribution",
                "1",
                "--cap",
                "1000",
                "--end-block",
                "500",
                "--target-address",
                "5target",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "create",
            "--deposit",
            "10",
            "--min-contribution",
            "1",
            "--cap",
            "1000",
            "--end-block",
            "500",
            "--target",
            "5target",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "contribute",
                "--id",
                "7",
                "--amount",
                "12.5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "contribute",
            "--crowdloan-id",
            "7",
            "--amount",
            "12.5",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "refund",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "refund",
            "--crowdloan-id",
            "7",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "withdraw",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "withdraw",
            "--crowdloan-id",
            "7",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "finalize",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "finalize",
            "--crowdloan-id",
            "7",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "crowd",
                "dissolve",
                "--id",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "crowdloan",
            "dissolve",
            "--crowdloan-id",
            "7",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "add",
                "--position-id",
                "1",
                "--liquidity",
                "1.25",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "add",
            "--position-id",
            "1",
            "--amount",
            "1250000000",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "add",
                "--position-id",
                "1",
                "--liquidity",
                "1.25",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "add",
            "--position-id",
            "1",
            "--amount",
            "1250000000",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "modify",
                "--position-id",
                "1",
                "--liquidity-delta",
                "0.5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "modify",
            "--position-id",
            "1",
            "--delta",
            "500000000",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "remove",
                "--position-id",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "remove",
            "--position-id",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "add",
                "--position-id",
                "1",
                "--liquidity",
                "1.25",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "add",
            "--position-id",
            "1",
            "--amount",
            "1250000000",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "add",
                "--position-id",
                "1",
                "--liquidity",
                "1.25",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "add",
            "--position-id",
            "1",
            "--amount",
            "1250000000",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "modify",
                "--position-id",
                "1",
                "--liquidity-delta",
                "0.5",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "modify",
            "--position-id",
            "1",
            "--delta",
            "500000000",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "liquidity",
                "remove",
                "--position-id",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "liquidity",
            "remove",
            "--position-id",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.ClickException, match="liquidity add"):
            normalize_passthrough_args(["liquidity", "add", "--proxy", "5proxy"])
        with pytest.raises(click.ClickException, match="liquidity remove"):
            normalize_passthrough_args(["liquidity", "remove", "--all"])
        with pytest.raises(click.ClickException, match="Invalid btcli liquidity amount"):
            normalize_passthrough_args(["liquidity", "add", "--liquidity", "not-a-number"])
        assert normalize_passthrough_args(
            [
                "proxy",
                "create",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--proxy-type",
                "Any",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "proxy",
            "create-pure",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--proxy-type",
            "any",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "proxy",
                "remove",
                "--all",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "proxy",
            "remove-all",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "proxy",
                "add",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--proxy-type",
                "RootWeights",
                "--delegate",
                "5proxy",
            ]
        ) == [
            "proxy",
            "add",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
            "--proxy-type",
            "root_weights",
            "--delegate",
            "5proxy",
        ]
        with pytest.raises(click.ClickException, match="proxy create"):
            normalize_passthrough_args(["proxy", "create", "--wait-for-inclusion"])
        with pytest.raises(click.ClickException, match="proxy type 'NonFungible'"):
            normalize_passthrough_args(["proxy", "create", "--proxy-type", "NonFungible"])
        assert normalize_passthrough_args(
            [
                "weights",
                "commit",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--uids",
                "1,2",
                "--weights",
                "1,2",
                "--json-output",
                "--no-prompt",
                "--version-key",
                "7",
            ]
        ) == [
            "weights",
            "commit",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--output",
            "json",
            "--yes",
            "--version-key",
            "7",
            "--weights",
            "1:32768,2:65535",
        ]
        assert normalize_passthrough_args(
            [
                "weights",
                "reveal",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "miner",
                "--uids",
                "1,2",
                "--weights",
                "1,2",
                "--json-output",
                "--no-prompt",
                "--version-key",
                "7",
            ]
        ) == [
            "weights",
            "reveal",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "miner",
            "--output",
            "json",
            "--yes",
            "--version-key",
            "7",
            "--weights",
            "1:32768,2:65535",
        ]
        assert normalize_passthrough_args(["utils", "convert", "--tao", "1.5"]) == [
            "utils",
            "convert",
            "--amount",
            "1.5",
            "--to-rao",
        ]
        assert normalize_passthrough_args(["utils", "latency", "--network", "ws://127.0.0.1:9944"]) == [
            "utils",
            "latency",
            "--extra",
            "ws://127.0.0.1:9944",
        ]
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(["utils", "convert", "--json-output"])
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(["utils", "latency", "--json-output"])
        assert normalize_passthrough_args(["stake", "list", "--ss58", "5abc", "--json-output"]) == [
            "stake",
            "list",
            "--address",
            "5abc",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "add",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "add",
            "--amount",
            "10",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "default",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "remove",
                "--amount",
                "10",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
                "--era",
                "24",
            ]
        ) == [
            "stake",
            "remove",
            "--amount",
            "10",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "default",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "24",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "transfer",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--dest",
                "5dest",
                "--amount",
                "10",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "transfer-stake",
            "--origin-netuid",
            "1",
            "--dest-netuid",
            "2",
            "--dest",
            "5dest",
            "--amount",
            "10",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "5hotkey",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "move",
                "--from",
                "5src",
                "--to",
                "5dst",
                "--origin-netuid",
                "1",
                "--dest-netuid",
                "2",
                "--amount",
                "10",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--prompt",
                "--era",
                "24",
            ]
        ) == [
            "stake",
            "move",
            "--from",
            "5src",
            "--to",
            "5dst",
            "--origin-netuid",
            "1",
            "--dest-netuid",
            "2",
            "--amount",
            "10",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--mortality-blocks",
            "24",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "wizard",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "wizard",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "swap",
                "--netuid",
                "2",
                "--amount",
                "10",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "5hotkey",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "swap",
            "--netuid",
            "2",
            "--amount",
            "10",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-address",
            "5hotkey",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "auto",
                "--ss58",
                "5abc",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "show-auto",
            "--address",
            "5abc",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "set-auto",
                "--netuid",
                "7",
                "--hotkey",
                "5hotkey",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--json-output",
                "--no-prompt",
                "--period",
                "32",
            ]
        ) == [
            "stake",
            "set-auto",
            "--netuid",
            "7",
            "--hotkey-address",
            "5hotkey",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--output",
            "json",
            "--yes",
            "--mortality-blocks",
            "32",
        ]
        assert normalize_passthrough_args(
            [
                "stake",
                "set-claim",
                "Manual",
                "--netuids",
                "1,2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "set-claim",
            "--claim-type",
            "manual",
            "--subnets",
            "1,2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.ClickException, match="stake set-auto` flag '--proxy'"):
            normalize_passthrough_args(["stake", "set-auto", "--proxy"])
        assert normalize_passthrough_args(
            [
                "stake",
                "process-claim",
                "--netuid",
                "7",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "process-claim",
            "--netuids",
            "7",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.ClickException, match="--safe-staking"):
            normalize_passthrough_args(["stake", "swap", "--safe-staking"])
        with pytest.raises(click.UsageError, match="stake child get"):
            normalize_passthrough_args(["stake", "child", "get"])
        assert normalize_passthrough_args(
            [
                "axon",
                "set",
                "--netuid",
                "1",
                "--ip",
                "1.2.3.4",
                "--port",
                "8091",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "serve",
            "axon",
            "--netuid",
            "1",
            "--ip",
            "1.2.3.4",
            "--port",
            "8091",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        assert normalize_passthrough_args(
            [
                "axon",
                "reset",
                "--netuid",
                "1",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--json-output",
                "--no-prompt",
            ]
        ) == [
            "serve",
            "reset",
            "--netuid",
            "1",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--output",
            "json",
            "--yes",
        ]
        with pytest.raises(click.ClickException, match="wait-for-inclusion"):
            normalize_passthrough_args(["axon", "set", "--wait-for-inclusion"])
        with pytest.raises(click.ClickException, match="--ip-type"):
            normalize_passthrough_args(["axon", "set", "--ip-type", "6"])
        assert normalize_passthrough_args(
            [
                "stake",
                "list",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--no-prompt",
            ]
        ) == [
            "stake",
            "list",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--yes",
        ]
        assert normalize_passthrough_args(["subnets", "get-identity", "--netuid", "1"]) == [
            "subnet",
            "get-identity",
            "--netuid",
            "1",
        ]
        assert normalize_passthrough_args(
            [
                "subnets",
                "register",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--period",
                "32",
                "--no-prompt",
                "--json-output",
            ]
        ) == [
            "subnet",
            "register-neuron",
            "--netuid",
            "2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--mortality-blocks",
            "32",
            "--yes",
            "--output",
            "json",
        ]
        assert normalize_passthrough_args(
            [
                "subnets",
                "pow-register",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--processors",
                "6",
                "--prompt",
            ]
        ) == [
            "subnet",
            "pow",
            "--netuid",
            "2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--threads",
            "6",
        ]
        with pytest.raises(click.NoSuchOption, match="--json-output"):
            normalize_passthrough_args(["subnets", "pow-register", "--netuid", "2", "--json-output"])
        assert normalize_passthrough_args(["sudo", "trim", "--netuid", "1", "--max", "64"]) == [
            "subnet",
            "trim",
            "--netuid",
            "1",
            "--max",
            "64",
        ]
        assert normalize_passthrough_args(["sudo", "trim", "--netuid", "1", "--max", "64"]) == [
            "subnet",
            "trim",
            "--netuid",
            "1",
            "--max",
            "64",
        ]
        assert normalize_passthrough_args(["crowd", "update", "--crowdloan-id", "7", "--end", "99"]) == [
            "crowdloan",
            "update-end",
            "--crowdloan-id",
            "7",
            "--end",
            "99",
        ]
        assert normalize_passthrough_args(
            ["axon", "set", "--netuid", "1", "--ip", "1.2.3.4", "--port", "8091"]
        ) == [
            "serve",
            "axon",
            "--netuid",
            "1",
            "--ip",
            "1.2.3.4",
            "--port",
            "8091",
        ]
        assert normalize_passthrough_args(
            [
                "weights",
                "commit",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--uids",
                "0,1",
                "--weights",
                "0.5,1.0",
                "--salt",
                "123,456",
                "--version-key",
                "9002000",
                "--no-prompt",
                "--json-output",
            ]
        ) == [
            "weights",
            "commit",
            "--netuid",
            "2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--salt",
            "123,456",
            "--version-key",
            "9002000",
            "--yes",
            "--output",
            "json",
            "--weights",
            "0:32768,1:65535",
        ]
        assert normalize_passthrough_args(
            [
                "weights",
                "reveal",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--uids",
                "3",
                "--weights",
                "1.0",
                "--salt",
                "42",
                "--version-key",
                "9",
                "--prompt",
            ]
        ) == [
            "weights",
            "reveal",
            "--netuid",
            "2",
            "--wallet",
            "alice",
            "--wallet-dir",
            "/tmp/wallets",
            "--hotkey-name",
            "default",
            "--salt",
            "42",
            "--version-key",
            "9",
            "--weights",
            "3:65535",
        ]

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_btcli_weights_commit_rewrites_to_agcli_syntax(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="committed\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "weights",
                "commit",
                "--netuid",
                "2",
                "--wallet-name",
                "alice",
                "--wallet-path",
                "/tmp/wallets",
                "--hotkey",
                "default",
                "--uids",
                "0,1",
                "--weights",
                "0.5,1.0",
                "--salt",
                "123,456",
                "--version-key",
                "9002000",
                "--no-prompt",
                "--json-output",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "weights",
                "commit",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--salt",
                "123,456",
                "--version-key",
                "9002000",
                "--yes",
                "--output",
                "json",
                "--weights",
                "0:32768,1:65535",
            ],
            check=False,
            capture=True,
        )

    def test_btcli_weights_require_matching_uids_and_weights(self, cli_runner):
        result = cli_runner.invoke(main, ["weights", "commit", "--uids", "0,1", "--weights", "1.0"])
        assert result.exit_code == 1
        assert "same number of entries" in result.output

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_agcli_style_weights_commit_passthrough_is_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="committed\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "weights",
                "commit",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--weights",
                "0:32768,1:65535",
                "--salt",
                "123,456",
                "--version-key",
                "9002000",
                "--yes",
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "weights",
                "commit",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--weights",
                "0:32768,1:65535",
                "--salt",
                "123,456",
                "--version-key",
                "9002000",
                "--yes",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

    @patch.object(_cli_main_module, "AgcliRunner")
    def test_agcli_style_weights_reveal_passthrough_is_unchanged(self, mock_cls, cli_runner):
        mock_instance = MagicMock()
        mock_instance.run.return_value = make_completed_process(stdout="revealed\n")
        mock_cls.return_value = mock_instance
        result = cli_runner.invoke(
            main,
            [
                "weights",
                "reveal",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--weights",
                "0:32768,1:65535",
                "--salt",
                "123,456",
                "--version-key",
                "9002000",
                "--yes",
                "--output",
                "json",
            ],
        )
        assert result.exit_code == 0
        mock_instance.run.assert_called_once_with(
            [
                "weights",
                "reveal",
                "--netuid",
                "2",
                "--wallet",
                "alice",
                "--wallet-dir",
                "/tmp/wallets",
                "--hotkey-name",
                "default",
                "--weights",
                "0:32768,1:65535",
                "--salt",
                "123,456",
                "--version-key",
                "9002000",
                "--yes",
                "--output",
                "json",
            ],
            check=False,
            capture=True,
        )

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
