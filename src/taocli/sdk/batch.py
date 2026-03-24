"""Batch SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Batch(SdkModule):
    """Batch operations — submit multiple extrinsics from a JSON file."""

    def run(self, file: str, no_atomic: bool = False, force: bool = False) -> Any:
        """Run a batch of extrinsics from a JSON file."""
        cmd = ["batch", "--file", file]
        cmd += self._flag("--no-atomic", no_atomic)
        cmd += self._flag("--force", force)
        return self._run(cmd)
