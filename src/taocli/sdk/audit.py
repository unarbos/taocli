"""Audit SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Audit(SdkModule):
    """Security audit of an account: proxies, delegates, stake exposure, permissions."""

    def run(self, address: str | None = None) -> Any:
        """Run security audit for an address (defaults to wallet coldkey)."""
        args = ["audit"]
        args.extend(self._opt("--address", address))
        return self._run(args)
