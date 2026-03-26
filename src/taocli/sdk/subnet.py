"""Subnet SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Subnet(SdkModule):
    """Subnet operations — list, show, metagraph, register, health, etc."""

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
    def _optional_text(name: str, value: str | None) -> str | None:
        """Normalize optional text arguments used in workflow helpers."""
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty")
        return normalized

    @classmethod
    def _registration_prefix(
        cls, *, wallet: str | None = None, hotkey: str | None = None
    ) -> tuple[str, dict[str, Any]]:
        """Build a workflow command prefix for registration helpers."""
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

    @classmethod
    def _wallet_prefix(cls, *, wallet: str | None = None) -> tuple[str, dict[str, Any]]:
        """Build a workflow command prefix for coldkey-signed subnet owner helpers."""
        prefix = "agcli"
        context: dict[str, Any] = {}
        wallet_arg = cls._optional_text("wallet", wallet)
        if wallet_arg is not None:
            prefix = f"{prefix} --wallet {wallet_arg}"
            context["wallet"] = wallet_arg
            context["wallet_selection_note"] = cls._WALLET_SELECTION_NOTE
        return prefix, context

    @staticmethod
    def _hyperparameter_mutation_note() -> str:
        """Return guidance for owner-vs-admin hyperparameter changes."""
        return (
            "Use subnet set-param for subnet-owner parameters. For root-only knobs on localnet, "
            "inspect agcli admin list and run the matching agcli admin set-* command with --sudo-key."
        )

    @staticmethod
    def _param_list_command(netuid_arg: str, prefix: str) -> str:
        """Return the discovery command for listable subnet parameters."""
        return f"{prefix} subnet set-param --netuid {netuid_arg} --param list"

    @classmethod
    def registration_workflow_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
        threads: int | None = None,
        max_cost: float | None = None,
        max_attempts: int | None = None,
    ) -> dict[str, Any]:
        """Return a compact runbook for subnet registration workflows."""
        netuid_arg = cls._netuid_arg(netuid)
        prefix, context = cls._registration_prefix(wallet=wallet, hotkey=hotkey)
        register_neuron = f"{prefix} subnet register-neuron --netuid {netuid_arg}"
        pow_cmd = f"{prefix} subnet pow --netuid {netuid_arg}"
        snipe_cmd = f"{prefix} subnet snipe --netuid {netuid_arg}"
        commands: dict[str, Any] = {
            "netuid": int(netuid_arg),
            "subnet": f"agcli subnet show --netuid {netuid_arg}",
            "hyperparams": f"agcli subnet hyperparams --netuid {netuid_arg}",
            "registration_cost": f"agcli subnet cost --netuid {netuid_arg}",
            "health": f"agcli subnet health --netuid {netuid_arg}",
            "register_neuron": register_neuron,
            "pow_register": pow_cmd,
            "snipe_register": snipe_cmd,
        }
        commands.update(context)
        if threads is not None:
            pow_cmd = f"{pow_cmd} --threads {int(threads)}"
            commands["threads"] = int(threads)
        if max_cost is not None:
            snipe_cmd = f"{snipe_cmd} --max-cost {max_cost}"
            commands["max_cost"] = max_cost
        if max_attempts is not None:
            snipe_cmd = f"{snipe_cmd} --max-attempts {int(max_attempts)}"
            commands["max_attempts"] = int(max_attempts)
        commands["register_neuron"] = register_neuron
        commands["pow_register"] = pow_cmd
        commands["snipe_register"] = snipe_cmd
        return commands

    @classmethod
    def hyperparameter_workflow_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
    ) -> dict[str, Any]:
        """Return a compact runbook for reading and updating subnet hyperparameters."""
        netuid_arg = cls._netuid_arg(netuid)
        prefix, context = cls._wallet_prefix(wallet=wallet)
        list_cmd = cls._param_list_command(netuid_arg, prefix)
        commands: dict[str, Any] = {
            "netuid": int(netuid_arg),
            "show": f"agcli subnet show --netuid {netuid_arg}",
            "get": f"agcli subnet hyperparams --netuid {netuid_arg}",
            "param_list": list_cmd,
            "owner_param_list": list_cmd,
            "set": f"{prefix} subnet set-param --netuid {netuid_arg}",
            "admin_list": "agcli admin list",
            "mutation_note": cls._hyperparameter_mutation_note(),
        }
        commands.update(context)
        param_arg = cls._optional_text("param", param)
        value_arg = cls._optional_text("value", value)
        if param_arg is not None:
            commands["param"] = param_arg
            commands["set"] = f"{prefix} subnet set-param --netuid {netuid_arg} --param {param_arg}"
            if value_arg is not None:
                commands["set"] = (
                    f"{prefix} subnet set-param --netuid {netuid_arg} --param {param_arg} --value {value_arg}"
                )
                commands["value"] = value_arg
        return commands

    @classmethod
    def hyperparameters_workflow_help(
        cls, netuid: int, *, wallet: str | None = None, param: str | None = None, value: str | None = None
    ) -> dict[str, Any]:
        """Backward-compatible alias for hyperparameter_workflow_help."""
        return cls.hyperparameter_workflow_help(netuid, wallet=wallet, param=param, value=value)

    def list(self, at_block: int | None = None) -> Any:
        """List all subnets on the network."""
        args = ["subnet", "list"]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def show(self, netuid: int, at_block: int | None = None) -> Any:
        """Show details for a specific subnet."""
        args = ["subnet", "show", "--netuid", str(netuid)]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def hyperparams(self, netuid: int, at_block: int | None = None) -> Any:
        """Show hyperparameters for a subnet."""
        args = ["subnet", "hyperparams", "--netuid", str(netuid)]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def metagraph(
        self,
        netuid: int,
        uid: int | None = None,
        full: bool = False,
        at_block: int | None = None,
        save: bool = False,
    ) -> Any:
        """View the metagraph for a subnet."""
        args = ["subnet", "metagraph", "--netuid", str(netuid)]
        args += self._opt("--uid", uid)
        args += self._flag("--full", full)
        args += self._opt("--at-block", at_block)
        args += self._flag("--save", save)
        return self._run(args)

    def register(self) -> Any:
        """Register a new subnet."""
        return self._run(["subnet", "register"])

    def register_neuron(self, netuid: int) -> Any:
        """Register a neuron (miner/validator) on a subnet."""
        return self._run(["subnet", "register-neuron", "--netuid", str(netuid)])

    def pow(self, netuid: int, threads: int | None = None) -> Any:
        """Register a neuron via proof-of-work."""
        args = ["subnet", "pow", "--netuid", str(netuid)]
        args += self._opt("--threads", threads)
        return self._run(args)

    def health(self, netuid: int) -> Any:
        """Check health status of a subnet."""
        return self._run(["subnet", "health", "--netuid", str(netuid)])

    def emissions(self, netuid: int) -> Any:
        """View emission info for a subnet."""
        return self._run(["subnet", "emissions", "--netuid", str(netuid)])

    def cost(self, netuid: int) -> Any:
        """View the current registration cost for a subnet."""
        return self._run(["subnet", "cost", "--netuid", str(netuid)])

    def create_cost(self) -> Any:
        """View the cost to create a new subnet."""
        return self._run(["subnet", "create-cost"])

    def liquidity(self, netuid: int | None = None) -> Any:
        """View liquidity pool info for a subnet."""
        args = ["subnet", "liquidity"]
        args += self._opt("--netuid", netuid)
        return self._run(args)

    def dissolve(self, netuid: int) -> Any:
        """Dissolve (destroy) a subnet you own."""
        return self._run(["subnet", "dissolve", "--netuid", str(netuid)])

    def set_param(self, netuid: int, param: str, value: str) -> Any:
        """Set a hyperparameter on a subnet."""
        return self._run(["subnet", "set-param", "--netuid", str(netuid), "--param", param, "--value", value])

    def set_symbol(self, netuid: int, symbol: str) -> Any:
        """Set the token symbol for a subnet."""
        return self._run(["subnet", "set-symbol", "--netuid", str(netuid), "--symbol", symbol])

    def commits(self, netuid: int, hotkey_address: str | None = None) -> Any:
        """View weight commits on a subnet."""
        args = ["subnet", "commits", "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def probe(self, netuid: int, uids: str | None = None, timeout_ms: int | None = None) -> Any:
        """Probe neuron axon endpoints on a subnet."""
        args = ["subnet", "probe", "--netuid", str(netuid)]
        args += self._opt("--uids", uids)
        args += self._opt("--timeout-ms", timeout_ms)
        return self._run(args)

    def snipe(self, netuid: int, max_cost: float | None = None, max_attempts: int | None = None) -> Any:
        """Attempt to register on a subnet at minimal cost."""
        args = ["subnet", "snipe", "--netuid", str(netuid)]
        args += self._opt("--max-cost", max_cost)
        args += self._opt("--max-attempts", max_attempts)
        return self._run(args)

    def trim(self, netuid: int, max_uids: int) -> Any:
        """Trim a subnet down to a max number of UIDs."""
        return self._run(["subnet", "trim", "--netuid", str(netuid), "--max-uids", str(max_uids)])

    def start(self, netuid: int) -> Any:
        """Start a subnet that is in pending state."""
        return self._run(["subnet", "start", "--netuid", str(netuid)])

    def check_start(self, netuid: int) -> Any:
        """Check if a subnet is ready to start."""
        return self._run(["subnet", "check-start", "--netuid", str(netuid)])

    def emission_split(self, netuid: int) -> Any:
        """View the emission split for a subnet."""
        return self._run(["subnet", "emission-split", "--netuid", str(netuid)])

    def mechanism_count(self, netuid: int) -> Any:
        """View the number of mechanisms on a subnet."""
        return self._run(["subnet", "mechanism-count", "--netuid", str(netuid)])

    def set_mechanism_count(self, netuid: int, count: int) -> Any:
        """Set the number of mechanisms on a subnet."""
        return self._run(["subnet", "set-mechanism-count", "--netuid", str(netuid), "--count", str(count)])

    def set_emission_split(self, netuid: int, weights: str) -> Any:
        """Set the emission split weights for a subnet."""
        return self._run(["subnet", "set-emission-split", "--netuid", str(netuid), "--weights", weights])

    def cache_load(self, netuid: int) -> Any:
        """Load subnet state into local cache."""
        return self._run(["subnet", "cache-load", "--netuid", str(netuid)])

    def cache_list(self) -> Any:
        """List locally cached subnets."""
        return self._run(["subnet", "cache-list"])

    def cache_diff(self, netuid: int) -> Any:
        """Show diff between cached and on-chain subnet state."""
        return self._run(["subnet", "cache-diff", "--netuid", str(netuid)])

    def cache_prune(self) -> Any:
        """Remove stale entries from the subnet cache."""
        return self._run(["subnet", "cache-prune"])

    def register_with_identity(self, name: str | None = None) -> Any:
        """Register a subnet with an on-chain identity."""
        args = ["subnet", "register-with-identity"]
        args += self._opt("--name", name)
        return self._run(args)

    def register_leased(self, netuid: int | None = None) -> Any:
        """Register a leased subnet."""
        args = ["subnet", "register-leased"]
        args += self._opt("--netuid", netuid)
        return self._run(args)

    def terminate_lease(self, netuid: int) -> Any:
        """Terminate a subnet lease."""
        return self._run(["subnet", "terminate-lease", "--netuid", str(netuid)])

    def root_dissolve(self, netuid: int) -> Any:
        """Dissolve a subnet via root governance."""
        return self._run(["subnet", "root-dissolve", "--netuid", str(netuid)])

    def watch(self, netuid: int) -> Any:
        """Watch a subnet for real-time updates."""
        return self._run(["subnet", "watch", "--netuid", str(netuid)])

    def monitor(self, netuid: int) -> Any:
        """Monitor a subnet continuously."""
        return self._run(["subnet", "monitor", "--netuid", str(netuid)])
