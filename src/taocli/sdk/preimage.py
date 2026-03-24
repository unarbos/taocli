"""Preimage SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Preimage(SdkModule):
    """Governance preimage — store and remove call preimages."""

    def note(self, pallet: str, call: str, args: str | None = None) -> Any:
        cmd = ["preimage", "note", "--pallet", pallet, "--call", call]
        cmd += self._opt("--args", args)
        return self._run(cmd)

    def unnote(self, hash: str) -> Any:
        return self._run(["preimage", "unnote", "--hash", hash])
