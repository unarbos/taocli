"""Tests for the Subnet SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.subnet import Subnet


@pytest.fixture
def subnet(mock_subprocess):
    return Subnet(AgcliRunner())


class TestSubnet:
    def test_list(self, subnet, mock_subprocess):
        subnet.list()
        cmd = mock_subprocess.call_args[0][0]
        assert "subnet" in cmd and "list" in cmd

    def test_list_at_block(self, subnet, mock_subprocess):
        subnet.list(at_block=100)
        cmd = mock_subprocess.call_args[0][0]
        assert "--at-block" in cmd

    def test_show(self, subnet, mock_subprocess):
        subnet.show(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "show" in cmd and "--netuid" in cmd

    def test_hyperparams(self, subnet, mock_subprocess):
        subnet.hyperparams(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "hyperparams" in cmd

    def test_metagraph(self, subnet, mock_subprocess):
        subnet.metagraph(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "metagraph" in cmd

    def test_metagraph_full(self, subnet, mock_subprocess):
        subnet.metagraph(1, uid=0, full=True, at_block=100)
        cmd = mock_subprocess.call_args[0][0]
        assert "--uid" in cmd and "--full" in cmd and "--at-block" in cmd

    def test_register(self, subnet, mock_subprocess):
        subnet.register()
        cmd = mock_subprocess.call_args[0][0]
        assert "register" in cmd

    def test_register_neuron(self, subnet, mock_subprocess):
        subnet.register_neuron(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "register-neuron" in cmd

    def test_pow(self, subnet, mock_subprocess):
        subnet.pow(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "pow" in cmd

    def test_pow_threads(self, subnet, mock_subprocess):
        subnet.pow(1, threads=8)
        cmd = mock_subprocess.call_args[0][0]
        assert "--threads" in cmd

    def test_health(self, subnet, mock_subprocess):
        subnet.health(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "health" in cmd

    def test_emissions(self, subnet, mock_subprocess):
        subnet.emissions(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "emissions" in cmd

    def test_cost(self, subnet, mock_subprocess):
        subnet.cost(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "cost" in cmd

    def test_create_cost(self, subnet, mock_subprocess):
        subnet.create_cost()
        cmd = mock_subprocess.call_args[0][0]
        assert "create-cost" in cmd

    def test_liquidity(self, subnet, mock_subprocess):
        subnet.liquidity()
        cmd = mock_subprocess.call_args[0][0]
        assert "liquidity" in cmd

    def test_liquidity_netuid(self, subnet, mock_subprocess):
        subnet.liquidity(netuid=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--netuid" in cmd

    def test_dissolve(self, subnet, mock_subprocess):
        subnet.dissolve(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "dissolve" in cmd

    def test_set_param(self, subnet, mock_subprocess):
        subnet.set_param(1, "tempo", "100")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-param" in cmd and "--param" in cmd

    def test_set_symbol(self, subnet, mock_subprocess):
        subnet.set_symbol(1, "ALPHA")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-symbol" in cmd

    def test_commits(self, subnet, mock_subprocess):
        subnet.commits(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "commits" in cmd

    def test_probe(self, subnet, mock_subprocess):
        subnet.probe(1, uids="0,1,2", timeout_ms=5000)
        cmd = mock_subprocess.call_args[0][0]
        assert "probe" in cmd and "--uids" in cmd

    def test_snipe(self, subnet, mock_subprocess):
        subnet.snipe(1, max_cost=10.0)
        cmd = mock_subprocess.call_args[0][0]
        assert "snipe" in cmd

    def test_trim(self, subnet, mock_subprocess):
        subnet.trim(1, 256)
        cmd = mock_subprocess.call_args[0][0]
        assert "trim" in cmd

    def test_start(self, subnet, mock_subprocess):
        subnet.start(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "start" in cmd

    def test_check_start(self, subnet, mock_subprocess):
        subnet.check_start(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "check-start" in cmd

    def test_emission_split(self, subnet, mock_subprocess):
        subnet.emission_split(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "emission-split" in cmd

    def test_mechanism_count(self, subnet, mock_subprocess):
        subnet.mechanism_count(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "mechanism-count" in cmd

    def test_set_mechanism_count(self, subnet, mock_subprocess):
        subnet.set_mechanism_count(1, 2)
        cmd = mock_subprocess.call_args[0][0]
        assert "set-mechanism-count" in cmd

    def test_set_emission_split(self, subnet, mock_subprocess):
        subnet.set_emission_split(1, "50,50")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-emission-split" in cmd

    def test_metagraph_save(self, subnet, mock_subprocess):
        subnet.metagraph(1, save=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--save" in cmd

    def test_cache_load(self, subnet, mock_subprocess):
        subnet.cache_load(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "cache-load" in cmd and "--netuid" in cmd

    def test_cache_list(self, subnet, mock_subprocess):
        subnet.cache_list()
        cmd = mock_subprocess.call_args[0][0]
        assert "cache-list" in cmd

    def test_cache_diff(self, subnet, mock_subprocess):
        subnet.cache_diff(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "cache-diff" in cmd

    def test_cache_prune(self, subnet, mock_subprocess):
        subnet.cache_prune()
        cmd = mock_subprocess.call_args[0][0]
        assert "cache-prune" in cmd

    def test_register_with_identity(self, subnet, mock_subprocess):
        subnet.register_with_identity(name="mysubnet")
        cmd = mock_subprocess.call_args[0][0]
        assert "register-with-identity" in cmd and "--name" in cmd

    def test_register_leased(self, subnet, mock_subprocess):
        subnet.register_leased()
        cmd = mock_subprocess.call_args[0][0]
        assert "register-leased" in cmd

    def test_terminate_lease(self, subnet, mock_subprocess):
        subnet.terminate_lease(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "terminate-lease" in cmd

    def test_root_dissolve(self, subnet, mock_subprocess):
        subnet.root_dissolve(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "root-dissolve" in cmd

    def test_watch(self, subnet, mock_subprocess):
        subnet.watch(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "watch" in cmd

    def test_monitor(self, subnet, mock_subprocess):
        subnet.monitor(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "monitor" in cmd

    def test_registration_workflow_help(self, subnet):
        helpers = subnet.registration_workflow_help(11)
        assert helpers["netuid"] == 11
        assert helpers["scope"] == "subnet"
        assert helpers["summary"] == "Check subnet 11 readiness, then register on subnet 11."
        assert helpers["recommended_order"] == [
            "subnet",
            "registration_cost",
            "health",
            "register_neuron",
            "post_registration_check",
        ]
        assert helpers["subnet"] == "agcli subnet show --netuid 11"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 11"
        assert helpers["registration_cost"] == "agcli subnet cost --netuid 11"
        assert helpers["health"] == "agcli subnet health --netuid 11"
        assert helpers["register_neuron"] == "agcli subnet register-neuron --netuid 11"
        assert helpers["pow_register"] == "agcli subnet pow --netuid 11"
        assert helpers["snipe_register"] == "agcli subnet snipe --netuid 11"
        assert helpers["primary_register"] == "agcli subnet register-neuron --netuid 11"
        assert helpers["post_registration_check"] == "agcli subnet metagraph --netuid 11 --full"
        assert helpers["registration_confirmation_note"]
        assert "wallet_selection_note" not in helpers
        assert "wallet" not in helpers
        assert "hotkey" not in helpers

    def test_registration_validation_help_without_payloads(self, subnet):
        helpers = subnet.registration_validation_help(11)
        assert helpers == {
            "netuid": 11,
            "scope": "subnet",
            "validated_reads": [],
            "missing_reads": ["subnet", "registration_cost", "health"],
            "confirmed_registered": False,
            "validation_status": "missing",
            "validation_summary": (
                "Registration on subnet 11 still needs preflight reads: "
                "subnet, registration_cost, health."
            ),
            "next_validation_step": "agcli subnet show --netuid 11",
            "workflow": subnet.registration_workflow_help(11),
        }

    def test_hyperparameter_validation_help_without_payloads(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11)
        assert helpers == {
            "netuid": 11,
            "validated_reads": [],
            "missing_reads": ["subnet", "hyperparams", "param_list"],
            "validation_status": "missing",
            "validation_summary": (
                "Hyperparameter reads for subnet 11 still need subnet, hyperparams, and param_list output."
            ),
            "next_validation_step": "agcli subnet show --netuid 11",
            "workflow": subnet.hyperparameter_workflow_help(11),
        }

    def test_hyperparameter_validation_help_with_partial_payloads(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet={"netuid": 11}, hyperparams="  ")
        assert helpers["validated_reads"] == ["subnet"]
        assert helpers["missing_reads"] == ["hyperparams", "param_list"]
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 11"

    def test_hyperparameter_validation_help_with_full_payloads_and_wallet(self, subnet):
        helpers = subnet.hyperparameter_validation_help(
            11,
            wallet="owner",
            param="tempo",
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["validated_reads"] == ["subnet", "hyperparams", "param_list"]
        assert helpers["missing_reads"] == []
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == (
            "agcli --wallet owner subnet set-param --netuid 11 --param tempo --value 360"
        )
        assert helpers["workflow"]["wallet"] == "owner"

    def test_hyperparameter_validation_text(self, subnet):
        text = subnet.hyperparameter_validation_text(11, subnet={"netuid": 11})
        assert (
            text == "Hyperparameter reads for subnet 11 have subnet; still missing hyperparams, param_list."
        )

    def test_hyperparameter_snapshot_help(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(
            11,
            wallet="owner",
            param="tempo",
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
        )
        assert helpers["workflow"] == subnet.hyperparameter_workflow_help(
            11, wallet="owner", param="tempo", value="360"
        )
        assert helpers["validation_status"] == "partial"
        assert helpers["missing_reads"] == ["param_list"]
        assert helpers["next_validation_step"] == "agcli --wallet owner subnet set-param --netuid 11 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 11 --param tempo --value 360"

    def test_hyperparameter_snapshot_text(self, subnet):
        text = subnet.hyperparameter_snapshot_text(11, hyperparams={"tempo": 360}, param_list=["tempo"])
        assert (
            text
            == "Hyperparameter reads for subnet 11 have hyperparams, param_list; still missing subnet. Next: agcli subnet show --netuid 11"
        )

    def test_hyperparameters_aliases_match_new_hyperparameter_helpers(self, subnet):
        kwargs = {
            "wallet": "owner",
            "param": "tempo",
            "value": "360",
            "subnet": {"netuid": 11},
            "hyperparams": {"tempo": 360},
            "param_list": ["tempo"],
        }
        assert subnet.hyperparameters_validation_help(11, **kwargs) == subnet.hyperparameter_validation_help(11, **kwargs)
        assert subnet.hyperparameters_validation_text(11, **kwargs) == subnet.hyperparameter_validation_text(11, **kwargs)
        assert subnet.hyperparameters_snapshot_help(11, **kwargs) == subnet.hyperparameter_snapshot_help(11, **kwargs)
        assert subnet.hyperparameters_snapshot_text(11, **kwargs) == subnet.hyperparameter_snapshot_text(11, **kwargs)

    def test_hyperparameter_validation_help_rejects_invalid_netuid(self, subnet):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            subnet.hyperparameter_validation_help(0)

    def test_hyperparameter_snapshot_help_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameter_snapshot_help(11, wallet="   ")

    def test_hyperparameters_snapshot_help_rejects_empty_param_alias(self, subnet):
        with pytest.raises(ValueError, match="param cannot be empty"):
            subnet.hyperparameters_snapshot_help(11, param="   ")

    def test_hyperparameter_snapshot_text_uses_trimmed_string_payloads(self, subnet):
        text = subnet.hyperparameter_snapshot_text(
            11,
            wallet=" owner ",
            param=" tempo ",
            value=" 360 ",
            subnet="  ok  ",
            hyperparams=" values ",
            param_list=" names ",
        )
        assert text == (
            "Hyperparameter reads for subnet 11 are ready: subnet, hyperparams, and param_list output are present. "
            "Next: agcli --wallet owner subnet set-param --netuid 11 --param tempo --value 360"
        )

    def test_hyperparameter_workflow_help_keeps_existing_surface(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(11, wallet="owner", param="tempo", value="360")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 11 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 11 --param tempo --value 360"
        assert helpers["mutation_note"]
        assert helpers["admin_list"] == "agcli admin list"
        assert "scope" not in helpers
        assert "summary" not in helpers
        assert "recommended_order" not in helpers
        assert "workflow" not in helpers
        assert "validation_status" not in helpers
        assert "next_validation_step" not in helpers
        assert "primary_read" not in helpers
        assert "mutation_check" not in helpers
        assert "raw" not in helpers

    def test_hyperparameter_validation_help_treats_blank_collections_as_missing(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet={}, hyperparams=[], param_list=set())
        assert helpers["validated_reads"] == []
        assert helpers["missing_reads"] == ["subnet", "hyperparams", "param_list"]
        assert helpers["validation_status"] == "missing"

    def test_hyperparameter_snapshot_help_preserves_workflow_identity(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, param="tempo")
        assert helpers["workflow"] == subnet.hyperparameter_workflow_help(11, param="tempo")
        assert helpers["set"] == "agcli subnet set-param --netuid 11 --param tempo"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_hyperparameter_validation_help_next_step_prefers_param_list_before_set(self, subnet):
        helpers = subnet.hyperparameter_validation_help(
            11,
            param="tempo",
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11 --param list"
        assert helpers["validation_status"] == "partial"

    def test_hyperparameter_snapshot_text_with_no_param_uses_base_set_command(self, subnet):
        text = subnet.hyperparameter_snapshot_text(
            11,
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text == (
            "Hyperparameter reads for subnet 11 are ready: subnet, hyperparams, and param_list output are present. "
            "Next: agcli subnet set-param --netuid 11"
        )

    def test_hyperparameter_validation_help_with_param_but_no_value_points_to_param_command(self, subnet):
        helpers = subnet.hyperparameter_validation_help(
            11,
            wallet="owner",
            param="tempo",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli --wallet owner subnet set-param --netuid 11 --param tempo"

    def test_hyperparameters_validation_text_alias_with_partial_payloads(self, subnet):
        text = subnet.hyperparameters_validation_text(11, hyperparams={"tempo": 360})
        assert text == "Hyperparameter reads for subnet 11 have hyperparams; still missing subnet, param_list."

    def test_hyperparameters_snapshot_text_alias_with_wallet_prefix(self, subnet):
        text = subnet.hyperparameters_snapshot_text(
            11,
            wallet="owner",
            param="tempo",
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text.endswith("Next: agcli --wallet owner subnet set-param --netuid 11 --param tempo --value 360")

    def test_hyperparameter_validation_help_accepts_truthy_scalar_payloads(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet=1, hyperparams=2, param_list=3)
        assert helpers["validation_status"] == "ready"
        assert helpers["validated_reads"] == ["subnet", "hyperparams", "param_list"]

    def test_hyperparameter_snapshot_help_with_value_without_param_keeps_base_set_command(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(
            11,
            wallet="owner",
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 11"
        assert helpers["next_validation_step"] == "agcli --wallet owner subnet set-param --netuid 11"

    def test_hyperparameter_validation_help_with_only_param_list_points_to_subnet(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, param_list=["tempo"])
        assert helpers["validated_reads"] == ["param_list"]
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_hyperparameter_snapshot_help_alias_rejects_invalid_netuid(self, subnet):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            subnet.hyperparameters_snapshot_help(0)

    def test_hyperparameter_validation_help_preserves_wallet_note_in_workflow(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, wallet="owner")
        assert helpers["workflow"]["wallet_selection_note"]
        assert helpers["workflow"]["wallet"] == "owner"

    def test_hyperparameter_snapshot_help_includes_workflow_commands(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, wallet="owner", param="tempo")
        assert helpers["show"] == "agcli subnet show --netuid 11"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 11"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 11 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 11 --param tempo"

    def test_hyperparameters_validation_help_alias_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameters_validation_help(11, wallet="")

    def test_hyperparameters_validation_text_alias_rejects_invalid_netuid(self, subnet):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            subnet.hyperparameters_validation_text(0)

    def test_hyperparameters_snapshot_text_alias_rejects_empty_value(self, subnet):
        with pytest.raises(ValueError, match="value cannot be empty"):
            subnet.hyperparameters_snapshot_text(11, param="tempo", value="   ")

    def test_hyperparameter_validation_help_param_only_workflow_next_step(self, subnet):
        helpers = subnet.hyperparameter_validation_help(
            11,
            param="tempo",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11 --param tempo"
        assert helpers["validation_status"] == "ready"

    def test_hyperparameter_snapshot_text_with_partial_and_wallet(self, subnet):
        text = subnet.hyperparameter_snapshot_text(11, wallet="owner", subnet={"netuid": 11})
        assert text == (
            "Hyperparameter reads for subnet 11 have subnet; still missing hyperparams, param_list. "
            "Next: agcli subnet hyperparams --netuid 11"
        )

    def test_hyperparameter_validation_help_with_whitespace_param_list_is_missing(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet={"netuid": 11}, hyperparams={"tempo": 360}, param_list="   ")
        assert helpers["missing_reads"] == ["param_list"]
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11 --param list"

    def test_hyperparameter_snapshot_help_with_alias_workflow_equality(self, subnet):
        assert subnet.hyperparameter_snapshot_help(11, wallet="owner") == subnet.hyperparameters_snapshot_help(11, wallet="owner")

    def test_hyperparameter_validation_help_next_step_uses_wallet_prefixed_show_when_missing_subnet(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, wallet="owner")
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_hyperparameter_snapshot_help_carries_mutation_note(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11)
        assert helpers["mutation_note"]
        assert helpers["admin_list"] == "agcli admin list"

    def test_hyperparameter_validation_help_uses_workflow_netuid_int(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11)
        assert helpers["netuid"] == 11

    def test_hyperparameter_snapshot_help_with_full_reads_no_param_uses_base_set(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, subnet={"netuid": 11}, hyperparams={"tempo": 360}, param_list=["tempo"])
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11"

    def test_hyperparameter_validation_help_param_list_only_text(self, subnet):
        text = subnet.hyperparameter_validation_text(11, param_list=["tempo"])
        assert text == "Hyperparameter reads for subnet 11 have param_list; still missing subnet, hyperparams."

    def test_hyperparameter_snapshot_text_param_only_ready(self, subnet):
        text = subnet.hyperparameter_snapshot_text(
            11,
            param="tempo",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text == (
            "Hyperparameter reads for subnet 11 are ready: subnet, hyperparams, and param_list output are present. "
            "Next: agcli subnet set-param --netuid 11 --param tempo"
        )

    def test_hyperparameter_snapshot_help_rejects_empty_value(self, subnet):
        with pytest.raises(ValueError, match="value cannot be empty"):
            subnet.hyperparameter_snapshot_help(11, param="tempo", value="   ")

    def test_hyperparameter_validation_help_rejects_empty_param(self, subnet):
        with pytest.raises(ValueError, match="param cannot be empty"):
            subnet.hyperparameter_validation_help(11, param="")

    def test_hyperparameter_validation_help_rejects_empty_value(self, subnet):
        with pytest.raises(ValueError, match="value cannot be empty"):
            subnet.hyperparameter_validation_help(11, param="tempo", value="")

    def test_hyperparameter_validation_help_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameter_validation_help(11, wallet="")

    def test_hyperparameter_snapshot_text_alias_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameters_snapshot_text(11, wallet="")

    def test_hyperparameter_validation_text_alias_rejects_empty_param(self, subnet):
        with pytest.raises(ValueError, match="param cannot be empty"):
            subnet.hyperparameters_validation_text(11, param="")

    def test_hyperparameter_validation_help_alias_with_value_without_param_keeps_base_set(self, subnet):
        helpers = subnet.hyperparameters_validation_help(
            11,
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11"

    def test_hyperparameter_snapshot_help_alias_with_value_without_param_keeps_base_set(self, subnet):
        helpers = subnet.hyperparameters_snapshot_help(
            11,
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["set"] == "agcli subnet set-param --netuid 11"

    def test_hyperparameter_validation_text_alias_with_wallet_and_param(self, subnet):
        text = subnet.hyperparameters_validation_text(
            11,
            wallet="owner",
            param="tempo",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text == "Hyperparameter reads for subnet 11 are ready: subnet, hyperparams, and param_list output are present."

    def test_hyperparameter_snapshot_help_alias_with_wallet_and_param(self, subnet):
        helpers = subnet.hyperparameters_snapshot_help(
            11,
            wallet="owner",
            param="tempo",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["next_validation_step"] == "agcli --wallet owner subnet set-param --netuid 11 --param tempo"

    def test_hyperparameter_snapshot_text_alias_with_wallet_and_param(self, subnet):
        text = subnet.hyperparameters_snapshot_text(
            11,
            wallet="owner",
            param="tempo",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text.endswith("Next: agcli --wallet owner subnet set-param --netuid 11 --param tempo")

    def test_hyperparameter_validation_help_with_whitespace_subnet_is_missing(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet="   ", hyperparams={"tempo": 360}, param_list=["tempo"])
        assert helpers["missing_reads"] == ["subnet"]
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_hyperparameter_validation_help_with_whitespace_hyperparams_is_missing(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet={"netuid": 11}, hyperparams="   ", param_list=["tempo"])
        assert helpers["missing_reads"] == ["hyperparams"]
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 11"

    def test_hyperparameter_workflow_help_alias_still_matches(self, subnet):
        assert subnet.hyperparameters_workflow_help(11, wallet="owner", param="tempo", value="360") == subnet.hyperparameter_workflow_help(
            11, wallet="owner", param="tempo", value="360"
        )

    def test_hyperparameter_snapshot_help_workflow_embeds_wallet_note(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, wallet="owner")
        assert helpers["workflow"]["wallet_selection_note"]
        assert helpers["wallet_selection_note"]

    def test_hyperparameter_snapshot_help_with_ready_reads_and_value(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(
            11,
            param="tempo",
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert helpers["validation_status"] == "ready"
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11 --param tempo --value 360"

    def test_hyperparameter_snapshot_text_with_ready_reads_and_value(self, subnet):
        text = subnet.hyperparameter_snapshot_text(
            11,
            param="tempo",
            value="360",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text.endswith("Next: agcli subnet set-param --netuid 11 --param tempo --value 360")

    def test_hyperparameter_validation_help_with_wallet_preserves_workflow_wallet(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, wallet="owner", subnet={"netuid": 11})
        assert helpers["workflow"]["wallet"] == "owner"
        assert helpers["workflow"]["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 11 --param list"

    def test_hyperparameter_snapshot_help_with_partial_reads_preserves_workflow(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, wallet="owner", hyperparams={"tempo": 360})
        assert helpers["workflow"] == subnet.hyperparameter_workflow_help(11, wallet="owner")
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_hyperparameter_validation_text_ready_without_value(self, subnet):
        text = subnet.hyperparameter_validation_text(
            11,
            param="tempo",
            subnet={"netuid": 11},
            hyperparams={"tempo": 360},
            param_list=["tempo"],
        )
        assert text == "Hyperparameter reads for subnet 11 are ready: subnet, hyperparams, and param_list output are present."

    def test_hyperparameter_validation_text_missing_everything(self, subnet):
        text = subnet.hyperparameter_validation_text(11)
        assert text == "Hyperparameter reads for subnet 11 still need subnet, hyperparams, and param_list output."

    def test_hyperparameter_snapshot_help_with_blank_strings_is_missing(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, subnet="", hyperparams="", param_list="")
        assert helpers["validation_status"] == "missing"
        assert helpers["missing_reads"] == ["subnet", "hyperparams", "param_list"]

    def test_hyperparameter_snapshot_text_alias_missing_everything(self, subnet):
        text = subnet.hyperparameters_snapshot_text(11)
        assert text == (
            "Hyperparameter reads for subnet 11 still need subnet, hyperparams, and param_list output. "
            "Next: agcli subnet show --netuid 11"
        )

    def test_hyperparameter_snapshot_help_with_trimmed_wallet_param_value(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, wallet=" owner ", param=" tempo ", value=" 360 ")
        assert helpers["workflow"]["wallet"] == "owner"
        assert helpers["workflow"]["param"] == "tempo"
        assert helpers["workflow"]["value"] == "360"

    def test_hyperparameter_validation_help_partial_from_param_list_and_hyperparams(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, hyperparams={"tempo": 360}, param_list=["tempo"])
        assert helpers["validated_reads"] == ["hyperparams", "param_list"]
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_hyperparameter_snapshot_help_with_partial_from_param_list_and_hyperparams(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, hyperparams={"tempo": 360}, param_list=["tempo"])
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_hyperparameter_validation_help_with_only_subnet_points_to_hyperparams(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet={"netuid": 11})
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 11"

    def test_hyperparameter_snapshot_help_with_only_subnet_points_to_hyperparams(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, subnet={"netuid": 11})
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 11"

    def test_hyperparameter_validation_help_with_only_subnet_and_hyperparams_points_to_param_list(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet={"netuid": 11}, hyperparams={"tempo": 360})
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11 --param list"

    def test_hyperparameter_snapshot_help_with_only_subnet_and_hyperparams_points_to_param_list(self, subnet):
        helpers = subnet.hyperparameter_snapshot_help(11, subnet={"netuid": 11}, hyperparams={"tempo": 360})
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11 --param list"

    def test_hyperparameter_validation_help_with_ready_reads_points_to_set(self, subnet):
        helpers = subnet.hyperparameter_validation_help(11, subnet={"netuid": 11}, hyperparams={"tempo": 360}, param_list=["tempo"])
        assert helpers["next_validation_step"] == "agcli subnet set-param --netuid 11"

    def test_registration_validation_help_with_partial_payloads(self, subnet):
        helpers = subnet.registration_validation_help(11, wallet="cold", subnet={"netuid": 11}, health=["ok"])
        assert helpers["scope"] == "wallet"
        assert helpers["validated_reads"] == ["subnet", "health"]
        assert helpers["missing_reads"] == ["registration_cost"]
        assert helpers["confirmed_registered"] is False
        assert helpers["validation_status"] == "partial"
        assert helpers["next_validation_step"] == "agcli subnet cost --netuid 11"
        assert helpers["workflow"]["primary_register"] == "agcli --wallet cold subnet register-neuron --netuid 11"

    def test_registration_validation_help_with_ready_preflight_reads(self, subnet):
        helpers = subnet.registration_validation_help(
            11,
            hotkey="miner",
            subnet={"netuid": 11},
            registration_cost={"tao": 1.0},
            health={"healthy": True},
        )
        assert helpers["scope"] == "hotkey"
        assert helpers["validated_reads"] == ["subnet", "registration_cost", "health"]
        assert helpers["missing_reads"] == []
        assert helpers["validation_status"] == "ready"
        assert helpers["confirmed_registered"] is False
        assert helpers["next_validation_step"] == "agcli --hotkey-name miner subnet register-neuron --netuid 11"

    def test_registration_validation_help_with_registration_proof(self, subnet):
        helpers = subnet.registration_validation_help(
            11,
            wallet="cold",
            hotkey="miner",
            subnet={"netuid": 11},
            registration_cost={"tao": 1.0},
            health={"healthy": True},
            registration_proof={"uid": 5},
        )
        assert helpers["scope"] == "wallet_and_hotkey"
        assert helpers["validation_status"] == "registered"
        assert helpers["confirmed_registered"] is True
        assert helpers["next_validation_step"] == "agcli subnet hyperparams --netuid 11"
        assert "metagraph proof is present" in helpers["validation_summary"]

    def test_registration_validation_help_treats_blank_payload_as_missing(self, subnet):
        helpers = subnet.registration_validation_help(11, subnet="  ", registration_cost={"tao": 1.0})
        assert helpers["validated_reads"] == ["registration_cost"]
        assert helpers["missing_reads"] == ["subnet", "health"]
        assert helpers["next_validation_step"] == "agcli subnet show --netuid 11"

    def test_registration_validation_text(self, subnet):
        text = subnet.registration_validation_text(11, subnet={"netuid": 11})
        assert text == "Registration on subnet 11 has preflight reads subnet; still missing registration_cost, health."

    def test_registration_snapshot_help_combines_workflow_and_validation_fields(self, subnet):
        helpers = subnet.registration_snapshot_help(
            11,
            hotkey="miner",
            subnet={"netuid": 11},
            registration_cost={"tao": 1.0},
        )
        assert helpers["scope"] == "hotkey"
        assert helpers["validation_status"] == "partial"
        assert helpers["validated_reads"] == ["subnet", "registration_cost"]
        assert helpers["missing_reads"] == ["health"]
        assert helpers["confirmed_registered"] is False
        assert helpers["next_validation_step"] == "agcli subnet health --netuid 11"
        assert helpers["workflow"]["register_neuron"] == "agcli --hotkey-name miner subnet register-neuron --netuid 11"

    def test_registration_snapshot_text(self, subnet):
        text = subnet.registration_snapshot_text(11, subnet={"netuid": 11}, registration_cost={"tao": 1.0})
        assert text == (
            "Registration on subnet 11 has preflight reads subnet, registration_cost; still missing health. "
            "Next: agcli subnet health --netuid 11"
        )

    def test_registration_snapshot_help_preserves_workflow_fields(self, subnet):
        helpers = subnet.registration_snapshot_help(11, wallet="cold", registration_proof={"uid": 7})
        assert helpers["workflow"]["scope"] == "wallet"
        assert helpers["workflow"]["summary"] == "Check subnet 11 readiness, then register from wallet cold."
        assert helpers["workflow"]["post_registration_check"] == "agcli subnet metagraph --netuid 11 --full"
        assert helpers["confirmed_registered"] is True

    def test_registration_workflow_help_with_options(self, subnet):
        helpers = subnet.registration_workflow_help(
            11,
            wallet="cold",
            hotkey="miner",
            threads=8,
            max_cost=1.5,
            max_attempts=3,
        )
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert helpers["threads"] == 8
        assert helpers["max_cost"] == 1.5
        assert helpers["max_attempts"] == 3
        assert helpers["wallet_selection_note"]
        assert (
            helpers["register_neuron"] == "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 11"
        )
        assert helpers["pow_register"] == "agcli --wallet cold --hotkey-name miner subnet pow --netuid 11 --threads 8"
        assert helpers["snipe_register"] == (
            "agcli --wallet cold --hotkey-name miner subnet snipe --netuid 11 --max-cost 1.5 --max-attempts 3"
        )

    def test_registration_workflow_help_with_wallet_only(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold")
        assert helpers["wallet"] == "cold"
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --wallet cold subnet register-neuron --netuid 11"

    def test_registration_workflow_help_with_hotkey_only(self, subnet):
        helpers = subnet.registration_workflow_help(11, hotkey="miner")
        assert helpers["hotkey"] == "miner"
        assert helpers["wallet_selection_note"]
        assert helpers["register_neuron"] == "agcli --hotkey-name miner subnet register-neuron --netuid 11"

    def test_hyperparameter_workflow_help_with_wallet(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet="owner", param="tempo", value="360")
        assert helpers["wallet"] == "owner"
        assert helpers["wallet_selection_note"]
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5 --param tempo --value 360"
        assert helpers["mutation_note"]

    def test_hyperparameter_workflow_help_base_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli subnet set-param --netuid 5"

    def test_hyperparameter_workflow_help_with_wallet_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet="owner")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"

    def test_hyperparameters_workflow_help_alias_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner", param="tempo")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"

    def test_hyperparameter_workflow_help_with_param_only_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, param="tempo")
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli subnet set-param --netuid 5 --param tempo"

    def test_hyperparameter_workflow_help_ignores_value_without_param_but_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet="owner", value="360")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5"
        assert "value" not in helpers

    def test_hyperparameters_workflow_help_alias_base_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["param_list"] == "agcli subnet set-param --netuid 5 --param list"

    def test_hyperparameters_workflow_help_alias_value_uses_owner_param_list(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner", param="tempo", value="360")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5 --param tempo --value 360"

    def test_hyperparameter_workflow_help_alias_matches_owner_param_list(self, subnet):
        alias = subnet.hyperparameter_workflow_help(5, wallet="owner", param="tempo", value="360")
        plural = subnet.hyperparameters_workflow_help(5, wallet="owner", param="tempo", value="360")
        assert alias["owner_param_list"] == plural["owner_param_list"]
        assert alias == plural

    def test_hyperparameter_workflow_help_show_get_and_admin_list_stay_available(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["show"] == "agcli subnet show --netuid 5"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 5"
        assert helpers["admin_list"] == "agcli admin list"
        assert helpers["mutation_note"]

    def test_hyperparameter_workflow_help_with_trimmed_wallet_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet=" owner ")
        assert helpers["wallet"] == "owner"
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"

    def test_hyperparameter_workflow_help_with_param_and_value_keeps_value_field(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, param=" tempo ", value=" 360 ")
        assert helpers["param"] == "tempo"
        assert helpers["value"] == "360"
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 5 --param list"

    def test_hyperparameter_workflow_help_rejects_empty_wallet_duplicate(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameter_workflow_help(5, wallet="")

    def test_hyperparameter_workflow_help_keeps_wallet_selection_note_absent_without_wallet(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert "wallet_selection_note" not in helpers

    def test_hyperparameter_workflow_help_keeps_wallet_selection_note_present_with_wallet(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet="owner")
        assert helpers["wallet_selection_note"]

    def test_hyperparameter_workflow_help_keeps_owner_param_list_exact(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["owner_param_list"] == "agcli subnet set-param --netuid 5 --param list"

    def test_hyperparameters_workflow_help_keeps_owner_param_list_exact(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"

    def test_hyperparameter_workflow_help_with_wallet_and_param_only_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet="owner", param="tempo")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5 --param tempo"

    def test_hyperparameter_workflow_help_keeps_netuid(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["netuid"] == 5

    def test_hyperparameter_workflow_help_keeps_show(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["show"] == "agcli subnet show --netuid 5"

    def test_hyperparameter_workflow_help_keeps_get(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["get"] == "agcli subnet hyperparams --netuid 5"

    def test_hyperparameter_workflow_help_keeps_admin_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["admin_list"] == "agcli admin list"

    def test_hyperparameter_workflow_help_with_wallet_and_value_keeps_owner_param_list(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet="owner", param="tempo", value="360")
        assert helpers["owner_param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["value"] == "360"

    def test_hyperparameter_workflow_help_rejects_empty_param_duplicate(self, subnet):
        with pytest.raises(ValueError, match="param cannot be empty"):
            subnet.hyperparameter_workflow_help(5, param="")

    def test_hyperparameter_workflow_help_rejects_empty_value_duplicate(self, subnet):
        with pytest.raises(ValueError, match="value cannot be empty"):
            subnet.hyperparameter_workflow_help(5, param="tempo", value="")

    def test_hyperparameter_workflow_help_base(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5)
        assert helpers["param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["mutation_note"]
        assert helpers["set"] == "agcli subnet set-param --netuid 5"
        assert "wallet" not in helpers
        assert "wallet_selection_note" not in helpers

    def test_hyperparameters_workflow_help_alias_with_wallet(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner", param="tempo")
        assert helpers["wallet"] == "owner"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5 --param tempo"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"

    def test_hyperparameter_workflow_help_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameter_workflow_help(5, wallet="   ")

    def test_hyperparameters_workflow_help_alias_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameters_workflow_help(5, wallet="   ")

    def test_hyperparameter_workflow_help_ignores_value_without_param(self, subnet):
        helpers = subnet.hyperparameter_workflow_help(5, wallet="owner", value="360")
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5"
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert "value" not in helpers
        assert helpers["get"] == "agcli subnet hyperparams --netuid 5"

    def test_hyperparameter_workflow_help_rejects_empty_param(self, subnet):
        with pytest.raises(ValueError, match="param cannot be empty"):
            subnet.hyperparameter_workflow_help(1, param="   ")

    def test_hyperparameter_workflow_help_rejects_empty_value(self, subnet):
        with pytest.raises(ValueError, match="value cannot be empty"):
            subnet.hyperparameter_workflow_help(1, param="tempo", value="   ")

    def test_hyperparameter_workflow_help_rejects_invalid_netuid(self, subnet):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            subnet.hyperparameter_workflow_help(0)

    def test_hyperparameters_workflow_help(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers == {
            "netuid": 5,
            "show": "agcli subnet show --netuid 5",
            "get": "agcli subnet hyperparams --netuid 5",
            "param_list": "agcli subnet set-param --netuid 5 --param list",
            "owner_param_list": "agcli subnet set-param --netuid 5 --param list",
            "set": "agcli subnet set-param --netuid 5",
            "admin_list": "agcli admin list",
            "mutation_note": (
                "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
                "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
            ),
        }

    def test_hyperparameters_workflow_help_with_param_only(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, param="tempo")
        assert helpers["param"] == "tempo"
        assert helpers["param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli subnet set-param --netuid 5 --param tempo"
        assert "value" not in helpers

    def test_hyperparameters_workflow_help_with_set_param(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, param=" tempo ", value=" 360 ")
        assert helpers["param"] == "tempo"
        assert helpers["value"] == "360"
        assert helpers["param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli subnet set-param --netuid 5 --param tempo --value 360"

    def test_hyperparameters_workflow_help_ignores_value_without_param(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, value="360")
        assert helpers["set"] == "agcli subnet set-param --netuid 5"
        assert helpers["param_list"] == "agcli subnet set-param --netuid 5 --param list"
        assert helpers["get"] == "agcli subnet hyperparams --netuid 5"

    def test_hyperparameters_workflow_help_keeps_mutation_note(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, param="tempo")
        assert helpers["mutation_note"]

    def test_hyperparameters_workflow_help_keeps_admin_list(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers["admin_list"] == "agcli admin list"

    def test_hyperparameters_workflow_help_rejects_invalid_netuid(self, subnet):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            subnet.hyperparameters_workflow_help(0)

    def test_hyperparameters_workflow_help_rejects_empty_param(self, subnet):
        with pytest.raises(ValueError, match="param cannot be empty"):
            subnet.hyperparameters_workflow_help(1, param="   ")

    def test_hyperparameters_workflow_help_rejects_empty_value(self, subnet):
        with pytest.raises(ValueError, match="value cannot be empty"):
            subnet.hyperparameters_workflow_help(1, param="tempo", value="   ")

    def test_hyperparameters_workflow_help_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.hyperparameters_workflow_help(5, wallet="")

    def test_hyperparameters_workflow_help_with_wallet_and_value(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner", param="tempo", value="360")
        assert helpers["wallet"] == "owner"
        assert helpers["wallet_selection_note"]
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5 --param tempo --value 360"

    def test_hyperparameters_workflow_help_with_wallet_and_no_param(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner")
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5"
        assert helpers["wallet_selection_note"]

    def test_hyperparameters_workflow_help_with_wallet_param_only(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner", param="tempo")
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5 --param tempo"

    def test_hyperparameters_workflow_help_with_wallet_ignores_value_without_param(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner", value="360")
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5"
        assert "value" not in helpers

    def test_hyperparameters_workflow_help_keeps_show(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers["show"] == "agcli subnet show --netuid 5"

    def test_hyperparameters_workflow_help_keeps_netuid(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers["netuid"] == 5

    def test_hyperparameters_workflow_help_keeps_get(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers["get"] == "agcli subnet hyperparams --netuid 5"

    def test_hyperparameters_workflow_help_keeps_wallet_selection_note_absent_without_wallet(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert "wallet_selection_note" not in helpers

    def test_hyperparameters_workflow_help_keeps_wallet_selection_note_present_with_wallet(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner")
        assert helpers["wallet_selection_note"]

    def test_hyperparameters_workflow_help_keeps_param_list_with_wallet(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner")
        assert helpers["param_list"] == "agcli --wallet owner subnet set-param --netuid 5 --param list"

    def test_hyperparameters_workflow_help_keeps_param_list_without_wallet(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers["param_list"] == "agcli subnet set-param --netuid 5 --param list"

    def test_hyperparameters_workflow_help_keeps_mutation_note_with_wallet(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner")
        assert helpers["mutation_note"]

    def test_hyperparameters_workflow_help_keeps_wallet_name(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet="owner")
        assert helpers["wallet"] == "owner"

    def test_hyperparameters_workflow_help_with_trimmed_wallet(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5, wallet=" owner ")
        assert helpers["wallet"] == "owner"
        assert helpers["set"] == "agcli --wallet owner subnet set-param --netuid 5"

    def test_hyperparameter_workflow_help_alias_matches_hyperparameters(self, subnet):
        alias = subnet.hyperparameter_workflow_help(5, wallet="owner", param="tempo", value="360")
        plural = subnet.hyperparameters_workflow_help(5, wallet="owner", param="tempo", value="360")
        assert alias == plural

    def test_registration_workflow_help_with_trimmed_wallet_and_hotkey(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet=" cold ", hotkey=" miner ")
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert helpers["register_neuron"] == (
            "agcli --wallet cold --hotkey-name miner subnet register-neuron --netuid 11"
        )

    def test_registration_workflow_help_keeps_wallet_selection_note_absent_without_overrides(self, subnet):
        helpers = subnet.registration_workflow_help(11)
        assert "wallet_selection_note" not in helpers

    def test_registration_workflow_help_keeps_wallet_selection_note_present_with_overrides(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold")
        assert helpers["wallet_selection_note"]

    def test_registration_workflow_help_keeps_snipe_wallet_prefix(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold", hotkey="miner")
        assert helpers["snipe_register"].startswith("agcli --wallet cold --hotkey-name miner subnet snipe")

    def test_registration_workflow_help_keeps_pow_wallet_prefix(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold", hotkey="miner")
        assert helpers["pow_register"].startswith("agcli --wallet cold --hotkey-name miner subnet pow")

    def test_registration_workflow_help_keeps_register_wallet_prefix(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold", hotkey="miner")
        assert helpers["register_neuron"].startswith("agcli --wallet cold --hotkey-name miner subnet register-neuron")

    def test_registration_workflow_help_rejects_empty_hotkey_duplicate(self, subnet):
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            subnet.registration_workflow_help(11, hotkey="")

    def test_registration_workflow_help_rejects_empty_wallet_duplicate(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.registration_workflow_help(11, wallet="")

    def test_registration_workflow_help_keeps_health(self, subnet):
        helpers = subnet.registration_workflow_help(11)
        assert helpers["health"] == "agcli subnet health --netuid 11"

    def test_registration_workflow_help_keeps_hyperparams(self, subnet):
        helpers = subnet.registration_workflow_help(11)
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 11"

    def test_registration_workflow_help_keeps_cost(self, subnet):
        helpers = subnet.registration_workflow_help(11)
        assert helpers["registration_cost"] == "agcli subnet cost --netuid 11"

    def test_registration_workflow_help_keeps_netuid(self, subnet):
        helpers = subnet.registration_workflow_help(11)
        assert helpers["netuid"] == 11

    def test_registration_workflow_help_keeps_subnet(self, subnet):
        helpers = subnet.registration_workflow_help(11)
        assert helpers["subnet"] == "agcli subnet show --netuid 11"

    def test_registration_workflow_help_keeps_threads(self, subnet):
        helpers = subnet.registration_workflow_help(11, threads=8)
        assert helpers["threads"] == 8
        assert helpers["pow_register"] == "agcli subnet pow --netuid 11 --threads 8"

    def test_registration_workflow_help_keeps_max_cost_and_attempts(self, subnet):
        helpers = subnet.registration_workflow_help(11, max_cost=1.5, max_attempts=3)
        assert helpers["max_cost"] == 1.5
        assert helpers["max_attempts"] == 3
        assert helpers["snipe_register"] == "agcli subnet snipe --netuid 11 --max-cost 1.5 --max-attempts 3"

    def test_registration_workflow_help_with_wallet_and_threads(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold", threads=8)
        assert helpers["pow_register"] == "agcli --wallet cold subnet pow --netuid 11 --threads 8"

    def test_registration_workflow_help_with_hotkey_and_threads(self, subnet):
        helpers = subnet.registration_workflow_help(11, hotkey="miner", threads=8)
        assert helpers["pow_register"] == "agcli --hotkey-name miner subnet pow --netuid 11 --threads 8"

    def test_registration_workflow_help_with_wallet_and_snipe_options(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold", max_cost=1.5, max_attempts=3)
        assert helpers["snipe_register"] == (
            "agcli --wallet cold subnet snipe --netuid 11 --max-cost 1.5 --max-attempts 3"
        )

    def test_registration_workflow_help_with_hotkey_and_snipe_options(self, subnet):
        helpers = subnet.registration_workflow_help(11, hotkey="miner", max_cost=1.5, max_attempts=3)
        assert helpers["snipe_register"] == (
            "agcli --hotkey-name miner subnet snipe --netuid 11 --max-cost 1.5 --max-attempts 3"
        )

    def test_registration_workflow_help_with_wallet_and_hotkey_keeps_note(self, subnet):
        helpers = subnet.registration_workflow_help(11, wallet="cold", hotkey="miner")
        assert helpers["wallet_selection_note"] == (
            "These commands use agcli's global wallet selectors before the subcommand: "
            "--wallet chooses the coldkey and --hotkey-name chooses the hotkey file name."
        )

    def test_hyperparameters_workflow_help_keeps_mutation_note_exact(self, subnet):
        helpers = subnet.hyperparameters_workflow_help(5)
        assert helpers["mutation_note"] == (
            "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
            "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
        )

    def test_registration_workflow_help_rejects_invalid_netuid(self, subnet):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            subnet.registration_workflow_help(0)

    def test_registration_workflow_help_rejects_boolean_netuid(self, subnet):
        with pytest.raises(ValueError, match="netuid must be an integer"):
            subnet.registration_workflow_help(True)

    def test_registration_workflow_help_rejects_empty_wallet(self, subnet):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            subnet.registration_workflow_help(1, wallet="   ")
