"""Multisig SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Multisig(SdkModule):
    """Multisig operations — submit, approve, execute, cancel threshold calls."""

    def address(self, signatories: str, threshold: int) -> Any:
        """Derive the multisig address from signatories and threshold."""
        return self._run(["multisig", "address", "--signatories", signatories, "--threshold", str(threshold)])

    def submit(self, others: str, threshold: int, pallet: str, call: str, args: str | None = None) -> Any:
        """Submit a new multisig call for approval."""
        cmd = [
            "multisig",
            "submit",
            "--others",
            others,
            "--threshold",
            str(threshold),
            "--pallet",
            pallet,
            "--call",
            call,
        ]
        cmd += self._opt("--args", args)
        return self._run(cmd)

    def approve(self, others: str, threshold: int, call_hash: str) -> Any:
        """Approve a pending multisig call."""
        return self._run(
            ["multisig", "approve", "--others", others, "--threshold", str(threshold), "--call-hash", call_hash]
        )

    def execute(
        self,
        others: str,
        threshold: int,
        pallet: str,
        call: str,
        args: str | None = None,
        timepoint_height: int | None = None,
        timepoint_index: int | None = None,
    ) -> Any:
        """Execute an approved multisig call."""
        cmd = [
            "multisig",
            "execute",
            "--others",
            others,
            "--threshold",
            str(threshold),
            "--pallet",
            pallet,
            "--call",
            call,
        ]
        cmd += self._opt("--args", args)
        cmd += self._opt("--timepoint-height", timepoint_height)
        cmd += self._opt("--timepoint-index", timepoint_index)
        return self._run(cmd)

    def cancel(
        self,
        others: str,
        threshold: int,
        call_hash: str,
        timepoint_height: int,
        timepoint_index: int,
    ) -> Any:
        """Cancel a pending multisig call."""
        return self._run(
            [
                "multisig",
                "cancel",
                "--others",
                others,
                "--threshold",
                str(threshold),
                "--call-hash",
                call_hash,
                "--timepoint-height",
                str(timepoint_height),
                "--timepoint-index",
                str(timepoint_index),
            ]
        )

    def list(self, address: str) -> Any:
        """List pending multisig calls for an address."""
        return self._run(["multisig", "list", "--address", address])
