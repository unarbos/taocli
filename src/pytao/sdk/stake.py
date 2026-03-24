"""Stake SDK module."""

from __future__ import annotations

from typing import Any

from pytao.sdk.base import SdkModule


class Stake(SdkModule):
    """Staking operations — add, remove, move, swap, list, etc."""

    def add(
        self, amount: float, netuid: int, hotkey_address: str | None = None, max_slippage: float | None = None
    ) -> Any:
        args = ["stake", "add", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--max-slippage", max_slippage)
        return self._run(args)

    def remove(
        self, amount: float, netuid: int, hotkey_address: str | None = None, max_slippage: float | None = None
    ) -> Any:
        args = ["stake", "remove", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--max-slippage", max_slippage)
        return self._run(args)

    def list(self, address: str | None = None, at_block: int | None = None) -> Any:
        args = ["stake", "list"]
        args += self._opt("--address", address)
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def move(self, amount: float, from_netuid: int, to_netuid: int, hotkey_address: str | None = None) -> Any:
        args = ["stake", "move", "--amount", str(amount), "--from", str(from_netuid), "--to", str(to_netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def swap(self, amount: float, from_netuid: int, to_netuid: int, hotkey_address: str | None = None) -> Any:
        args = ["stake", "swap", "--amount", str(amount), "--from", str(from_netuid), "--to", str(to_netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def unstake_all(self, hotkey_address: str | None = None) -> Any:
        args = ["stake", "unstake-all"]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def claim_root(self, netuid: int | None = None) -> Any:
        args = ["stake", "claim-root"]
        args += self._opt("--netuid", netuid)
        return self._run(args)

    def add_limit(self, amount: float, netuid: int, price: float, partial: bool = False) -> Any:
        args = ["stake", "add-limit", "--amount", str(amount), "--netuid", str(netuid), "--price", str(price)]
        args += self._flag("--partial", partial)
        return self._run(args)

    def remove_limit(self, amount: float, netuid: int, price: float, partial: bool = False) -> Any:
        args = ["stake", "remove-limit", "--amount", str(amount), "--netuid", str(netuid), "--price", str(price)]
        args += self._flag("--partial", partial)
        return self._run(args)

    def childkey_take(self, take: float, netuid: int, hotkey_address: str | None = None) -> Any:
        args = ["stake", "childkey-take", "--take", str(take), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def set_children(self, netuid: int, children: str, hotkey_address: str | None = None) -> Any:
        args = ["stake", "set-children", "--netuid", str(netuid), "--children", children]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def recycle_alpha(self, amount: float, netuid: int, hotkey_address: str | None = None) -> Any:
        args = ["stake", "recycle-alpha", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def burn_alpha(self, amount: float, netuid: int, hotkey_address: str | None = None) -> Any:
        args = ["stake", "burn-alpha", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def swap_limit(self, amount: float, from_netuid: int, to_netuid: int, price: float, partial: bool = False) -> Any:
        args = [
            "stake",
            "swap-limit",
            "--amount",
            str(amount),
            "--from",
            str(from_netuid),
            "--to",
            str(to_netuid),
            "--price",
            str(price),
        ]
        args += self._flag("--partial", partial)
        return self._run(args)

    def set_auto(self, netuid: int, hotkey_address: str | None = None) -> Any:
        args = ["stake", "set-auto", "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def show_auto(self, address: str | None = None) -> Any:
        args = ["stake", "show-auto"]
        args += self._opt("--address", address)
        return self._run(args)

    def process_claim(self, hotkey_address: str | None = None, netuids: str | None = None) -> Any:
        args = ["stake", "process-claim"]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--netuids", netuids)
        return self._run(args)

    def set_claim(self, claim_type: str, subnets: str | None = None) -> Any:
        args = ["stake", "set-claim", "--claim-type", claim_type]
        args += self._opt("--subnets", subnets)
        return self._run(args)

    def transfer_stake(
        self, dest: str, amount: float, from_netuid: int, to_netuid: int, hotkey_address: str | None = None
    ) -> Any:
        args = [
            "stake",
            "transfer-stake",
            "--dest",
            dest,
            "--amount",
            str(amount),
            "--from",
            str(from_netuid),
            "--to",
            str(to_netuid),
        ]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def remove_full_limit(self, netuid: int, price: float, hotkey_address: str | None = None) -> Any:
        args = ["stake", "remove-full-limit", "--netuid", str(netuid), "--price", str(price)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def wizard(self, netuid: int | None = None, amount: float | None = None, hotkey_address: str | None = None) -> Any:
        args = ["stake", "wizard"]
        args += self._opt("--netuid", netuid)
        args += self._opt("--amount", amount)
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)
