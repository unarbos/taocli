# taocli

Python CLI + SDK wrapper for [agcli](https://github.com/unarbos/agcli) — Bittensor staking, transfers, wallets, weights, subnets, and more.

[![CI](https://github.com/unarbos/taocli/actions/workflows/ci.yml/badge.svg)](https://github.com/unarbos/taocli/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/unarbos/taocli/graph/badge.svg)](https://codecov.io/gh/unarbos/taocli)
[![PyPI](https://img.shields.io/pypi/v/tao-cli)](https://pypi.org/project/tao-cli/)

## Current release status

- `taocli` is the CLI command and Python import name.
- `tao-cli` is the intended PyPI distribution name.
- The README CI badge tracks lint/test/coverage only; PyPI publishing now runs in a separate GitHub Actions workflow.
- The last failed GitHub publish attempted the old `taocli` `0.6.5` package name, which PyPI rejected as too similar to an existing project.
- The intended public install command is `uv pip install tao-cli` once the refreshed wheels are live from the separate publish workflow.
- Once those platform wheels are published, supported Linux/macOS installs should work without a separate `agcli` on `PATH` because the bundled-binary path is already implemented in code.

## Install

### Planned PyPI install

```bash
uv pip install tao-cli
```

That installs the package, but the command you run stays:

```bash
taocli --help
```

Do not use `uv pip install taocli`; the published distribution name is `tao-cli`.

### Current pre-release/source install

Until `tao-cli` wheels are live on PyPI, install from a local checkout:

```bash
git clone https://github.com/unarbos/taocli
cd taocli
uv pip install -e .
```

Source installs do **not** bundle `agcli`. For now, source installs still require `agcli` on `PATH` or an explicit `--agcli-binary` / `TAOCLI_AGCLI_BINARY` override.

When published as supported Linux/macOS wheels, `tao-cli` will use the bundled `agcli` binary automatically.

Agent/discovery metadata is also shipped in `llms.txt`.

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

# Weights
c.weights.set(1, {0: 100, 1: 200}, version_key=7)
workflow = c.weights.workflow_help(1, {0: 100, 1: 200}, salt="round-42", version_key=7, wait=True)
print(workflow["commit_reveal"])
print(workflow["reveal"])
print(c.weights.troubleshoot_help(1, "IncorrectCommitRevealVersion", {0: 100, 1: 200}, salt="round-42", version_key=7))

# Operator-priority workflow helpers
print(c.view.chain_data_workflow_help(1, uid=0))
print(c.subnet.registration_workflow_help(1, wallet="cold", hotkey="miner"))
print(c.serve.axon_workflow_help(1, "0.0.0.0", 8091, version=1, prometheus_port=9090))
print(c.subnet.hyperparameters_workflow_help(1, param="tempo", value="360"))
print(c.admin.hyperparameter_workflow_help(1, command="set-tempo", value_flag="--tempo", value=360))
print(c.admin.hyperparameter_mutation_help("set-tempo", 1, value_flag="--tempo", value=360))

# View
c.view.portfolio()
c.view.network()
```

`c.weights` accepts the native agcli CSV form (`"0:100,1:200"`) plus agent-friendlier mappings, `(uid, weight)` pairs, JSON strings, `-` for stdin, and `@file.json` inputs. Use `workflow_help(...)` when you want copy-pasteable `set`, `commit-reveal`, `commit`, `reveal`, `status`, and adjacent follow-up commands (`inspect_metagraph_command`, `inspect_chain_data_command`, `inspect_hyperparams_command`, `inspect_emissions_command`, `inspect_owner_param_list_command`, `inspect_admin_list_command`, `inspect_health_command`, `inspect_axon_command`) for an operator runbook or agent handoff. For atomic commit-reveal flows, prefer `commit_reveal_runbook_help(...)` or `create_commit_reveal_state_help(...)` first so the original weights, salt, derived hash, and reusable reveal command can be saved and reused if the reveal step stalls.

`troubleshoot_help(...)` now also carries those adjacent pivots so operators can move from a weights error into metagraph/emissions inspection, hyperparameter read/write discovery, subnet summary, registration readiness, or serve verification without reconstructing discovery commands manually.


`save_commit_reveal_state_help(...)`, `load_commit_reveal_state_help(...)`, `recover_reveal_from_state_help(...)`, and `troubleshoot_unrevealed_commit_help(...)` are the recovery path: persist a JSON state record before or during commit, then reload it later to reveal the exact same commit manually instead of losing the original reveal inputs. Those saved-state helpers also keep the adjacent metagraph/hyperparameter/subnet/serve pivots (`inspect_metagraph_command`, `inspect_chain_data_command`, `inspect_hyperparams_command`, `inspect_emissions_command`, `inspect_owner_param_list_command`, `inspect_admin_list_command`, `inspect_registration_cost_command`, `inspect_health_command`, `inspect_axon_command`) on the recovery record so operators can jump out of a stuck reveal without rediscovering the follow-up commands.

`operator_note_for_atomic_commit_reveal_help(...)` wraps that runbook in operator-facing guidance for handoff situations where another person or agent may need to finish the reveal later.

## Operator-priority workflow quick reference

```python
from taocli import Client

c = Client(network="finney")

# 1) Metagraph / miner endpoints / chain state
chain = c.view.chain_data_workflow_help(1, uid=0)
print(chain["metagraph"])
print(chain["neurons"])
print(chain["miner_endpoints"])
print(chain["commits"])
print(chain["hyperparams"])

# 2) Register on a subnet
register = c.subnet.registration_workflow_help(1, wallet="cold", hotkey="miner", threads=8)
print(register["registration_cost"])
print(register["register_neuron"])
print(register["pow_register"])

# 3) Serve an axon
serve = c.serve.axon_workflow_help(1, "0.0.0.0", 8091, version=1, prometheus_port=9090)
print(serve["serve_axon"])
print(serve["status_check"])

# 4) Set weights
weights = c.weights.operator_workflow_help(
    1,
    {0: 100, 1: 200},
    salt="round-42",
    version_key=7,
    wait=True,
    wallet="cold",
    hotkey="validator",
)
print(weights["status"])
print(weights["show"])
print(weights["hyperparams"])
print(weights["inspect_metagraph_command"])
print(weights["inspect_chain_data_command"])
print(weights["inspect_hyperparams_command"])
print(weights["inspect_emissions_command"])
print(weights["inspect_owner_param_list_command"])
print(weights["inspect_admin_list_command"])
print(weights["inspect_axon_command"])
print(weights["set"])
print(weights["commit_reveal"])

# Saved-state recovery if reveal stalls later
state = c.weights.commit_reveal_runbook_help(
    1,
    {0: 100, 1: 200},
    salt="round-42",
    version_key=7,
    state_path="weights-state.json",
)
print(state["reveal_command"])
recovery = c.weights.troubleshoot_unrevealed_commit_help(
    "weights-state.json",
    status={"block": 125, "commit_reveal_enabled": True, "reveal_period_epochs": 3, "commits": []},
)
print(recovery["inspect_metagraph_command"])
print(recovery["inspect_hyperparams_command"])
print(recovery["inspect_emissions_command"])
print(recovery["inspect_owner_param_list_command"])
print(recovery["inspect_admin_list_command"])
print(recovery["inspect_health_command"])
print(recovery["inspect_axon_command"])
print(recovery["adjacent_recovery_note"])

# 5) Get hyperparameters
hparams = c.subnet.hyperparameters_workflow_help(1)
print(hparams["get"])
print(hparams["owner_param_list"])

# 6) Set hyperparameters
proposal = c.subnet.hyperparameters_workflow_help(1, param="tempo", value="360")
print(proposal["owner_param_list"])
print(proposal["set"])
admin = c.admin.hyperparameter_workflow_help(1, command="set-tempo", value_flag="--tempo", value=360)
print(admin["owner_param_list"])
print(admin["admin_list"])
print(admin["set"])
print(c.admin.hyperparameter_mutation_help("set-tempo", 1, value_flag="--tempo", value=360))
```

These helpers are the intended discovery surface for the high-value workflows above: they return normalized, copy-pasteable commands for operators and agents without requiring them to rediscover flags manually.

## Weights SDK quick reference

```python
from taocli import Client

c = Client(network="local")

# Direct set
c.weights.set(1, {0: 100, 1: 200}, version_key=7)

# Auto commit + reveal
c.weights.commit_reveal(1, {0: 100, 1: 200}, version_key=7, wait=True)

# Manual workflow hints for operator/agent guidance
workflow = c.weights.workflow_help(1, {0: 100, 1: 200}, salt="round-42", version_key=7, wait=True)
# workflow keys: normalized_weights, status, set, commit_reveal, commit, reveal

# Compact troubleshooting runbook for common failures
troubleshoot = c.weights.troubleshoot_help(
    1,
    "IncorrectCommitRevealVersion",
    {0: 100, 1: 200},
    salt="round-42",
    version_key=7,
)
# troubleshoot keys: error, likely_cause, next_step, status, normalized_weights, set, commit, reveal, commit_reveal

# Mechanism-specific helper runbook
mechanism = c.weights.mechanism_workflow_help(
    1,
    4,
    {0: 100, 1: 200},
    salt="round-42",
    hash_value="11" * 32,
    version_key=7,
)
# mechanism keys: normalized_weights, status, set_mechanism, reveal_mechanism, optional commit_mechanism

# Mechanism troubleshooting / next-step guidance
# hash_value is optional here; taocli can derive it from weights + salt.
print(
    c.weights.troubleshoot_mechanism_help(
        1,
        4,
        "RevealTooEarly",
        {0: 100, 1: 200},
        salt="round-42",
        version_key=7,
    )
)

# Timelocked helper runbook
print(c.weights.timelocked_workflow_help(1, {0: 100, 1: 200}, 42, salt="round-42", version_key=7))
# timelocked keys: normalized_weights, status, set, commit_timelocked

# Timelocked troubleshooting / next-step guidance
print(c.weights.next_timelocked_action(1, {0: 100, 1: 200}, round=42, salt="round-42"))

# Compact live diagnose helpers
print(c.weights.diagnose_mechanism(1, 4, "RevealTooEarly", {0: 100, 1: 200}, salt="round-42", version_key=7))
print(c.weights.diagnose_timelocked(1, "ExpiredWeightCommit", {0: 100, 1: 200}, round=42, salt="round-42"))
```

For commit-reveal flows, check subnet status and hyperparameters first: validator permit, whether commit-reveal is enabled, the required `version_key`, and any rate limits.
Mechanism-specific and timelocked helpers use the same normalized weights parser, so agents can reuse the exact same payload across direct set, mechanism, and timelocked flows without hand-reformatting.
When `weights status` output is available, the mechanism and timelocked helpers can now turn it into a recommended next command (`REVEAL`, `RECOMMIT`, `WAIT`, or direct `SET`) instead of only showing static runbooks.

Common troubleshooting shortcuts:
- `NeuronNoValidatorPermit`: the hotkey is not currently allowed to set weights on that subnet.
- `IncorrectCommitRevealVersion`: the subnet expects a different `version_key`; inspect subnet hyperparameters before retrying.
- `RevealTooEarly` / `ExpiredWeightCommit`: the commit-reveal timing window is wrong; check `c.weights.status(netuid)` or `c.weights.workflow_help(...)` first and retry in the correct window.
- `troubleshoot_help(...)` turns a common runtime error plus optional weights inputs into a compact runbook with likely cause, next step, and normalized retry commands.
- `workflow_help(...)` is the fastest way to hand an operator or another agent a normalized `status`, `set`, `commit-reveal`, `commit`, and `reveal` runbook for the same weights payload.
- `commit_reveal_runbook_help(...)` / `create_commit_reveal_state_help(...)` now also carry explicit preflight commands (`inspect_status_command`, `inspect_pending_commits_command`, `inspect_version_key_command`) plus notes for reconciling saved reveal state against wallet-specific status before retrying.

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
