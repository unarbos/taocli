"""Swap SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Swap(SdkModule):
    """Key swap operations."""

    def schedule(self, new_coldkey: str) -> Any:
        """Schedule a coldkey swap to a new address."""
        return self._run(["swap", "schedule", "--new-coldkey", new_coldkey])

    def status(self) -> Any:
        """Check the status of a pending coldkey swap."""
        return self._run(["swap", "status"])
