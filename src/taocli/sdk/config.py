"""Config SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Config(SdkModule):
    """Configuration management — get, set, list, reset persistent config."""

    def get(self, key: str) -> Any:
        return self._run(["config", "get", "--key", key])

    def set(self, key: str, value: str) -> Any:
        return self._run(["config", "set", "--key", key, "--value", value])

    def list(self) -> Any:
        return self._run(["config", "list"])

    def reset(self) -> Any:
        return self._run(["config", "reset"])
