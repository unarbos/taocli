"""Crowdloan SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Crowdloan(SdkModule):
    """Crowdloan operations — create, contribute, withdraw, finalize, refund, dissolve."""

    def create(
        self,
        deposit: str,
        min_contribution: str,
        cap: str,
        end_block: int,
        target: str | None = None,
    ) -> Any:
        cmd = [
            "crowdloan",
            "create",
            "--deposit",
            deposit,
            "--min-contribution",
            min_contribution,
            "--cap",
            cap,
            "--end-block",
            str(end_block),
        ]
        cmd += self._opt("--target", target)
        return self._run(cmd)

    def contribute(self, crowdloan_id: str, amount: str) -> Any:
        return self._run(["crowdloan", "contribute", "--crowdloan-id", crowdloan_id, "--amount", amount])

    def withdraw(self, crowdloan_id: str) -> Any:
        return self._run(["crowdloan", "withdraw", "--crowdloan-id", crowdloan_id])

    def finalize(self, crowdloan_id: str) -> Any:
        return self._run(["crowdloan", "finalize", "--crowdloan-id", crowdloan_id])

    def refund(self, crowdloan_id: str) -> Any:
        return self._run(["crowdloan", "refund", "--crowdloan-id", crowdloan_id])

    def dissolve(self, crowdloan_id: str) -> Any:
        return self._run(["crowdloan", "dissolve", "--crowdloan-id", crowdloan_id])

    def update_cap(self, crowdloan_id: str, cap: str) -> Any:
        return self._run(["crowdloan", "update-cap", "--crowdloan-id", crowdloan_id, "--cap", cap])

    def update_end(self, crowdloan_id: str, end_block: int) -> Any:
        return self._run(["crowdloan", "update-end", "--crowdloan-id", crowdloan_id, "--end-block", str(end_block)])

    def update_min_contribution(self, crowdloan_id: str, min_contribution: str) -> Any:
        return self._run(
            [
                "crowdloan",
                "update-min-contribution",
                "--crowdloan-id",
                crowdloan_id,
                "--min-contribution",
                min_contribution,
            ]
        )

    def list(self) -> Any:
        return self._run(["crowdloan", "list"])

    def info(self, crowdloan_id: str) -> Any:
        return self._run(["crowdloan", "info", "--crowdloan-id", crowdloan_id])

    def contributors(self, crowdloan_id: str) -> Any:
        return self._run(["crowdloan", "contributors", "--crowdloan-id", crowdloan_id])
