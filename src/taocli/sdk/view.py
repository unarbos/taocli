"""View SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class View(SdkModule):
    """Read-only view operations — portfolio, network, neuron, etc."""

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
    def _uid_arg(uid: int) -> str:
        """Normalize a neuron UID for workflow helpers."""
        if isinstance(uid, bool):
            raise ValueError("uid must be an integer")
        normalized = int(uid)
        if normalized < 0:
            raise ValueError("uid must be greater than or equal to 0")
        return str(normalized)

    @staticmethod
    def _hotkey_arg(hotkey_address: str) -> str:
        """Normalize a hotkey address for workflow helpers."""
        normalized = hotkey_address.strip()
        if not normalized:
            raise ValueError("hotkey_address cannot be empty")
        return normalized

    @staticmethod
    def _workflow_scope(uid: str | None, hotkey_address: str | None) -> str:
        """Return the operator-facing scope label for chain-data helpers."""
        if uid is not None and hotkey_address is not None:
            return "uid+hotkey"
        if uid is not None:
            return "uid"
        if hotkey_address is not None:
            return "hotkey"
        return "subnet"

    @staticmethod
    def _workflow_summary(netuid_arg: str, uid: str | None, hotkey_address: str | None) -> str:
        """Return a concise chain-data workflow summary."""
        if uid is not None and hotkey_address is not None:
            return (
                f"Start with the SN{netuid_arg} metagraph, then inspect UID {uid} and hotkey {hotkey_address}; "
                "axon is filtered by hotkey while probe stays UID-scoped."
            )
        if uid is not None:
            return (
                f"Start with the SN{netuid_arg} metagraph, then inspect UID {uid} directly "
                "with neuron, axon, and probe reads."
            )
        if hotkey_address is not None:
            return (
                f"Start with the SN{netuid_arg} metagraph, then inspect hotkey {hotkey_address} with view axon; "
                "use subnet probe for reachability checks."
            )
        return (
            f"Start with subnet and metagraph reads for SN{netuid_arg}, then inspect axon and probe output "
            "to confirm live endpoints."
        )

    @staticmethod
    def _filter_note(uid: str | None, hotkey_address: str | None) -> str | None:
        """Return guidance describing how focused chain-data filters behave."""
        if uid is not None and hotkey_address is not None:
            return (
                "view axon is filtered by hotkey_address while subnet probe stays filtered by uid, "
                "because probe only accepts UID selectors."
            )
        if uid is not None:
            return (
                "UID focus narrows neuron, axon, and probe reads while metagraph and validators stay "
                "subnet-wide for context."
            )
        if hotkey_address is not None:
            return (
                "Hotkey focus narrows view axon only; keep metagraph and probe subnet-wide unless you also "
                "know the UID."
            )
        return None

    @staticmethod
    def _recommended_order() -> list[str]:
        """Return the recommended read order for chain-data workflows."""
        return ["subnet", "metagraph", "validators", "axon", "probe", "hyperparams"]

    @staticmethod
    def _primary_read(commands: dict[str, Any]) -> str:
        """Return the primary focused read command for the workflow."""
        return str(commands.get("neuron") or commands["metagraph"])

    @staticmethod
    def _endpoint_check(commands: dict[str, Any]) -> str:
        """Return the focused endpoint inspection command for the workflow."""
        return str(commands["axon"])

    @staticmethod
    def _reachability_check(commands: dict[str, Any]) -> str:
        """Return the focused reachability command for the workflow."""
        return str(commands["probe"])

    @staticmethod
    def _has_payload(payload: object) -> bool:
        """Return whether a supplied chain-data read looks meaningfully populated."""
        if payload is None:
            return False
        if isinstance(payload, str):
            return bool(payload.strip())
        if isinstance(payload, (list, tuple, set, dict)):
            return bool(payload)
        return True

    @staticmethod
    def _validation_status(validated_reads: list[str]) -> str:
        """Return a coarse validation status for supplied chain-data reads."""
        if len(validated_reads) == 3:
            return "ready"
        if validated_reads:
            return "partial"
        return "missing"

    @staticmethod
    def _validation_summary(netuid_arg: str, validated_reads: list[str], missing_reads: list[str]) -> str:
        """Return an operator-facing summary of supplied chain-data reads."""
        if not validated_reads:
            return f"No metagraph, axon, or probe output has been supplied yet for SN{netuid_arg}."
        validated = ", ".join(validated_reads)
        if not missing_reads:
            return f"Metagraph, axon, and probe output are all present for SN{netuid_arg}."
        missing = ", ".join(missing_reads)
        return f"Validated {validated} output for SN{netuid_arg}; still missing {missing}."

    @staticmethod
    def _next_validation_step(workflow: dict[str, Any], missing_reads: list[str]) -> str:
        """Return the next command to run for missing chain-data reads."""
        if "metagraph" in missing_reads:
            return str(workflow["primary_read"])
        if "axon" in missing_reads:
            return str(workflow["endpoint_check"])
        if "probe" in missing_reads:
            return str(workflow["reachability_check"])
        return str(workflow["hyperparams"])

    @classmethod
    def chain_data_workflow_help(
        cls,
        netuid: int,
        uid: int | None = None,
        hotkey_address: str | None = None,
    ) -> dict[str, Any]:
        """Return a compact runbook for metagraph, endpoint, and subnet state reads."""
        netuid_arg = cls._netuid_arg(netuid)
        uid_arg = cls._uid_arg(uid) if uid is not None else None
        hotkey_arg = cls._hotkey_arg(hotkey_address) if hotkey_address is not None else None
        axon_cmd = f"agcli view axon --netuid {netuid_arg}"
        probe_cmd = f"agcli subnet probe --netuid {netuid_arg}"
        commands: dict[str, Any] = {
            "netuid": int(netuid_arg),
            "scope": cls._workflow_scope(uid_arg, hotkey_arg),
            "summary": cls._workflow_summary(netuid_arg, uid_arg, hotkey_arg),
            "recommended_order": cls._recommended_order(),
            "subnet": f"agcli subnet show --netuid {netuid_arg}",
            "metagraph": f"agcli view metagraph --netuid {netuid_arg}",
            "neurons": f"agcli view metagraph --netuid {netuid_arg}",
            "subnet_metagraph_full": f"agcli subnet metagraph --netuid {netuid_arg} --full",
            "validators": f"agcli view validators --netuid {netuid_arg}",
            "endpoints": axon_cmd,
            "miner_endpoints": axon_cmd,
            "validator_endpoints": axon_cmd,
            "axon": axon_cmd,
            "probe": probe_cmd,
            "commits": f"agcli subnet commits --netuid {netuid_arg}",
            "health": f"agcli view health --netuid {netuid_arg}",
            "emissions": f"agcli view emissions --netuid {netuid_arg}",
            "hyperparams": f"agcli subnet hyperparams --netuid {netuid_arg}",
        }
        if uid_arg is not None:
            commands["uid"] = int(uid_arg)
            commands["neuron"] = f"agcli view neuron --netuid {netuid_arg} --uid {uid_arg}"
            commands["axon"] = f"{axon_cmd} --uid {uid_arg}"
            commands["probe"] = f"{probe_cmd} --uids {uid_arg}"
        if hotkey_arg is not None:
            commands["hotkey_address"] = hotkey_arg
            commands["axon"] = f"{axon_cmd} --hotkey-address {hotkey_arg}"
        filter_note = cls._filter_note(uid_arg, hotkey_arg)
        if filter_note is not None:
            commands["filter_note"] = filter_note
        commands["primary_read"] = cls._primary_read(commands)
        commands["endpoint_check"] = cls._endpoint_check(commands)
        commands["reachability_check"] = cls._reachability_check(commands)
        return commands

    @classmethod
    def chain_data_validation_help(
        cls,
        netuid: int,
        *,
        uid: int | None = None,
        hotkey_address: str | None = None,
        metagraph: object | None = None,
        axon: object | None = None,
        probe: object | None = None,
    ) -> dict[str, Any]:
        """Return a compact validation summary for supplied chain-data reads."""
        workflow = cls.chain_data_workflow_help(netuid, uid=uid, hotkey_address=hotkey_address)
        read_payloads = (("metagraph", metagraph), ("axon", axon), ("probe", probe))
        validated_reads = [name for name, payload in read_payloads if cls._has_payload(payload)]
        missing_reads = [
            name for name in ("metagraph", "axon", "probe") if name not in validated_reads
        ]
        return {
            "netuid": workflow["netuid"],
            "scope": workflow["scope"],
            "validated_reads": validated_reads,
            "missing_reads": missing_reads,
            "validation_status": cls._validation_status(validated_reads),
            "validation_summary": cls._validation_summary(str(workflow["netuid"]), validated_reads, missing_reads),
            "next_validation_step": cls._next_validation_step(workflow, missing_reads),
            "workflow": workflow,
        }

    @classmethod
    def chain_data_validation_text(
        cls,
        netuid: int,
        *,
        uid: int | None = None,
        hotkey_address: str | None = None,
        metagraph: object | None = None,
        axon: object | None = None,
        probe: object | None = None,
    ) -> str:
        """Return a concise text summary for supplied chain-data reads."""
        summary = cls.chain_data_validation_help(
            netuid,
            uid=uid,
            hotkey_address=hotkey_address,
            metagraph=metagraph,
            axon=axon,
            probe=probe,
        )
        return summary["validation_summary"]

    @classmethod
    def chain_data_snapshot_help(
        cls,
        netuid: int,
        *,
        uid: int | None = None,
        hotkey_address: str | None = None,
        metagraph: object | None = None,
        axon: object | None = None,
        probe: object | None = None,
    ) -> dict[str, Any]:
        """Return a practical operator snapshot combining workflow and validation fields."""
        validation = cls.chain_data_validation_help(
            netuid,
            uid=uid,
            hotkey_address=hotkey_address,
            metagraph=metagraph,
            axon=axon,
            probe=probe,
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
    def chain_data_snapshot_text(
        cls,
        netuid: int,
        *,
        uid: int | None = None,
        hotkey_address: str | None = None,
        metagraph: object | None = None,
        axon: object | None = None,
        probe: object | None = None,
    ) -> str:
        """Return a concise operator snapshot text for supplied chain-data reads."""
        snapshot = cls.chain_data_snapshot_help(
            netuid,
            uid=uid,
            hotkey_address=hotkey_address,
            metagraph=metagraph,
            axon=axon,
            probe=probe,
        )
        return f"{snapshot['validation_summary']} Next: {snapshot['next_validation_step']}"

    def portfolio(self, address: str | None = None, at_block: int | None = None) -> Any:
        """View a portfolio summary with balances and stakes."""
        args = ["view", "portfolio"]
        args += self._opt("--address", address)
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def network(self, at_block: int | None = None) -> Any:
        """View the full network state across all subnets."""
        args = ["view", "network"]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def dynamic(self, at_block: int | None = None) -> Any:
        """View dynamic subnet parameters (TAO price, emission, etc.)."""
        args = ["view", "dynamic"]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def neuron(self, netuid: int, uid: int, at_block: int | None = None) -> Any:
        """View a single neuron's details by UID."""
        args = ["view", "neuron", "--netuid", str(netuid), "--uid", str(uid)]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def validators(self, netuid: int, limit: int | None = None, at_block: int | None = None) -> Any:
        """List validators on a subnet with their stats."""
        args = ["view", "validators", "--netuid", str(netuid)]
        args += self._opt("--limit", limit)
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def account(self, address: str, at_block: int | None = None) -> Any:
        """View full account details for an address."""
        args = ["view", "account", "--address", address]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def history(self, address: str | None = None, limit: int | None = None) -> Any:
        """View recent extrinsic history for an address."""
        args = ["view", "history"]
        args += self._opt("--address", address)
        args += self._opt("--limit", limit)
        return self._run(args)

    def subnet_analytics(self, netuid: int) -> Any:
        """View analytics and stats for a subnet."""
        return self._run(["view", "subnet-analytics", "--netuid", str(netuid)])

    def staking_analytics(self, address: str | None = None) -> Any:
        """View staking analytics for an address."""
        args = ["view", "staking-analytics"]
        args += self._opt("--address", address)
        return self._run(args)

    def swap_sim(self, netuid: int, tao: float | None = None, alpha: float | None = None) -> Any:
        """Simulate a TAO-to-alpha or alpha-to-TAO swap."""
        args = ["view", "swap-sim", "--netuid", str(netuid)]
        args += self._opt("--tao", tao)
        args += self._opt("--alpha", alpha)
        return self._run(args)

    def nominations(self, hotkey_address: str) -> Any:
        """View delegation nominations for a hotkey."""
        return self._run(["view", "nominations", "--hotkey-address", hotkey_address])

    def metagraph(self, netuid: int, since_block: int | None = None, limit: int | None = None) -> Any:
        """View the metagraph for a subnet (neurons, weights, bonds)."""
        args = ["view", "metagraph", "--netuid", str(netuid)]
        args += self._opt("--since-block", since_block)
        args += self._opt("--limit", limit)
        return self._run(args)

    def axon(self, netuid: int, uid: int | None = None, hotkey_address: str | None = None) -> Any:
        """View axon serving info for a neuron."""
        args = ["view", "axon", "--netuid", str(netuid)]
        args += self._opt("--uid", uid)
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def health(self, netuid: int) -> Any:
        """View health metrics for a subnet."""
        return self._run(["view", "health", "--netuid", str(netuid)])

    def emissions(self, netuid: int, limit: int | None = None) -> Any:
        """View emission distribution for a subnet."""
        args = ["view", "emissions", "--netuid", str(netuid)]
        args += self._opt("--limit", limit)
        return self._run(args)
