"""Stake SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Stake(SdkModule):
    """Staking operations — add, remove, move, swap, list, etc."""

    def add(
        self, amount: float, netuid: int, hotkey_address: str | None = None, max_slippage: float | None = None
    ) -> Any:
        """Add stake to a hotkey on a subnet."""
        args = ["stake", "add", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--max-slippage", max_slippage)
        return self._run(args)

    def remove(
        self, amount: float, netuid: int, hotkey_address: str | None = None, max_slippage: float | None = None
    ) -> Any:
        """Remove stake from a hotkey on a subnet."""
        args = ["stake", "remove", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--max-slippage", max_slippage)
        return self._run(args)

    def list(self, address: str | None = None, at_block: int | None = None) -> Any:
        """List all stakes for an address."""
        args = ["stake", "list"]
        args += self._opt("--address", address)
        args += self._opt("--at-block", at_block)
        return self._run(args)

    def move(self, amount: float, from_netuid: int, to_netuid: int, hotkey_address: str | None = None) -> Any:
        """Move stake between subnets for the same hotkey."""
        args = ["stake", "move", "--amount", str(amount), "--from", str(from_netuid), "--to", str(to_netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def swap(self, amount: float, from_netuid: int, to_netuid: int, hotkey_address: str | None = None) -> Any:
        """Swap stake between subnets through TAO."""
        args = ["stake", "swap", "--amount", str(amount), "--from", str(from_netuid), "--to", str(to_netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def unstake_all(self, hotkey_address: str | None = None) -> Any:
        """Unstake all TAO from a hotkey across all subnets."""
        args = ["stake", "unstake-all"]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def unstake_all_alpha(self, hotkey_address: str | None = None) -> Any:
        """Unstake all alpha tokens from a hotkey."""
        args = ["stake", "unstake-all-alpha"]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def claim_root(self, netuid: int, hotkey_address: str | None = None) -> Any:
        """Claim root network emissions for a subnet."""
        args = ["stake", "claim-root", "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def add_limit(self, amount: float, netuid: int, price: float, partial: bool = False) -> Any:
        """Place a limit order to add stake at a target price."""
        args = ["stake", "add-limit", "--amount", str(amount), "--netuid", str(netuid), "--price", str(price)]
        args += self._flag("--partial", partial)
        return self._run(args)

    def remove_limit(self, amount: float, netuid: int, price: float, partial: bool = False) -> Any:
        """Place a limit order to remove stake at a target price."""
        args = ["stake", "remove-limit", "--amount", str(amount), "--netuid", str(netuid), "--price", str(price)]
        args += self._flag("--partial", partial)
        return self._run(args)

    def childkey_take(self, take: float, netuid: int, hotkey_address: str | None = None) -> Any:
        """Set the childkey take percentage on a subnet."""
        args = ["stake", "childkey-take", "--take", str(take), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def set_children(self, netuid: int, children: str, hotkey_address: str | None = None) -> Any:
        """Set child hotkeys and their proportions on a subnet."""
        args = ["stake", "set-children", "--netuid", str(netuid), "--children", children]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def recycle_alpha(self, amount: float, netuid: int, hotkey_address: str | None = None) -> Any:
        """Recycle alpha tokens back to the subnet pool."""
        args = ["stake", "recycle-alpha", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def burn_alpha(self, amount: float, netuid: int, hotkey_address: str | None = None) -> Any:
        """Burn alpha tokens permanently."""
        args = ["stake", "burn-alpha", "--amount", str(amount), "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def swap_limit(self, amount: float, from_netuid: int, to_netuid: int, price: float, partial: bool = False) -> Any:
        """Place a limit order to swap stake between subnets."""
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
        """Enable automatic stake compounding on a subnet."""
        args = ["stake", "set-auto", "--netuid", str(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def show_auto(self, address: str | None = None) -> Any:
        """Show auto-compounding settings for an address."""
        args = ["stake", "show-auto"]
        args += self._opt("--address", address)
        return self._run(args)

    def process_claim(self, hotkey_address: str | None = None, netuids: str | None = None) -> Any:
        """Process pending stake claims for a hotkey."""
        args = ["stake", "process-claim"]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--netuids", netuids)
        return self._run(args)

    def set_claim(self, claim_type: str, subnets: str | None = None) -> Any:
        """Set the claim type (all, subnets, or root) for rewards."""
        args = ["stake", "set-claim", "--claim-type", claim_type]
        args += self._opt("--subnets", subnets)
        return self._run(args)

    def transfer_stake(
        self, dest: str, amount: float, from_netuid: int, to_netuid: int, hotkey_address: str | None = None
    ) -> Any:
        """Transfer stake to another coldkey address."""
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
        """Place a limit order to fully remove stake on a subnet."""
        args = ["stake", "remove-full-limit", "--netuid", str(netuid), "--price", str(price)]
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)

    def wizard(self, netuid: int | None = None, amount: float | None = None, hotkey_address: str | None = None) -> Any:
        """Interactive staking wizard with guided prompts."""
        args = ["stake", "wizard"]
        args += self._opt("--netuid", netuid)
        args += self._opt("--amount", amount)
        args += self._opt("--hotkey-address", hotkey_address)
        return self._run(args)
