"""Drand SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Drand(SdkModule):
    """Drand randomness — write randomness pulses."""

    def write_pulse(self, payload: str, signature: str) -> Any:
        """Write a drand randomness pulse to the chain."""
        return self._run(["drand", "write-pulse", "--payload", payload, "--signature", signature])
