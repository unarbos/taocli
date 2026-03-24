# taocli

Python CLI + SDK wrapper for [agcli](https://github.com/unarbos/agcli) — Bittensor staking, transfers, wallets, weights, subnets, and more.

[![CI](https://github.com/unarbos/taocli/actions/workflows/ci.yml/badge.svg)](https://github.com/unarbos/taocli/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/unarbos/taocli/branch/main/graph/badge.svg)](https://codecov.io/gh/unarbos/taocli)
[![PyPI](https://img.shields.io/pypi/v/taocli)](https://pypi.org/project/taocli/)

## Install

```bash
uv pip install taocli
```

Requires the `agcli` binary on your PATH. See [agcli releases](https://github.com/unarbos/agcli/releases).

## CLI

taocli mirrors agcli 1:1 — same commands, same flags, same output:

```bash
taocli wallet list
taocli balance --address 5G...
taocli stake add --amount 10 --netuid 1
taocli subnet list
taocli view portfolio
taocli transfer --dest 5G... --amount 1.0
```

## SDK

```python
from taocli import Client

c = Client(network="finney")

# Balance
c.balance(address="5G...")

# Wallet
c.wallet.list()
c.wallet.create()

# Staking
c.stake.add(10.0, netuid=1)
c.stake.list()

# Transfer
c.transfer.transfer("5G...", 1.0)

# Subnet
c.subnet.list()
c.subnet.show(1)

# View
c.view.portfolio()
c.view.network()
```

## SDK Modules

All modules are accessible as attributes on the `Client` instance.

| Module | Attribute | Description |
|--------|-----------|-------------|
| **Balance** | `c.balance()` | Query account balances |
| **Wallet** | `c.wallet` | Create, list, import, sign, verify wallets |
| **Stake** | `c.stake` | Add, remove, move, swap stake; limit orders; auto-compound |
| **Transfer** | `c.transfer` | Send TAO between accounts |
| **Subnet** | `c.subnet` | List, register, metagraph, health, cache, dissolve |
| **Weights** | `c.weights` | Set, commit, reveal, commit-reveal weights |
| **View** | `c.view` | Portfolio, network, dynamic, neuron, validators, analytics |
| **Delegate** | `c.delegate` | Show, list delegates; adjust take |
| **Root** | `c.root` | Root network registration and weights |
| **Identity** | `c.identity` | Set, get, remove on-chain + subnet identity |
| **Proxy** | `c.proxy` | Add, remove, pure, announced proxy accounts |
| **Serve** | `c.serve` | Serve axon/prometheus endpoints |
| **Commitment** | `c.commitment` | Set, get, list miner commitments |
| **Config** | `c.config` | Get, set, list, reset config; cache management |
| **Swap** | `c.swap` | Hotkey swap, coldkey swap, EVM key association |
| **Admin** | `c.admin` | Sudo operations — set hyperparameters |
| **Audit** | `c.audit` | Security audit of account exposure |
| **Explain** | `c.explain` | Built-in Bittensor concept reference |
| **Block** | `c.block` | Query block info, latest, ranges |
| **Diff** | `c.diff` | Compare state between blocks |
| **Multisig** | `c.multisig` | Submit, approve, execute threshold calls |
| **Crowdloan** | `c.crowdloan` | Create, contribute, manage crowdloans |
| **Liquidity** | `c.liquidity` | Add, remove, modify AMM positions |
| **Subscribe** | `c.subscribe` | Subscribe to blocks and events |
| **Scheduler** | `c.scheduler` | Schedule on-chain calls |
| **Preimage** | `c.preimage` | Store governance preimages |
| **Contracts** | `c.contracts` | Upload, instantiate, call WASM contracts |
| **EVM** | `c.evm` | Call EVM contracts, withdraw to Substrate |
| **SafeMode** | `c.safe_mode` | Enter/exit safe mode |
| **Drand** | `c.drand` | Write drand randomness pulses |
| **Localnet** | `c.localnet` | Start, stop, reset local dev chain |
| **Batch** | `c.batch` | Run batch extrinsics from JSON |
| **Utils** | `c.utils` | Convert denominations, measure latency |

## License

MIT
