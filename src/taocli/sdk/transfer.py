"""Transfer SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Transfer(SdkModule):
    """Transfer operations — send TAO between accounts."""

    def transfer(self, dest: str, amount: float) -> Any:
        """Transfer TAO to a destination address."""
        return self._run(["transfer", "--dest", dest, "--amount", str(amount)])

    def transfer_all(self, dest: str, keep_alive: bool = False) -> Any:
        """Transfer entire balance to a destination address."""
        args = ["transfer-all", "--dest", dest]
        args += self._flag("--keep-alive", keep_alive)
        return self._run(args)

    def transfer_keep_alive(self, dest: str, amount: float) -> Any:
        """Transfer TAO while keeping the sender account alive."""
        return self._run(["transfer-keep-alive", "--dest", dest, "--amount", str(amount)])
