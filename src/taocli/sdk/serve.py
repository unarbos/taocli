"""Serve SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Serve(SdkModule):
    """Axon serving operations — serve/unserve endpoints."""

    def axon(self, netuid: int, ip: str, port: int, protocol: int | None = None, version: int | None = None) -> Any:
        args = ["serve", "axon", "--netuid", str(netuid), "--ip", ip, "--port", str(port)]
        args += self._opt("--protocol", protocol)
        args += self._opt("--version", version)
        return self._run(args)

    def reset(self, netuid: int) -> Any:
        return self._run(["serve", "reset", "--netuid", str(netuid)])

    def batch_axon(self, file: str) -> Any:
        return self._run(["serve", "batch-axon", "--file", file])

    def prometheus(self, netuid: int, ip: str, port: int, version: int | None = None) -> Any:
        cmd = ["serve", "prometheus", "--netuid", str(netuid), "--ip", ip, "--port", str(port)]
        cmd += self._opt("--version", version)
        return self._run(cmd)

    def axon_tls(
        self, netuid: int, ip: str, port: int, cert: str, protocol: int | None = None, version: int | None = None
    ) -> Any:
        cmd = ["serve", "axon-tls", "--netuid", str(netuid), "--ip", ip, "--port", str(port), "--cert", cert]
        cmd += self._opt("--protocol", protocol)
        cmd += self._opt("--version", version)
        return self._run(cmd)
