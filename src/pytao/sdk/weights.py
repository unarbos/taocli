"""Weights SDK module."""

from __future__ import annotations

from typing import Any

from pytao.sdk.base import SdkModule


class Weights(SdkModule):
    """Weight-setting operations — set, commit, reveal, show, etc."""

    def show(self, netuid: int, hotkey_address: str | None = None, limit: int | None = None) -> Any:
        args = ["weights", "show", "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--limit", limit)
        return self._run(args)

    def set(self, netuid: int, weights: str, version_key: int | None = None) -> Any:
        args = ["weights", "set", "--netuid", str(netuid), "--weights", weights]
        args += self._opt("--version-key", version_key)
        return self._run(args)

    def commit(self, netuid: int, weights: str, salt: str | None = None) -> Any:
        args = ["weights", "commit", "--netuid", str(netuid), "--weights", weights]
        args += self._opt("--salt", salt)
        return self._run(args)

    def reveal(self, netuid: int, weights: str, salt: str, version_key: int | None = None) -> Any:
        args = ["weights", "reveal", "--netuid", str(netuid), "--weights", weights, "--salt", salt]
        args += self._opt("--version-key", version_key)
        return self._run(args)

    def status(self, netuid: int) -> Any:
        return self._run(["weights", "status", "--netuid", str(netuid)])

    def commit_reveal(self, netuid: int, weights: str, version_key: int | None = None, wait: bool = False) -> Any:
        args = ["weights", "commit-reveal", "--netuid", str(netuid), "--weights", weights]
        args += self._opt("--version-key", version_key)
        args += self._flag("--wait", wait)
        return self._run(args)
