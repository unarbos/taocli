"""Client — main entry point for the taocli SDK."""

from __future__ import annotations

from typing import Any

from taocli.runner import AgcliRunner
from taocli.sdk.admin import Admin
from taocli.sdk.audit import Audit
from taocli.sdk.batch import Batch
from taocli.sdk.block import Block
from taocli.sdk.commitment import Commitment
from taocli.sdk.config import Config
from taocli.sdk.contracts import Contracts
from taocli.sdk.crowdloan import Crowdloan
from taocli.sdk.delegate import Delegate
from taocli.sdk.diff import Diff
from taocli.sdk.drand import Drand
from taocli.sdk.evm import Evm
from taocli.sdk.explain import Explain
from taocli.sdk.identity import Identity
from taocli.sdk.liquidity import Liquidity
from taocli.sdk.localnet import Localnet
from taocli.sdk.multisig import Multisig
from taocli.sdk.preimage import Preimage
from taocli.sdk.proxy import Proxy
from taocli.sdk.root import Root
from taocli.sdk.safe_mode import SafeMode
from taocli.sdk.scheduler import Scheduler
from taocli.sdk.serve import Serve
from taocli.sdk.stake import Stake
from taocli.sdk.subnet import Subnet
from taocli.sdk.subscribe import Subscribe
from taocli.sdk.swap import Swap
from taocli.sdk.transfer import Transfer
from taocli.sdk.utils import Utils
from taocli.sdk.view import View
from taocli.sdk.wallet import Wallet
from taocli.sdk.weights import Weights


class Client:
    """Main taocli client — provides access to all SDK modules.

    Args:
        binary: Path to agcli binary (default: bundled agcli when available, else 'agcli' on PATH).
        network: Network name — 'finney' (mainnet), 'test' (testnet), 'local'.
        endpoint: WebSocket chain endpoint (e.g. 'ws://127.0.0.1:9944').
            Overrides ``network`` when set.
        wallet_dir: Directory containing wallet keys (default: ~/.bittensor/wallets).
        wallet: Coldkey wallet name (default: 'default').
        hotkey_name: Hotkey name within the wallet (default: 'default').
        password: Wallet decryption password. If omitted and required, agcli
            will prompt (only works when not in batch mode).
        proxy: SS58 address of a proxy account — all extrinsics will be
            wrapped via ``Proxy.proxy``.
        timeout: Global subprocess timeout in seconds for every agcli call.

    Example::

        from taocli import Client

        c = Client(network="finney")
        print(c.balance("5C4hrfjw9DjXZTzV3MwzrrAr9P1MJhSrvWGWqi1eSuyUpnhM"))
        print(c.view.network())
    """

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
        self.identity = Identity(self._runner)
        self.proxy = Proxy(self._runner)
        self.serve = Serve(self._runner)
        self.commitment = Commitment(self._runner)
        self.utils = Utils(self._runner)
        self.config = Config(self._runner)
        self.swap = Swap(self._runner)
        self.admin = Admin(self._runner)
        self.audit = Audit(self._runner)
        self.batch = Batch(self._runner)
        self.block = Block(self._runner)
        self.contracts = Contracts(self._runner)
        self.crowdloan = Crowdloan(self._runner)
        self.diff = Diff(self._runner)
        self.drand = Drand(self._runner)
        self.evm = Evm(self._runner)
        self.explain = Explain(self._runner)
        self.liquidity = Liquidity(self._runner)
        self.localnet = Localnet(self._runner)
        self.multisig = Multisig(self._runner)
        self.preimage = Preimage(self._runner)
        self.safe_mode = SafeMode(self._runner)
        self.scheduler = Scheduler(self._runner)
        self.subscribe = Subscribe(self._runner)

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
