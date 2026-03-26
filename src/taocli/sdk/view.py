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

    @classmethod
    def chain_data_workflow_help(
        cls,
        netuid: int,
        uid: int | None = None,
        hotkey_address: str | None = None,
    ) -> dict[str, Any]:
        """Return a compact runbook for metagraph, endpoint, and subnet state reads."""
        netuid_arg = cls._netuid_arg(netuid)
        axon_cmd = f"agcli view axon --netuid {netuid_arg}"
        probe_cmd = f"agcli subnet probe --netuid {netuid_arg}"
        commands: dict[str, Any] = {
            "netuid": int(netuid_arg),
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
        if uid is not None:
            uid_arg = cls._uid_arg(uid)
            commands["neuron"] = f"agcli view neuron --netuid {netuid_arg} --uid {uid_arg}"
            commands["axon"] = f"{axon_cmd} --uid {uid_arg}"
            commands["probe"] = f"{probe_cmd} --uids {uid_arg}"
        if hotkey_address is not None:
            commands["axon"] = f"{axon_cmd} --hotkey-address {cls._hotkey_arg(hotkey_address)}"
        return commands

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
