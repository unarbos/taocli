"""Utils SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Utils(SdkModule):
    """Utility commands — convert, latency, etc."""

    def convert(self, value: str, from_unit: str | None = None, to_unit: str | None = None) -> Any:
        """Convert between TAO denominations (rao, tao, etc.)."""
        args = ["utils", "convert", "--value", value]
        args += self._opt("--from", from_unit)
        args += self._opt("--to", to_unit)
        return self._run(args)

    def latency(self) -> Any:
        """Measure RPC endpoint latency."""
        return self._run(["utils", "latency"])
