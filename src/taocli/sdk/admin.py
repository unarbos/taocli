"""Admin SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Admin(SdkModule):
    """Admin (sudo) operations — set hyperparameters, raw sudo calls."""

    _SUDO_NOTE = (
        "Use admin list to discover the exact set-* command for root-only knobs, then "
        "run it with --sudo-key. Subnet-owner knobs can usually use subnet set-param instead."
    )
    _RECOMMENDED_ORDER = ["show", "get", "owner_param_list", "admin_list", "set"]

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

    @staticmethod
    def _optional_text_arg(name: str, value: str | None) -> str | None:
        """Normalize optional text arguments used in workflow helpers."""
        if value is None:
            return None
        return Admin._text_arg(name, value)

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
    def _validation_status(validated_reads: list[str], has_mutation_plan: bool) -> str:
        """Return a compact workflow status for admin hyperparameter helpers."""
        if len(validated_reads) == 4:
            return "ready_to_mutate" if has_mutation_plan else "ready"
        if validated_reads:
            return "partial"
        return "missing"

    @classmethod
    def _validation_summary(
        cls,
        netuid_arg: str,
        validated_reads: list[str],
        missing_reads: list[str],
        has_mutation_plan: bool,
    ) -> str:
        """Return a compact text summary for admin hyperparameter helpers."""
        if not validated_reads:
            return (
                f"Admin hyperparameter reads for subnet {netuid_arg} still need show, get, "
                "owner_param_list, and admin_list output."
            )
        if missing_reads:
            return (
                f"Admin hyperparameter reads for subnet {netuid_arg} have {', '.join(validated_reads)}; "
                f"still missing {', '.join(missing_reads)}."
            )
        if has_mutation_plan:
            return (
                f"Admin hyperparameter reads for subnet {netuid_arg} are ready and the mutation command is prepared."
            )
        return (
            f"Admin hyperparameter reads for subnet {netuid_arg} are ready: show, get, "
            "owner_param_list, and admin_list output are present."
        )

    @classmethod
    def _next_validation_step(
        cls,
        workflow: dict[str, Any],
        missing_reads: list[str],
    ) -> str:
        """Return the next command operators should run for admin hyperparameter validation."""
        if "show" in missing_reads:
            return str(workflow["show"])
        if "get" in missing_reads:
            return str(workflow["get"])
        if "owner_param_list" in missing_reads:
            return str(workflow["owner_param_list"])
        if "admin_list" in missing_reads:
            return str(workflow["admin_list"])
        return str(workflow.get("set") or workflow["raw"])

    @classmethod
    def hyperparameter_workflow_help(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
    ) -> dict[str, Any]:
        """Return a compact runbook for root-only subnet hyperparameter mutations."""
        netuid_arg = cls._netuid_arg(netuid)
        command_arg = cls._optional_text_arg("command", command)
        value_flag_arg = cls._optional_text_arg("value_flag", value_flag)
        sudo_key_arg = cls._optional_text_arg("sudo_key", sudo_key)

        if value_flag_arg is not None and command_arg is None:
            raise ValueError("value_flag requires command")
        if value is not None and (command_arg is None or value_flag_arg is None):
            raise ValueError("value requires command and value_flag")
        if sudo_key_arg is not None and command_arg is None:
            raise ValueError("sudo_key requires command")

        commands: dict[str, Any] = {
            "netuid": int(netuid_arg),
            "scope": "subnet_admin",
            "summary": (
                f"Inspect subnet {netuid_arg} hyperparameters, compare subnet-owner vs root-only knobs, "
                "then prepare the exact admin set-* command you need."
            ),
            "recommended_order": list(cls._RECOMMENDED_ORDER),
            "show": f"agcli subnet show --netuid {netuid_arg}",
            "get": f"agcli subnet hyperparams --netuid {netuid_arg}",
            "owner_param_list": f"agcli subnet set-param --netuid {netuid_arg} --param list",
            "admin_list": "agcli admin list",
            "raw": "agcli admin raw --call <sudo-call>",
            "sudo_note": cls._SUDO_NOTE,
            "primary_read": f"agcli subnet hyperparams --netuid {netuid_arg}",
            "mutation_check": "agcli admin list",
        }

        if command_arg is None:
            return commands

        mutation = f"agcli admin {command_arg} --netuid {netuid_arg}"
        commands["command"] = command_arg
        if value_flag_arg is not None:
            mutation = f"{mutation} {value_flag_arg}"
            commands["value_flag"] = value_flag_arg
            if value is None:
                mutation = f"{mutation} <value>"
            else:
                normalized_value = str(value).lower() if isinstance(value, bool) else str(value)
                mutation = f"{mutation} {normalized_value}"
                commands["value"] = normalized_value
        if sudo_key_arg is not None:
            mutation = f"{mutation} --sudo-key {sudo_key_arg}"
            commands["sudo_key"] = sudo_key_arg
        commands["set"] = mutation
        return commands

    @classmethod
    def hyperparameter_validation_help(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> dict[str, Any]:
        """Return a compact validation summary for supplied admin hyperparameter reads."""
        workflow = cls.hyperparameter_workflow_help(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
        )
        read_payloads = (
            ("show", show),
            ("get", get),
            ("owner_param_list", owner_param_list),
            ("admin_list", admin_list),
        )
        validated_reads = [name for name, payload in read_payloads if cls._has_payload(payload)]
        missing_reads = [
            name for name in ("show", "get", "owner_param_list", "admin_list") if name not in validated_reads
        ]
        has_mutation_plan = "set" in workflow
        return {
            "netuid": workflow["netuid"],
            "scope": workflow["scope"],
            "validated_reads": validated_reads,
            "missing_reads": missing_reads,
            "has_mutation_plan": has_mutation_plan,
            "validation_status": cls._validation_status(validated_reads, has_mutation_plan),
            "validation_summary": cls._validation_summary(
                str(workflow["netuid"]), validated_reads, missing_reads, has_mutation_plan
            ),
            "next_validation_step": cls._next_validation_step(workflow, missing_reads),
            "workflow": workflow,
        }

    @classmethod
    def hyperparameter_validation_text(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> str:
        """Return a concise text summary for supplied admin hyperparameter reads."""
        summary = cls.hyperparameter_validation_help(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
            show=show,
            get=get,
            owner_param_list=owner_param_list,
            admin_list=admin_list,
        )
        return str(summary["validation_summary"])

    @classmethod
    def hyperparameter_snapshot_help(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> dict[str, Any]:
        """Return a practical operator snapshot combining admin workflow and validation fields."""
        validation = cls.hyperparameter_validation_help(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
            show=show,
            get=get,
            owner_param_list=owner_param_list,
            admin_list=admin_list,
        )
        workflow = dict(validation["workflow"])
        snapshot = dict(workflow)
        snapshot["workflow"] = workflow
        snapshot["validation_status"] = validation["validation_status"]
        snapshot["validation_summary"] = validation["validation_summary"]
        snapshot["validated_reads"] = validation["validated_reads"]
        snapshot["missing_reads"] = validation["missing_reads"]
        snapshot["has_mutation_plan"] = validation["has_mutation_plan"]
        snapshot["next_validation_step"] = validation["next_validation_step"]
        return snapshot

    @classmethod
    def hyperparameter_snapshot_text(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> str:
        """Return a concise operator snapshot text for supplied admin hyperparameter reads."""
        snapshot = cls.hyperparameter_snapshot_help(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
            show=show,
            get=get,
            owner_param_list=owner_param_list,
            admin_list=admin_list,
        )
        return f"{snapshot['validation_summary']} Next: {snapshot['next_validation_step']}"

    @classmethod
    def hyperparameters_validation_help(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> dict[str, Any]:
        """Backward-compatible alias for hyperparameter_validation_help."""
        return cls.hyperparameter_validation_help(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
            show=show,
            get=get,
            owner_param_list=owner_param_list,
            admin_list=admin_list,
        )

    @classmethod
    def hyperparameters_validation_text(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> str:
        """Backward-compatible alias for hyperparameter_validation_text."""
        return cls.hyperparameter_validation_text(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
            show=show,
            get=get,
            owner_param_list=owner_param_list,
            admin_list=admin_list,
        )

    @classmethod
    def hyperparameters_snapshot_help(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> dict[str, Any]:
        """Backward-compatible alias for hyperparameter_snapshot_help."""
        return cls.hyperparameter_snapshot_help(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
            show=show,
            get=get,
            owner_param_list=owner_param_list,
            admin_list=admin_list,
        )

    @classmethod
    def hyperparameters_snapshot_text(
        cls,
        netuid: int,
        *,
        command: str | None = None,
        value_flag: str | None = None,
        value: str | int | float | bool | None = None,
        sudo_key: str | None = None,
        show: object | None = None,
        get: object | None = None,
        owner_param_list: object | None = None,
        admin_list: object | None = None,
    ) -> str:
        """Backward-compatible alias for hyperparameter_snapshot_text."""
        return cls.hyperparameter_snapshot_text(
            netuid,
            command=command,
            value_flag=value_flag,
            value=value,
            sudo_key=sudo_key,
            show=show,
            get=get,
            owner_param_list=owner_param_list,
            admin_list=admin_list,
        )

    @classmethod
    def hyperparameter_mutation_help(
        cls,
        command: str,
        netuid: int,
        *,
        value_flag: str,
        value: str | int | float | bool,
        sudo_key: str | None = None,
    ) -> str:
        """Build a normalized agcli admin command for a subnet hyperparameter change."""
        command_arg = cls._text_arg("command", command)
        value_flag_arg = cls._text_arg("value_flag", value_flag)
        normalized_value = str(value).lower() if isinstance(value, bool) else str(value)
        cmd = f"agcli admin {command_arg} --netuid {cls._netuid_arg(netuid)} {value_flag_arg} {normalized_value}"
        if sudo_key is not None:
            cmd = f"{cmd} --sudo-key {cls._text_arg('sudo_key', sudo_key)}"
        return cmd

    def set_tempo(self, netuid: int, tempo: int, sudo_key: str | None = None) -> Any:
        """Set the tempo (blocks per epoch) for a subnet."""
        cmd = ["admin", "set-tempo", "--netuid", str(netuid), "--tempo", str(tempo)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_validators(self, netuid: int, max: int, sudo_key: str | None = None) -> Any:
        """Set the maximum number of validators on a subnet."""
        cmd = ["admin", "set-max-validators", "--netuid", str(netuid), "--max", str(max)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_uids(self, netuid: int, max: int, sudo_key: str | None = None) -> Any:
        """Set the maximum number of UIDs on a subnet."""
        cmd = ["admin", "set-max-uids", "--netuid", str(netuid), "--max", str(max)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_immunity_period(self, netuid: int, period: int, sudo_key: str | None = None) -> Any:
        """Set the immunity period (epochs) for a subnet."""
        cmd = ["admin", "set-immunity-period", "--netuid", str(netuid), "--period", str(period)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_min_weights(self, netuid: int, min: int, sudo_key: str | None = None) -> Any:
        """Set the minimum number of weights per validator."""
        cmd = ["admin", "set-min-weights", "--netuid", str(netuid), "--min", str(min)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_weight_limit(self, netuid: int, limit: int, sudo_key: str | None = None) -> Any:
        """Set the maximum weight value per UID."""
        cmd = ["admin", "set-max-weight-limit", "--netuid", str(netuid), "--limit", str(limit)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_weights_rate_limit(self, netuid: int, limit: int, sudo_key: str | None = None) -> Any:
        """Set the rate limit for weight updates."""
        cmd = ["admin", "set-weights-rate-limit", "--netuid", str(netuid), "--limit", str(limit)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_commit_reveal(self, netuid: int, enabled: bool, sudo_key: str | None = None) -> Any:
        """Enable or disable commit-reveal for weights."""
        cmd = ["admin", "set-commit-reveal", "--netuid", str(netuid), "--enabled", str(enabled).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_difficulty(self, netuid: int, difficulty: int, sudo_key: str | None = None) -> Any:
        """Set the PoW difficulty for a subnet."""
        cmd = ["admin", "set-difficulty", "--netuid", str(netuid), "--difficulty", str(difficulty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_activity_cutoff(self, netuid: int, cutoff: int, sudo_key: str | None = None) -> Any:
        """Set the activity cutoff (epochs) for a subnet."""
        cmd = ["admin", "set-activity-cutoff", "--netuid", str(netuid), "--cutoff", str(cutoff)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_default_take(self, take: int, sudo_key: str | None = None) -> Any:
        """Set the default delegate take percentage."""
        cmd = ["admin", "set-default-take", "--take", str(take)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_tx_rate_limit(self, limit: int, sudo_key: str | None = None) -> Any:
        """Set the global transaction rate limit."""
        cmd = ["admin", "set-tx-rate-limit", "--limit", str(limit)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_min_difficulty(self, netuid: int, difficulty: int, sudo_key: str | None = None) -> Any:
        """Set the minimum PoW difficulty for a subnet."""
        cmd = ["admin", "set-min-difficulty", "--netuid", str(netuid), "--difficulty", str(difficulty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_difficulty(self, netuid: int, difficulty: int, sudo_key: str | None = None) -> Any:
        """Set the maximum PoW difficulty for a subnet."""
        cmd = ["admin", "set-max-difficulty", "--netuid", str(netuid), "--difficulty", str(difficulty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_adjustment_interval(self, netuid: int, interval: int, sudo_key: str | None = None) -> Any:
        """Set the difficulty adjustment interval."""
        cmd = ["admin", "set-adjustment-interval", "--netuid", str(netuid), "--interval", str(interval)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_kappa(self, netuid: int, kappa: int, sudo_key: str | None = None) -> Any:
        """Set the kappa consensus parameter."""
        cmd = ["admin", "set-kappa", "--netuid", str(netuid), "--kappa", str(kappa)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_rho(self, netuid: int, rho: int, sudo_key: str | None = None) -> Any:
        """Set the rho consensus parameter."""
        cmd = ["admin", "set-rho", "--netuid", str(netuid), "--rho", str(rho)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_min_burn(self, netuid: int, burn: str, sudo_key: str | None = None) -> Any:
        """Set the minimum burn amount for registration."""
        cmd = ["admin", "set-min-burn", "--netuid", str(netuid), "--burn", burn]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_max_burn(self, netuid: int, burn: str, sudo_key: str | None = None) -> Any:
        """Set the maximum burn amount for registration."""
        cmd = ["admin", "set-max-burn", "--netuid", str(netuid), "--burn", burn]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_liquid_alpha(self, netuid: int, enabled: bool, sudo_key: str | None = None) -> Any:
        """Enable or disable liquid alpha on a subnet."""
        cmd = ["admin", "set-liquid-alpha", "--netuid", str(netuid), "--enabled", str(enabled).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_alpha_values(self, netuid: int, alpha_low: str, alpha_high: str, sudo_key: str | None = None) -> Any:
        """Set alpha low and high values for a subnet."""
        cmd = [
            "admin",
            "set-alpha-values",
            "--netuid",
            str(netuid),
            "--alpha-low",
            alpha_low,
            "--alpha-high",
            alpha_high,
        ]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_yuma3(self, netuid: int, enabled: bool, sudo_key: str | None = None) -> Any:
        """Enable or disable Yuma3 consensus."""
        cmd = ["admin", "set-yuma3", "--netuid", str(netuid), "--enabled", str(enabled).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_bonds_penalty(self, netuid: int, penalty: int, sudo_key: str | None = None) -> Any:
        """Set the bonds penalty for a subnet."""
        cmd = ["admin", "set-bonds-penalty", "--netuid", str(netuid), "--penalty", str(penalty)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_stake_threshold(self, threshold: str, sudo_key: str | None = None) -> Any:
        """Set the global stake threshold."""
        cmd = ["admin", "set-stake-threshold", "--threshold", threshold]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_network_registration(self, netuid: int, allowed: bool, sudo_key: str | None = None) -> Any:
        """Allow or disallow network registration on a subnet."""
        cmd = ["admin", "set-network-registration", "--netuid", str(netuid), "--allowed", str(allowed).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_pow_registration(self, netuid: int, allowed: bool, sudo_key: str | None = None) -> Any:
        """Allow or disallow PoW registration on a subnet."""
        cmd = ["admin", "set-pow-registration", "--netuid", str(netuid), "--allowed", str(allowed).lower()]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_adjustment_alpha(self, netuid: int, alpha: str, sudo_key: str | None = None) -> Any:
        """Set the difficulty adjustment alpha."""
        cmd = ["admin", "set-adjustment-alpha", "--netuid", str(netuid), "--alpha", alpha]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_subnet_moving_alpha(self, alpha: str, sudo_key: str | None = None) -> Any:
        """Set the global subnet moving alpha."""
        cmd = ["admin", "set-subnet-moving-alpha", "--alpha", alpha]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_mechanism_count(self, netuid: int, count: int, sudo_key: str | None = None) -> Any:
        """Set the number of mechanisms on a subnet."""
        cmd = ["admin", "set-mechanism-count", "--netuid", str(netuid), "--count", str(count)]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_mechanism_emission_split(self, netuid: int, weights: str, sudo_key: str | None = None) -> Any:
        """Set the emission split between mechanisms."""
        cmd = ["admin", "set-mechanism-emission-split", "--netuid", str(netuid), "--weights", weights]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def set_nominator_min_stake(self, stake: str, sudo_key: str | None = None) -> Any:
        """Set the minimum stake for nominators."""
        cmd = ["admin", "set-nominator-min-stake", "--stake", stake]
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def raw(self, call: str, args: str | None = None, sudo_key: str | None = None) -> Any:
        """Execute a raw sudo call."""
        cmd = ["admin", "raw", "--call", call]
        cmd += self._opt("--args", args)
        cmd += self._opt("--sudo-key", sudo_key)
        return self._run(cmd)

    def list(self) -> Any:
        """List all admin-configurable parameters."""
        return self._run(["admin", "list"])
