"""Root SDK module."""

from __future__ import annotations

from typing import Any

from pytao.sdk.base import SdkModule


class Root(SdkModule):
    """Root network operations — register, set weights."""

    def register(self) -> Any:
        return self._run(["root", "register"])

    def weights(self, weights: str) -> Any:
        return self._run(["root", "weights", "--weights", weights])
