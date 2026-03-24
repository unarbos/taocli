"""Wallet SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Wallet(SdkModule):
    """Wallet operations — create, list, import, sign, verify, etc."""

    def create(self, name: str | None = None) -> Any:
        """Create a new wallet (coldkey + hotkey pair)."""
        args = ["wallet", "create"]
        args += self._opt("--wallet", name)
        return self._run(args)

    def list(self) -> Any:
        """List all wallets in the wallet directory."""
        return self._run(["wallet", "list"])

    def show(self, name: str | None = None) -> Any:
        """Show details for a wallet."""
        args = ["wallet", "show"]
        args += self._opt("--wallet", name)
        return self._run(args)

    def import_wallet(self, mnemonic: str, name: str | None = None) -> Any:
        """Import a wallet from a mnemonic phrase."""
        args = ["wallet", "import", "--mnemonic", mnemonic]
        args += self._opt("--wallet", name)
        return self._run(args)

    def regen_coldkey(self, mnemonic: str) -> Any:
        """Regenerate a coldkey from a mnemonic phrase."""
        return self._run(["wallet", "regen-coldkey", "--mnemonic", mnemonic])

    def regen_hotkey(self, mnemonic: str) -> Any:
        """Regenerate a hotkey from a mnemonic phrase."""
        return self._run(["wallet", "regen-hotkey", "--mnemonic", mnemonic])

    def new_hotkey(self, name: str | None = None) -> Any:
        """Generate a new hotkey for the current wallet."""
        args = ["wallet", "new-hotkey"]
        args += self._opt("--hotkey-name", name)
        return self._run(args)

    def sign(self, message: str) -> Any:
        """Sign a message with the wallet's coldkey."""
        return self._run(["wallet", "sign", "--message", message])

    def verify(self, message: str, signature: str, address: str | None = None) -> Any:
        """Verify a signed message against an address."""
        args = ["wallet", "verify", "--message", message, "--signature", signature]
        args += self._opt("--address", address)
        return self._run(args)

    def derive(self, pubkey: str | None = None, mnemonic: str | None = None) -> Any:
        """Derive an SS58 address from a public key or mnemonic."""
        args = ["wallet", "derive"]
        args += self._opt("--pubkey", pubkey)
        args += self._opt("--mnemonic", mnemonic)
        return self._run(args)

    def dev_key(self, account: str = "Alice") -> Any:
        """Get a well-known development key (Alice, Bob, etc.)."""
        return self._run(["wallet", "dev-key", "--account", account])

    def associate_hotkey(self) -> Any:
        """Associate a hotkey with the current coldkey."""
        return self._run(["wallet", "associate-hotkey"])

    def check_swap(self) -> Any:
        """Check the status of a pending coldkey swap."""
        return self._run(["wallet", "check-swap"])

    def show_mnemonic(self) -> Any:
        """Display the wallet's mnemonic phrase."""
        return self._run(["wallet", "show-mnemonic"])
