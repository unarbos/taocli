"""SafeMode SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class SafeMode(SdkModule):
    """Safe-mode operations — enter, extend, force-enter, force-exit."""

    def enter(self) -> Any:
        """Enter safe mode (transaction restrictions)."""
        return self._run(["safe-mode", "enter"])

    def extend(self) -> Any:
        """Extend the current safe mode duration."""
        return self._run(["safe-mode", "extend"])

    def force_enter(self, duration: int) -> Any:
        """Force-enter safe mode for a specified duration."""
        return self._run(["safe-mode", "force-enter", "--duration", str(duration)])

    def force_exit(self) -> Any:
        """Force-exit safe mode."""
        return self._run(["safe-mode", "force-exit"])
