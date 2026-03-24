"""Proxy SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Proxy(SdkModule):
    """Proxy account management — add and remove proxy accounts."""

    def add(self, delegate: str, proxy_type: str | None = None) -> Any:
        args = ["proxy", "add", "--delegate", delegate]
        args += self._opt("--proxy-type", proxy_type)
        return self._run(args)

    def remove(self, delegate: str, proxy_type: str | None = None) -> Any:
        args = ["proxy", "remove", "--delegate", delegate]
        args += self._opt("--proxy-type", proxy_type)
        return self._run(args)

    def list(self, address: str | None = None) -> Any:
        args = ["proxy", "list"]
        args += self._opt("--address", address)
        return self._run(args)
