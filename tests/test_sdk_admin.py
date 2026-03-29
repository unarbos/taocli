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
        assert helpers["netuid"] == 9
        assert helpers["scope"] == "subnet_admin"
        assert helpers["show"] == "agcli subnet show --netuid 9"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 9"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 9 --param list"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["raw"] == "agcli admin raw --call <sudo-call>"
        assert helpers["sudo_note"] == (
            "Use admin list to discover the exact set-* command for root-only knobs, then "
            "run it with --sudo-key. Subnet-owner knobs can usually use subnet set-param instead."
        )
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]
        assert helpers["primary_read"] == "agcli subnet hyperparams --netuid 9"
        assert helpers["mutation_check"] == "agcli admin list"
        assert "set" not in helpers
        assert helpers["summary"]

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

    def test_hyperparameter_workflow_help_rejects_boolean_netuid(self, admin):
        with pytest.raises(ValueError, match="netuid must be an integer"):
            admin.hyperparameter_workflow_help(True)

    def test_hyperparameter_workflow_help_stringifies_bool_value(self, admin):
        helpers = admin.hyperparameter_workflow_help(
            9, command="set-network-registration", value_flag="--allowed", value=False
        )
        assert helpers["value"] == "false"
        assert helpers["set"] == "agcli admin set-network-registration --netuid 9 --allowed false"

    def test_hyperparameter_workflow_help_keeps_existing_surface(self, admin):
        helpers = admin.hyperparameter_workflow_help(9)
        assert helpers["scope"] == "subnet_admin"
        assert helpers["summary"]
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]
        assert helpers["primary_read"] == "agcli subnet hyperparams --netuid 9"
        assert helpers["mutation_check"] == "agcli admin list"
        assert helpers["raw"] == "agcli admin raw --call <sudo-call>"
        assert helpers["sudo_note"]

    def test_hyperparameter_validation_help_without_payloads(self, admin):
        helpers = admin.hyperparameter_validation_help(9)
        assert helpers == {
            "netuid": 9,
            "scope": "subnet_admin",
            "validated_reads": [],
            "missing_reads": ["show", "get", "owner_param_list", "admin_list"],
            "has_mutation_plan": False,
            "validation_status": "missing",
            "validation_summary": (
                "Admin hyperparameter reads for subnet 9 still need show, get, owner_param_list, and admin_list output."
            ),
            "next_validation_step": "agcli subnet show --netuid 9",
            "workflow": admin.hyperparameter_workflow_help(9),
        }

    def test_hyperparameter_validation_help_with_partial_payloads(self, admin):
        helpers = admin.hyperparameter_validation_help(9, show={"netuid": 9}, get="  ")
        assert helpers["validated_reads"] == ["show"]
        assert helpers["missing_reads"] == ["get", "owner_param_list", "admin_list"]
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 9"

    def test_hyperparameter_validation_help_with_full_payloads_and_mutation(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            sudo_key="//Alice",
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validated_reads"] == ["show", "get", "owner_param_list", "admin_list"]
        assert helpers["missing_reads"] == []
        assert helpers["has_mutation_plan"] is True
        assert helpers["validation_status"] == "ready_to_mutate"
        assert helpers["next_validation_step"] == "agcli admin set-tempo --netuid 9 --tempo 360 --sudo-key //Alice"

    def test_hyperparameter_validation_text(self, admin):
        text = admin.hyperparameter_validation_text(9, get={"tempo": 360})
        assert (
            text
            == "Admin hyperparameter reads for subnet 9 have get; still missing show, owner_param_list, admin_list."
        )

    def test_hyperparameter_snapshot_help(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9,
            command="set-network-registration",
            value_flag="--allowed",
            value=False,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
        )
        assert helpers["workflow"] == admin.hyperparameter_workflow_help(
            9,
            command="set-network-registration",
            value_flag="--allowed",
            value=False,
        )
        assert helpers["validation_status"] == "partial"
        assert helpers["missing_reads"] == ["admin_list"]
        assert helpers["has_mutation_plan"] is True
        assert helpers["next_validation_step"] == "agcli admin list"

    def test_hyperparameter_snapshot_text(self, admin):
        text = admin.hyperparameter_snapshot_text(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text == (
            "Admin hyperparameter reads for subnet 9 are ready and the mutation command is prepared. "
            "Next: agcli admin set-tempo --netuid 9 --tempo 360"
        )

    def test_hyperparameters_aliases_match_new_hyperparameter_helpers(self, admin):
        kwargs = {
            "command": "set-tempo",
            "value_flag": "--tempo",
            "value": 360,
            "show": {"netuid": 9},
            "get": {"tempo": 360},
            "owner_param_list": ["tempo"],
            "admin_list": ["set-tempo"],
        }
        assert admin.hyperparameters_validation_help(9, **kwargs) == admin.hyperparameter_validation_help(9, **kwargs)
        assert admin.hyperparameters_validation_text(9, **kwargs) == admin.hyperparameter_validation_text(9, **kwargs)
        assert admin.hyperparameters_snapshot_help(9, **kwargs) == admin.hyperparameter_snapshot_help(9, **kwargs)
        assert admin.hyperparameters_snapshot_text(9, **kwargs) == admin.hyperparameter_snapshot_text(9, **kwargs)

    def test_hyperparameter_validation_help_without_mutation_plan_ready(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["has_mutation_plan"] is False
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    def test_hyperparameter_validation_help_treats_blank_payloads_as_missing(self, admin):
        helpers = admin.hyperparameter_validation_help(9, show={}, get=[], owner_param_list=set(), admin_list="   ")
        assert helpers["validated_reads"] == []
        assert helpers["missing_reads"] == ["show", "get", "owner_param_list", "admin_list"]
        assert helpers["validation_status"] == "missing"

    def test_hyperparameter_snapshot_help_preserves_workflow_fields(self, admin):
        helpers = admin.hyperparameter_snapshot_help(9, command="set-tempo", value_flag="--tempo")
        assert helpers["show"] == "agcli subnet show --netuid 9"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 9"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 9 --param list"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["set"] == "agcli admin set-tempo --netuid 9 --tempo <value>"
        assert helpers["workflow"] == admin.hyperparameter_workflow_help(9, command="set-tempo", value_flag="--tempo")

    def test_hyperparameter_validation_help_accepts_truthy_scalar_payloads(self, admin):
        helpers = admin.hyperparameter_validation_help(9, show=1, get=2, owner_param_list=3, admin_list=4)
        assert helpers["validation_status"] == "ready"
        assert helpers["validated_reads"] == ["show", "get", "owner_param_list", "admin_list"]

    def test_hyperparameter_validation_help_rejects_invalid_netuid(self, admin):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            admin.hyperparameter_validation_help(0)

    def test_hyperparameter_snapshot_help_rejects_empty_command(self, admin):
        with pytest.raises(ValueError, match="command cannot be empty"):
            admin.hyperparameter_snapshot_help(9, command="   ")

    def test_hyperparameters_snapshot_text_alias_rejects_empty_value_flag(self, admin):
        with pytest.raises(ValueError, match="value_flag cannot be empty"):
            admin.hyperparameters_snapshot_text(9, command="set-tempo", value_flag="   ")

    def test_hyperparameter_validation_text_ready_without_mutation_plan(self, admin):
        text = admin.hyperparameter_validation_text(
            9,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text == (
            "Admin hyperparameter reads for subnet 9 are ready: show, get, "
            "owner_param_list, and admin_list output are present."
        )

    def test_hyperparameter_snapshot_text_with_partial_reads(self, admin):
        text = admin.hyperparameter_snapshot_text(9, get={"tempo": 360}, admin_list=["set-tempo"])
        assert text == (
            "Admin hyperparameter reads for subnet 9 have get, admin_list; still missing show, owner_param_list. "
            "Next: agcli subnet show --netuid 9"
        )

    def test_hyperparameter_workflow_help_without_command_keeps_no_set(self, admin):
        helpers = admin.hyperparameter_workflow_help(9)
        assert "set" not in helpers
        assert helpers["recommended_order"][-1] == "set"
        assert helpers["primary_read"] == helpers["get"]
        assert helpers["mutation_check"] == helpers["admin_list"]

    def test_hyperparameter_validation_help_full_ready_without_sudo(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["next_validation_step"] == "agcli admin set-tempo --netuid 9 --tempo 360"

    def test_hyperparameter_validation_help_with_stub_mutation_plan(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            command="set-tempo",
            value_flag="--tempo",
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_status"] == "ready_to_mutate"
        assert helpers["next_validation_step"] == "agcli admin set-tempo --netuid 9 --tempo <value>"

    def test_hyperparameters_validation_text_alias_with_partial_payloads(self, admin):
        text = admin.hyperparameters_validation_text(9, admin_list=["set-tempo"])
        assert (
            text
            == "Admin hyperparameter reads for subnet 9 have admin_list; still missing show, get, owner_param_list."
        )

    def test_hyperparameters_snapshot_help_alias_with_mutation_plan(self, admin):
        helpers = admin.hyperparameters_snapshot_help(
            9, command="set-network-registration", value_flag="--allowed", value=False
        )
        assert helpers["workflow"]["set"] == "agcli admin set-network-registration --netuid 9 --allowed false"
        assert helpers["has_mutation_plan"] is True

    def test_hyperparameter_snapshot_help_with_trimmed_sudo_key(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            sudo_key=" //Alice ",
        )
        assert helpers["workflow"]["sudo_key"] == "//Alice"
        assert helpers["workflow"]["set"] == "agcli admin set-tempo --netuid 9 --tempo 360 --sudo-key //Alice"

    def test_hyperparameter_validation_help_with_string_payloads(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            show="show",
            get="get",
            owner_param_list="owner",
            admin_list="admin",
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    def test_hyperparameter_snapshot_text_with_bool_mutation_value(self, admin):
        text = admin.hyperparameter_snapshot_text(
            9,
            command="set-commit-reveal",
            value_flag="--enabled",
            value=True,
            show={"netuid": 9},
            get={"commit_reveal": True},
            owner_param_list=["commit_reveal"],
            admin_list=["set-commit-reveal"],
        )
        assert text.endswith("Next: agcli admin set-commit-reveal --netuid 9 --enabled true")

    def test_hyperparameter_validation_help_uses_scope_from_workflow(self, admin):
        helpers = admin.hyperparameter_validation_help(9)
        assert helpers["scope"] == "subnet_admin"

    def test_hyperparameter_snapshot_help_includes_summary_fields(self, admin):
        helpers = admin.hyperparameter_snapshot_help(9)
        assert helpers["summary"]
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]
        assert helpers["primary_read"] == "agcli subnet hyperparams --netuid 9"
        assert helpers["mutation_check"] == "agcli admin list"

    def test_hyperparameter_validation_help_with_only_show_points_to_get(self, admin):
        helpers = admin.hyperparameter_validation_help(9, show={"netuid": 9})
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 9"

    def test_hyperparameter_validation_help_with_show_and_get_points_to_owner_param_list(self, admin):
        helpers = admin.hyperparameter_validation_help(9, show={"netuid": 9}, get={"tempo": 360})
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 9 --param list"

    def test_hyperparameter_validation_help_with_show_get_owner_param_list_points_to_admin_list(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9, show={"netuid": 9}, get={"tempo": 360}, owner_param_list=["tempo"]
        )
        assert helpers["next_validation_step"] == "agcli admin list"

    def test_hyperparameter_snapshot_help_ready_without_mutation_plan_points_to_raw(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    def test_hyperparameter_workflow_help_summary_mentions_root_only_knobs(self, admin):
        helpers = admin.hyperparameter_workflow_help(9)
        assert "root-only knobs" in helpers["summary"]

    def test_hyperparameter_snapshot_help_workflow_embeds_set_when_present(self, admin):
        helpers = admin.hyperparameter_snapshot_help(9, command="set-tempo", value_flag="--tempo", value=360)
        assert helpers["workflow"]["set"] == "agcli admin set-tempo --netuid 9 --tempo 360"

    def test_hyperparameter_validation_text_missing_everything(self, admin):
        text = admin.hyperparameter_validation_text(9)
        assert text == (
            "Admin hyperparameter reads for subnet 9 still need show, get, owner_param_list, and admin_list output."
        )

    def test_hyperparameters_snapshot_text_alias_missing_everything(self, admin):
        text = admin.hyperparameters_snapshot_text(9)
        assert text == (
            "Admin hyperparameter reads for subnet 9 still need show, get, owner_param_list, and admin_list output. "
            "Next: agcli subnet show --netuid 9"
        )

    def test_hyperparameter_validation_help_with_all_reads_and_bool_value(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            command="set-network-registration",
            value_flag="--allowed",
            value=False,
            show={"netuid": 9},
            get={"allowed": False},
            owner_param_list=["network_registration_allowed"],
            admin_list=["set-network-registration"],
        )
        assert helpers["validation_status"] == "ready_to_mutate"
        assert helpers["next_validation_step"] == "agcli admin set-network-registration --netuid 9 --allowed false"

    def test_hyperparameter_snapshot_help_with_float_value(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9,
            command="set-adjustment-alpha",
            value_flag="--alpha",
            value=0.5,
        )
        assert helpers["workflow"]["value"] == "0.5"
        assert helpers["workflow"]["set"] == "agcli admin set-adjustment-alpha --netuid 9 --alpha 0.5"

    def test_hyperparameter_validation_help_alias_rejects_empty_sudo_key(self, admin):
        with pytest.raises(ValueError, match="sudo_key cannot be empty"):
            admin.hyperparameters_validation_help(9, command="set-tempo", value_flag="--tempo", sudo_key="   ")

    def test_hyperparameter_snapshot_help_alias_rejects_invalid_netuid(self, admin):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            admin.hyperparameters_snapshot_help(0)

    def test_hyperparameter_validation_help_with_only_owner_param_list_points_to_show(self, admin):
        helpers = admin.hyperparameter_validation_help(9, owner_param_list=["tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_validation_help_with_only_admin_list_points_to_show(self, admin):
        helpers = admin.hyperparameter_validation_help(9, admin_list=["set-tempo"])
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_snapshot_help_with_partial_reads_preserves_workflow(self, admin):
        helpers = admin.hyperparameter_snapshot_help(9, get={"tempo": 360})
        assert helpers["workflow"] == admin.hyperparameter_workflow_help(9)
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_validation_help_with_command_only_no_reads(self, admin):
        helpers = admin.hyperparameter_validation_help(9, command="set-tempo", value_flag="--tempo")
        assert helpers["has_mutation_plan"] is True
        assert helpers["validation_status"] == "missing"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_snapshot_text_with_command_only_no_reads(self, admin):
        text = admin.hyperparameter_snapshot_text(9, command="set-tempo", value_flag="--tempo")
        assert text == (
            "Admin hyperparameter reads for subnet 9 still need show, get, owner_param_list, and admin_list output. "
            "Next: agcli subnet show --netuid 9"
        )

    def test_hyperparameter_workflow_help_with_command_preserves_summary_fields(self, admin):
        helpers = admin.hyperparameter_workflow_help(9, command="set-tempo", value_flag="--tempo")
        assert helpers["scope"] == "subnet_admin"
        assert helpers["summary"]
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]
        assert helpers["primary_read"] == helpers["get"]
        assert helpers["mutation_check"] == helpers["admin_list"]

    def test_hyperparameter_snapshot_help_with_ready_reads_and_no_command_uses_raw(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    def test_hyperparameter_validation_text_with_mutation_plan_ready(self, admin):
        text = admin.hyperparameter_validation_text(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text == "Admin hyperparameter reads for subnet 9 are ready and the mutation command is prepared."

    def test_hyperparameter_snapshot_help_rejects_sudo_without_command(self, admin):
        with pytest.raises(ValueError, match="sudo_key requires command"):
            admin.hyperparameter_snapshot_help(9, sudo_key="//Alice")

    def test_hyperparameter_validation_help_rejects_value_without_flag(self, admin):
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            admin.hyperparameter_validation_help(9, command="set-tempo", value=1)

    def test_hyperparameters_validation_text_alias_rejects_empty_command(self, admin):
        with pytest.raises(ValueError, match="command cannot be empty"):
            admin.hyperparameters_validation_text(9, command="   ")

    def test_hyperparameter_snapshot_help_rejects_value_flag_without_command(self, admin):
        with pytest.raises(ValueError, match="value_flag requires command"):
            admin.hyperparameter_snapshot_help(9, value_flag="--tempo")

    def test_hyperparameter_validation_help_rejects_value_without_command(self, admin):
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            admin.hyperparameter_validation_help(9, value=1)

    def test_hyperparameter_snapshot_help_rejects_value_without_command(self, admin):
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            admin.hyperparameter_snapshot_help(9, value=1)

    def test_hyperparameter_snapshot_help_rejects_sudo_key_without_command(self, admin):
        with pytest.raises(ValueError, match="sudo_key requires command"):
            admin.hyperparameter_snapshot_help(9, sudo_key="//Alice")

    def test_hyperparameter_snapshot_help_rejects_value_without_flag(self, admin):
        with pytest.raises(ValueError, match="value requires command and value_flag"):
            admin.hyperparameter_snapshot_help(9, command="set-tempo", value=1)

    def test_hyperparameter_validation_help_rejects_empty_value_flag(self, admin):
        with pytest.raises(ValueError, match="value_flag cannot be empty"):
            admin.hyperparameter_validation_help(9, command="set-tempo", value_flag="   ")

    def test_hyperparameter_validation_help_rejects_empty_command(self, admin):
        with pytest.raises(ValueError, match="command cannot be empty"):
            admin.hyperparameter_validation_help(9, command="   ")

    def test_hyperparameter_validation_help_rejects_empty_sudo_key(self, admin):
        with pytest.raises(ValueError, match="sudo_key cannot be empty"):
            admin.hyperparameter_validation_help(9, command="set-tempo", value_flag="--tempo", sudo_key="   ")

    def test_hyperparameter_snapshot_text_alias_with_mutation_plan_ready(self, admin):
        text = admin.hyperparameters_snapshot_text(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text.endswith("Next: agcli admin set-tempo --netuid 9 --tempo 360")

    def test_hyperparameter_validation_help_with_show_owner_admin_points_to_get(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9, show={"netuid": 9}, owner_param_list=["tempo"], admin_list=["set-tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 9"

    def test_hyperparameter_validation_help_with_get_owner_admin_points_to_show(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9, get={"tempo": 360}, owner_param_list=["tempo"], admin_list=["set-tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_validation_help_with_show_get_admin_points_to_owner_param_list(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9, show={"netuid": 9}, get={"tempo": 360}, admin_list=["set-tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 9 --param list"

    def test_hyperparameter_snapshot_help_with_show_get_admin_points_to_owner_param_list(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9, show={"netuid": 9}, get={"tempo": 360}, admin_list=["set-tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 9 --param list"

    def test_hyperparameter_snapshot_help_with_show_owner_admin_points_to_get(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9, show={"netuid": 9}, owner_param_list=["tempo"], admin_list=["set-tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 9"

    def test_hyperparameter_snapshot_help_with_get_owner_admin_points_to_show(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9, get={"tempo": 360}, owner_param_list=["tempo"], admin_list=["set-tempo"]
        )
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_workflow_help_recommended_order_is_copy(self, admin):
        helpers = admin.hyperparameter_workflow_help(9)
        helpers["recommended_order"].append("oops")
        assert admin.hyperparameter_workflow_help(9)["recommended_order"] == [
            "show",
            "get",
            "owner_param_list",
            "admin_list",
            "set",
        ]

    def test_hyperparameter_snapshot_help_workflow_is_copy(self, admin):
        helpers = admin.hyperparameter_snapshot_help(9)
        helpers["workflow"]["show"] = "mutated"
        assert admin.hyperparameter_workflow_help(9)["show"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_validation_help_workflow_contains_raw(self, admin):
        helpers = admin.hyperparameter_validation_help(9)
        assert helpers["workflow"]["raw"] == "agcli admin raw --call <sudo-call>"

    def test_hyperparameter_validation_help_with_command_only_ready_fields_not_used(self, admin):
        helpers = admin.hyperparameter_validation_help(9, command="set-tempo", value_flag="--tempo")
        assert helpers["workflow"]["set"] == "agcli admin set-tempo --netuid 9 --tempo <value>"

    def test_hyperparameter_snapshot_text_with_ready_reads_and_sudo(self, admin):
        text = admin.hyperparameter_snapshot_text(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            sudo_key="//Alice",
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert text.endswith("Next: agcli admin set-tempo --netuid 9 --tempo 360 --sudo-key //Alice")

    def test_hyperparameter_validation_help_empty_string_admin_list_is_missing(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9, show={"netuid": 9}, get={"tempo": 360}, owner_param_list=["tempo"], admin_list=""
        )
        assert helpers["missing_reads"] == ["admin_list"]
        assert helpers["next_validation_step"] == "agcli admin list"

    def test_hyperparameter_snapshot_help_with_empty_string_admin_list_is_missing(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9, show={"netuid": 9}, get={"tempo": 360}, owner_param_list=["tempo"], admin_list=""
        )
        assert helpers["missing_reads"] == ["admin_list"]
        assert helpers["next_validation_step"] == "agcli admin list"

    def test_hyperparameter_validation_help_with_float_value_ready_to_mutate(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            command="set-adjustment-alpha",
            value_flag="--alpha",
            value=0.5,
            show={"netuid": 9},
            get={"alpha": 0.5},
            owner_param_list=["alpha"],
            admin_list=["set-adjustment-alpha"],
        )
        assert helpers["next_validation_step"] == "agcli admin set-adjustment-alpha --netuid 9 --alpha 0.5"

    def test_hyperparameter_snapshot_help_with_bool_value_ready_to_mutate(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9,
            command="set-commit-reveal",
            value_flag="--enabled",
            value=True,
            show={"netuid": 9},
            get={"enabled": True},
            owner_param_list=["commit_reveal"],
            admin_list=["set-commit-reveal"],
        )
        assert helpers["next_validation_step"] == "agcli admin set-commit-reveal --netuid 9 --enabled true"

    def test_hyperparameter_snapshot_help_without_reads_is_missing(self, admin):
        helpers = admin.hyperparameter_snapshot_help(9)
        assert helpers["validation_status"] == "missing"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_validation_help_with_show_get_owner_param_list_admin_list_and_no_command_is_ready(
        self, admin
    ):
        helpers = admin.hyperparameter_validation_help(
            9,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli admin raw --call <sudo-call>"

    def test_hyperparameter_validation_help_with_only_get_points_to_show(self, admin):
        helpers = admin.hyperparameter_validation_help(9, get={"tempo": 360})
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 9"

    def test_hyperparameter_validation_help_with_only_show_and_admin_points_to_get(self, admin):
        helpers = admin.hyperparameter_validation_help(9, show={"netuid": 9}, admin_list=["set-tempo"])
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 9"

    def test_hyperparameter_validation_help_with_only_show_get_and_owner_points_to_admin(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9, show={"netuid": 9}, get={"tempo": 360}, owner_param_list=["tempo"]
        )
        assert helpers["next_validation_step"] == "agcli admin list"

    def test_hyperparameter_validation_help_summary_for_ready_to_mutate(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert (
            helpers["validation_summary"]
            == "Admin hyperparameter reads for subnet 9 are ready and the mutation command is prepared."
        )

    def test_hyperparameter_validation_help_summary_for_ready(self, admin):
        helpers = admin.hyperparameter_validation_help(
            9,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_summary"] == (
            "Admin hyperparameter reads for subnet 9 are ready: show, get, "
            "owner_param_list, and admin_list output are present."
        )

    def test_hyperparameter_validation_help_summary_for_partial(self, admin):
        helpers = admin.hyperparameter_validation_help(9, show={"netuid": 9}, admin_list=["set-tempo"])
        assert helpers["validation_summary"] == (
            "Admin hyperparameter reads for subnet 9 have show, admin_list; still missing get, owner_param_list."
        )

    def test_hyperparameter_workflow_help_command_trim_preserves_summary(self, admin):
        helpers = admin.hyperparameter_workflow_help(9, command=" set-tempo ", value_flag=" --tempo ")
        assert helpers["command"] == "set-tempo"
        assert helpers["summary"]
        assert helpers["recommended_order"] == ["show", "get", "owner_param_list", "admin_list", "set"]

    def test_hyperparameter_snapshot_help_ready_to_mutate_status(self, admin):
        helpers = admin.hyperparameter_snapshot_help(
            9,
            command="set-tempo",
            value_flag="--tempo",
            value=360,
            show={"netuid": 9},
            get={"tempo": 360},
            owner_param_list=["tempo"],
            admin_list=["set-tempo"],
        )
        assert helpers["validation_status"] == "ready_to_mutate"

    def test_hyperparameters_validation_help_alias_with_string_payloads(self, admin):
        helpers = admin.hyperparameters_validation_help(
            9, show="show", get="get", owner_param_list="owner", admin_list="admin"
        )
        assert helpers["validation_status"] == "ready"
