"""Contracts SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Contracts(SdkModule):
    """WASM contract operations — upload, instantiate, call, remove code."""

    def upload(self, code: str, storage_deposit_limit: str | None = None) -> Any:
        cmd = ["contracts", "upload", "--code", code]
        cmd += self._opt("--storage-deposit-limit", storage_deposit_limit)
        return self._run(cmd)

    def instantiate(
        self,
        code_hash: str,
        value: str = "0",
        data: str = "0x",
        salt: str = "0x",
        gas_ref_time: int | None = None,
        gas_proof_size: int | None = None,
        storage_deposit_limit: str | None = None,
    ) -> Any:
        cmd = [
            "contracts",
            "instantiate",
            "--code-hash",
            code_hash,
            "--value",
            value,
            "--data",
            data,
            "--salt",
            salt,
        ]
        cmd += self._opt("--gas-ref-time", gas_ref_time)
        cmd += self._opt("--gas-proof-size", gas_proof_size)
        cmd += self._opt("--storage-deposit-limit", storage_deposit_limit)
        return self._run(cmd)

    def call(
        self,
        contract: str,
        value: str = "0",
        data: str = "0x",
        gas_ref_time: int | None = None,
        gas_proof_size: int | None = None,
        storage_deposit_limit: str | None = None,
    ) -> Any:
        cmd = ["contracts", "call", "--contract", contract, "--value", value, "--data", data]
        cmd += self._opt("--gas-ref-time", gas_ref_time)
        cmd += self._opt("--gas-proof-size", gas_proof_size)
        cmd += self._opt("--storage-deposit-limit", storage_deposit_limit)
        return self._run(cmd)

    def remove_code(self, code_hash: str) -> Any:
        return self._run(["contracts", "remove-code", "--code-hash", code_hash])
