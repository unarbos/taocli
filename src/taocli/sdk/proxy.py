"""Proxy SDK module."""

from __future__ import annotations

from typing import Any

from taocli.sdk.base import SdkModule


class Proxy(SdkModule):
    """Proxy account management — add and remove proxy accounts."""

    def add(self, delegate: str, proxy_type: str | None = None) -> Any:
        """Add a proxy account with a given type."""
        args = ["proxy", "add", "--delegate", delegate]
        args += self._opt("--proxy-type", proxy_type)
        return self._run(args)

    def remove(self, delegate: str, proxy_type: str | None = None) -> Any:
        """Remove a proxy account."""
        args = ["proxy", "remove", "--delegate", delegate]
        args += self._opt("--proxy-type", proxy_type)
        return self._run(args)

    def list(self, address: str | None = None) -> Any:
        """List proxy accounts for an address."""
        args = ["proxy", "list"]
        args += self._opt("--address", address)
        return self._run(args)

    def create_pure(self, proxy_type: str | None = None, delay: int | None = None, index: int | None = None) -> Any:
        """Create a pure (anonymous) proxy account."""
        cmd = ["proxy", "create-pure"]
        cmd += self._opt("--proxy-type", proxy_type)
        cmd += self._opt("--delay", delay)
        cmd += self._opt("--index", index)
        return self._run(cmd)

    def kill_pure(
        self,
        spawner: str,
        proxy_type: str,
        index: int,
        height: int,
        ext_index: int,
    ) -> Any:
        """Kill (remove) a pure proxy account."""
        return self._run(
            [
                "proxy",
                "kill-pure",
                "--spawner",
                spawner,
                "--proxy-type",
                proxy_type,
                "--index",
                str(index),
                "--height",
                str(height),
                "--ext-index",
                str(ext_index),
            ]
        )

    def announce(self, real: str, call_hash: str) -> Any:
        """Announce a proxy call for time-delayed execution."""
        return self._run(["proxy", "announce", "--real", real, "--call-hash", call_hash])

    def proxy_announced(
        self,
        delegate: str,
        real: str,
        pallet: str,
        call: str,
        proxy_type: str | None = None,
        args: str | None = None,
    ) -> Any:
        """Execute a previously announced proxy call."""
        cmd = ["proxy", "proxy-announced", "--delegate", delegate, "--real", real, "--pallet", pallet, "--call", call]
        cmd += self._opt("--proxy-type", proxy_type)
        cmd += self._opt("--args", args)
        return self._run(cmd)

    def reject_announcement(self, delegate: str, call_hash: str) -> Any:
        """Reject a pending proxy announcement."""
        return self._run(["proxy", "reject-announcement", "--delegate", delegate, "--call-hash", call_hash])

    def list_announcements(self, address: str | None = None) -> Any:
        """List pending proxy announcements."""
        cmd = ["proxy", "list-announcements"]
        cmd += self._opt("--address", address)
        return self._run(cmd)

    def remove_all(self) -> Any:
        """Remove all proxy accounts."""
        return self._run(["proxy", "remove-all"])

    def remove_announcement(self, real: str, call_hash: str) -> Any:
        """Remove a specific proxy announcement."""
        return self._run(["proxy", "remove-announcement", "--real", real, "--call-hash", call_hash])
