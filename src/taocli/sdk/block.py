"""Block SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Block(SdkModule):
    """Block explorer — query block info, latest, and ranges."""

    def info(self, number: int) -> Any:
        """Get info for a specific block by number."""
        return self._run(["block", "info", "--number", str(number)])

    def latest(self) -> Any:
        """Get the latest block."""
        return self._run(["block", "latest"])

    def range(self, from_block: int, to_block: int) -> Any:
        """Get a range of blocks."""
        return self._run(["block", "range", "--from", str(from_block), "--to", str(to_block)])
