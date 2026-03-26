"""Tests for the Serve SDK module."""

from __future__ import annotations

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.serve import Serve


@pytest.fixture
def serve(mock_subprocess):
    return Serve(AgcliRunner())


class TestServe:
    def test_axon(self, serve, mock_subprocess):
        serve.axon(1, "0.0.0.0", 8080)
        cmd = mock_subprocess.call_args[0][0]
        assert "serve" in cmd and "axon" in cmd
        assert "--netuid" in cmd and "--ip" in cmd and "--port" in cmd

    def test_axon_with_protocol(self, serve, mock_subprocess):
        serve.axon(1, "0.0.0.0", 8080, protocol=4)
        cmd = mock_subprocess.call_args[0][0]
        assert "--protocol" in cmd

    def test_axon_with_version(self, serve, mock_subprocess):
        serve.axon(1, "0.0.0.0", 8080, version=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version" in cmd

    def test_reset(self, serve, mock_subprocess):
        serve.reset(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "reset" in cmd and "--netuid" in cmd

    def test_batch_axon(self, serve, mock_subprocess):
        serve.batch_axon("axons.json")
        cmd = mock_subprocess.call_args[0][0]
        assert "batch-axon" in cmd and "--file" in cmd

    def test_prometheus(self, serve, mock_subprocess):
        serve.prometheus(1, "0.0.0.0", 9090)
        cmd = mock_subprocess.call_args[0][0]
        assert "prometheus" in cmd and "--ip" in cmd

    def test_prometheus_with_version(self, serve, mock_subprocess):
        serve.prometheus(1, "0.0.0.0", 9090, version=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version" in cmd

    def test_axon_tls(self, serve, mock_subprocess):
        serve.axon_tls(1, "0.0.0.0", 8080, "/path/cert.pem")
        cmd = mock_subprocess.call_args[0][0]
        assert "axon-tls" in cmd and "--cert" in cmd

    def test_axon_tls_with_opts(self, serve, mock_subprocess):
        serve.axon_tls(1, "0.0.0.0", 8080, "/path/cert.pem", protocol=4, version=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--protocol" in cmd and "--version" in cmd

    def test_axon_workflow_help(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080)
        assert helpers == {
            "netuid": 8,
            "serve_axon": "agcli serve axon --netuid 8 --ip 0.0.0.0 --port 8080",
            "reset": "agcli serve reset --netuid 8",
            "inspect_axon": "agcli view axon --netuid 8",
            "probe": "agcli subnet probe --netuid 8",
            "status_check": "agcli view axon --netuid 8",
            "registration_check": "agcli subnet show --netuid 8",
            "weights_status": "agcli weights status --netuid 8",
            "hyperparams": "agcli subnet hyperparams --netuid 8",
            "registration_note": (
                "Axon serving only updates endpoint metadata. Make sure the configured hotkey "
                "is already registered on SN8 before serving, then confirm the endpoint with "
                "view axon / subnet probe."
            ),
            "weights_note": (
                "If this hotkey will also validate or set weights, check weights status and "
                "subnet hyperparams after serving so validator-permit, commit-reveal, and "
                "rate-limit expectations stay aligned with the same hotkey."
            ),
            "hotkey_selector_note": (
                "weights status resolves the hotkey from agcli's global wallet selectors. Use "
                "the same --wallet / --hotkey-name values you plan to serve with so the "
                "validator permit and pending commit checks are for the correct hotkey."
            ),
            "version_note": (
                "The serve --version flag is the endpoint metadata version reported on-chain, "
                "not the subnet weights_version hyperparameter used by weights set / reveal "
                "flows."
            ),
            "protocol_note": "Use protocol 4 for IPv4 and 6 for IPv6 to match agcli's serve endpoint expectations.",
            "network_probe_note": (
                "subnet probe is the fastest post-serve check for whether the subnet can "
                "actually reach the advertised endpoint."
            ),
            "serve_port_note": (
                "taocli validates serve helper ports as 1..65535 so the generated commands "
                "are copy-pasteable against agcli's runtime checks."
            ),
            "serve_prereq_note": (
                "After serving SN8 0.0.0.0:8080, verify the endpoint and any validator "
                "workflow assumptions before advertising it to operators."
            ),
        }

    def test_axon_workflow_help_with_wallet_and_hotkey(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert helpers["wallet_selection_note"]
        assert (
            helpers["serve_axon"]
            == "agcli --wallet cold --hotkey-name miner serve axon --netuid 8 --ip 0.0.0.0 --port 8080"
        )
        assert helpers["reset"] == "agcli --wallet cold --hotkey-name miner serve reset --netuid 8"
        assert helpers["weights_status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 8"
        assert "miner" in helpers["registration_note"]

    def test_axon_workflow_help_with_wallet_rejects_empty_wallet(self, serve):
        with pytest.raises(ValueError, match="wallet cannot be empty"):
            serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="   ")

    def test_axon_workflow_help_with_hotkey_rejects_empty_hotkey(self, serve):
        with pytest.raises(ValueError, match="hotkey cannot be empty"):
            serve.axon_workflow_help(8, "0.0.0.0", 8080, hotkey="   ")

    def test_axon_workflow_help_with_hotkey_only(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, hotkey="miner")
        assert helpers["wallet_selection_note"]
        assert helpers["serve_axon"] == "agcli --hotkey-name miner serve axon --netuid 8 --ip 0.0.0.0 --port 8080"
        assert helpers["weights_status"] == "agcli --hotkey-name miner weights status --netuid 8"

    def test_axon_workflow_help_with_wallet_only(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold")
        assert helpers["wallet_selection_note"]
        assert helpers["serve_axon"] == "agcli --wallet cold serve axon --netuid 8 --ip 0.0.0.0 --port 8080"
        assert helpers["weights_status"] == "agcli --wallet cold weights status --netuid 8"

    def test_axon_workflow_help_with_trimmed_wallet_and_hotkey(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet=" cold ", hotkey=" miner ")
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert (
            helpers["serve_axon"]
            == "agcli --wallet cold --hotkey-name miner serve axon --netuid 8 --ip 0.0.0.0 --port 8080"
        )

    def test_axon_workflow_help_prometheus_inherits_wallet_prefix(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", prometheus_port=9090)
        assert helpers["serve_prometheus"] == "agcli --wallet cold serve prometheus --netuid 8 --ip 0.0.0.0 --port 9090"
        assert helpers["prometheus_check"] == "agcli view axon --netuid 8"
        assert helpers["prometheus_note"]

    def test_axon_workflow_help_tls_inherits_wallet_prefix(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, hotkey="miner", cert="/tmp/cert.pem")
        assert (
            helpers["serve_axon_tls"]
            == "agcli --hotkey-name miner serve axon-tls --netuid 8 --ip 0.0.0.0 --port 8080 --cert /tmp/cert.pem"
        )
        assert helpers["tls_note"]

    def test_axon_workflow_help_weights_and_hyperparams_notes_are_present(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080)
        assert helpers["weights_status"] == "agcli weights status --netuid 8"
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 8"
        assert helpers["weights_note"]
        assert helpers["hotkey_selector_note"]
        assert helpers["serve_prereq_note"]
        assert helpers["serve_port_note"]
        assert helpers["protocol_note"]
        assert helpers["version_note"]
        assert helpers["network_probe_note"]

    def test_axon_workflow_help_port_zero_is_rejected_even_if_agcli_cli_parses_it(self, serve):
        with pytest.raises(ValueError, match="port must be between 1 and 65535"):
            serve.axon_workflow_help(8, "0.0.0.0", 0)

    def test_axon_workflow_help_prometheus_port_zero_is_rejected(self, serve):
        with pytest.raises(ValueError, match="prometheus_port must be between 1 and 65535"):
            serve.axon_workflow_help(8, "0.0.0.0", 8080, prometheus_port=0)

    def test_axon_workflow_help_includes_status_for_operator_workflows(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["weights_status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 8"
        assert helpers["registration_check"] == "agcli subnet show --netuid 8"
        assert helpers["inspect_axon"] == "agcli view axon --netuid 8"
        assert helpers["probe"] == "agcli subnet probe --netuid 8"

    def test_axon_workflow_help_with_protocol_and_version_notes(self, serve):
        helpers = serve.axon_workflow_help(8, "127.0.0.1", 8080, protocol=6, version=7)
        assert (
            helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080 --protocol 6 --version 7"
        )
        assert helpers["protocol_note"]
        assert helpers["version_note"]

    def test_axon_workflow_help_prometheus_and_tls_include_version_when_present(self, serve):
        helpers = serve.axon_workflow_help(8, "127.0.0.1", 8080, version=7, prometheus_port=9090, cert="/tmp/cert.pem")
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 7"
        assert (
            helpers["serve_axon_tls"]
            == "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem --version 7"
        )

    def test_axon_workflow_help_tls_and_prometheus_inherit_protocol_and_version_independently(self, serve):
        helpers = serve.axon_workflow_help(
            8, "127.0.0.1", 8080, protocol=4, version=7, prometheus_port=9090, cert="/tmp/cert.pem"
        )
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 7"
        assert (
            helpers["serve_axon_tls"] == "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 "
            "--cert /tmp/cert.pem --protocol 4 --version 7"
        )

    def test_axon_workflow_help_keeps_status_check_as_view_axon(self, serve):
        helpers = serve.axon_workflow_help(8, "127.0.0.1", 8080, wallet="cold")
        assert helpers["status_check"] == "agcli view axon --netuid 8"
        assert helpers["weights_status"] == "agcli --wallet cold weights status --netuid 8"

    def test_axon_workflow_help_handles_hostname_with_wallet(self, serve):
        helpers = serve.axon_workflow_help(8, "validator-1.local", 8080, wallet="cold")
        assert helpers["serve_axon"] == "agcli --wallet cold serve axon --netuid 8 --ip validator-1.local --port 8080"
        assert (
            helpers["serve_prereq_note"]
            == "After serving SN8 validator-1.local:8080, verify the endpoint and any validator "
            "workflow assumptions before advertising it to operators."
        )

    def test_axon_workflow_help_prometheus_with_wallet_and_version(self, serve):
        helpers = serve.axon_workflow_help(8, "validator-1.local", 8080, wallet="cold", version=3, prometheus_port=9090)
        assert (
            helpers["serve_prometheus"]
            == "agcli --wallet cold serve prometheus --netuid 8 --ip validator-1.local --port 9090 --version 3"
        )

    def test_axon_workflow_help_tls_with_wallet_and_protocol(self, serve):
        helpers = serve.axon_workflow_help(
            8, "validator-1.local", 8080, wallet="cold", protocol=4, cert="/tmp/cert.pem"
        )
        assert (
            helpers["serve_axon_tls"]
            == "agcli --wallet cold serve axon-tls --netuid 8 --ip validator-1.local --port 8080 "
            "--cert /tmp/cert.pem --protocol 4"
        )

    def test_axon_workflow_help_hotkey_only_registration_note(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, hotkey="miner")
        assert (
            helpers["registration_note"]
            == "Axon serving only updates endpoint metadata. Make sure miner is already registered "
            "on SN8 before serving, then confirm the endpoint with view axon / subnet probe."
        )

    def test_axon_workflow_help_default_registration_note_mentions_configured_hotkey(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080)
        assert (
            helpers["registration_note"]
            == "Axon serving only updates endpoint metadata. Make sure the configured hotkey is "
            "already registered on SN8 before serving, then confirm the endpoint with view axon "
            "/ subnet probe."
        )

    def test_axon_workflow_help_wallet_fields_do_not_hide_selection_note(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold")
        assert helpers["wallet"] == "cold"
        assert helpers["wallet_selection_note"]

    def test_axon_workflow_help_hotkey_fields_do_not_hide_selection_note(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, hotkey="miner")
        assert helpers["hotkey"] == "miner"
        assert helpers["wallet_selection_note"]

    def test_axon_workflow_help_wallet_and_hotkey_fields_do_not_hide_selection_note(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["wallet"] == "cold"
        assert helpers["hotkey"] == "miner"
        assert helpers["wallet_selection_note"]

    def test_axon_workflow_help_prometheus_note_only_when_present(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080)
        assert "prometheus_note" not in helpers
        assert "prometheus_check" not in helpers

    def test_axon_workflow_help_tls_note_only_when_present(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080)
        assert "tls_note" not in helpers

    def test_axon_workflow_help_prometheus_note_when_present(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, prometheus_port=9090)
        assert helpers["prometheus_note"]
        assert helpers["prometheus_check"] == "agcli view axon --netuid 8"

    def test_axon_workflow_help_tls_note_when_present(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, cert="/tmp/cert.pem")
        assert helpers["tls_note"]

    def test_axon_workflow_help_serve_prereq_note_uses_hostname(self, serve):
        helpers = serve.axon_workflow_help(8, "example.com", 8080)
        assert (
            helpers["serve_prereq_note"] == "After serving SN8 example.com:8080, verify the endpoint and any validator "
            "workflow assumptions before advertising it to operators."
        )

    def test_axon_workflow_help_hyperparams_command_stays_unprefixed(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["hyperparams"] == "agcli subnet hyperparams --netuid 8"

    def test_axon_workflow_help_registration_check_stays_unprefixed(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["registration_check"] == "agcli subnet show --netuid 8"

    def test_axon_workflow_help_probe_stays_unprefixed(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["probe"] == "agcli subnet probe --netuid 8"

    def test_axon_workflow_help_inspect_axon_stays_unprefixed(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["inspect_axon"] == "agcli view axon --netuid 8"

    def test_axon_workflow_help_status_check_stays_unprefixed(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["status_check"] == "agcli view axon --netuid 8"

    def test_axon_workflow_help_without_wallet_or_hotkey_has_no_selection_note(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080)
        assert "wallet_selection_note" not in helpers
        assert "wallet" not in helpers
        assert "hotkey" not in helpers

    def test_axon_workflow_help_weights_status_can_be_used_for_validator_checks(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["weights_status"] == "agcli --wallet cold --hotkey-name miner weights status --netuid 8"
        assert helpers["weights_note"]

    def test_axon_workflow_help_keeps_existing_aliases(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080)
        assert helpers["inspect_axon"] == helpers["status_check"]

    def test_axon_workflow_help_reuses_prefixed_reset(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, wallet="cold", hotkey="miner")
        assert helpers["reset"] == "agcli --wallet cold --hotkey-name miner serve reset --netuid 8"

    def test_axon_workflow_help_supports_version_zero(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, version=0)
        assert helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 0.0.0.0 --port 8080 --version 0"

    def test_axon_workflow_help_supports_protocol_six(self, serve):
        helpers = serve.axon_workflow_help(8, "0.0.0.0", 8080, protocol=6)
        assert helpers["serve_axon"] == "agcli serve axon --netuid 8 --ip 0.0.0.0 --port 8080 --protocol 6"

    def test_axon_workflow_help_prometheus_uses_same_host(self, serve):
        helpers = serve.axon_workflow_help(8, "example.com", 8080, prometheus_port=9090)
        assert helpers["serve_prometheus"] == "agcli serve prometheus --netuid 8 --ip example.com --port 9090"

    def test_axon_workflow_help_tls_uses_same_host(self, serve):
        helpers = serve.axon_workflow_help(8, "example.com", 8080, cert="/tmp/cert.pem")
        assert (
            helpers["serve_axon_tls"]
            == "agcli serve axon-tls --netuid 8 --ip example.com --port 8080 --cert /tmp/cert.pem"
        )

    def test_axon_workflow_help_prometheus_check_matches_view_axon(self, serve):
        helpers = serve.axon_workflow_help(8, "example.com", 8080, prometheus_port=9090)
        assert helpers["prometheus_check"] == helpers["inspect_axon"]

    def test_axon_workflow_help_with_all_options(self, serve):
        helpers = serve.axon_workflow_help(
            8,
            "127.0.0.1",
            8080,
            protocol=4,
            version=7,
            cert=" /tmp/cert.pem ",
            prometheus_port=9090,
        )
        assert helpers["serve_axon"] == (
            "agcli serve axon --netuid 8 --ip 127.0.0.1 --port 8080 --protocol 4 --version 7"
        )
        assert helpers["serve_prometheus"] == (
            "agcli serve prometheus --netuid 8 --ip 127.0.0.1 --port 9090 --version 7"
        )
        assert helpers["serve_axon_tls"] == (
            "agcli serve axon-tls --netuid 8 --ip 127.0.0.1 --port 8080 --cert /tmp/cert.pem --protocol 4 --version 7"
        )
        assert helpers["status_check"] == "agcli view axon --netuid 8"
        assert helpers["registration_check"] == "agcli subnet show --netuid 8"

    def test_axon_workflow_help_includes_verification_aliases(self, serve):
        helpers = serve.axon_workflow_help(12, "0.0.0.0", 9000)
        assert helpers["inspect_axon"] == "agcli view axon --netuid 12"
        assert helpers["status_check"] == "agcli view axon --netuid 12"
        assert helpers["registration_check"] == "agcli subnet show --netuid 12"
        assert helpers["probe"] == "agcli subnet probe --netuid 12"

    def test_axon_workflow_help_rejects_invalid_netuid(self, serve):
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            serve.axon_workflow_help(0, "0.0.0.0", 8080)

    def test_axon_workflow_help_rejects_empty_ip(self, serve):
        with pytest.raises(ValueError, match="ip cannot be empty"):
            serve.axon_workflow_help(1, "   ", 8080)

    def test_axon_workflow_help_rejects_empty_cert(self, serve):
        with pytest.raises(ValueError, match="cert cannot be empty"):
            serve.axon_workflow_help(1, "0.0.0.0", 8080, cert="   ")

    def test_axon_workflow_help_rejects_invalid_ip(self, serve):
        with pytest.raises(ValueError, match="ip must be a valid IP address or hostname"):
            serve.axon_workflow_help(1, "bad host!", 8080)

    def test_axon_workflow_help_rejects_invalid_port(self, serve):
        with pytest.raises(ValueError, match="port must be between 1 and 65535"):
            serve.axon_workflow_help(1, "0.0.0.0", 0)

    def test_axon_workflow_help_rejects_invalid_prometheus_port(self, serve):
        with pytest.raises(ValueError, match="prometheus_port must be between 1 and 65535"):
            serve.axon_workflow_help(1, "0.0.0.0", 8080, prometheus_port=70000)

    def test_axon_workflow_help_rejects_invalid_protocol(self, serve):
        with pytest.raises(ValueError, match="protocol must be 4 or 6"):
            serve.axon_workflow_help(1, "0.0.0.0", 8080, protocol=5)

    def test_axon_workflow_help_rejects_boolean_protocol(self, serve):
        with pytest.raises(ValueError, match="protocol must be an integer"):
            serve.axon_workflow_help(1, "0.0.0.0", 8080, protocol=True)

    def test_axon_workflow_help_rejects_boolean_version(self, serve):
        with pytest.raises(ValueError, match="version must be an integer"):
            serve.axon_workflow_help(1, "0.0.0.0", 8080, version=True)

    def test_axon_workflow_help_rejects_negative_version(self, serve):
        with pytest.raises(ValueError, match="version must be greater than or equal to 0"):
            serve.axon_workflow_help(1, "0.0.0.0", 8080, version=-1)

    def test_axon_workflow_help_rejects_boolean_netuid(self, serve):
        with pytest.raises(ValueError, match="netuid must be an integer"):
            serve.axon_workflow_help(True, "0.0.0.0", 8080)

    def test_axon_workflow_help_rejects_boolean_port(self, serve):
        with pytest.raises(ValueError, match="port must be an integer"):
            serve.axon_workflow_help(1, "0.0.0.0", True)

    def test_serve_prefix_fields_returns_copy(self, serve):
        context = {"wallet": "cold", "extra": 42}
        fields = Serve._serve_prefix_fields(context)
        assert fields == context
        assert fields is not context

    def test_versioned_prometheus_command_without_version(self, serve):
        result = Serve._versioned_prometheus_command("agcli serve prometheus --netuid 1", None)
        assert result == "agcli serve prometheus --netuid 1"

    def test_versioned_prometheus_command_with_version(self, serve):
        result = Serve._versioned_prometheus_command("agcli serve prometheus --netuid 1", 3)
        assert result == "agcli serve prometheus --netuid 1 --version 3"

    def test_versioned_tls_command_without_version(self, serve):
        result = Serve._versioned_tls_command("agcli serve axon-tls --netuid 1", None)
        assert result == "agcli serve axon-tls --netuid 1"

    def test_versioned_tls_command_with_version(self, serve):
        result = Serve._versioned_tls_command("agcli serve axon-tls --netuid 1", 5)
        assert result == "agcli serve axon-tls --netuid 1 --version 5"

    def test_protocolized_tls_command_without_protocol(self, serve):
        result = Serve._protocolized_tls_command("agcli serve axon-tls --netuid 1", None)
        assert result == "agcli serve axon-tls --netuid 1"

    def test_protocolized_tls_command_with_protocol(self, serve):
        result = Serve._protocolized_tls_command("agcli serve axon-tls --netuid 1", 4)
        assert result == "agcli serve axon-tls --netuid 1 --protocol 4"

    def test_axon_workflow_help_accepts_hostname(self, serve):
        helpers = serve.axon_workflow_help(1, "validator-1.local", 8080)
        assert helpers["serve_axon"].endswith("--ip validator-1.local --port 8080")
