"""Serve SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Serve(SdkModule):
    """Axon serving operations — serve/unserve endpoints."""

    def axon(
        self, netuid: int, ip: str, port: int, protocol: int | None = None, placeholder1: str | None = None
    ) -> Any:
        args = ["serve", "axon", "--netuid", str(netuid), "--ip", ip, "--port", str(port)]
        args += self._opt("--protocol", protocol)
        args += self._opt("--placeholder1", placeholder1)
        return self._run(args)
