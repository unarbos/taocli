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

    @staticmethod
    def _has_payload(payload: object | None) -> bool:
        """Return whether a workflow payload is meaningfully present."""
        if payload is None:
            return False
        if isinstance(payload, str):
            return bool(payload.strip())
        if isinstance(payload, (list, tuple, set, dict)):
            return bool(payload)
        return True

    @staticmethod
    def _hyperparameter_validation_status(validated_reads: list[str]) -> str:
        """Return a compact workflow status for hyperparameter validation helpers."""
        if len(validated_reads) == 3:
            return "ready"
        if validated_reads:
            return "partial"
        return "missing"

    @classmethod
    def _hyperparameter_validation_summary(
        cls,
        netuid_arg: str,
        validated_reads: list[str],
        missing_reads: list[str],
    ) -> str:
        """Return a compact text summary for hyperparameter validation helpers."""
        if not validated_reads:
            return (
                f"Hyperparameter reads for subnet {netuid_arg} still need subnet, hyperparams, and param_list output."
            )
        if missing_reads:
            return (
                f"Hyperparameter reads for subnet {netuid_arg} have {', '.join(validated_reads)}; "
                f"still missing {', '.join(missing_reads)}."
            )
        return (
            f"Hyperparameter reads for subnet {netuid_arg} are ready: subnet, "
            "hyperparams, and param_list output are present."
        )

    @classmethod
    def _hyperparameter_next_validation_step(
        cls,
        workflow: dict[str, Any],
        missing_reads: list[str],
    ) -> str:
        """Return the next command operators should run for hyperparameter validation."""
        if "subnet" in missing_reads:
            return str(workflow["show"])
        if "hyperparams" in missing_reads:
            return str(workflow["get"])
        if "param_list" in missing_reads:
            return str(workflow["param_list"])
        return str(workflow["set"])

    @staticmethod
    def _registration_scope(wallet: str | None, hotkey: str | None) -> str:
        """Return a compact selector label for registration helpers."""
        if wallet is not None and hotkey is not None:
            return "wallet_and_hotkey"
        if hotkey is not None:
            return "hotkey"
        if wallet is not None:
            return "wallet"
        return "subnet"

    @staticmethod
    def _registration_summary(netuid_arg: str, wallet: str | None, hotkey: str | None) -> str:
        """Return a compact operator summary for registration workflows."""
        if wallet is not None and hotkey is not None:
            return (
                f"Check subnet {netuid_arg} readiness, then register hotkey {hotkey} from wallet {wallet}."
            )
        if hotkey is not None:
            return f"Check subnet {netuid_arg} readiness, then register hotkey {hotkey}."
        if wallet is not None:
            return f"Check subnet {netuid_arg} readiness, then register from wallet {wallet}."
        return f"Check subnet {netuid_arg} readiness, then register on subnet {netuid_arg}."

    @staticmethod
    def _registration_confirmation_note() -> str:
        """Return guidance for proving a registration landed on-chain."""
        return (
            "After registration, inspect the full metagraph and confirm the new hotkey or UID appears before moving on."
        )

    @staticmethod
    def _registration_validation_status(validated_reads: list[str], confirmed_registered: bool) -> str:
        """Return a compact workflow status for registration validation helpers."""
        if confirmed_registered:
            return "registered"
        if len(validated_reads) == 3:
            return "ready"
        if validated_reads:
            return "partial"
        return "missing"

    @classmethod
    def _registration_validation_summary(
        cls,
        netuid_arg: str,
        validated_reads: list[str],
        missing_reads: list[str],
        confirmed_registered: bool,
    ) -> str:
        """Return a compact text summary for registration validation helpers."""
        if confirmed_registered:
            return (
                "Registration on subnet "
                f"{netuid_arg} looks confirmed: preflight reads are ready and metagraph proof is present."
            )
        if not validated_reads:
            return (
                f"Registration on subnet {netuid_arg} still needs preflight reads: {', '.join(missing_reads)}."
            )
        if missing_reads:
            return (
                f"Registration on subnet {netuid_arg} has preflight reads {', '.join(validated_reads)}; "
                f"still missing {', '.join(missing_reads)}."
            )
        return (
            f"Registration on subnet {netuid_arg} is ready: subnet, registration cost, and health checks are present."
        )

    @classmethod
    def _registration_next_validation_step(
        cls,
        workflow: dict[str, Any],
        missing_reads: list[str],
        confirmed_registered: bool,
    ) -> str:
        """Return the next command operators should run for registration validation."""
        if "subnet" in missing_reads:
            return str(workflow["subnet"])
        if "registration_cost" in missing_reads:
            return str(workflow["registration_cost"])
        if "health" in missing_reads:
            return str(workflow["health"])
        if confirmed_registered:
            return str(workflow["hyperparams"])
        return str(workflow["primary_register"])

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
        wallet_arg = context.get("wallet")
        hotkey_arg = context.get("hotkey")
        register_neuron = f"{prefix} subnet register-neuron --netuid {netuid_arg}"
        pow_cmd = f"{prefix} subnet pow --netuid {netuid_arg}"
        snipe_cmd = f"{prefix} subnet snipe --netuid {netuid_arg}"
        commands: dict[str, Any] = {
            "netuid": int(netuid_arg),
            "scope": cls._registration_scope(wallet_arg, hotkey_arg),
            "summary": cls._registration_summary(netuid_arg, wallet_arg, hotkey_arg),
            "recommended_order": [
                "subnet",
                "registration_cost",
                "health",
                "register_neuron",
                "post_registration_check",
            ],
            "subnet": f"agcli subnet show --netuid {netuid_arg}",
            "hyperparams": f"agcli subnet hyperparams --netuid {netuid_arg}",
            "registration_cost": f"agcli subnet cost --netuid {netuid_arg}",
            "health": f"agcli subnet health --netuid {netuid_arg}",
            "register_neuron": register_neuron,
            "pow_register": pow_cmd,
            "snipe_register": snipe_cmd,
            "post_registration_check": f"agcli subnet metagraph --netuid {netuid_arg} --full",
            "primary_register": register_neuron,
            "registration_confirmation_note": cls._registration_confirmation_note(),
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
    def registration_validation_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
        subnet: object | None = None,
        registration_cost: object | None = None,
        health: object | None = None,
        registration_proof: object | None = None,
    ) -> dict[str, Any]:
        """Return a compact validation summary for supplied registration reads."""
        workflow = cls.registration_workflow_help(netuid, wallet=wallet, hotkey=hotkey)
        read_payloads = (("subnet", subnet), ("registration_cost", registration_cost), ("health", health))
        validated_reads = [name for name, payload in read_payloads if cls._has_payload(payload)]
        missing_reads = [name for name in ("subnet", "registration_cost", "health") if name not in validated_reads]
        confirmed_registered = cls._has_payload(registration_proof)
        return {
            "netuid": workflow["netuid"],
            "scope": workflow["scope"],
            "validated_reads": validated_reads,
            "missing_reads": missing_reads,
            "confirmed_registered": confirmed_registered,
            "validation_status": cls._registration_validation_status(validated_reads, confirmed_registered),
            "validation_summary": cls._registration_validation_summary(
                str(workflow["netuid"]), validated_reads, missing_reads, confirmed_registered
            ),
            "next_validation_step": cls._registration_next_validation_step(
                workflow, missing_reads, confirmed_registered
            ),
            "workflow": workflow,
        }

    @classmethod
    def registration_validation_text(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
        subnet: object | None = None,
        registration_cost: object | None = None,
        health: object | None = None,
        registration_proof: object | None = None,
    ) -> str:
        """Return a concise text summary for supplied registration reads."""
        summary = cls.registration_validation_help(
            netuid,
            wallet=wallet,
            hotkey=hotkey,
            subnet=subnet,
            registration_cost=registration_cost,
            health=health,
            registration_proof=registration_proof,
        )
        return str(summary["validation_summary"])

    @classmethod
    def registration_snapshot_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
        subnet: object | None = None,
        registration_cost: object | None = None,
        health: object | None = None,
        registration_proof: object | None = None,
    ) -> dict[str, Any]:
        """Return a practical operator snapshot combining registration workflow and validation fields."""
        validation = cls.registration_validation_help(
            netuid,
            wallet=wallet,
            hotkey=hotkey,
            subnet=subnet,
            registration_cost=registration_cost,
            health=health,
            registration_proof=registration_proof,
        )
        workflow = dict(validation["workflow"])
        snapshot = dict(workflow)
        snapshot["workflow"] = workflow
        snapshot["validation_status"] = validation["validation_status"]
        snapshot["validation_summary"] = validation["validation_summary"]
        snapshot["validated_reads"] = validation["validated_reads"]
        snapshot["missing_reads"] = validation["missing_reads"]
        snapshot["confirmed_registered"] = validation["confirmed_registered"]
        snapshot["next_validation_step"] = validation["next_validation_step"]
        return snapshot

    @classmethod
    def registration_snapshot_text(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
        subnet: object | None = None,
        registration_cost: object | None = None,
        health: object | None = None,
        registration_proof: object | None = None,
    ) -> str:
        """Return a concise operator snapshot text for supplied registration reads."""
        snapshot = cls.registration_snapshot_help(
            netuid,
            wallet=wallet,
            hotkey=hotkey,
            subnet=subnet,
            registration_cost=registration_cost,
            health=health,
            registration_proof=registration_proof,
        )
        return f"{snapshot['validation_summary']} Next: {snapshot['next_validation_step']}"

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

    @classmethod
    def hyperparameter_validation_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> dict[str, Any]:
        """Return a compact validation summary for supplied hyperparameter reads."""
        workflow = cls.hyperparameter_workflow_help(netuid, wallet=wallet, param=param, value=value)
        read_payloads = (("subnet", subnet), ("hyperparams", hyperparams), ("param_list", param_list))
        validated_reads = [name for name, payload in read_payloads if cls._has_payload(payload)]
        missing_reads = [name for name in ("subnet", "hyperparams", "param_list") if name not in validated_reads]
        return {
            "netuid": workflow["netuid"],
            "validated_reads": validated_reads,
            "missing_reads": missing_reads,
            "validation_status": cls._hyperparameter_validation_status(validated_reads),
            "validation_summary": cls._hyperparameter_validation_summary(
                str(workflow["netuid"]), validated_reads, missing_reads
            ),
            "next_validation_step": cls._hyperparameter_next_validation_step(workflow, missing_reads),
            "workflow": workflow,
        }

    @classmethod
    def hyperparameter_validation_text(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> str:
        """Return a concise text summary for supplied hyperparameter reads."""
        summary = cls.hyperparameter_validation_help(
            netuid,
            wallet=wallet,
            param=param,
            value=value,
            subnet=subnet,
            hyperparams=hyperparams,
            param_list=param_list,
        )
        return str(summary["validation_summary"])

    @classmethod
    def hyperparameter_snapshot_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> dict[str, Any]:
        """Return a practical operator snapshot combining hyperparameter workflow and validation fields."""
        validation = cls.hyperparameter_validation_help(
            netuid,
            wallet=wallet,
            param=param,
            value=value,
            subnet=subnet,
            hyperparams=hyperparams,
            param_list=param_list,
        )
        workflow = dict(validation["workflow"])
        snapshot = dict(workflow)
        snapshot["workflow"] = workflow
        snapshot["validation_status"] = validation["validation_status"]
        snapshot["validation_summary"] = validation["validation_summary"]
        snapshot["validated_reads"] = validation["validated_reads"]
        snapshot["missing_reads"] = validation["missing_reads"]
        snapshot["next_validation_step"] = validation["next_validation_step"]
        return snapshot

    @classmethod
    def hyperparameter_snapshot_text(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> str:
        """Return a concise operator snapshot text for supplied hyperparameter reads."""
        snapshot = cls.hyperparameter_snapshot_help(
            netuid,
            wallet=wallet,
            param=param,
            value=value,
            subnet=subnet,
            hyperparams=hyperparams,
            param_list=param_list,
        )
        return f"{snapshot['validation_summary']} Next: {snapshot['next_validation_step']}"

    @classmethod
    def hyperparameters_validation_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> dict[str, Any]:
        """Backward-compatible alias for hyperparameter_validation_help."""
        return cls.hyperparameter_validation_help(
            netuid,
            wallet=wallet,
            param=param,
            value=value,
            subnet=subnet,
            hyperparams=hyperparams,
            param_list=param_list,
        )

    @classmethod
    def hyperparameters_validation_text(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> str:
        """Backward-compatible alias for hyperparameter_validation_text."""
        return cls.hyperparameter_validation_text(
            netuid,
            wallet=wallet,
            param=param,
            value=value,
            subnet=subnet,
            hyperparams=hyperparams,
            param_list=param_list,
        )

    @classmethod
    def hyperparameters_snapshot_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> dict[str, Any]:
        """Backward-compatible alias for hyperparameter_snapshot_help."""
        return cls.hyperparameter_snapshot_help(
            netuid,
            wallet=wallet,
            param=param,
            value=value,
            subnet=subnet,
            hyperparams=hyperparams,
            param_list=param_list,
        )

    @classmethod
    def hyperparameters_snapshot_text(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        param: str | None = None,
        value: str | None = None,
        subnet: object | None = None,
        hyperparams: object | None = None,
        param_list: object | None = None,
    ) -> str:
        """Backward-compatible alias for hyperparameter_snapshot_text."""
        return cls.hyperparameter_snapshot_text(
            netuid,
            wallet=wallet,
            param=param,
            value=value,
            subnet=subnet,
            hyperparams=hyperparams,
            param_list=param_list,
        )

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
