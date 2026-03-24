"""Localnet SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Localnet(SdkModule):
    """Localnet operations — start, stop, status, reset, logs, scaffold Docker chains."""

    def start(
        self,
        image: str | None = None,
        container: str | None = None,
        port: int | None = None,
        wait: bool = True,
        timeout: int | None = None,
    ) -> Any:
        cmd = ["localnet", "start"]
        cmd += self._opt("--image", image)
        cmd += self._opt("--container", container)
        cmd += self._opt("--port", port)
        cmd += self._flag("--wait", wait)
        cmd += self._opt("--timeout", timeout)
        return self._run(cmd)

    def stop(self, container: str | None = None) -> Any:
        cmd = ["localnet", "stop"]
        cmd += self._opt("--container", container)
        return self._run(cmd)

    def status(self, container: str | None = None, port: int | None = None) -> Any:
        cmd = ["localnet", "status"]
        cmd += self._opt("--container", container)
        cmd += self._opt("--port", port)
        return self._run(cmd)

    def reset(
        self,
        image: str | None = None,
        container: str | None = None,
        port: int | None = None,
        timeout: int | None = None,
    ) -> Any:
        cmd = ["localnet", "reset"]
        cmd += self._opt("--image", image)
        cmd += self._opt("--container", container)
        cmd += self._opt("--port", port)
        cmd += self._opt("--timeout", timeout)
        return self._run(cmd)

    def logs(self, container: str | None = None, tail: int | None = None) -> str:
        cmd = ["localnet", "logs"]
        cmd += self._opt("--container", container)
        cmd += self._opt("--tail", tail)
        return self._run_raw(cmd)

    def scaffold(
        self,
        config: str | None = None,
        image: str | None = None,
        port: int | None = None,
        no_start: bool = False,
    ) -> Any:
        cmd = ["localnet", "scaffold"]
        cmd += self._opt("--config", config)
        cmd += self._opt("--image", image)
        cmd += self._opt("--port", port)
        cmd += self._flag("--no-start", no_start)
        return self._run(cmd)
