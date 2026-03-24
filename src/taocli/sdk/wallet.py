"""Wallet SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Wallet(SdkModule):
    """Wallet operations — create, list, import, sign, verify, etc."""

    def create(self, name: str | None = None) -> Any:
        args = ["wallet", "create"]
        args += self._opt("--wallet", name)
        return self._run(args)

    def list(self) -> Any:
        return self._run(["wallet", "list"])

    def show(self, name: str | None = None) -> Any:
        args = ["wallet", "show"]
        args += self._opt("--wallet", name)
        return self._run(args)

    def import_wallet(self, mnemonic: str, name: str | None = None) -> Any:
        args = ["wallet", "import", "--mnemonic", mnemonic]
        args += self._opt("--wallet", name)
        return self._run(args)

    def regen_coldkey(self, mnemonic: str) -> Any:
        return self._run(["wallet", "regen-coldkey", "--mnemonic", mnemonic])

    def regen_hotkey(self, mnemonic: str) -> Any:
        return self._run(["wallet", "regen-hotkey", "--mnemonic", mnemonic])

    def new_hotkey(self, name: str | None = None) -> Any:
        args = ["wallet", "new-hotkey"]
        args += self._opt("--hotkey-name", name)
        return self._run(args)

    def sign(self, message: str) -> Any:
        return self._run(["wallet", "sign", "--message", message])

    def verify(self, message: str, signature: str, address: str | None = None) -> Any:
        args = ["wallet", "verify", "--message", message, "--signature", signature]
        args += self._opt("--address", address)
        return self._run(args)

    def derive(self, pubkey: str | None = None, mnemonic: str | None = None) -> Any:
        args = ["wallet", "derive"]
        args += self._opt("--pubkey", pubkey)
        args += self._opt("--mnemonic", mnemonic)
        return self._run(args)

    def dev_key(self, account: str = "Alice") -> Any:
        return self._run(["wallet", "dev-key", "--account", account])

    def associate_hotkey(self) -> Any:
        return self._run(["wallet", "associate-hotkey"])

    def check_swap(self) -> Any:
        return self._run(["wallet", "check-swap"])

    def show_mnemonic(self) -> Any:
        return self._run(["wallet", "show-mnemonic"])
