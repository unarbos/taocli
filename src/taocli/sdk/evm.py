"""EVM SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Evm(SdkModule):
    """EVM operations — call contracts and withdraw to Substrate."""

    def call(
        self,
        source: str,
        target: str,
        input: str,
        value: str | None = None,
        gas_limit: int | None = None,
        max_fee_per_gas: str | None = None,
    ) -> Any:
        cmd = ["evm", "call", "--source", source, "--target", target, "--input", input]
        cmd += self._opt("--value", value)
        cmd += self._opt("--gas-limit", gas_limit)
        cmd += self._opt("--max-fee-per-gas", max_fee_per_gas)
        return self._run(cmd)

    def withdraw(self, address: str, amount: str) -> Any:
        return self._run(["evm", "withdraw", "--address", address, "--amount", amount])
