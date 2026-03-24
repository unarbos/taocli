"""Swap SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Swap(SdkModule):
    """Key swap operations — hotkey swap, coldkey swap, EVM key association."""

    def hotkey(self, new_hotkey: str) -> Any:
        """Swap hotkey to a new address.

        Args:
            new_hotkey: SS58 address of the new hotkey.
        """
        return self._run(["swap", "hotkey", "--new-hotkey", new_hotkey])

    def coldkey(self, new_coldkey: str) -> Any:
        """Schedule a coldkey swap to a new address.

        Args:
            new_coldkey: SS58 address of the new coldkey.
        """
        return self._run(["swap", "coldkey", "--new-coldkey", new_coldkey])

    def evm_key(self, evm_address: str, block_number: int, signature: str) -> Any:
        """Associate an EVM (Ethereum) address with your SS58 account.

        Args:
            evm_address: EVM address (0x-prefixed hex, 20 bytes).
            block_number: Block number used when creating the signature.
            signature: EVM signature (0x-prefixed hex, 65 bytes: r+s+v).
        """
        return self._run(
            [
                "swap",
                "evm-key",
                "--evm-address",
                evm_address,
                "--block-number",
                str(block_number),
                "--signature",
                signature,
            ]
        )

    def schedule(self, new_coldkey: str) -> Any:
        """Schedule a coldkey swap (alias for :meth:`coldkey`)."""
        return self.coldkey(new_coldkey)

    def status(self) -> Any:
        """Check the status of a pending coldkey swap."""
        return self._run(["swap", "status"])
