"""Diff SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Diff(SdkModule):
    """State comparison — diff portfolio, subnet, network, metagraph between blocks."""

    def portfolio(self, address: str, block1: int | None = None, block2: int | None = None) -> Any:
        cmd = ["diff", "portfolio", "--address", address]
        cmd += self._opt("--block1", block1)
        cmd += self._opt("--block2", block2)
        return self._run(cmd)

    def subnet(self, netuid: int, block1: int, block2: int) -> Any:
        return self._run(["diff", "subnet", "--netuid", str(netuid), "--block1", str(block1), "--block2", str(block2)])

    def network(self, block1: int, block2: int) -> Any:
        return self._run(["diff", "network", "--block1", str(block1), "--block2", str(block2)])

    def metagraph(self, netuid: int, block1: int, block2: int) -> Any:
        return self._run(
            ["diff", "metagraph", "--netuid", str(netuid), "--block1", str(block1), "--block2", str(block2)]
        )
