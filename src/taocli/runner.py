"""Core subprocess wrapper for calling agcli."""

from __future__ import annotations

import json
import os
import platform
import shutil
import stat
import subprocess
from importlib.abc import Traversable
from importlib.resources import files
from typing import Any


def _bundled_candidate(system: str, machine: str) -> Traversable:
    return files("taocli").joinpath("bin").joinpath(system).joinpath(machine).joinpath("agcli")


def _normalize_machine(machine: str) -> str | None:
    normalized = machine.lower()
    if normalized in {"x86_64", "amd64"}:
        return "x86_64"
    if normalized in {"aarch64", "arm64"}:
        return "aarch64"
    return None


def _ensure_executable(path: str) -> bool:
    if os.access(path, os.X_OK):
        return True
    try:
        current_mode = os.stat(path).st_mode
        os.chmod(path, current_mode | stat.S_IXUSR)
    except OSError:
        return False
    return os.access(path, os.X_OK)


def find_bundled_agcli_binary() -> str | None:
    """Return a bundled agcli binary path for the current platform, if present."""
    system = platform.system().lower()
    machine = _normalize_machine(platform.machine())
    if system not in {"linux", "darwin"} or machine is None:
        return None

    candidate = _bundled_candidate(system, machine)
    if not candidate.is_file():
        return None

    candidate_path = str(candidate)
    if not _ensure_executable(candidate_path):
        return None
    return candidate_path


def resolve_agcli_binary(binary: str | None) -> str:
    """Resolve the agcli binary path, preferring bundled binaries when available."""
    if binary:
        return binary
    return find_bundled_agcli_binary() or "agcli"


class AgcliError(Exception):
    """Raised when agcli returns a non-zero exit code."""

    def __init__(self, message: str, returncode: int = 1, stderr: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class AgcliRunner:
    """Wraps the agcli binary as a subprocess."""

    def __init__(
        self,
        binary: str | None = None,
        network: str | None = None,
        endpoint: str | None = None,
        wallet_dir: str | None = None,
        wallet: str | None = None,
        hotkey_name: str | None = None,
        yes: bool = False,
        batch: bool = False,
        output: str | None = None,
        password: str | None = None,
        proxy: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self.binary = resolve_agcli_binary(binary)
        self.network = network
        self.endpoint = endpoint
        self.wallet_dir = wallet_dir
        self.wallet = wallet
        self.hotkey_name = hotkey_name
        self.yes = yes
        self.batch = batch
        self.output = output
        self.password = password
        self.proxy = proxy
        self.timeout = timeout

    def _build_global_args(self) -> list[str]:
        args: list[str] = []
        if self.network:
            args.extend(["--network", self.network])
        if self.endpoint:
            args.extend(["--endpoint", self.endpoint])
        if self.wallet_dir:
            args.extend(["--wallet-dir", self.wallet_dir])
        if self.wallet:
            args.extend(["--wallet", self.wallet])
        if self.hotkey_name:
            args.extend(["--hotkey-name", self.hotkey_name])
        if self.yes:
            args.append("--yes")
        if self.batch:
            args.append("--batch")
        if self.output:
            args.extend(["--output", self.output])
        if self.password:
            args.extend(["--password", self.password])
        if self.proxy:
            args.extend(["--proxy", self.proxy])
        if self.timeout is not None:
            args.extend(["--timeout", str(self.timeout)])
        return args

    def run(
        self,
        args: list[str],
        *,
        check: bool = True,
        capture: bool = True,
        timeout_secs: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run agcli with the given args plus global flags."""
        cmd = [self.binary] + self._build_global_args() + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=capture,
                text=True,
                timeout=timeout_secs,
            )
        except FileNotFoundError as exc:
            raise AgcliError(
                f"agcli binary not found at '{self.binary}'.\n"
                "Install the published wheel package 'tao-cli' for your platform "
                "when available, or download agcli from: "
                "https://github.com/unarbos/agcli/releases\n"
                "Or set the path: Client(binary='/path/to/agcli')",
                returncode=-1,
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise AgcliError(
                f"agcli timed out after {timeout_secs}s. "
                f"Try increasing timeout: Client(timeout={timeout_secs * 2 if timeout_secs else 60})",
                returncode=-1,
                stderr=str(exc),
            ) from exc
        if check and result.returncode != 0:
            raise AgcliError(
                f"agcli exited with code {result.returncode}: {result.stderr.strip()}",
                returncode=result.returncode,
                stderr=result.stderr,
            )
        return result

    def run_json(
        self,
        args: list[str],
        *,
        timeout_secs: int | None = None,
    ) -> Any:
        """Run agcli with --output json --batch --yes and parse the result."""
        extra = ["--output", "json", "--batch", "--yes"]
        result = self.run(args + extra, timeout_secs=timeout_secs)
        stdout = result.stdout.strip()
        if not stdout:
            return None
        return json.loads(stdout)

    def find_binary(self) -> str | None:
        """Find the agcli binary on PATH."""
        return shutil.which(self.binary)

    def version(self) -> str:
        """Get agcli version string."""
        result = self.run(["--version"])
        return result.stdout.strip()
