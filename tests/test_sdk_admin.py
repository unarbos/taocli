"""Tests for the Admin SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.admin import Admin


@pytest.fixture
def admin(mock_subprocess):
    return Admin(AgcliRunner())


class TestAdmin:
    def test_set_tempo(self, admin, mock_subprocess):
        admin.set_tempo(1, 100)
        cmd = mock_subprocess.call_args[0][0]
        assert "admin" in cmd and "set-tempo" in cmd
        assert "--netuid" in cmd and "--tempo" in cmd

    def test_set_tempo_with_sudo(self, admin, mock_subprocess):
        admin.set_tempo(1, 100, sudo_key="//Alice")
        cmd = mock_subprocess.call_args[0][0]
        assert "--sudo-key" in cmd

    def test_set_max_validators(self, admin, mock_subprocess):
        admin.set_max_validators(1, 64)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-max-validators" in cmd and "--max" in cmd

    def test_set_max_uids(self, admin, mock_subprocess):
        admin.set_max_uids(1, 256)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-max-uids" in cmd

    def test_set_immunity_period(self, admin, mock_subprocess):
        admin.set_immunity_period(1, 7200)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-immunity-period" in cmd

    def test_set_min_weights(self, admin, mock_subprocess):
        admin.set_min_weights(1, 1)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-min-weights" in cmd

    def test_set_max_weight_limit(self, admin, mock_subprocess):
        admin.set_max_weight_limit(1, 65535)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-max-weight-limit" in cmd

    def test_set_weights_rate_limit(self, admin, mock_subprocess):
        admin.set_weights_rate_limit(1, 100)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-weights-rate-limit" in cmd

    def test_set_commit_reveal(self, admin, mock_subprocess):
        admin.set_commit_reveal(1, True)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-commit-reveal" in cmd and "--enabled" in cmd

    def test_set_difficulty(self, admin, mock_subprocess):
        admin.set_difficulty(1, 1000000)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-difficulty" in cmd

    def test_set_activity_cutoff(self, admin, mock_subprocess):
        admin.set_activity_cutoff(1, 5000)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-activity-cutoff" in cmd

    def test_set_default_take(self, admin, mock_subprocess):
        admin.set_default_take(11796)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-default-take" in cmd and "--take" in cmd

    def test_set_tx_rate_limit(self, admin, mock_subprocess):
        admin.set_tx_rate_limit(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-tx-rate-limit" in cmd

    def test_set_min_difficulty(self, admin, mock_subprocess):
        admin.set_min_difficulty(1, 100)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-min-difficulty" in cmd

    def test_set_max_difficulty(self, admin, mock_subprocess):
        admin.set_max_difficulty(1, 999999)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-max-difficulty" in cmd

    def test_set_adjustment_interval(self, admin, mock_subprocess):
        admin.set_adjustment_interval(1, 100)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-adjustment-interval" in cmd

    def test_set_kappa(self, admin, mock_subprocess):
        admin.set_kappa(1, 32767)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-kappa" in cmd

    def test_set_rho(self, admin, mock_subprocess):
        admin.set_rho(1, 10)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-rho" in cmd

    def test_set_min_burn(self, admin, mock_subprocess):
        admin.set_min_burn(1, "0.1")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-min-burn" in cmd

    def test_set_max_burn(self, admin, mock_subprocess):
        admin.set_max_burn(1, "100")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-max-burn" in cmd

    def test_set_liquid_alpha(self, admin, mock_subprocess):
        admin.set_liquid_alpha(1, True)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-liquid-alpha" in cmd

    def test_set_alpha_values(self, admin, mock_subprocess):
        admin.set_alpha_values(1, "0.1", "0.9")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-alpha-values" in cmd and "--alpha-low" in cmd

    def test_set_yuma3(self, admin, mock_subprocess):
        admin.set_yuma3(1, True)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-yuma3" in cmd

    def test_set_bonds_penalty(self, admin, mock_subprocess):
        admin.set_bonds_penalty(1, 100)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-bonds-penalty" in cmd

    def test_set_stake_threshold(self, admin, mock_subprocess):
        admin.set_stake_threshold("1000")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-stake-threshold" in cmd

    def test_set_network_registration(self, admin, mock_subprocess):
        admin.set_network_registration(1, True)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-network-registration" in cmd

    def test_set_pow_registration(self, admin, mock_subprocess):
        admin.set_pow_registration(1, False)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-pow-registration" in cmd

    def test_set_adjustment_alpha(self, admin, mock_subprocess):
        admin.set_adjustment_alpha(1, "0.5")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-adjustment-alpha" in cmd

    def test_set_subnet_moving_alpha(self, admin, mock_subprocess):
        admin.set_subnet_moving_alpha("0.9")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-subnet-moving-alpha" in cmd

    def test_set_mechanism_count(self, admin, mock_subprocess):
        admin.set_mechanism_count(1, 2)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-mechanism-count" in cmd

    def test_set_mechanism_emission_split(self, admin, mock_subprocess):
        admin.set_mechanism_emission_split(1, "50,50")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-mechanism-emission-split" in cmd

    def test_set_nominator_min_stake(self, admin, mock_subprocess):
        admin.set_nominator_min_stake("100")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-nominator-min-stake" in cmd

    def test_raw(self, admin, mock_subprocess):
        admin.raw("sudo_set_tempo", args="[1, 100]")
        cmd = mock_subprocess.call_args[0][0]
        assert "raw" in cmd and "--call" in cmd and "--args" in cmd

    def test_raw_with_sudo_key(self, admin, mock_subprocess):
        admin.raw("sudo_set_tempo", sudo_key="//Alice")
        cmd = mock_subprocess.call_args[0][0]
        assert "--sudo-key" in cmd

    def test_list(self, admin, mock_subprocess):
        admin.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "admin" in cmd and "list" in cmd

    def test_hyperparameter_mutation_help(self, admin):
        command = admin.hyperparameter_mutation_help(
            "set-tempo",
            9,
            value_flag="--tempo",
            value=360,
            sudo_key=" //Alice ",
        )
        assert command == "agcli admin set-tempo --netuid 9 --tempo 360 --sudo-key //Alice"

    def test_hyperparameter_mutation_help_with_bool(self, admin):
        command = admin.hyperparameter_mutation_help(
            "set-commit-reveal",
            9,
            value_flag="--enabled",
            value=True,
        )
        assert command == "agcli admin set-commit-reveal --netuid 9 --enabled true"

    def test_hyperparameter_mutation_help_rejects_invalid_netuid(self, admin):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            admin.hyperparameter_mutation_help("set-tempo", 0, value_flag="--tempo", value=1)

    def test_hyperparameter_mutation_help_rejects_empty_command(self, admin):
        with pytest.raises(ValueError, match="command cannot be empty"):
            admin.hyperparameter_mutation_help("   ", 1, value_flag="--tempo", value=1)

    def test_hyperparameter_mutation_help_rejects_empty_value_flag(self, admin):
        with pytest.raises(ValueError, match="value_flag cannot be empty"):
            admin.hyperparameter_mutation_help("set-tempo", 1, value_flag="   ", value=1)

    def test_hyperparameter_mutation_help_rejects_empty_sudo_key(self, admin):
        with pytest.raises(ValueError, match="sudo_key cannot be empty"):
            admin.hyperparameter_mutation_help("set-tempo", 1, value_flag="--tempo", value=1, sudo_key="   ")

    def test_hyperparameter_mutation_help_stringifies_float(self, admin):
        command = admin.hyperparameter_mutation_help("set-adjustment-alpha", 9, value_flag="--alpha", value=0.5)
        assert command == "agcli admin set-adjustment-alpha --netuid 9 --alpha 0.5"

    def test_hyperparameter_workflow_help_base(self, admin):
        helpers = admin.hyperparameter_workflow_help(9)
        assert helpers == {
            "netuid": 9,
            "show": "agcli subnet show --netuid 9",
            "get": "agcli subnet hyperparams --netuid 9",
            "owner_param_list": "agcli subnet set-param --netuid 9 --param list",
            "admin_list": "agcli admin list",
            "raw": "agcli admin raw --call <sudo-call>",
            "sudo_note": (
                "Use admin list to discover the exact set-* command for root-only knobs, then "
                "run it with --sudo-key. Subnet-owner knobs can usually use subnet set-param instead."
            ),
        }

    def test_hyperparameter_workflow_help_with_command_stub(self, admin):
        helpers = admin.hyperparameter_workflow_help(9, command=" set-tempo ", value_flag=" --tempo ")
        assert helpers["command"] == "set-tempo"
        assert helpers["value_flag"] == "--tempo"
        assert helpers["set"] == "agcli admin set-tempo --netuid 9 --tempo <value>"

    def test_hyperparameter_workflow_help_with_full_command(self, admin):
        helpers = admin.hyperparameter_workflow_help(
            9,
            command="set-commit-reveal",
            value_flag="--enabled",
            value=True,
            sudo_key=" //Alice ",
        )
        assert helpers["command"] == "set-commit-reveal"
        assert helpers["value_flag"] == "--enabled"
        assert helpers["value"] == "true"
        assert helpers["sudo_key"] == "//Alice"
        assert helpers["set"] == "agcli admin set-commit-reveal --netuid 9 --enabled true --sudo-key //Alice"

    def test_hyperparameter_workflow_help_rejects_value_flag_without_command(self, admin):
        with pytest.raises(ValueError, match="value_flag requires command"):
            admin.hyperparameter_workflow_help(9, value_flag="--tempo")

    def test_hyperparameter_workflow_help_rejects_value_without_command(self, admin):
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            admin.hyperparameter_workflow_help(9, value=12)

    def test_hyperparameter_workflow_help_rejects_value_without_flag(self, admin):
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            admin.hyperparameter_workflow_help(9, command="set-tempo", value=12)

    def test_hyperparameter_workflow_help_rejects_sudo_key_without_command(self, admin):
        with pytest.raises(ValueError, match="sudo_key requires command"):
            admin.hyperparameter_workflow_help(9, sudo_key="//Alice")

    def test_hyperparameter_workflow_help_rejects_empty_command(self, admin):
        with pytest.raises(ValueError, match="command cannot be empty"):
            admin.hyperparameter_workflow_help(9, command="   ")

    def test_hyperparameter_workflow_help_rejects_empty_value_flag(self, admin):
        with pytest.raises(ValueError, match="value_flag cannot be empty"):
            admin.hyperparameter_workflow_help(9, command="set-tempo", value_flag="   ")

    def test_hyperparameter_workflow_help_rejects_empty_sudo_key(self, admin):
        with pytest.raises(ValueError, match="sudo_key cannot be empty"):
            admin.hyperparameter_workflow_help(9, command="set-tempo", sudo_key="   ")

    def test_hyperparameter_workflow_help_rejects_invalid_netuid(self, admin):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            admin.hyperparameter_workflow_help(0)

    def test_hyperparameter_workflow_help_stringifies_float_value(self, admin):
        helpers = admin.hyperparameter_workflow_help(9, command="set-adjustment-alpha", value_flag="--alpha", value=0.5)
        assert helpers["value"] == "0.5"
        assert helpers["set"] == "agcli admin set-adjustment-alpha --netuid 9 --alpha 0.5"

    def test_hyperparameter_workflow_help_stringifies_bool_value(self, admin):
        helpers = admin.hyperparameter_workflow_help(
            9, command="set-network-registration", value_flag="--allowed", value=False
        )
        assert helpers["value"] == "false"
        assert helpers["set"] == "agcli admin set-network-registration --netuid 9 --allowed false"
