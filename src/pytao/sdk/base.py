"""Base class for SDK modules."""

from __future__ import annotations

from typing import Any

from pytao.runner import AgcliRunner


class SdkModule:
    """Base for all SDK modules — holds a shared AgcliRunner."""

    def __init__(self, runner: AgcliRunner) -> None:
        self._runner = runner

    def _run(self, args: list[str], **kwargs: Any) -> Any:
        """Run agcli with JSON output and return parsed result."""
        return self._runner.run_json(args, **kwargs)

    def _run_raw(self, args: list[str], **kwargs: Any) -> str:
        """Run agcli and return raw stdout."""
        result = self._runner.run(args, **kwargs)
        return result.stdout.strip()

    @staticmethod
    def _opt(flag: str, value: Any) -> list[str]:
        """Build optional flag pair."""
        if value is not None:
            return [flag, str(value)]
        return []

    @staticmethod
    def _flag(flag: str, value: bool) -> list[str]:
        """Build boolean flag."""
        if value:
            return [flag]
        return []
