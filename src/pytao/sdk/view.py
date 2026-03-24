"""View SDK module."""

from __future__ import annotations

from typing import Any

from pytao.sdk.base import SdkModule


class View(SdkModule):
    """Read-only view operations — portfolio, network, neuron, etc."""

    def portfolio(self, address: str | None = None, at_block: int | None = None) -> Any:
        args = ["view", "portfolio"]
        args += self._opt("--address", address)
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def network(self, at_block: int | None = None) -> Any:
        args = ["view", "network"]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def dynamic(self, at_block: int | None = None) -> Any:
        args = ["view", "dynamic"]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def neuron(self, netuid: int, uid: int, at_block: int | None = None) -> Any:
        args = ["view", "neuron", "--netuid", str(netuid), "--uid", str(uid)]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def validators(self, netuid: int, limit: int | None = None, at_block: int | None = None) -> Any:
        args = ["view", "validators", "--netuid", str(netuid)]
        args += self._opt("--limit", limit)
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def account(self, address: str, at_block: int | None = None) -> Any:
        args = ["view", "account", "--address", address]
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def history(self, address: str | None = None, limit: int | None = None) -> Any:
        args = ["view", "history"]
        args += self._opt("--address", address)
        args += self._opt("--limit", limit)
        return self._run(args)

    def subnet_analytics(self, netuid: int) -> Any:
        return self._run(["view", "subnet-analytics", "--netuid", str(netuid)])

    def staking_analytics(self, address: str | None = None) -> Any:
        args = ["view", "staking-analytics"]
        args += self._opt("--address", address)
        return self._run(args)

    def swap_sim(self, netuid: int, tao: float | None = None, alpha: float | None = None) -> Any:
        args = ["view", "swap-sim", "--netuid", str(netuid)]
        args += self._opt("--tao", tao)
        args += self._opt("--alpha", alpha)
        return self._run(args)

    def nominations(self, hotkey_address: str) -> Any:
        return self._run(["view", "nominations", "--hotkey-address", hotkey_address])

    def metagraph(self, netuid: int, since_block: int | None = None, limit: int | None = None) -> Any:
        args = ["view", "metagraph", "--netuid", str(netuid)]
        args += self._opt("--since-block", since_block)
        args += self._opt("--limit", limit)
        return self._run(args)

    def axon(self, netuid: int, uid: int | None = None, hotkey_address: str | None = None) -> Any:
        args = ["view", "axon", "--netuid", str(netuid)]
        args += self._opt("--uid", uid)
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def health(self, netuid: int) -> Any:
        return self._run(["view", "health", "--netuid", str(netuid)])

    def emissions(self, netuid: int, limit: int | None = None) -> Any:
        args = ["view", "emissions", "--netuid", str(netuid)]
        args += self._opt("--limit", limit)
        return self._run(args)
