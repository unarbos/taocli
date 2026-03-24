"""Liquidity SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Liquidity(SdkModule):
    """Liquidity operations — add, remove, modify AMM positions."""

    def add(
        self,
        netuid: int,
        price_low: str,
        price_high: str,
        amount: str,
        hotkey_address: str | None = None,
    ) -> Any:
        """Add a liquidity position to a subnet's AMM pool."""
        cmd = [
            "liquidity",
            "add",
            "--netuid",
            str(netuid),
            "--price-low",
            price_low,
            "--price-high",
            price_high,
            "--amount",
            amount,
        ]
        cmd += self._opt("--hotkey-address", hotkey_address)
        return self._run(cmd)

    def remove(self, netuid: int, position_id: str, hotkey_address: str | None = None) -> Any:
        """Remove a liquidity position."""
        cmd = ["liquidity", "remove", "--netuid", str(netuid), "--position-id", position_id]
        cmd += self._opt("--hotkey-address", hotkey_address)
        return self._run(cmd)

    def modify(self, netuid: int, position_id: str, delta: str, hotkey_address: str | None = None) -> Any:
        """Modify an existing liquidity position."""
        cmd = ["liquidity", "modify", "--netuid", str(netuid), "--position-id", position_id, "--delta", delta]
        cmd += self._opt("--hotkey-address", hotkey_address)
        return self._run(cmd)

    def toggle(self, netuid: int, enable: bool) -> Any:
        """Enable or disable the liquidity pool on a subnet."""
        return self._run(["liquidity", "toggle", "--netuid", str(netuid), "--enable", str(enable).lower()])
