"""Scheduler SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Scheduler(SdkModule):
    """Governance scheduler — schedule and cancel on-chain calls."""

    def schedule(
        self,
        when: int,
        pallet: str,
        call: str,
        args: str | None = None,
        priority: int | None = None,
        repeat_every: int | None = None,
        repeat_count: int | None = None,
    ) -> Any:
        cmd = ["scheduler", "schedule", "--when", str(when), "--pallet", pallet, "--call", call]
        cmd += self._opt("--args", args)
        cmd += self._opt("--priority", priority)
        cmd += self._opt("--repeat-every", repeat_every)
        cmd += self._opt("--repeat-count", repeat_count)
        return self._run(cmd)

    def schedule_named(
        self,
        id: str,
        when: int,
        pallet: str,
        call: str,
        args: str | None = None,
        priority: int | None = None,
        repeat_every: int | None = None,
        repeat_count: int | None = None,
    ) -> Any:
        cmd = ["scheduler", "schedule-named", "--id", id, "--when", str(when), "--pallet", pallet, "--call", call]
        cmd += self._opt("--args", args)
        cmd += self._opt("--priority", priority)
        cmd += self._opt("--repeat-every", repeat_every)
        cmd += self._opt("--repeat-count", repeat_count)
        return self._run(cmd)

    def cancel(self, when: int, index: int) -> Any:
        return self._run(["scheduler", "cancel", "--when", str(when), "--index", str(index)])

    def cancel_named(self, id: str) -> Any:
        return self._run(["scheduler", "cancel-named", "--id", id])
