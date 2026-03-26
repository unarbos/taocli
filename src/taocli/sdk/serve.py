"""Serve SDK module."""

from __future__ import annotations

import ipaddress
import re
from typing import Any

from taocli.sdk.base import SdkModule


class Serve(SdkModule):
    """Axon serving operations — serve/unserve endpoints."""

    _WALLET_SELECTION_NOTE = (
        "These commands use agcli's global wallet selectors before the subcommand: "
        "--wallet chooses the coldkey and --hotkey-name chooses the hotkey file name."
    )

    @staticmethod
    def _netuid_arg(netuid: int) -> str:
        """Normalize a subnet identifier for workflow helpers."""
        if isinstance(netuid, bool):
            raise ValueError("netuid must be an integer")
        normalized = int(netuid)
        if normalized <= 0:
            raise ValueError("netuid must be greater than 0")
        return str(normalized)

    @staticmethod
    def _text_arg(name: str, value: str) -> str:
        """Normalize required text arguments used in workflow helpers."""
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty")
        return normalized

    @classmethod
    def _ip_arg(cls, ip: str) -> str:
        """Normalize an IP address or hostname for serve helpers."""
        normalized = cls._text_arg("ip", ip)
        try:
            ipaddress.ip_address(normalized)
        except ValueError:
            if not re.fullmatch(r"[A-Za-z0-9.-]+", normalized):
                raise ValueError("ip must be a valid IP address or hostname") from None
        return normalized

    @classmethod
    def _optional_text(cls, name: str, value: str | None) -> str | None:
        """Normalize optional text arguments used in workflow helpers."""
        if value is None:
            return None
        return cls._text_arg(name, value)

    @classmethod
    def _command_prefix(cls, *, wallet: str | None = None, hotkey: str | None = None) -> tuple[str, dict[str, Any]]:
        """Build a workflow command prefix for serve helpers."""
        prefix = "agcli"
        context: dict[str, Any] = {}
        wallet_arg = cls._optional_text("wallet", wallet)
        hotkey_arg = cls._optional_text("hotkey", hotkey)
        if wallet_arg is not None:
            prefix = f"{prefix} --wallet {wallet_arg}"
            context["wallet"] = wallet_arg
        if hotkey_arg is not None:
            prefix = f"{prefix} --hotkey-name {hotkey_arg}"
            context["hotkey"] = hotkey_arg
        if wallet_arg is not None or hotkey_arg is not None:
            context["wallet_selection_note"] = cls._WALLET_SELECTION_NOTE
        return prefix, context

    @staticmethod
    def _hotkey_selector_note() -> str:
        """Return guidance for weights status wallet semantics."""
        return (
            "weights status resolves the hotkey from agcli's global wallet selectors. "
            "Use the same --wallet / --hotkey-name values you plan to serve with so the validator permit and pending "
            "commit checks are for the correct hotkey."
        )

    @staticmethod
    def _registration_note(netuid_arg: str, hotkey_label: str) -> str:
        """Return operator guidance for serve prerequisites and verification."""
        return (
            "Axon serving only updates endpoint metadata. "
            f"Make sure {hotkey_label} is already registered on SN{netuid_arg} "
            "before serving, then confirm the endpoint with view axon / subnet probe."
        )

    @staticmethod
    def _version_note() -> str:
        """Return guidance for the serve version field."""
        return (
            "The serve --version flag is the endpoint metadata version reported on-chain, "
            "not the subnet weights_version hyperparameter used by weights set / reveal flows."
        )

    @staticmethod
    def _weights_note() -> str:
        """Return guidance for checking validator permit before serving + weights."""
        return (
            "If this hotkey will also validate or set weights, check weights status "
            "and subnet hyperparams after serving so validator-permit, commit-reveal, "
            "and rate-limit expectations stay aligned with the same hotkey."
        )

    @staticmethod
    def _prometheus_note() -> str:
        """Return guidance for prometheus endpoint semantics."""
        return (
            "Prometheus metadata is advertised separately from the axon endpoint; "
            "serve it only if you expose metrics publicly."
        )

    @staticmethod
    def _tls_note() -> str:
        """Return guidance for axon TLS serving."""
        return (
            "axon-tls reads the certificate file locally before submitting the on-chain "
            "endpoint update; keep the cert path accessible on the serving host."
        )

    @staticmethod
    def _network_probe_note() -> str:
        """Return guidance for probe usage after serving."""
        return (
            "subnet probe is the fastest post-serve check for whether the subnet can "
            "actually reach the advertised endpoint."
        )

    @staticmethod
    def _serve_port_note() -> str:
        """Return guidance for serve port validation differences."""
        return (
            "taocli validates serve helper ports as 1..65535 so the generated commands "
            "are copy-pasteable against agcli's runtime checks."
        )

    @staticmethod
    def _served_endpoint_selector(netuid_arg: str, ip_arg: str, port_arg: int) -> str:
        """Return a human-readable endpoint label for notes."""
        return f"SN{netuid_arg} {ip_arg}:{port_arg}"

    @staticmethod
    def _protocol_note() -> str:
        """Return guidance for protocol/IP version selection."""
        return "Use protocol 4 for IPv4 and 6 for IPv6 to match agcli's serve endpoint expectations."

    @staticmethod
    def _prometheus_status_check(netuid_arg: str) -> str:
        """Return the view command used to inspect served prometheus metadata."""
        return f"agcli view axon --netuid {netuid_arg}"

    @staticmethod
    def _wallet_fields(context: dict[str, Any]) -> dict[str, Any]:
        """Return workflow context fields that should be surfaced in helper output."""
        surfaced = dict(context)
        wallet_selection_note = surfaced.pop("wallet_selection_note", None)
        if wallet_selection_note is not None:
            surfaced["wallet_selection_note"] = wallet_selection_note
        return surfaced

    @staticmethod
    def _weights_prereq(prefix: str, netuid_arg: str) -> str:
        """Return the weights status command tied to the same wallet selectors."""
        return f"{prefix} weights status --netuid {netuid_arg}"

    @staticmethod
    def _registration_check(netuid_arg: str) -> str:
        """Return the subnet status command used to verify registration context."""
        return f"agcli subnet show --netuid {netuid_arg}"

    @staticmethod
    def _probe_command(netuid_arg: str) -> str:
        """Return the probe command used after serving."""
        return f"agcli subnet probe --netuid {netuid_arg}"

    @staticmethod
    def _inspect_axon_command(netuid_arg: str) -> str:
        """Return the view command used to inspect served axon metadata."""
        return f"agcli view axon --netuid {netuid_arg}"

    @staticmethod
    def _hyperparams_command(netuid_arg: str) -> str:
        """Return the hyperparameter inspection command used alongside serve helpers."""
        return f"agcli subnet hyperparams --netuid {netuid_arg}"

    @staticmethod
    def _reset_command(prefix: str, netuid_arg: str) -> str:
        """Return the reset command tied to the same wallet selectors."""
        return f"{prefix} serve reset --netuid {netuid_arg}"

    @staticmethod
    def _serve_prefix_fields(context: dict[str, Any]) -> dict[str, Any]:
        """Normalize surfaced prefix fields for helper output."""
        return dict(context)

    @staticmethod
    def _serve_prereq_note(endpoint_label: str) -> str:
        """Return a concise endpoint-specific note."""
        return (
            f"After serving {endpoint_label}, verify the endpoint and any validator "
            "workflow assumptions before advertising it to operators."
        )

    @staticmethod
    def _hotkey_label(context: dict[str, Any]) -> str:
        """Return a human-readable hotkey label for notes."""
        return str(context.get("hotkey") or "the configured hotkey")

    @staticmethod
    def _versioned_prometheus_command(base: str, version: int | None) -> str:
        """Append version to a prometheus command when provided."""
        if version is None:
            return base
        return f"{base} --version {version}"

    @staticmethod
    def _versioned_tls_command(base: str, version: int | None) -> str:
        """Append version to a TLS serve command when provided."""
        if version is None:
            return base
        return f"{base} --version {version}"

    @staticmethod
    def _protocolized_tls_command(base: str, protocol: int | None) -> str:
        """Append protocol to a TLS serve command when provided."""
        if protocol is None:
            return base
        return f"{base} --protocol {protocol}"

    @staticmethod
    def _port_arg(name: str, port: int) -> int:
        """Normalize a TCP port value."""
        if isinstance(port, bool):
            raise ValueError(f"{name} must be an integer")
        normalized = int(port)
        if normalized < 1 or normalized > 65535:
            raise ValueError(f"{name} must be between 1 and 65535")
        return normalized

    @staticmethod
    def _protocol_arg(protocol: int) -> int:
        """Normalize a protocol / IP version selector."""
        if isinstance(protocol, bool):
            raise ValueError("protocol must be an integer")
        normalized = int(protocol)
        if normalized not in {4, 6}:
            raise ValueError("protocol must be 4 or 6")
        return normalized

    @staticmethod
    def _version_arg(version: int) -> int:
        """Normalize an endpoint version value."""
        if isinstance(version, bool):
            raise ValueError("version must be an integer")
        normalized = int(version)
        if normalized < 0:
            raise ValueError("version must be greater than or equal to 0")
        return normalized

    @classmethod
    def axon_workflow_help(
        cls,
        netuid: int,
        ip: str,
        port: int,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
        protocol: int | None = None,
        version: int | None = None,
        cert: str | None = None,
        prometheus_port: int | None = None,
    ) -> dict[str, Any]:
        """Return a compact runbook for serving and verifying axon endpoints."""
        netuid_arg = cls._netuid_arg(netuid)
        ip_arg = cls._ip_arg(ip)
        port_arg = cls._port_arg("port", port)
        prefix, context = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        protocol_arg = cls._protocol_arg(protocol) if protocol is not None else None
        version_arg = cls._version_arg(version) if version is not None else None

        serve_axon = f"{prefix} serve axon --netuid {netuid_arg} --ip {ip_arg} --port {port_arg}"
        if protocol_arg is not None:
            serve_axon = f"{serve_axon} --protocol {protocol_arg}"
        if version_arg is not None:
            serve_axon = f"{serve_axon} --version {version_arg}"

        inspect_axon = cls._inspect_axon_command(netuid_arg)
        probe = cls._probe_command(netuid_arg)
        registration_check = cls._registration_check(netuid_arg)
        weights_status = cls._weights_prereq(prefix, netuid_arg)
        hyperparams = cls._hyperparams_command(netuid_arg)
        commands: dict[str, Any] = {
            "netuid": int(netuid_arg),
            **cls._wallet_fields(context),
            "serve_axon": serve_axon,
            "reset": cls._reset_command(prefix, netuid_arg),
            "inspect_axon": inspect_axon,
            "probe": probe,
            "status_check": inspect_axon,
            "registration_check": registration_check,
            "weights_status": weights_status,
            "hyperparams": hyperparams,
            "registration_note": cls._registration_note(netuid_arg, cls._hotkey_label(context)),
            "weights_note": cls._weights_note(),
            "hotkey_selector_note": cls._hotkey_selector_note(),
            "version_note": cls._version_note(),
            "protocol_note": cls._protocol_note(),
            "network_probe_note": cls._network_probe_note(),
            "serve_port_note": cls._serve_port_note(),
            "serve_prereq_note": cls._serve_prereq_note(cls._served_endpoint_selector(netuid_arg, ip_arg, port_arg)),
        }
        if prometheus_port is not None:
            prometheus_port_arg = cls._port_arg("prometheus_port", prometheus_port)
            serve_prometheus = (
                f"{prefix} serve prometheus --netuid {netuid_arg} --ip {ip_arg} --port {prometheus_port_arg}"
            )
            if version_arg is not None:
                serve_prometheus = f"{serve_prometheus} --version {version_arg}"
            commands["serve_prometheus"] = serve_prometheus
            commands["prometheus_check"] = cls._prometheus_status_check(netuid_arg)
            commands["prometheus_note"] = cls._prometheus_note()
        if cert is not None:
            cert_arg = cls._text_arg("cert", cert)
            serve_axon_tls = (
                f"{prefix} serve axon-tls --netuid {netuid_arg} --ip {ip_arg} --port {port_arg} --cert {cert_arg}"
            )
            if protocol_arg is not None:
                serve_axon_tls = f"{serve_axon_tls} --protocol {protocol_arg}"
            if version_arg is not None:
                serve_axon_tls = f"{serve_axon_tls} --version {version_arg}"
            commands["serve_axon_tls"] = serve_axon_tls
            commands["tls_note"] = cls._tls_note()
        return commands

    def axon(self, netuid: int, ip: str, port: int, protocol: int | None = None, version: int | None = None) -> Any:
        """Serve an axon endpoint on a subnet."""
        args = ["serve", "axon", "--netuid", str(netuid), "--ip", ip, "--port", str(port)]
        args += self._opt("--protocol", protocol)
        args += self._opt("--version", version)
        return self._run(args)

    def reset(self, netuid: int) -> Any:
        """Reset axon serving info for a subnet."""
        return self._run(["serve", "reset", "--netuid", str(netuid)])

    def batch_axon(self, file: str) -> Any:
        """Serve multiple axon endpoints from a batch file."""
        return self._run(["serve", "batch-axon", "--file", file])

    def prometheus(self, netuid: int, ip: str, port: int, version: int | None = None) -> Any:
        """Serve a Prometheus metrics endpoint."""
        cmd = ["serve", "prometheus", "--netuid", str(netuid), "--ip", ip, "--port", str(port)]
        cmd += self._opt("--version", version)
        return self._run(cmd)

    def axon_tls(
        self, netuid: int, ip: str, port: int, cert: str, protocol: int | None = None, version: int | None = None
    ) -> Any:
        """Serve an axon endpoint with TLS encryption."""
        cmd = ["serve", "axon-tls", "--netuid", str(netuid), "--ip", ip, "--port", str(port), "--cert", cert]
        cmd += self._opt("--protocol", protocol)
        cmd += self._opt("--version", version)
        return self._run(cmd)
