"""Commitment SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Commitment(SdkModule):
    """Miner commitment operations — set, get, list endpoint data."""

    def set(self, netuid: int, data: str) -> Any:
        """Set commitment data for a neuron on a subnet."""
        return self._run(["commitment", "set", "--netuid", str(netuid), "--data", data])

    def get(self, netuid: int, address: str | None = None) -> Any:
        """Get commitment data for a neuron on a subnet."""
        args = ["commitment", "get", "--netuid", str(netuid)]
        args += self._opt("--address", address)
        return self._run(args)

    def list(self, netuid: int) -> Any:
        """List all commitments on a subnet."""
        return self._run(["commitment", "list", "--netuid", str(netuid)])
