"""Client — main entry point for the taocli SDK."""

from __future__ import annotations

from typing import Any

from taocli.runner import AgcliRunner
from taocli.sdk.delegate import Delegate
from taocli.sdk.root import Root
from taocli.sdk.stake import Stake
from taocli.sdk.subnet import Subnet
from taocli.sdk.transfer import Transfer
from taocli.sdk.view import View
from taocli.sdk.wallet import Wallet
from taocli.sdk.weights import Weights


class Client:
    """Main taocli client — provides access to all SDK modules."""

    def __init__(
        self,
        binary: str | None = None,
        network: str | None = None,
        endpoint: str | None = None,
        wallet_dir: str | None = None,
        wallet: str | None = None,
        hotkey_name: str | None = None,
        password: str | None = None,
        proxy: str | None = None,
        timeout: int | None = None,
    ) -> None:
        self._runner = AgcliRunner(
            binary=binary,
            network=network,
            endpoint=endpoint,
            wallet_dir=wallet_dir,
            wallet=wallet,
            hotkey_name=hotkey_name,
            yes=True,
            batch=True,
            output="json",
            password=password,
            proxy=proxy,
            timeout=timeout,
        )
        self.wallet = Wallet(self._runner)
        self.stake = Stake(self._runner)
        self.transfer = Transfer(self._runner)
        self.subnet = Subnet(self._runner)
        self.weights = Weights(self._runner)
        self.delegate = Delegate(self._runner)
        self.root = Root(self._runner)
        self.view = View(self._runner)

    def balance(self, address: str | None = None, at_block: int | None = None) -> Any:
        """Get balance for an address."""
        args = ["balance"]
        if address:
            args.extend(["--address", address])
        if at_block is not None:
            args.extend(["--at-block", str(at_block)])
        return self._runner.run_json(args)

    def doctor(self) -> str:
        """Run diagnostic check."""
        result = self._runner.run(["doctor"])
        return result.stdout.strip()

    def version(self) -> str:
        """Get agcli version."""
        return self._runner.version()
