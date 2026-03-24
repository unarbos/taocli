"""Subnet SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Subnet(SdkModule):
    """Subnet operations — list, show, metagraph, register, health, etc."""

    def list(self, at_block: int | None = None) -> Any:
        args = ["subnet", "list"]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def show(self, netuid: int, at_block: int | None = None) -> Any:
        args = ["subnet", "show", "--netuid", str(netuid)]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def hyperparams(self, netuid: int, at_block: int | None = None) -> Any:
        args = ["subnet", "hyperparams", "--netuid", str(netuid)]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def metagraph(self, netuid: int, uid: int | None = None, full: bool = False, at_block: int | None = None) -> Any:
        args = ["subnet", "metagraph", "--netuid", str(netuid)]
        args += self._opt("--uid", uid)
        args += self._flag("--full", full)
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def register(self) -> Any:
        return self._run(["subnet", "register"])

    def register_neuron(self, netuid: int) -> Any:
        return self._run(["subnet", "register-neuron", "--netuid", str(netuid)])

    def pow(self, netuid: int, threads: int | None = None) -> Any:
        args = ["subnet", "pow", "--netuid", str(netuid)]
        args += self._opt("--threads", threads)
        return self._run(args)

    def health(self, netuid: int) -> Any:
        return self._run(["subnet", "health", "--netuid", str(netuid)])

    def emissions(self, netuid: int) -> Any:
        return self._run(["subnet", "emissions", "--netuid", str(netuid)])

    def cost(self, netuid: int) -> Any:
        return self._run(["subnet", "cost", "--netuid", str(netuid)])

    def create_cost(self) -> Any:
        return self._run(["subnet", "create-cost"])

    def liquidity(self, netuid: int | None = None) -> Any:
        args = ["subnet", "liquidity"]
        args += self._opt("--netuid", netuid)
        return self._run(args)

    def dissolve(self, netuid: int) -> Any:
        return self._run(["subnet", "dissolve", "--netuid", str(netuid)])

    def set_param(self, netuid: int, param: str, value: str) -> Any:
        return self._run(["subnet", "set-param", "--netuid", str(netuid), "--param", param, "--value", value])

    def set_symbol(self, netuid: int, symbol: str) -> Any:
        return self._run(["subnet", "set-symbol", "--netuid", str(netuid), "--symbol", symbol])

    def commits(self, netuid: int, hotkey_address: str | None = None) -> Any:
        args = ["subnet", "commits", "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def probe(self, netuid: int, uids: str | None = None, timeout_ms: int | None = None) -> Any:
        args = ["subnet", "probe", "--netuid", str(netuid)]
        args += self._opt("--uids", uids)
        args += self._opt("--timeout-ms", timeout_ms)
        return self._run(args)

    def snipe(self, netuid: int, max_cost: float | None = None, max_attempts: int | None = None) -> Any:
        args = ["subnet", "snipe", "--netuid", str(netuid)]
        args += self._opt("--max-cost", max_cost)
        args += self._opt("--max-attempts", max_attempts)
        return self._run(args)

    def trim(self, netuid: int, max_uids: int) -> Any:
        return self._run(["subnet", "trim", "--netuid", str(netuid), "--max-uids", str(max_uids)])

    def start(self, netuid: int) -> Any:
        return self._run(["subnet", "start", "--netuid", str(netuid)])

    def check_start(self, netuid: int) -> Any:
        return self._run(["subnet", "check-start", "--netuid", str(netuid)])

    def emission_split(self, netuid: int) -> Any:
        return self._run(["subnet", "emission-split", "--netuid", str(netuid)])

    def mechanism_count(self, netuid: int) -> Any:
        return self._run(["subnet", "mechanism-count", "--netuid", str(netuid)])

    def set_mechanism_count(self, netuid: int, count: int) -> Any:
        return self._run(["subnet", "set-mechanism-count", "--netuid", str(netuid), "--count", str(count)])

    def set_emission_split(self, netuid: int, weights: str) -> Any:
        return self._run(["subnet", "set-emission-split", "--netuid", str(netuid), "--weights", weights])
