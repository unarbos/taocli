"""Explain SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Explain(SdkModule):
    """Built-in Bittensor concept reference."""

    def topic(self, topic: str | None = None, *, full: bool = False) -> Any:
        """Explain a Bittensor concept. Omit topic to list all available topics."""
        args = ["explain"]
        args.extend(self._opt("--topic", topic))
        args.extend(self._flag("--full", full))
        return self._run(args)

    def list_topics(self) -> Any:
        """List all available explanation topics."""
        return self._run(["explain"])
