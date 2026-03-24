"""Root SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Root(SdkModule):
    """Root network operations — register, set weights."""

    def register(self) -> Any:
        """Register as a root network validator."""
        return self._run(["root", "register"])

    def weights(self, weights: str) -> Any:
        """Set root network weights."""
        return self._run(["root", "weights", "--weights", weights])
