"""Identity SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Identity(SdkModule):
    """On-chain identity operations — set, get, remove."""

    def set(self, name: str | None = None, url: str | None = None, description: str | None = None) -> Any:
        args = ["identity", "set"]
        args += self._opt("--name", name)
        args += self._opt("--url", url)
        args += self._opt("--description", description)
        return self._run(args)

    def get(self, address: str | None = None) -> Any:
        args = ["identity", "get"]
        args += self._opt("--address", address)
        return self._run(args)

    def remove(self) -> Any:
        return self._run(["identity", "remove"])
