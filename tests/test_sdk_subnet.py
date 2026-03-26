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
        assert helpers == {
            "netuid": 11,
            "subnet": "agcli subnet show --netuid 11",
            "hyperparams": "agcli subnet hyperparams --netuid 11",
            "registration_cost": "agcli subnet cost --netuid 11",
            "health": "agcli subnet health --netuid 11",
            "register_neuron": "agcli subnet register-neuron --netuid 11",
            "pow_register": "agcli subnet pow --netuid 11",
            "snipe_register": "agcli subnet snipe --netuid 11",
        }

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
