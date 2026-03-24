"""Transfer SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Transfer(SdkModule):
    """Transfer operations — send TAO between accounts."""

    def transfer(self, dest: str, amount: float) -> Any:
        return self._run(["transfer", "--dest", dest, "--amount", str(amount)])

    def transfer_all(self, dest: str, keep_alive: bool = False) -> Any:
        args = ["transfer-all", "--dest", dest]
        args += self._flag("--keep-alive", keep_alive)
        return self._run(args)

    def transfer_keep_alive(self, dest: str, amount: float) -> Any:
        return self._run(["transfer-keep-alive", "--dest", dest, "--amount", str(amount)])
