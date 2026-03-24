"""Subscribe SDK module."""

from __future__ import annotations

from taocli.sdk.base import SdkModule


class Subscribe(SdkModule):
    """Subscribe to on-chain events — blocks and filtered events."""

    def blocks(self) -> str:
        """Subscribe to new block headers."""
        return self._run_raw(["subscribe", "blocks"])

    def events(
        self,
        filter: str | None = None,
        netuid: int | None = None,
        account: str | None = None,
    ) -> str:
        """Subscribe to on-chain events with optional filters."""
        cmd = ["subscribe", "events"]
        cmd += self._opt("--filter", filter)
        cmd += self._opt("--netuid", netuid)
        cmd += self._opt("--account", account)
        return self._run_raw(cmd)
