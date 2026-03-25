"""Weights SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Weights(SdkModule):
    """Weight-setting operations — set, commit, reveal, show, etc."""

    def show(self, netuid: int, hotkey_address: str | None = None, limit: int | None = None) -> Any:
        """Show current weights set by a hotkey on a subnet."""
        args = ["weights", "show", "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--limit", limit)
        return self._run(args)

    def set(self, netuid: int, weights: str, version_key: int | None = None) -> Any:
        """Set weights on a subnet."""
        args = ["weights", "set", "--netuid", str(netuid), "--weights", weights]
        args += self._opt("--version-key", version_key)
        return self._run(args)

    def commit(self, netuid: int, weights: str, salt: str | None = None) -> Any:
        """Commit weights (hash) for later reveal."""
        args = ["weights", "commit", "--netuid", str(netuid), "--weights", weights]
        args += self._opt("--salt", salt)
        return self._run(args)

    def reveal(self, netuid: int, weights: str, salt: str, version_key: int | None = None) -> Any:
        """Reveal previously committed weights."""
        args = ["weights", "reveal", "--netuid", str(netuid), "--weights", weights, "--salt", salt]
        args += self._opt("--version-key", version_key)
        return self._run(args)

    def status(self, netuid: int) -> Any:
        """Show commit/reveal status for a subnet."""
        return self._run(["weights", "status", "--netuid", str(netuid)])

    def commit_reveal(self, netuid: int, weights: str, version_key: int | None = None, wait: bool = False) -> Any:
        """Commit and auto-reveal weights in one operation."""
        args = ["weights", "commit-reveal", "--netuid", str(netuid), "--weights", weights]
        args += self._opt("--version-key", version_key)
        args += self._flag("--wait", wait)
        return self._run(args)

    def set_mechanism(
        self,
        netuid: int,
        mechanism_id: int,
        weights: str,
        version_key: int | None = None,
    ) -> Any:
        """Set mechanism-specific weights on a subnet."""
        args = [
            "weights",
            "set-mechanism",
            "--netuid",
            str(netuid),
            "--mechanism-id",
            str(mechanism_id),
            "--weights",
            weights,
        ]
        args += self._opt("--version-key", version_key)
        return self._run(args)

    def commit_mechanism(self, netuid: int, mechanism_id: int, hash: str) -> Any:
        """Commit a precomputed mechanism-specific weights hash."""
        args = [
            "weights",
            "commit-mechanism",
            "--netuid",
            str(netuid),
            "--mechanism-id",
            str(mechanism_id),
            "--hash",
            hash,
        ]
        return self._run(args)

    def reveal_mechanism(
        self,
        netuid: int,
        mechanism_id: int,
        weights: str,
        salt: str,
        version_key: int | None = None,
    ) -> Any:
        """Reveal previously committed mechanism-specific weights."""
        args = [
            "weights",
            "reveal-mechanism",
            "--netuid",
            str(netuid),
            "--mechanism-id",
            str(mechanism_id),
            "--weights",
            weights,
            "--salt",
            salt,
        ]
        args += self._opt("--version-key", version_key)
        return self._run(args)

    def commit_timelocked(self, netuid: int, weights: str, round: int, salt: str | None = None) -> Any:
        """Commit timelocked weights using drand randomness."""
        args = ["weights", "commit-timelocked", "--netuid", str(netuid), "--weights", weights, "--round", str(round)]
        args += self._opt("--salt", salt)
        return self._run(args)
