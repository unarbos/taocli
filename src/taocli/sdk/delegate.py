"""Delegate SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Delegate(SdkModule):
    """Delegate operations — show, list, change take."""

    def show(self, hotkey_address: str) -> Any:
        """Show details for a delegate by hotkey address."""
        return self._run(["delegate", "show", "--hotkey-address", hotkey_address])

    def list(self) -> Any:
        """List all delegates on the network."""
        return self._run(["delegate", "list"])

    def decrease_take(self, take: float, hotkey_address: str | None = None) -> Any:
        """Decrease the delegate take percentage."""
        args = ["delegate", "decrease-take", "--take", str(take)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def increase_take(self, take: float, hotkey_address: str | None = None) -> Any:
        """Increase the delegate take percentage."""
        args = ["delegate", "increase-take", "--take", str(take)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)
