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

## License

MIT
