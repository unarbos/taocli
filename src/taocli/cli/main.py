"""Main CLI entry point — passes all commands through to agcli."""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation
from pathlib import Path

import click

from taocli.runner import AgcliError, AgcliRunner

# All agcli command groups and top-level commands
COMMAND_GROUPS = [
    "wallet",
    "balance",
    "transfer",
    "transfer-all",
    "transfer-keep-alive",
    "stake",
    "subnet",
    "weights",
    "root",
    "delegate",
    "view",
    "identity",
    "commitment",
    "serve",
    "proxy",
    "swap",
    "multisig",
    "crowdloan",
    "liquidity",
    "subscribe",
    "block",
    "diff",
    "utils",
    "config",
    "scheduler",
    "preimage",
    "contracts",
    "evm",
    "safe-mode",
    "drand",
    "batch",
    "localnet",
    "admin",
    "doctor",
    "explain",
    "audit",
    "completions",
    "update",
]

BTCLI_TOP_LEVEL_ALIASES: dict[str, Sequence[str]] = {
    "subnets": ("subnet",),
    "sudo": ("admin",),
    "axon": ("serve",),
    "crowd": ("crowdloan",),
}

BTCLI_SUBCOMMAND_ALIASES: dict[tuple[str, ...], Sequence[str]] = {
    ("subnet", "hyperparameters"): ("subnet", "hyperparams"),
    ("subnet", "burn-cost"): ("subnet", "create-cost"),
    ("subnet", "register"): ("subnet", "register-neuron"),
    ("subnet", "pow-register"): ("subnet", "pow"),
    ("subnet", "create"): ("subnet", "register-with-identity"),
    ("subnet", "set-identity"): ("identity", "set-subnet"),
    ("subnet", "mechanisms", "count"): ("subnet", "mechanism-count"),
    ("subnet", "mechanisms", "set"): ("subnet", "set-mechanism-count"),
    ("subnet", "mechanisms", "emissions"): ("subnet", "emission-split"),
    ("subnet", "mechanisms", "split-emissions"): ("subnet", "set-emission-split"),
    ("admin", "get"): ("subnet", "hyperparams"),
    ("admin", "set"): ("subnet", "set-param"),
    ("admin", "trim"): ("subnet", "trim"),
    ("axon", "set"): ("serve", "axon"),
    ("axon", "reset"): ("serve", "reset"),
    ("serve", "set"): ("serve", "axon"),
    ("wallet", "balance"): ("balance",),
    ("wallet", "get-identity"): ("identity", "show"),
    ("wallet", "swap-check"): ("wallet", "check-swap"),
    ("wallet", "overview"): ("view", "portfolio"),
    ("wallet", "set-identity"): ("identity", "set"),
    ("wallet", "transfer"): ("transfer",),
    ("stake", "auto"): ("stake", "show-auto"),
    ("stake", "transfer"): ("stake", "transfer-stake"),
    ("proxy", "create"): ("proxy", "create-pure"),
    ("proxy", "kill"): ("proxy", "kill-pure"),
}

BTCLI_STAKE_COMMANDS_WITH_FLAG_NORMALIZATION = {
    "add",
    "remove",
    "move",
    "swap",
    "set-auto",
    "set-claim",
    "process-claim",
    "transfer",
    "transfer-stake",
    "wizard",
}

BTCLI_STAKE_SET_AUTO_UNSUPPORTED_FLAGS = {
    "--proxy",
    "--announce-only",
    "--no-announce-only",
    "--no",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
    "--quiet",
}

BTCLI_STAKE_SET_AUTO_UNSUPPORTED_FLAG_HELP: dict[str, str] = {
    "--proxy": "agcli does not expose btcli's proxy execution path on this compatibility surface.",
    "--announce-only": "agcli does not expose btcli's announce-only auto-stake flow on this compatibility surface.",
    "--no-announce-only": "agcli does not expose btcli's announce-only auto-stake flow on this compatibility surface.",
    "--no": "agcli does not expose btcli's automatic decline flag on this compatibility surface.",
    "--wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--quiet": "agcli does not expose btcli's quiet-mode toggle on this compatibility surface.",
}

BTCLI_STAKE_AUTO_EMPTY_OUTPUT_PREFIX = "No auto-stake destinations set for "

BTCLI_STAKE_ADD_UNSUPPORTED_FLAG_HELP: dict[str, str] = {
    "--all-tokens": "agcli stake add requires an explicit --amount on this compatibility surface.",
    "--all": "agcli stake add requires an explicit --amount on this compatibility surface.",
    "--include-hotkeys": "agcli stake add targets a single hotkey/address per invocation on this compatibility surface.",
    "--exclude-hotkeys": "agcli stake add targets a single hotkey/address per invocation on this compatibility surface.",
    "--all-hotkeys": "agcli stake add targets a single hotkey/address per invocation on this compatibility surface.",
    "--netuids": "agcli stake add requires a single --netuid on this compatibility surface.",
    "--all-netuids": "agcli stake add requires a single --netuid on this compatibility surface.",
    "--proxy": "agcli does not expose btcli's proxy execution path on this compatibility surface.",
    "--announce-only": "agcli does not expose btcli's announce-only staking flow on this compatibility surface.",
    "--tolerance": "agcli does not expose btcli's safe-staking tolerance controls on this compatibility surface.",
    "--safe-staking": "agcli does not expose btcli's safe-staking mode toggles on this compatibility surface.",
    "--allow-partial-stake": "agcli does not expose btcli's partial-stake toggles on this compatibility surface.",
    "--mev-protection": "agcli only exposes native `--mev` transport wrapping, not btcli stake-add MEV-protection toggles.",
    "--no": "agcli does not expose btcli's automatic decline flag on this compatibility surface.",
    "--quiet": "agcli does not expose btcli's quiet-mode toggle on this compatibility surface.",
    "--verbose": "agcli does not expose btcli's verbose-mode toggle on this compatibility surface.",
}

BTCLI_STAKE_REMOVE_UNSUPPORTED_FLAG_HELP: dict[str, str] = {
    "--all-netuids": "agcli stake remove requires a single --netuid on this compatibility surface.",
    "--unstake-all": "use native `taocli stake unstake-all` or btcli for all-subnet hotkey unstaking.",
    "--unstake-all-alpha": "use native `taocli stake unstake-all-alpha` or btcli for all-alpha unstaking.",
    "--include-hotkeys": "agcli stake remove targets a single hotkey/address per invocation on this compatibility surface.",
    "--exclude-hotkeys": "agcli stake remove targets a single hotkey/address per invocation on this compatibility surface.",
    "--all-hotkeys": "agcli stake remove targets a single hotkey/address per invocation on this compatibility surface.",
    "--proxy": "agcli does not expose btcli's proxy execution path on this compatibility surface.",
    "--announce-only": "agcli does not expose btcli's announce-only unstaking flow on this compatibility surface.",
    "--tolerance": "agcli does not expose btcli's safe-staking tolerance controls on this compatibility surface.",
    "--safe-staking": "agcli does not expose btcli's safe-staking mode toggles on this compatibility surface.",
    "--allow-partial-stake": "agcli does not expose btcli's partial-stake toggles on this compatibility surface.",
    "--interactive": "agcli does not expose btcli's interactive unstake selector on this compatibility surface.",
    "--mev-protection": "agcli only exposes native `--mev` transport wrapping, not btcli stake-remove MEV-protection toggles.",
    "--no": "agcli does not expose btcli's automatic decline flag on this compatibility surface.",
    "--quiet": "agcli does not expose btcli's quiet-mode toggle on this compatibility surface.",
    "--verbose": "agcli does not expose btcli's verbose-mode toggle on this compatibility surface.",
}

BTCLI_STAKE_SWAP_UNSUPPORTED_FLAGS = {
    "--swap-all",
    "--all",
    "--tolerance",
    "--rate-tolerance",
    "--safe-staking",
    "--no-safe-staking",
    "--unsafe",
    "--allow-partial-stake",
    "--no-allow-partial-stake",
    "--announce-only",
    "--no-announce-only",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
    "--quiet",
}

BTCLI_STAKE_SWAP_UNSUPPORTED_FLAG_HELP: dict[str, str] = {
    "--swap-all": "agcli requires an explicit --amount on `stake swap`.",
    "--all": "agcli requires an explicit --amount on `stake swap`.",
    "--tolerance": "agcli does not expose btcli's safe-staking tolerance controls on this path.",
    "--rate-tolerance": "agcli does not expose btcli's safe-staking tolerance controls on this path.",
    "--safe-staking": "agcli does not expose btcli's safe-staking mode toggles on this path.",
    "--no-safe-staking": "agcli does not expose btcli's safe-staking mode toggles on this path.",
    "--unsafe": "agcli does not expose btcli's safe-staking mode toggles on this path.",
    "--allow-partial-stake": "agcli does not expose btcli's partial-stake toggles on this path.",
    "--no-allow-partial-stake": "agcli does not expose btcli's partial-stake toggles on this path.",
    "--announce-only": "agcli does not expose btcli's proxy announce-only flow on this path.",
    "--no-announce-only": "agcli does not expose btcli's proxy announce-only flow on this path.",
    "--wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this path.",
    "--no-wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this path.",
    "--wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this path.",
    "--no-wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this path.",
    "--quiet": "agcli does not expose btcli's quiet-mode toggle on this path.",
}

BTCLI_STAKE_CHILD_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `stake child` is only partially implemented in taocli/agcli yet; "
    "taocli currently maps `stake child set` onto `stake set-children` and the mutating "
    "`stake child take --take ...` path onto `stake childkey-take`, while btcli-only read/revoke "
    "flows still require btcli."
)

BTCLI_STAKE_CHILD_GET_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `stake child get` is not implemented in taocli/agcli yet; "
    "agcli on this host has no matching child-hotkey read command."
)

BTCLI_STAKE_CHILD_REVOKE_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `stake child revoke` is not implemented in taocli/agcli yet; "
    "agcli on this host has no matching child-hotkey revoke command."
)

BTCLI_STAKE_CHILD_TAKE_READ_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `stake child take` read mode is not implemented in taocli/agcli yet; "
    "agcli only exposes the mutating `stake childkey-take --take ...` surface, not btcli's current-take read path."
)

BTCLI_STAKE_CHILD_SET_UNSUPPORTED_FLAG_HELP: dict[str, str] = {
    "--all-netuids": "agcli stake set-children requires a single --netuid on this compatibility surface.",
    "--all": "agcli stake set-children requires a single --netuid on this compatibility surface.",
    "--allnetuids": "agcli stake set-children requires a single --netuid on this compatibility surface.",
    "--proxy": "agcli does not expose btcli's proxy execution path on this compatibility surface.",
    "--announce-only": "agcli does not expose btcli's announce-only child-setting flow on this compatibility surface.",
    "--no-announce-only": "agcli does not expose btcli's announce-only child-setting flow on this compatibility surface.",
    "--wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--quiet": "agcli does not expose btcli's quiet-mode toggle on this compatibility surface.",
    "--verbose": "agcli does not expose btcli's verbose-mode toggle on this compatibility surface.",
}

BTCLI_STAKE_CHILD_TAKE_UNSUPPORTED_FLAG_HELP: dict[str, str] = {
    "--all-netuids": "agcli stake childkey-take requires a single --netuid on this compatibility surface.",
    "--all": "agcli stake childkey-take requires a single --netuid on this compatibility surface.",
    "--allnetuids": "agcli stake childkey-take requires a single --netuid on this compatibility surface.",
    "--proxy": "agcli does not expose btcli's proxy execution path on this compatibility surface.",
    "--announce-only": "agcli does not expose btcli's announce-only child-take flow on this compatibility surface.",
    "--no-announce-only": "agcli does not expose btcli's announce-only child-take flow on this compatibility surface.",
    "--wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--quiet": "agcli does not expose btcli's quiet-mode toggle on this compatibility surface.",
    "--verbose": "agcli does not expose btcli's verbose-mode toggle on this compatibility surface.",
}

BTCLI_STAKE_CHILD_SET_CHILDREN_REQUIRED_MESSAGE = (
    "btcli-compatible `stake child set` requires the same number of --children and --proportions values."
)

BTCLI_STAKE_CHILD_SET_PROPORTIONS_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `stake child set` interactive proportion prompting is not implemented in taocli/agcli yet; "
    "pass one --proportions value per child."
)

BTCLI_STAKE_CHILD_SET_CHILDREN_PROMPT_ABORT = "Enter the child hotkeys (ss58), comma-separated for multiple: \nAborted.\n"
BTCLI_STAKE_CHILD_SET_NETUID_PROMPT_ABORT = "Enter the netuid to use. Leave blank for all netuids: \nAborted.\n"
BTCLI_STAKE_CHILD_SET_WALLET_PROMPT_ABORT = (
    "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
    "Aborted.\n"
)
BTCLI_STAKE_CHILD_SET_PROPORTIONS_PROMPT_ABORT = (
    "Enter comma-separated proportions equal to the number of children (sum not exceeding a total of 1.0): \n"
    "Aborted.\n"
)
BTCLI_STAKE_CHILD_TAKE_WALLET_PROMPT_ABORT = (
    "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
    "Aborted.\n"
)

BTCLI_PROXY_TYPE_ALIASES: dict[str, str] = {
    "Any": "any",
    "Owner": "owner",
    "NonCritical": "non_critical",
    "NonTransfer": "non_transfer",
    "Senate": "senate",
    "Governance": "governance",
    "Staking": "staking",
    "Registration": "registration",
    "Transfer": "transfer",
    "SmallTransfer": "small_transfer",
    "RootWeights": "root_weights",
    "ChildKeys": "child_keys",
    "SwapHotkey": "swap_hotkey",
    "SubnetLeaseBeneficiary": "subnet_lease_beneficiary",
    "RootClaim": "root_claim",
}

BTCLI_PROXY_UNSUPPORTED_PROXY_TYPES = {
    "NonFungible",
    "Triumvirate",
    "SudoUncheckedSetCode",
}

BTCLI_PROXY_UNSUPPORTED_FLAGS = {
    "--no",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
}

BTCLI_PROXY_KILL_UNSUPPORTED_FLAGS = {
    "--announce-only",
    "--no-announce-only",
}

BTCLI_PROXY_VALUE_ALIASES: dict[str, str] = {
    "--wallet-name": "--wallet",
    "--wallet-path": "--wallet-dir",
    "--hotkey": "--hotkey-name",
    "--json-output": "--output",
    "--period": "--mortality-blocks",
    "--era": "--mortality-blocks",
}

BTCLI_PROXY_REMOVE_ALL_INCOMPATIBLE_FLAGS = {
    "--delegate",
    "--proxy-type",
    "--delay",
}

BTCLI_PROXY_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--period",
    "--era",
    "--no",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
    "--announce-only",
    "--no-announce-only",
    "--all",
}

BTCLI_PROXY_SUPPORTED_COMMANDS = {
    ("proxy", "create-pure"),
    ("proxy", "add"),
    ("proxy", "remove"),
    ("proxy", "remove-all"),
    ("proxy", "kill-pure"),
}

BTCLI_PROXY_REWRITE_LABELS: dict[tuple[str, ...], str] = {
    ("proxy", "create-pure"): "proxy create",
    ("proxy", "add"): "proxy add",
    ("proxy", "remove"): "proxy remove",
    ("proxy", "remove-all"): "proxy remove --all",
    ("proxy", "kill-pure"): "proxy kill",
}

BTCLI_PROXY_UNSUPPORTED_FLAG_HELP: dict[str, str] = {
    "--no": "taocli/agcli does not expose btcli's automatic decline flag on this compatibility surface.",
    "--wait-for-inclusion": (
        "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface."
    ),
    "--no-wait-for-inclusion": (
        "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface."
    ),
    "--wait-for-finalization": (
        "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface."
    ),
    "--no-wait-for-finalization": (
        "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface."
    ),
    "--announce-only": (
        "taocli/agcli does not expose btcli pure-proxy announce-only execution on this compatibility surface."
    ),
    "--no-announce-only": (
        "taocli/agcli does not expose btcli pure-proxy announce-only execution on this compatibility surface."
    ),
}

BTCLI_PROXY_REMOVE_ALL_MESSAGE = (
    "btcli-compatible `proxy remove --all` does not accept --delegate, --proxy-type, or --delay "
    "on the taocli/agcli surface."
)

BTCLI_PROXY_FLAG_ERROR_TEMPLATE = (
    "btcli-compatible {label} flag '{flag}' is not implemented in taocli yet: {detail}"
)

BTCLI_PROXY_UNSUPPORTED_DEFAULT_DETAIL = "not implemented in taocli/agcli yet."

BTCLI_PROXY_WAIT_FLAG_MESSAGE = "taocli/agcli does not expose btcli wait/finalization toggles on this surface."

BTCLI_PROXY_ANNOUNCE_ONLY_MESSAGE = (
    "taocli/agcli does not expose btcli pure-proxy announce-only execution on this compatibility surface."
)

BTCLI_PROXY_UNSUPPORTED_PROXY_TYPE_TEMPLATE = (
    "btcli-compatible proxy type '{proxy_type}' is not implemented in taocli/agcli yet."
)

BTCLI_PROXY_EXECUTE_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `proxy execute` is not implemented in taocli/agcli yet; "
    "agcli requires explicit pallet/call details rather than btcli call-hash/call-hex execution."
)

BTCLI_LIQUIDITY_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `liquidity list` is not implemented in taocli/agcli yet; "
    "agcli exposes add/remove/modify/toggle but not a matching liquidity list command."
)

BTCLI_LIQUIDITY_COMMANDS = {
    ("liquidity", "add"),
    ("liquidity", "remove"),
    ("liquidity", "modify"),
}

BTCLI_LIQUIDITY_UNSUPPORTED_FLAGS = {
    "--proxy",
    "--announce-only",
    "--no-announce-only",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
    "--quiet",
}

BTCLI_LIQUIDITY_REMOVE_UNSUPPORTED_FLAGS = {
    "--all",
}

BTCLI_LIQUIDITY_FLAG_HELP: dict[str, str] = {
    "--proxy": "agcli does not expose btcli's proxy execution path on this compatibility surface.",
    "--announce-only": "agcli does not expose btcli's announce-only liquidity flow on this compatibility surface.",
    "--no-announce-only": "agcli does not expose btcli's announce-only liquidity flow on this compatibility surface.",
    "--wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "agcli does not expose btcli's wait/finalization toggles on this compatibility surface.",
    "--quiet": "agcli does not expose btcli's quiet-mode toggle on this compatibility surface.",
    "--all": "agcli requires an explicit --position-id on `liquidity remove`.",
}

BTCLI_PROXY_OUTPUT_ALIASES: dict[str, Sequence[str]] = {
    "--json-output": ("--output", "json"),
}

BTCLI_SUBNET_REGISTER_UNSUPPORTED_FLAGS = {
    "--announce-only",
    "--no-announce-only",
}

BTCLI_SUBNET_POW_UNSUPPORTED_FLAGS = {
    "--update-interval",
    "-u",
    "--output-in-place",
    "--no-output-in-place",
    "--use-cuda",
    "--cuda",
    "--no-use-cuda",
    "--no-cuda",
    "--dev-id",
    "-d",
    "--threads-per-block",
    "-tbp",
}

BTCLI_SUBNET_POW_VALUE_ALIASES: dict[str, str] = {
    "--processors": "--threads",
}

BTCLI_SUBNET_REGISTER_VALUE_ALIASES: dict[str, str] = {
    "--period": "--mortality-blocks",
    "--era": "--mortality-blocks",
}

BTCLI_SUBNET_REGISTRATION_COMMANDS = {
    ("subnet", "register-neuron"),
    ("subnet", "pow"),
}

BTCLI_SUBNET_REGISTRATION_UNSUPPORTED_FLAGS: dict[tuple[str, ...], set[str]] = {
    ("subnet", "register-neuron"): BTCLI_SUBNET_REGISTER_UNSUPPORTED_FLAGS,
    ("subnet", "pow"): BTCLI_SUBNET_POW_UNSUPPORTED_FLAGS,
}

BTCLI_SUBNET_REGISTRATION_VALUE_ALIASES: dict[tuple[str, ...], dict[str, str]] = {
    ("subnet", "register-neuron"): BTCLI_SUBNET_REGISTER_VALUE_ALIASES,
    ("subnet", "pow"): BTCLI_SUBNET_POW_VALUE_ALIASES,
}

BTCLI_SUBNET_REGISTRATION_FLAG_LABELS: dict[tuple[str, ...], str] = {
    ("subnet", "register-neuron"): "subnets register",
    ("subnet", "pow"): "subnets pow-register",
}

BTCLI_SUBNET_REGISTRATION_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--period",
    "--era",
    "--announce-only",
    "--no-announce-only",
    "--processors",
    "--update-interval",
    "-u",
    "--output-in-place",
    "--no-output-in-place",
    "--use-cuda",
    "--cuda",
    "--no-use-cuda",
    "--no-cuda",
    "--dev-id",
    "-d",
    "--threads-per-block",
    "-tbp",
}

BTCLI_SUBNET_POW_FLAG_ONLY_VALUES = {
    "--cuda",
    "--use-cuda",
    "--no-cuda",
    "--no-use-cuda",
    "--output-in-place",
    "--no-output-in-place",
}

BTCLI_SUBNET_REGISTER_FLAG_ONLY_VALUES = {
    "--announce-only",
    "--no-announce-only",
}

BTCLI_SUBNET_REGISTRATION_FLAG_ONLY_VALUES: dict[tuple[str, ...], set[str]] = {
    ("subnet", "register-neuron"): BTCLI_SUBNET_REGISTER_FLAG_ONLY_VALUES,
    ("subnet", "pow"): BTCLI_SUBNET_POW_FLAG_ONLY_VALUES,
}

BTCLI_SUBNET_REGISTRATION_VALUE_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--period",
    "--era",
    "--processors",
    "--update-interval",
    "--dev-id",
    "--threads-per-block",
    "-u",
    "-d",
    "-tbp",
}

BTCLI_SUBNET_REGISTRATION_HELP: dict[tuple[str, ...], dict[str, str]] = {
    ("subnet", "register-neuron"): {
        "--announce-only": (
            "taocli/agcli does not support btcli announce-only proxy registration; "
            "run the registration directly instead."
        ),
        "--no-announce-only": "taocli/agcli does not expose btcli announce-only proxy registration toggles.",
    },
    ("subnet", "pow"): {
        "--update-interval": (
            "taocli/agcli does not expose btcli POW update-interval tuning; "
            "use agcli's native `subnet pow --threads ...` surface."
        ),
        "-u": (
            "taocli/agcli does not expose btcli POW update-interval tuning; "
            "use agcli's native `subnet pow --threads ...` surface."
        ),
        "--output-in-place": "taocli/agcli does not expose btcli POW in-place output toggles.",
        "--no-output-in-place": "taocli/agcli does not expose btcli POW in-place output toggles.",
        "--use-cuda": "taocli/agcli does not expose btcli CUDA POW flags on this compatibility surface.",
        "--cuda": "taocli/agcli does not expose btcli CUDA POW flags on this compatibility surface.",
        "--no-use-cuda": "taocli/agcli does not expose btcli CUDA POW flags on this compatibility surface.",
        "--no-cuda": "taocli/agcli does not expose btcli CUDA POW flags on this compatibility surface.",
        "--dev-id": "taocli/agcli does not expose btcli CUDA device selection flags on this compatibility surface.",
        "-d": "taocli/agcli does not expose btcli CUDA device selection flags on this compatibility surface.",
        "--threads-per-block": (
            "taocli/agcli does not expose btcli CUDA threads-per-block flags "
            "on this compatibility surface."
        ),
        "-tbp": "taocli/agcli does not expose btcli CUDA threads-per-block flags on this compatibility surface.",
    },
}

BTCLI_SUBNET_SET_SYMBOL_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--proxy": "agcli does not expose btcli proxy execution on this compatibility surface.",
    "--announce-only": "agcli does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--quiet": "agcli does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--verbose": "agcli does not expose btcli verbose-mode output expansion on this compatibility surface.",
    "--no": "agcli does not expose btcli automatic-decline prompts on this compatibility surface.",
}

BTCLI_SUBNET_SHOW_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--mechid": "agcli subnet show does not expose btcli mechanism-id filtering on this compatibility surface.",
    "--sort": "agcli subnet show does not expose btcli sorting controls on this compatibility surface.",
}

BTCLI_SUBNET_CHECK_START_UNSUPPORTED_FLAGS: dict[str, str] = {}
BTCLI_SUBNET_CREATE_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--announce-only": "agcli does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--logo-url": "agcli subnet register-with-identity does not expose btcli logo URL metadata on this compatibility surface.",
    "--mev-protection": "agcli only exposes native `--mev` transport wrapping, not btcli subnet create MEV-protection toggles.",
    "--no-mev-protection": "agcli only exposes native `--mev` transport wrapping, not btcli subnet create MEV-protection toggles.",
    "--quiet": "agcli does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--verbose": "agcli does not expose btcli verbose-mode output expansion on this compatibility surface.",
    "--no": "agcli does not expose btcli automatic-decline prompts on this compatibility surface.",
}
BTCLI_SUBNET_SET_IDENTITY_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--announce-only": "agcli identity set-subnet does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli identity set-subnet does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--subnet-contact": "agcli identity set-subnet does not expose btcli subnet-contact metadata on this compatibility surface.",
    "--discord-handle": "agcli identity set-subnet does not expose btcli Discord metadata on this compatibility surface.",
    "--description": "agcli identity set-subnet does not expose btcli description metadata on this compatibility surface.",
    "--logo-url": "agcli identity set-subnet does not expose btcli logo URL metadata on this compatibility surface.",
    "--additional-info": "agcli identity set-subnet does not expose btcli additional-info metadata on this compatibility surface.",
    "--quiet": "agcli does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--verbose": "agcli does not expose btcli verbose-mode output expansion on this compatibility surface.",
    "--no": "agcli does not expose btcli automatic-decline prompts on this compatibility surface.",
}
BTCLI_SUBNET_START_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--announce-only": "agcli does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--quiet": "agcli does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--no": "agcli does not expose btcli automatic-decline prompts on this compatibility surface.",
}
BTCLI_SUBNET_MECHANISM_COUNT_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--quiet": "agcli subnet mechanism-count does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--verbose": "agcli subnet mechanism-count does not expose btcli verbose-mode output expansion on this compatibility surface.",
}
BTCLI_SUBNET_MECHANISM_SET_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--proxy": "agcli subnet set-mechanism-count does not expose btcli proxy execution on this compatibility surface.",
    "--announce-only": "agcli subnet set-mechanism-count does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli subnet set-mechanism-count does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--wait-for-inclusion": "agcli subnet set-mechanism-count does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "agcli subnet set-mechanism-count does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--wait-for-finalization": "agcli subnet set-mechanism-count does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "agcli subnet set-mechanism-count does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--quiet": "agcli subnet set-mechanism-count does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--verbose": "agcli subnet set-mechanism-count does not expose btcli verbose-mode output expansion on this compatibility surface.",
    "--no": "agcli subnet set-mechanism-count does not expose btcli automatic-decline prompts on this compatibility surface.",
}
BTCLI_SUBNET_MECHANISM_EMISSIONS_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--quiet": "agcli subnet emission-split does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--verbose": "agcli subnet emission-split does not expose btcli verbose-mode output expansion on this compatibility surface.",
}
BTCLI_SUBNET_MECHANISM_SPLIT_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--proxy": "agcli subnet set-emission-split does not expose btcli proxy execution on this compatibility surface.",
    "--announce-only": "agcli subnet set-emission-split does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli subnet set-emission-split does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--wait-for-inclusion": "agcli subnet set-emission-split does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "agcli subnet set-emission-split does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--wait-for-finalization": "agcli subnet set-emission-split does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "agcli subnet set-emission-split does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--quiet": "agcli subnet set-emission-split does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--verbose": "agcli subnet set-emission-split does not expose btcli verbose-mode output expansion on this compatibility surface.",
    "--no": "agcli subnet set-emission-split does not expose btcli automatic-decline prompts on this compatibility surface.",
}

BTCLI_SUBNET_SET_SYMBOL_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--proxy",
    "--announce-only",
    "--no-announce-only",
    "--quiet",
    "--verbose",
    "--no",
}

BTCLI_SUBNET_SHOW_BTCLI_FLAGS = {
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--mechid",
    "--sort",
}

BTCLI_SUBNET_CHECK_START_BTCLI_FLAGS = {
    "--json-output",
    "--no-prompt",
    "--prompt",
}

BTCLI_SUBNET_CREATE_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--proxy",
    "--subnet-name",
    "--github-repo",
    "--repo",
    "--subnet-contact",
    "--subnet-url",
    "--url",
    "--discord-handle",
    "--description",
    "--logo-url",
    "--additional-info",
    "--mev-protection",
    "--no-mev-protection",
    "--announce-only",
    "--no-announce-only",
    "--quiet",
    "--verbose",
    "--no",
}

BTCLI_SUBNET_SET_IDENTITY_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--proxy",
    "--subnet-name",
    "--github-repo",
    "--repo",
    "--subnet-contact",
    "--subnet-url",
    "--url",
    "--discord-handle",
    "--description",
    "--logo-url",
    "--additional-info",
    "--announce-only",
    "--no-announce-only",
    "--quiet",
    "--verbose",
    "--no",
}

BTCLI_SUBNET_START_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--proxy",
    "--announce-only",
    "--no-announce-only",
    "--quiet",
    "--verbose",
    "--no",
}
BTCLI_SUBNET_MECHANISM_COUNT_BTCLI_FLAGS = {
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--quiet",
    "--verbose",
}
BTCLI_SUBNET_MECHANISM_SET_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--count",
    "--mech-count",
    "--proxy",
    "--announce-only",
    "--no-announce-only",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
    "--quiet",
    "--verbose",
    "--no",
}
BTCLI_SUBNET_MECHANISM_EMISSIONS_BTCLI_FLAGS = {
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--quiet",
    "--verbose",
}
BTCLI_SUBNET_MECHANISM_SPLIT_BTCLI_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--split",
    "--proxy",
    "--announce-only",
    "--no-announce-only",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
    "--quiet",
    "--verbose",
    "--no",
}

BTCLI_SUBNET_SET_SYMBOL_POSITIONAL_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--output",
    "--symbol",
    "--netuid",
    "--endpoint",
    "--network",
}

BTCLI_SUBNET_SHOW_POSITIONAL_FLAGS = {
    "--output",
    "--netuid",
    "--endpoint",
    "--network",
    "--mechid",
    "--sort",
}

BTCLI_SUBNET_CHECK_START_POSITIONAL_FLAGS = {
    "--output",
    "--netuid",
    "--endpoint",
    "--network",
}

BTCLI_SUBNET_CREATE_POSITIONAL_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--output",
    "--endpoint",
    "--network",
    "--proxy",
    "--subnet-name",
    "--github-repo",
    "--repo",
    "--subnet-contact",
    "--subnet-url",
    "--url",
    "--discord-handle",
    "--description",
    "--logo-url",
    "--additional-info",
}

BTCLI_SUBNET_START_POSITIONAL_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--output",
    "--netuid",
    "--endpoint",
    "--network",
    "--proxy",
}
BTCLI_SUBNET_MECHANISM_COUNT_POSITIONAL_FLAGS = {
    "--output",
    "--netuid",
    "--endpoint",
    "--network",
}
BTCLI_SUBNET_MECHANISM_SET_POSITIONAL_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--output",
    "--netuid",
    "--endpoint",
    "--network",
    "--count",
    "--mech-count",
    "--proxy",
}
BTCLI_SUBNET_MECHANISM_EMISSIONS_POSITIONAL_FLAGS = {
    "--output",
    "--netuid",
    "--endpoint",
    "--network",
}
BTCLI_SUBNET_BURN_COST_POSITIONAL_FLAGS = {
    "--output",
    "--endpoint",
    "--network",
}
BTCLI_SUBNET_MECHANISM_SPLIT_POSITIONAL_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--output",
    "--netuid",
    "--endpoint",
    "--network",
    "--split",
    "--proxy",
}

BTCLI_SUBNET_FLAG_ONLY_VALUES = {
    "--json-output",
    "--no-prompt",
    "--prompt",
    "--announce-only",
    "--no-announce-only",
    "--quiet",
    "--verbose",
    "--no",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
}

BTCLI_SUBNET_FLAG_ERROR_TEMPLATE = (
    "btcli-compatible {label} flag '{flag}' is not implemented in taocli yet: {detail}"
)

BTCLI_SUBNET_SYMBOL_REQUIRED_MESSAGE = "btcli-compatible `subnets set-symbol` requires a subnet symbol."

BTCLI_SUBNET_SYMBOL_DUPLICATE_MESSAGE = (
    "btcli-compatible `subnets set-symbol` accepts a single symbol value; pass it either positionally or via --symbol."
)

BTCLI_SUBNET_SHOW_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets show` flag '{flag}' requires a value."
BTCLI_SUBNET_CHECK_START_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets check-start` flag '{flag}' requires a value."
BTCLI_SUBNET_CREATE_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets create` flag '{flag}' requires a value."
BTCLI_SUBNET_SET_IDENTITY_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets set-identity` flag '{flag}' requires a value."
BTCLI_SUBNET_SET_SYMBOL_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets set-symbol` flag '{flag}' requires a value."
BTCLI_SUBNET_START_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets start` flag '{flag}' requires a value."
BTCLI_SUBNET_MECHANISM_COUNT_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets mechanisms count` flag '{flag}' requires a value."
BTCLI_SUBNET_MECHANISM_SET_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets mechanisms set` flag '{flag}' requires a value."
BTCLI_SUBNET_MECHANISM_EMISSIONS_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets mechanisms emissions` flag '{flag}' requires a value."
BTCLI_SUBNET_MECHANISM_SPLIT_FLAG_VALUE_MESSAGE = "btcli-compatible `subnets mechanisms split-emissions` flag '{flag}' requires a value."

BTCLI_SUBNET_CREATE_REQUIRED_MESSAGE = "btcli-compatible `subnets create` requires --subnet-name."
BTCLI_SUBNET_SET_IDENTITY_JSON_PROMPT_CONFLICT_MESSAGE = "Invalid value: Cannot specify both '--json-output' and '--prompt'"
BTCLI_SUBNET_CREATE_JSON_PROMPT_CONFLICT_MESSAGE = "Invalid value: Cannot specify both '--json-output' and '--prompt'"

BTCLI_SUBNET_SET_SYMBOL_NATIVE_COMMAND = ["subnet", "set-symbol"]
BTCLI_SUBNET_SET_IDENTITY_NATIVE_COMMAND = ["identity", "set-subnet"]
BTCLI_SUBNET_LIST_NATIVE_COMMAND = ["subnet", "list"]
BTCLI_SUBNET_SHOW_NATIVE_COMMAND = ["subnet", "show"]
BTCLI_SUBNET_CHECK_START_NATIVE_COMMAND = ["subnet", "check-start"]
BTCLI_SUBNET_CREATE_NATIVE_COMMAND = ["subnet", "register-with-identity"]
BTCLI_SUBNET_START_NATIVE_COMMAND = ["subnet", "start"]
BTCLI_SUBNET_MECHANISM_COUNT_NATIVE_COMMAND = ["subnet", "mechanism-count"]
BTCLI_SUBNET_MECHANISM_SET_NATIVE_COMMAND = ["subnet", "set-mechanism-count"]
BTCLI_SUBNET_MECHANISM_EMISSIONS_NATIVE_COMMAND = ["subnet", "emission-split"]
BTCLI_SUBNET_MECHANISM_SPLIT_NATIVE_COMMAND = ["subnet", "set-emission-split"]
BTCLI_SUBNET_BURN_COST_NATIVE_COMMAND = ["subnet", "create-cost"]

BTCLI_SUBNET_SHOW_VALUE_FLAGS = {"--mechid", "--sort"}
BTCLI_SUBNET_CHECK_START_VALUE_FLAGS: set[str] = set()
BTCLI_SUBNET_CREATE_VALUE_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--proxy",
    "--subnet-name",
    "--github-repo",
    "--repo",
    "--subnet-contact",
    "--subnet-url",
    "--url",
    "--discord-handle",
    "--description",
    "--logo-url",
    "--additional-info",
}
BTCLI_SUBNET_SET_SYMBOL_VALUE_FLAGS = {"--wallet-name", "--wallet-path", "--hotkey"}
BTCLI_SUBNET_SET_IDENTITY_VALUE_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--proxy",
    "--subnet-name",
    "--github-repo",
    "--repo",
    "--subnet-contact",
    "--subnet-url",
    "--url",
    "--discord-handle",
    "--description",
    "--logo-url",
    "--additional-info",
}
BTCLI_SUBNET_START_VALUE_FLAGS = {"--wallet-name", "--wallet-path", "--hotkey", "--proxy"}
BTCLI_SUBNET_MECHANISM_COUNT_VALUE_FLAGS: set[str] = set()
BTCLI_SUBNET_MECHANISM_SET_VALUE_FLAGS = {
    "--wallet-name",
    "--wallet-path",
    "--hotkey",
    "--count",
    "--mech-count",
    "--proxy",
}
BTCLI_SUBNET_MECHANISM_EMISSIONS_VALUE_FLAGS: set[str] = set()
BTCLI_SUBNET_MECHANISM_SPLIT_VALUE_FLAGS = {"--wallet-name", "--wallet-path", "--hotkey", "--split", "--proxy"}

BTCLI_SUBNET_LIST_LABEL = "subnets list"
BTCLI_SUBNET_SHOW_LABEL = "subnets show"
BTCLI_SUBNET_CHECK_START_LABEL = "subnets check-start"
BTCLI_SUBNET_CREATE_LABEL = "subnets create"
BTCLI_SUBNET_SET_IDENTITY_LABEL = "subnets set-identity"
BTCLI_SUBNET_SET_SYMBOL_LABEL = "subnets set-symbol"
BTCLI_SUBNET_START_LABEL = "subnets start"
BTCLI_SUBNET_MECHANISM_COUNT_LABEL = "subnets mechanisms count"
BTCLI_SUBNET_MECHANISM_SET_LABEL = "subnets mechanisms set"
BTCLI_SUBNET_MECHANISM_EMISSIONS_LABEL = "subnets mechanisms emissions"
BTCLI_SUBNET_MECHANISM_SPLIT_LABEL = "subnets mechanisms split-emissions"
BTCLI_SUBNET_BURN_COST_LABEL = "subnets burn-cost"

BTCLI_SUBNET_SHOW_COMMANDS = {("subnet", "show")}
BTCLI_SUBNET_CHECK_START_COMMANDS = {("subnet", "check-start")}
BTCLI_SUBNET_CREATE_COMMANDS = {("subnet", "register-with-identity")}
BTCLI_SUBNET_SET_SYMBOL_COMMANDS = {("subnet", "set-symbol")}
BTCLI_SUBNET_START_COMMANDS = {("subnet", "start")}
BTCLI_SUBNET_MECHANISM_COUNT_COMMANDS = {("subnet", "mechanism-count")}
BTCLI_SUBNET_MECHANISM_SET_COMMANDS = {("subnet", "set-mechanism-count")}
BTCLI_SUBNET_MECHANISM_EMISSIONS_COMMANDS = {("subnet", "emission-split")}
BTCLI_SUBNET_MECHANISM_SPLIT_COMMANDS = {("subnet", "set-emission-split")}
BTCLI_SUBNET_BURN_COST_COMMANDS = {("subnet", "create-cost")}

BTCLI_SUBNET_SET_IDENTITY_COMMANDS = {("identity", "set-subnet")}

BTCLI_SUBNET_COMPAT_COMMANDS = (
    BTCLI_SUBNET_SHOW_COMMANDS
    | BTCLI_SUBNET_CHECK_START_COMMANDS
    | BTCLI_SUBNET_CREATE_COMMANDS
    | BTCLI_SUBNET_SET_IDENTITY_COMMANDS
    | BTCLI_SUBNET_SET_SYMBOL_COMMANDS
    | BTCLI_SUBNET_START_COMMANDS
    | BTCLI_SUBNET_MECHANISM_COUNT_COMMANDS
    | BTCLI_SUBNET_MECHANISM_SET_COMMANDS
    | BTCLI_SUBNET_MECHANISM_EMISSIONS_COMMANDS
    | BTCLI_SUBNET_MECHANISM_SPLIT_COMMANDS
    | BTCLI_SUBNET_BURN_COST_COMMANDS
)

BTCLI_SUBNET_COMPAT_BTCLI_FLAGS = (
    BTCLI_SUBNET_SET_SYMBOL_BTCLI_FLAGS
    | BTCLI_SUBNET_SHOW_BTCLI_FLAGS
    | BTCLI_SUBNET_CHECK_START_BTCLI_FLAGS
    | BTCLI_SUBNET_CREATE_BTCLI_FLAGS
    | BTCLI_SUBNET_SET_IDENTITY_BTCLI_FLAGS
    | BTCLI_SUBNET_START_BTCLI_FLAGS
    | BTCLI_SUBNET_MECHANISM_COUNT_BTCLI_FLAGS
    | BTCLI_SUBNET_MECHANISM_SET_BTCLI_FLAGS
    | BTCLI_SUBNET_MECHANISM_EMISSIONS_BTCLI_FLAGS
    | BTCLI_SUBNET_MECHANISM_SPLIT_BTCLI_FLAGS
)

BTCLI_SUBNET_COMPAT_POSITIONAL_FLAGS = (
    BTCLI_SUBNET_SET_SYMBOL_POSITIONAL_FLAGS
    | BTCLI_SUBNET_SHOW_POSITIONAL_FLAGS
    | BTCLI_SUBNET_CHECK_START_POSITIONAL_FLAGS
    | BTCLI_SUBNET_CREATE_POSITIONAL_FLAGS
    | BTCLI_SUBNET_START_POSITIONAL_FLAGS
    | BTCLI_SUBNET_MECHANISM_COUNT_POSITIONAL_FLAGS
    | BTCLI_SUBNET_MECHANISM_SET_POSITIONAL_FLAGS
    | BTCLI_SUBNET_MECHANISM_EMISSIONS_POSITIONAL_FLAGS
    | BTCLI_SUBNET_MECHANISM_SPLIT_POSITIONAL_FLAGS
    | BTCLI_SUBNET_BURN_COST_POSITIONAL_FLAGS
)

BTCLI_SUBNET_COMPAT_VALUE_FLAGS = (
    BTCLI_SUBNET_SET_SYMBOL_VALUE_FLAGS
    | BTCLI_SUBNET_SHOW_VALUE_FLAGS
    | BTCLI_SUBNET_CREATE_VALUE_FLAGS
    | BTCLI_SUBNET_SET_IDENTITY_VALUE_FLAGS
    | BTCLI_SUBNET_START_VALUE_FLAGS
    | BTCLI_SUBNET_MECHANISM_SET_VALUE_FLAGS
    | BTCLI_SUBNET_MECHANISM_SPLIT_VALUE_FLAGS
)

BTCLI_SUBNET_COMPAT_FLAG_ONLY_VALUES = BTCLI_SUBNET_FLAG_ONLY_VALUES

BTCLI_SUBNET_COMPAT_UNSUPPORTED_FLAGS: dict[tuple[str, ...], dict[str, str]] = {
    ("subnet", "set-symbol"): BTCLI_SUBNET_SET_SYMBOL_UNSUPPORTED_FLAGS,
    ("subnet", "show"): BTCLI_SUBNET_SHOW_UNSUPPORTED_FLAGS,
    ("subnet", "check-start"): BTCLI_SUBNET_CHECK_START_UNSUPPORTED_FLAGS,
    ("subnet", "register-with-identity"): BTCLI_SUBNET_CREATE_UNSUPPORTED_FLAGS,
    ("identity", "set-subnet"): BTCLI_SUBNET_SET_IDENTITY_UNSUPPORTED_FLAGS,
    ("subnet", "start"): BTCLI_SUBNET_START_UNSUPPORTED_FLAGS,
    ("subnet", "mechanism-count"): BTCLI_SUBNET_MECHANISM_COUNT_UNSUPPORTED_FLAGS,
    ("subnet", "set-mechanism-count"): BTCLI_SUBNET_MECHANISM_SET_UNSUPPORTED_FLAGS,
    ("subnet", "emission-split"): BTCLI_SUBNET_MECHANISM_EMISSIONS_UNSUPPORTED_FLAGS,
    ("subnet", "set-emission-split"): BTCLI_SUBNET_MECHANISM_SPLIT_UNSUPPORTED_FLAGS,
}

BTCLI_SUBNET_COMPAT_LABELS: dict[tuple[str, ...], str] = {
    ("subnet", "list"): BTCLI_SUBNET_LIST_LABEL,
    ("subnet", "set-symbol"): BTCLI_SUBNET_SET_SYMBOL_LABEL,
    ("subnet", "show"): BTCLI_SUBNET_SHOW_LABEL,
    ("subnet", "check-start"): BTCLI_SUBNET_CHECK_START_LABEL,
    ("subnet", "register-with-identity"): BTCLI_SUBNET_CREATE_LABEL,
    ("identity", "set-subnet"): BTCLI_SUBNET_SET_IDENTITY_LABEL,
    ("subnet", "start"): BTCLI_SUBNET_START_LABEL,
    ("subnet", "mechanism-count"): BTCLI_SUBNET_MECHANISM_COUNT_LABEL,
    ("subnet", "set-mechanism-count"): BTCLI_SUBNET_MECHANISM_SET_LABEL,
    ("subnet", "emission-split"): BTCLI_SUBNET_MECHANISM_EMISSIONS_LABEL,
    ("subnet", "set-emission-split"): BTCLI_SUBNET_MECHANISM_SPLIT_LABEL,
    ("subnet", "create-cost"): BTCLI_SUBNET_BURN_COST_LABEL,
}

BTCLI_SUBNET_COMPAT_NATIVE_COMMANDS: dict[tuple[str, ...], list[str]] = {
    ("subnet", "list"): BTCLI_SUBNET_LIST_NATIVE_COMMAND,
    ("subnet", "set-symbol"): BTCLI_SUBNET_SET_SYMBOL_NATIVE_COMMAND,
    ("subnet", "show"): BTCLI_SUBNET_SHOW_NATIVE_COMMAND,
    ("subnet", "check-start"): BTCLI_SUBNET_CHECK_START_NATIVE_COMMAND,
    ("subnet", "register-with-identity"): BTCLI_SUBNET_CREATE_NATIVE_COMMAND,
    ("identity", "set-subnet"): BTCLI_SUBNET_SET_IDENTITY_NATIVE_COMMAND,
    ("subnet", "start"): BTCLI_SUBNET_START_NATIVE_COMMAND,
    ("subnet", "mechanism-count"): BTCLI_SUBNET_MECHANISM_COUNT_NATIVE_COMMAND,
    ("subnet", "set-mechanism-count"): BTCLI_SUBNET_MECHANISM_SET_NATIVE_COMMAND,
    ("subnet", "emission-split"): BTCLI_SUBNET_MECHANISM_EMISSIONS_NATIVE_COMMAND,
    ("subnet", "set-emission-split"): BTCLI_SUBNET_MECHANISM_SPLIT_NATIVE_COMMAND,
    ("subnet", "create-cost"): BTCLI_SUBNET_BURN_COST_NATIVE_COMMAND,
}

BTCLI_SUBNET_COMPAT_VALUE_FLAG_ERRORS: dict[tuple[str, ...], str] = {
    ("subnet", "set-symbol"): BTCLI_SUBNET_SET_SYMBOL_FLAG_VALUE_MESSAGE,
    ("subnet", "show"): BTCLI_SUBNET_SHOW_FLAG_VALUE_MESSAGE,
    ("subnet", "check-start"): BTCLI_SUBNET_CHECK_START_FLAG_VALUE_MESSAGE,
    ("subnet", "register-with-identity"): BTCLI_SUBNET_CREATE_FLAG_VALUE_MESSAGE,
    ("identity", "set-subnet"): BTCLI_SUBNET_SET_IDENTITY_FLAG_VALUE_MESSAGE,
    ("subnet", "start"): BTCLI_SUBNET_START_FLAG_VALUE_MESSAGE,
    ("subnet", "mechanism-count"): BTCLI_SUBNET_MECHANISM_COUNT_FLAG_VALUE_MESSAGE,
    ("subnet", "set-mechanism-count"): BTCLI_SUBNET_MECHANISM_SET_FLAG_VALUE_MESSAGE,
    ("subnet", "emission-split"): BTCLI_SUBNET_MECHANISM_EMISSIONS_FLAG_VALUE_MESSAGE,
    ("subnet", "set-emission-split"): BTCLI_SUBNET_MECHANISM_SPLIT_FLAG_VALUE_MESSAGE,
}

BTCLI_SUBNET_COMPAT_VALUE_FLAGS_BY_COMMAND: dict[tuple[str, ...], set[str]] = {
    ("subnet", "set-symbol"): BTCLI_SUBNET_SET_SYMBOL_VALUE_FLAGS,
    ("subnet", "show"): BTCLI_SUBNET_SHOW_VALUE_FLAGS,
    ("subnet", "check-start"): BTCLI_SUBNET_CHECK_START_VALUE_FLAGS,
    ("subnet", "register-with-identity"): BTCLI_SUBNET_CREATE_VALUE_FLAGS,
    ("identity", "set-subnet"): BTCLI_SUBNET_SET_IDENTITY_VALUE_FLAGS,
    ("subnet", "start"): BTCLI_SUBNET_START_VALUE_FLAGS,
    ("subnet", "mechanism-count"): BTCLI_SUBNET_MECHANISM_COUNT_VALUE_FLAGS,
    ("subnet", "set-mechanism-count"): BTCLI_SUBNET_MECHANISM_SET_VALUE_FLAGS,
    ("subnet", "emission-split"): BTCLI_SUBNET_MECHANISM_EMISSIONS_VALUE_FLAGS,
    ("subnet", "set-emission-split"): BTCLI_SUBNET_MECHANISM_SPLIT_VALUE_FLAGS,
}

BTCLI_SUBNET_COMPAT_POSITIONAL_FLAGS_BY_COMMAND: dict[tuple[str, ...], set[str]] = {
    ("subnet", "set-symbol"): BTCLI_SUBNET_SET_SYMBOL_POSITIONAL_FLAGS,
    ("subnet", "show"): BTCLI_SUBNET_SHOW_POSITIONAL_FLAGS,
    ("subnet", "check-start"): BTCLI_SUBNET_CHECK_START_POSITIONAL_FLAGS,
    ("subnet", "register-with-identity"): BTCLI_SUBNET_CREATE_POSITIONAL_FLAGS,
    ("subnet", "start"): BTCLI_SUBNET_START_POSITIONAL_FLAGS,
    ("subnet", "mechanism-count"): BTCLI_SUBNET_MECHANISM_COUNT_POSITIONAL_FLAGS,
    ("subnet", "set-mechanism-count"): BTCLI_SUBNET_MECHANISM_SET_POSITIONAL_FLAGS,
    ("subnet", "emission-split"): BTCLI_SUBNET_MECHANISM_EMISSIONS_POSITIONAL_FLAGS,
    ("subnet", "set-emission-split"): BTCLI_SUBNET_MECHANISM_SPLIT_POSITIONAL_FLAGS,
    ("subnet", "create-cost"): BTCLI_SUBNET_BURN_COST_POSITIONAL_FLAGS,
}

BTCLI_SUBNET_COMPAT_REQUIRED_POSITIONAL: dict[tuple[str, ...], str | None] = {
    ("subnet", "set-symbol"): BTCLI_SUBNET_SYMBOL_REQUIRED_MESSAGE,
    ("subnet", "show"): None,
    ("subnet", "check-start"): None,
    ("subnet", "register-with-identity"): None,
    ("identity", "set-subnet"): None,
    ("subnet", "start"): None,
    ("subnet", "mechanism-count"): None,
    ("subnet", "set-mechanism-count"): None,
    ("subnet", "emission-split"): None,
    ("subnet", "set-emission-split"): None,
}

BTCLI_SUBNET_COMPAT_REQUIRED_FLAGS: dict[tuple[str, ...], tuple[str, str] | None] = {
    ("subnet", "set-symbol"): None,
    ("subnet", "show"): None,
    ("subnet", "check-start"): None,
    ("subnet", "register-with-identity"): None,
    ("identity", "set-subnet"): None,
    ("subnet", "start"): None,
    ("subnet", "mechanism-count"): None,
    ("subnet", "set-mechanism-count"): None,
    ("subnet", "emission-split"): None,
    ("subnet", "set-emission-split"): None,
}

BTCLI_SUBNET_COMPAT_POSITIONAL_TARGET = {("subnet", "set-symbol"): "--symbol"}

BTCLI_SUBNET_COMPAT_DUPLICATE_POSITIONAL = {
    ("subnet", "set-symbol"): BTCLI_SUBNET_SYMBOL_DUPLICATE_MESSAGE,
}

BTCLI_SUBNET_COMPAT_PRESERVE_OUTPUT = {
    ("subnet", "show"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "create-cost"),
}

BTCLI_SUBNET_COMPAT_MAP_HOTKEY_TO = {
    ("subnet", "set-symbol"): "--hotkey-name",
    ("identity", "set-subnet"): "--hotkey-name",
    ("subnet", "start"): "--hotkey-name",
    ("subnet", "set-mechanism-count"): "--hotkey-name",
    ("subnet", "set-emission-split"): "--hotkey-name",
}

BTCLI_SUBNET_COMPAT_MAP_WALLET = {
    ("subnet", "show"),
    ("subnet", "check-start"),
    ("subnet", "register-with-identity"),
    ("identity", "set-subnet"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "set-mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "set-emission-split"),
}

BTCLI_SUBNET_COMPAT_MAP_JSON = {
    ("subnet", "show"),
    ("subnet", "check-start"),
    ("subnet", "register-with-identity"),
    ("identity", "set-subnet"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "set-mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "set-emission-split"),
}

BTCLI_SUBNET_COMPAT_MAP_BOOL = {
    ("subnet", "show"),
    ("subnet", "check-start"),
    ("subnet", "register-with-identity"),
    ("identity", "set-subnet"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "set-mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "set-emission-split"),
}

BTCLI_SUBNET_COMPAT_HANDLED_COMMANDS = {
    ("subnet", "list"),
    ("subnet", "show"),
    ("subnet", "check-start"),
    ("subnet", "register-with-identity"),
    ("identity", "set-subnet"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "set-mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "set-emission-split"),
}

BTCLI_SUBNET_COMPAT_VALUE_ALIASES: dict[tuple[str, ...], dict[str, str]] = {
    ("subnet", "set-symbol"): {
        "--wallet-name": "--wallet",
        "--wallet-path": "--wallet-dir",
        "--hotkey": "--hotkey-name",
    },
    ("subnet", "show"): {},
    ("subnet", "check-start"): {},
    ("subnet", "register-with-identity"): {
        "--wallet-name": "--wallet",
        "--wallet-path": "--wallet-dir",
        "--hotkey": "--hotkey-name",
        "--subnet-name": "--name",
        "--github-repo": "--github",
        "--repo": "--github",
        "--subnet-contact": "--contact",
        "--subnet-url": "--url",
        "--url": "--url",
        "--discord-handle": "--discord",
        "--additional-info": "--additional",
    },
    ("identity", "set-subnet"): {
        "--wallet-name": "--wallet",
        "--wallet-path": "--wallet-dir",
        "--hotkey": "--hotkey-name",
        "--subnet-name": "--name",
        "--github-repo": "--github",
        "--repo": "--github",
        "--subnet-url": "--url",
        "--url": "--url",
    },
    ("subnet", "start"): {
        "--wallet-name": "--wallet",
        "--wallet-path": "--wallet-dir",
        "--hotkey": "--hotkey-name",
    },
    ("subnet", "mechanism-count"): {},
    ("subnet", "set-mechanism-count"): {
        "--wallet-name": "--wallet",
        "--wallet-path": "--wallet-dir",
        "--hotkey": "--hotkey-name",
        "--mech-count": "--count",
    },
    ("subnet", "emission-split"): {},
    ("subnet", "set-emission-split"): {
        "--wallet-name": "--wallet",
        "--wallet-path": "--wallet-dir",
        "--hotkey": "--hotkey-name",
        "--split": "--weights",
    },
}

BTCLI_SUBNET_COMPAT_OUTPUT_JSON_FLAGS = {
    ("subnet", "show"),
    ("subnet", "check-start"),
    ("subnet", "register-with-identity"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "set-mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "set-emission-split"),
}

BTCLI_SUBNET_COMPAT_BOOL_ALIASES = {
    ("subnet", "show"),
    ("subnet", "check-start"),
    ("subnet", "register-with-identity"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "set-mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "set-emission-split"),
}

BTCLI_SUBNET_COMPAT_SYMBOL_COMMANDS = {("subnet", "set-symbol")}

BTCLI_SUBNET_COMPAT_SHOW_COMMANDS = {("subnet", "show")}

BTCLI_SUBNET_COMPAT_DIRECT_PASS = {
    ("subnet", "show"),
    ("subnet", "check-start"),
    ("subnet", "register-with-identity"),
    ("subnet", "set-symbol"),
    ("subnet", "start"),
    ("subnet", "mechanism-count"),
    ("subnet", "set-mechanism-count"),
    ("subnet", "emission-split"),
    ("subnet", "set-emission-split"),
}

BTCLI_SUBNET_COMPAT_TRIGGER_FLAGS = BTCLI_SUBNET_COMPAT_BTCLI_FLAGS

BTCLI_WALLET_OVERVIEW_UNSUPPORTED_FLAGS = {
    "--all",
    "-a",
    "--sort-by",
    "--sort_by",
    "--sort-order",
    "--sort_order",
    "--include-hotkeys",
    "-in",
    "--exclude-hotkeys",
    "-ex",
    "--netuids",
    "--netuid",
    "-n",
}

BTCLI_WALLET_SWAP_CHECK_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--all": "agcli wallet check-swap requires an explicit --address and does not expose btcli's all-announcements view.",
    "--quiet": "agcli wallet check-swap does not expose btcli quiet-mode output suppression on this compatibility surface.",
}

BTCLI_WALLET_NEW_HOTKEY_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--n-words": "agcli wallet new-hotkey does not expose btcli mnemonic word-count selection.",
    "--n_words": "agcli wallet new-hotkey does not expose btcli mnemonic word-count selection.",
    "--use-password": "agcli wallet new-hotkey does not expose btcli password-protection toggles.",
    "--no-use-password": "agcli wallet new-hotkey does not expose btcli password-protection toggles.",
    "--uri": "agcli wallet new-hotkey does not expose btcli URI-based key generation on this surface.",
    "--overwrite": "agcli wallet new-hotkey does not expose btcli overwrite toggles on this surface.",
    "--no-overwrite": "agcli wallet new-hotkey does not expose btcli overwrite toggles on this surface.",
    "--quiet": "agcli wallet new-hotkey does not expose btcli quiet-mode output suppression.",
}

BTCLI_WALLET_CREATE_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--n-words": "agcli wallet create does not expose btcli mnemonic word-count selection.",
    "--n_words": "agcli wallet create does not expose btcli mnemonic word-count selection.",
    "--use-password": "agcli wallet create uses explicit passwords rather than btcli password-protection toggles.",
    "--no-use-password": "agcli wallet create uses explicit passwords rather than btcli password-protection toggles.",
    "--uri": "agcli wallet create does not expose btcli URI-based wallet generation on this surface.",
    "--overwrite": "agcli wallet create does not expose btcli overwrite toggles on this surface.",
    "--no-overwrite": "agcli wallet create does not expose btcli overwrite toggles on this surface.",
    "--quiet": "agcli wallet create does not expose btcli quiet-mode output suppression.",
}

BTCLI_WALLET_ASSOCIATE_HOTKEY_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--proxy": "agcli wallet associate-hotkey does not expose btcli proxy execution on this surface.",
    "--announce-only": "agcli wallet associate-hotkey does not expose btcli announce-only proxy submission on this surface.",
    "--no-announce-only": "agcli wallet associate-hotkey does not expose btcli announce-only proxy submission on this surface.",
    "--quiet": "agcli wallet associate-hotkey does not expose btcli quiet-mode output suppression.",
}

BTCLI_WALLET_REGEN_COLDKEY_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--seed": "agcli wallet regen-coldkey currently exposes mnemonic-based regeneration on this compatibility surface, not raw seed input.",
    "--json": "agcli wallet regen-coldkey does not expose btcli JSON key-backup restoration on this surface.",
    "-j": "agcli wallet regen-coldkey does not expose btcli JSON key-backup restoration on this surface.",
    "--json-password": "agcli wallet regen-coldkey does not expose btcli JSON key-backup restoration on this surface.",
    "--use-password": "agcli wallet regen-coldkey uses an explicit --password value rather than btcli password-protection toggles.",
    "--no-use-password": "agcli wallet regen-coldkey always writes an encrypted coldkey on this surface.",
    "--overwrite": "agcli wallet regen-coldkey does not expose btcli overwrite toggles on this surface.",
    "--no-overwrite": "agcli wallet regen-coldkey does not expose btcli overwrite toggles on this surface.",
    "--quiet": "agcli wallet regen-coldkey does not expose btcli quiet-mode output suppression.",
}

BTCLI_WALLET_REGEN_HOTKEY_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--seed": "agcli wallet regen-hotkey currently exposes mnemonic-based regeneration on this compatibility surface, not raw seed input.",
    "--json": "agcli wallet regen-hotkey does not expose btcli JSON key-backup restoration on this surface.",
    "-j": "agcli wallet regen-hotkey does not expose btcli JSON key-backup restoration on this surface.",
    "--json-password": "agcli wallet regen-hotkey does not expose btcli JSON key-backup restoration on this surface.",
    "--use-password": "agcli wallet regen-hotkey uses an explicit --password value rather than btcli password-protection toggles.",
    "--no-use-password": "agcli wallet regen-hotkey does not expose btcli password-removal toggles on this surface.",
    "--overwrite": "agcli wallet regen-hotkey does not expose btcli overwrite toggles on this surface.",
    "--no-overwrite": "agcli wallet regen-hotkey does not expose btcli overwrite toggles on this surface.",
    "--quiet": "agcli wallet regen-hotkey does not expose btcli quiet-mode output suppression.",
}

BTCLI_WALLET_SIGN_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--use-hotkey": "agcli wallet sign currently signs with the coldkey only on this compatibility surface.",
    "--no-use-hotkey": "agcli wallet sign currently signs with the coldkey only on this compatibility surface.",
    "--no": "agcli wallet sign does not expose btcli automatic-decline prompts on this surface.",
    "--quiet": "agcli wallet sign does not expose btcli quiet-mode output suppression.",
}

BTCLI_WALLET_VERIFY_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--public-key": "agcli wallet verify expects an SS58 signer address, not a raw public key, on this compatibility surface.",
    "-p": "agcli wallet verify expects an SS58 signer address, not a raw public key, on this compatibility surface.",
    "--quiet": "agcli wallet verify does not expose btcli quiet-mode output suppression.",
}

BTCLI_WALLET_TRANSFER_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--all": "use native `taocli transfer-all --dest ...` or btcli for full-balance transfers.",
    "--allow-death": "use native `taocli transfer` / `transfer-keep-alive` explicitly; taocli does not infer btcli account-survival semantics on this compatibility path.",
    "--proxy": "agcli transfer does not expose btcli proxy execution on this compatibility surface.",
    "--announce-only": "agcli transfer does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli transfer does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--quiet": "agcli transfer does not expose btcli quiet-mode output suppression.",
    "--verbose": "agcli transfer does not expose btcli verbose-mode output expansion on this compatibility surface.",
}

BTCLI_WALLET_SET_IDENTITY_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--hotkey": "agcli identity set on this host does not expose btcli's distinct hotkey-identity target semantics on this compatibility surface.",
    "--discord": "agcli identity set does not expose btcli's discord field on this compatibility surface.",
    "--additional": "agcli identity set does not expose btcli's additional-details field on this compatibility surface.",
    "--proxy": "agcli identity set does not expose btcli proxy execution on this compatibility surface.",
    "--announce-only": "agcli identity set does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--no-announce-only": "agcli identity set does not expose btcli announce-only proxy submission on this compatibility surface.",
    "--quiet": "agcli identity set does not expose btcli quiet-mode output suppression.",
    "--verbose": "agcli identity set does not expose btcli verbose-mode output expansion on this compatibility surface.",
    "--no": "agcli identity set does not expose btcli automatic-decline prompts on this compatibility surface.",
}

BTCLI_WALLET_NEW_COLDKEY_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `wallet new-coldkey` is not implemented in taocli/agcli yet; "
    "agcli exposes `wallet create` and `wallet regen-coldkey`, but not a matching standalone coldkey-generation command."
)

BTCLI_WALLET_REGEN_COLDKEYPUB_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `wallet regen-coldkeypub` is not implemented in taocli/agcli yet; "
    "agcli on this host has no matching `wallet regen-coldkeypub` subcommand."
)

BTCLI_WALLET_REGEN_HOTKEYPUB_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `wallet regen-hotkeypub` is not implemented in taocli/agcli yet; "
    "agcli on this host has no matching `wallet regen-hotkeypub` subcommand."
)

BTCLI_WALLET_FAUCET_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `wallet faucet` is not implemented in taocli/agcli yet; "
    "agcli on this host has no matching `wallet faucet` or top-level `faucet` command."
)

BTCLI_AXON_UNSUPPORTED_FLAGS = {
    "--ip-type",
    "--quiet",
    "--wait-for-inclusion",
    "--no-wait-for-inclusion",
    "--wait-for-finalization",
    "--no-wait-for-finalization",
}

BTCLI_AXON_FLAG_HELP: dict[str, str] = {
    "--ip-type": "taocli/agcli does not expose btcli IP family selection on this compatibility surface.",
    "--quiet": "taocli/agcli does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--wait-for-inclusion": (
        "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface."
    ),
    "--no-wait-for-inclusion": (
        "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface."
    ),
    "--wait-for-finalization": (
        "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface."
    ),
    "--no-wait-for-finalization": (
        "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface."
    ),
}

RAO_PER_TAO = 1_000_000_000

BTCLI_PROXY_EXECUTE_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `proxy execute` is not implemented in taocli/agcli yet; "
    "agcli requires explicit pallet/call details rather than btcli call-hash/call-hex execution."
)

BTCLI_LIQUIDITY_UNSUPPORTED_MESSAGE = (
    "btcli-compatible `liquidity list` is not implemented in taocli/agcli yet; "
    "agcli exposes add/remove/modify/toggle but not a matching liquidity list command."
)

UNSUPPORTED_BTCLI_ALIASES: dict[tuple[str, ...], str] = {
    (
        "wallet",
        "swap-hotkey",
    ): (
        "btcli-compatible `wallet swap-hotkey` is not implemented in taocli yet; "
        "use `taocli swap hotkey --new-hotkey ...` or btcli."
    ),
    (
        "wallet",
        "swap-coldkey",
    ): (
        "btcli-compatible `wallet swap-coldkey` is not implemented in taocli yet; "
        "use `taocli swap coldkey --new-coldkey ...` or btcli."
    ),
    (
        "wallet",
        "new-coldkey",
    ): BTCLI_WALLET_NEW_COLDKEY_UNSUPPORTED_MESSAGE,
    (
        "wallet",
        "regen-coldkeypub",
    ): BTCLI_WALLET_REGEN_COLDKEYPUB_UNSUPPORTED_MESSAGE,
    (
        "wallet",
        "regen-hotkeypub",
    ): BTCLI_WALLET_REGEN_HOTKEYPUB_UNSUPPORTED_MESSAGE,
    (
        "wallet",
        "faucet",
    ): BTCLI_WALLET_FAUCET_UNSUPPORTED_MESSAGE,
    (
        "sudo",
        "senate",
    ): "btcli-compatible `sudo senate` is not implemented in taocli/agcli yet; use btcli for governance reads.",
    (
        "sudo",
        "proposals",
    ): "btcli-compatible `sudo proposals` is not implemented in taocli/agcli yet; use btcli for governance reads.",
    (
        "sudo",
        "senate-vote",
    ): "btcli-compatible `sudo senate-vote` is not implemented in taocli/agcli yet; use btcli for governance actions.",
    (
        "sudo",
        "stake-burn",
    ): "btcli-compatible `sudo stake-burn` is not implemented in taocli/agcli yet.",
    (
        "sudo",
        "set-take",
    ): "btcli-compatible `sudo set-take` is not implemented in taocli/agcli yet; nearest agcli family is `delegate`.",
    (
        "sudo",
        "get-take",
    ): "btcli-compatible `sudo get-take` is not implemented in taocli/agcli yet; nearest agcli family is `delegate`.",
    (
        "proxy",
        "execute",
    ): BTCLI_PROXY_EXECUTE_UNSUPPORTED_MESSAGE,
    (
        "liquidity",
        "list",
    ): BTCLI_LIQUIDITY_UNSUPPORTED_MESSAGE,
    (
        "stake",
        "child",
    ): BTCLI_STAKE_CHILD_UNSUPPORTED_MESSAGE,
    (
        "view",
        "dashboard",
    ): (
        "btcli-compatible `view dashboard` is not implemented in taocli/agcli yet; "
        "use btcli for the HTML dashboard or native taocli `view network` / `view portfolio` reads."
    ),
    (
        "subnets",
        "price",
    ): (
        "btcli-compatible `subnets price` is not implemented in taocli/agcli yet; "
        "agcli exposes no matching `subnet price` command on this host, so use btcli for subnet price history/current-price reads."
    ),
}

CROWDLOAN_UPDATE_OPTIONS: dict[str, str] = {
    "--cap": "update-cap",
    "--end": "update-end",
    "--end-block": "update-end",
    "--min-contribution": "update-min-contribution",
}

BTCLI_CROWD_LIST_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--quiet": "taocli/agcli does not expose btcli quiet-mode filtering on this compatibility surface.",
    "--status": "taocli/agcli crowdloan list does not expose btcli status filtering on this compatibility surface.",
    "--type": "taocli/agcli crowdloan list does not expose btcli type filtering on this compatibility surface.",
    "--sort-by": "taocli/agcli crowdloan list does not expose btcli sorting controls on this compatibility surface.",
    "--sort-order": "taocli/agcli crowdloan list does not expose btcli sorting controls on this compatibility surface.",
    "--search-creator": (
        "taocli/agcli crowdloan list does not expose btcli creator search on this compatibility surface."
    ),
}

BTCLI_CROWD_INFO_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--quiet": "taocli/agcli does not expose btcli quiet-mode filtering on this compatibility surface.",
    "--show-contributors": (
        "use `taocli crowd contributors --crowdloan-id <id>` or btcli for combined detail+contributors output."
    ),
}
BTCLI_CROWD_CONTRIBUTORS_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--quiet": "taocli/agcli does not expose btcli quiet-mode filtering on this compatibility surface.",
}
BTCLI_CROWD_CREATE_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--announce-only": "taocli/agcli does not expose btcli announce-only proxy execution on this compatibility surface.",
    "--no-announce-only": "taocli/agcli does not expose btcli announce-only proxy execution on this compatibility surface.",
    "--wait-for-inclusion": "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--wait-for-finalization": "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--quiet": "taocli/agcli does not expose btcli quiet-mode output suppression on this compatibility surface.",
    "--duration": "taocli/agcli crowdloan create expects an absolute --end-block; btcli duration-based create timing does not map cleanly on this compatibility surface.",
    "--subnet-lease": "taocli/agcli crowdloan create does not expose btcli subnet-lease creation on this compatibility surface.",
    "--fundraising": "taocli/agcli crowdloan create does not expose btcli fundraising-mode toggles on this compatibility surface.",
    "--emissions-share": "taocli/agcli crowdloan create does not expose btcli emissions-share controls on this compatibility surface.",
    "--emissions": "taocli/agcli crowdloan create does not expose btcli emissions-share controls on this compatibility surface.",
    "--lease-end-block": "taocli/agcli crowdloan create does not expose btcli lease-end controls on this compatibility surface.",
    "--lease-end": "taocli/agcli crowdloan create does not expose btcli lease-end controls on this compatibility surface.",
    "--custom-call-pallet": "taocli/agcli crowdloan create does not expose btcli custom-call attachment on this compatibility surface.",
    "--custom-call-method": "taocli/agcli crowdloan create does not expose btcli custom-call attachment on this compatibility surface.",
    "--custom-call-args": "taocli/agcli crowdloan create does not expose btcli custom-call attachment on this compatibility surface.",
}
BTCLI_CROWD_MUTATION_UNSUPPORTED_FLAGS: dict[str, str] = {
    "--announce-only": "taocli/agcli does not expose btcli announce-only proxy execution on this compatibility surface.",
    "--no-announce-only": "taocli/agcli does not expose btcli announce-only proxy execution on this compatibility surface.",
    "--wait-for-inclusion": "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--no-wait-for-inclusion": "taocli/agcli does not expose btcli wait-for-inclusion toggles on this compatibility surface.",
    "--wait-for-finalization": "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--no-wait-for-finalization": "taocli/agcli does not expose btcli wait-for-finalization toggles on this compatibility surface.",
    "--quiet": "taocli/agcli does not expose btcli quiet-mode output suppression on this compatibility surface.",
}
BTCLI_CROWD_MUTATION_COMMANDS = {
    ("crowdloan", "contribute"),
    ("crowdloan", "withdraw"),
    ("crowdloan", "finalize"),
    ("crowdloan", "refund"),
    ("crowdloan", "dissolve"),
}
BTCLI_CROWD_VALUE_ALIASES: dict[str, str] = {
    "--crowdloan_id": "--crowdloan-id",
    "--id": "--crowdloan-id",
    "--min": "--min-contribution",
}

BTCLI_OUTPUT_ALIASES: dict[str, str] = {
    "--json-output": "json",
}

BTCLI_BOOL_FLAG_ALIASES: dict[str, str | None] = {
    "--no-prompt": "--yes",
    "--prompt": None,
}

BTCLI_CONFIG_UNSUPPORTED_SUBCOMMANDS = {
    "set",
    "clear",
    "proxies",
    "add-proxy",
    "remove-proxy",
    "update-proxy",
    "clear-proxies",
}

BTCLI_WEIGHTS_COMMANDS = {"commit", "reveal"}

BTCLI_UTILS_CONVERT_FLAGS = {"--rao", "--tao", "--json-output"}

BTCLI_SUDO_GET_PARAM_ALIASES: dict[str, str] = {
    "max_weights_limit": "max_weight_limit",
    "commit_reveal_weights_interval": "commit_reveal_period",
    "yuma3_enabled": "yuma_version",
}

BTCLI_LOCALNET_SUBNET_NAMES: dict[str, str] = {
    "0": "root",
    "1": "apex",
    "2": "omron",
}

BTCLI_SUDO_GET_METADATA: dict[str, dict[str, object]] = {
    "activity_cutoff": {
        "description": "Minimum activity level required for neurons to remain active.",
        "side_effects": "Lower values keep more neurons active; higher values prune inactive neurons more aggressively.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#activitycutoff",
    },
    "adjustment_alpha": {
        "description": "Alpha parameter for difficulty adjustment algorithm.",
        "side_effects": "Higher values make difficulty adjustments more aggressive; lower values provide smoother transitions.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#adjustmentalpha",
    },
    "adjustment_interval": {
        "description": "Number of blocks between automatic difficulty adjustments.",
        "side_effects": "Shorter intervals make difficulty more responsive but may cause volatility. Longer intervals provide stability.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#adjustmentinterval",
    },
    "bonds_moving_avg": {
        "description": "Moving average window size for bond calculations.",
        "side_effects": "Larger windows provide smoother bond values but slower response to changes. Smaller windows react faster but may be more volatile.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#bondsmovingaverage",
    },
    "commit_reveal_period": {
        "description": "Duration (in blocks) for commit-reveal weight submission scheme.",
        "side_effects": "Longer periods provide more time for commits but delay weight revelation. Shorter periods increase frequency.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#commitrevealperiod",
    },
    "commit_reveal_weights_enabled": {
        "description": "Enable or disable commit-reveal scheme for weight submissions.",
        "side_effects": "Enabling prevents front-running of weight submissions. Disabling allows immediate weight visibility.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#commitrevealweightsenabled",
    },
    "difficulty": {
        "description": "Current proof-of-work difficulty for registration.",
        "side_effects": "Directly affects registration cost and time. Higher difficulty makes registration harder and more expensive.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#difficulty",
    },
    "immunity_period": {
        "description": "Duration (in blocks) during which newly registered neurons are protected from certain penalties.",
        "side_effects": "Increasing immunity period gives new neurons more time to establish themselves before facing penalties.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#immunityperiod",
    },
    "kappa": {
        "description": "Kappa determines the scaling factor for consensus calculations.",
        "side_effects": "Modifying kappa changes how validator votes are weighted in consensus mechanisms.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#kappa",
    },
    "liquid_alpha_enabled": {
        "description": "Enable or disable liquid alpha staking mechanism.",
        "side_effects": "Enabling provides more staking flexibility. Disabling uses traditional staking mechanisms.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#liquidalphaenabled",
    },
    "max_burn": {
        "description": "Maximum TAO burn amount cap for subnet registration.",
        "side_effects": "Caps registration costs, ensuring registration remains accessible even as difficulty increases.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#maxburn",
    },
    "max_difficulty": {
        "description": "Maximum proof-of-work difficulty cap.",
        "side_effects": "Caps the maximum computational requirement, ensuring registration remains feasible.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#maxdifficulty",
    },
    "max_regs_per_block": {
        "description": "Maximum number of registrations allowed per block.",
        "side_effects": "Lower values reduce chain load but may create registration bottlenecks. Higher values allow more throughput.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#maxregistrationsperblock",
    },
    "max_validators": {
        "description": "Maximum number of validators allowed in the subnet.",
        "side_effects": "Lower values reduce consensus overhead but limit decentralization. Higher values increase decentralization but may slow consensus.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#maxallowedvalidators",
    },
    "max_weight_limit": {
        "description": "No description available.",
        "side_effects": "No side effects documented.",
        "owner_settable": False,
        "docs_link": "",
    },
    "min_allowed_weights": {
        "description": "Minimum number of weight connections a neuron must maintain to stay active.",
        "side_effects": "Lower values allow neurons with fewer connections to remain active; higher values enforce stricter connectivity requirements.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#minallowedweights",
    },
    "min_burn": {
        "description": "Minimum TAO burn amount required for subnet registration.",
        "side_effects": "Increasing min_burn raises the barrier to entry, potentially reducing spam but also limiting participation.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#minburn",
    },
    "min_difficulty": {
        "description": "Minimum proof-of-work difficulty required for registration",
        "side_effects": "Increasing min_difficulty raises the computational barrier for new neuron registrations.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#mindifficulty",
    },
    "registration_allowed": {
        "description": "Enable or disable new registrations to the subnet.",
        "side_effects": "Disabling registration closes the subnet to new participants. Enabling allows open registration.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#networkregistrationallowed",
    },
    "rho": {
        "description": "Rho controls the rate at which weights decay over time.",
        "side_effects": "Changing rho affects how quickly neurons' influence diminishes, impacting consensus dynamics.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#rho",
    },
    "serving_rate_limit": {
        "description": "Rate limit for serving requests.",
        "side_effects": "Affects network throughput and prevents individual neurons from monopolizing serving capacity.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#servingratelimit",
    },
    "target_regs_per_interval": {
        "description": "Target number of new registrations per adjustment interval.",
        "side_effects": "Affects how the difficulty adjustment algorithm targets registration rates.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#targetregistrationsperinterval",
    },
    "tempo": {
        "description": "Number of blocks between epoch transitions",
        "side_effects": "Lower tempo means more frequent updates but higher chain load. Higher tempo reduces frequency but may slow responsiveness.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#tempo",
    },
    "weights_rate_limit": {
        "description": "Maximum number of weight updates allowed per epoch.",
        "side_effects": "Lower values reduce chain load but may limit legitimate weight updates. Higher values allow more flexibility.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#weightsratelimit--commitmentratelimit",
    },
    "weights_version": {
        "description": "Version key for weight sets.",
        "side_effects": "Changing this invalidates all existing weights, forcing neurons to resubmit weights.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#weightsversion",
    },
    "alpha_sigmoid_steepness": {
        "description": "Steepness parameter for alpha sigmoid function.",
        "side_effects": "Affects how alpha values are transformed in staking calculations. Higher values create steeper curves.",
        "owner_settable": False,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#alphasigmoidsteepness",
    },
    "user_liquidity_enabled": {
        "description": "Enable or disable user liquidity features.",
        "side_effects": "Enabling allows liquidity provision and swaps. Disabling restricts liquidity operations.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#userliquidityenabled",
    },
    "bonds_reset_enabled": {
        "description": "Enable or disable periodic bond resets.",
        "side_effects": "Enabling provides periodic bond resets, preventing bond accumulation. Disabling allows bonds to accumulate.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#bondsresetenabled",
    },
    "transfers_enabled": {
        "description": "Enable or disable TAO transfers within the subnet.",
        "side_effects": "Enabling allows TAO transfers between neurons. Disabling prevents all transfer operations.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#toggletransfer",
    },
    "alpha_high": {
        "description": "High bound of the alpha range for stake calculations.",
        "side_effects": "Affects the upper bound of alpha conversion in staking mechanisms. Set via alpha_values parameter.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#alphasigmoidsteepness",
    },
    "alpha_low": {
        "description": "Low bound of the alpha range for stake calculations.",
        "side_effects": "Affects the lower bound of alpha conversion in staking mechanisms. Set via alpha_values parameter.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#alphasigmoidsteepness",
    },
    "subnet_is_active": {
        "description": "Whether the subnet is currently active and operational.",
        "side_effects": "When inactive, the subnet cannot process requests or participate in network operations. Set via 'btcli subnets start' command.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#subnetisactive",
    },
    "yuma_version": {
        "description": "Version of the Yuma consensus mechanism.",
        "side_effects": "Changing the version affects which Yuma consensus features are active. Use yuma3_enabled to toggle Yuma3.",
        "owner_settable": True,
        "docs_link": "docs.learnbittensor.org/subnets/subnet-hyperparameters#yuma3",
    },
}


def _split_csv_numbers(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _convert_btcli_weights_list(uids_value: str, weights_value: str) -> str:
    uid_tokens = _split_csv_numbers(uids_value)
    weight_tokens = _split_csv_numbers(weights_value)
    if not uid_tokens or not weight_tokens:
        raise click.ClickException("btcli-compatible weights require non-empty --uids and --weights.")
    if len(uid_tokens) != len(weight_tokens):
        raise click.ClickException("btcli-compatible --uids and --weights must have the same number of entries.")

    converted: list[str] = []
    float_weights: list[float] = []
    for raw in weight_tokens:
        try:
            weight = float(raw)
        except ValueError as exc:
            raise click.ClickException(f"Invalid btcli weight '{raw}'.") from exc
        if weight < 0:
            raise click.ClickException("btcli-compatible weights cannot be negative.")
        float_weights.append(weight)

    if not float_weights or max(float_weights) <= 0:
        raise click.ClickException("btcli-compatible weights must include at least one positive value.")

    max_weight = max(float_weights)
    scaled_weights = [round((weight / max_weight) * 65535) for weight in float_weights]

    for uid, scaled in zip(uid_tokens, scaled_weights, strict=True):
        try:
            uid_int = int(uid)
        except ValueError as exc:
            raise click.ClickException(f"Invalid btcli uid '{uid}'.") from exc
        if uid_int < 0:
            raise click.ClickException("btcli-compatible uids cannot be negative.")
        converted.append(f"{uid_int}:{scaled}")
    return ",".join(converted)


def _normalize_btcli_weight_flags(args: Sequence[str]) -> list[str]:
    if len(args) < 2 or args[0] != "weights" or args[1] not in BTCLI_WEIGHTS_COMMANDS:
        return list(args)

    btcli_weight_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--uids",
        "--json-output",
        "--no-prompt",
        "--prompt",
    }
    if not any(token in btcli_weight_flags for token in args[2:]):
        return list(args)

    command = list(args[:2])
    normalized: list[str] = []
    uids_value: str | None = None
    weights_value: str | None = None
    i = 2
    while i < len(args):
        token = args[i]
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--uids":
            uids_value = args[i + 1]
            i += 2
            continue
        if token == "--weights":
            weights_value = args[i + 1]
            i += 2
            continue
        if token == "--version-key":
            normalized.extend([token, args[i + 1]])
            i += 2
            continue
        output_alias = BTCLI_OUTPUT_ALIASES.get(token)
        if output_alias:
            normalized.extend(["--output", output_alias])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    if uids_value is not None or weights_value is not None:
        if uids_value is None or weights_value is None:
            raise click.ClickException("btcli-compatible weights require both --uids and --weights.")
        normalized.extend(["--weights", _convert_btcli_weights_list(uids_value, weights_value)])

    return [*command, *normalized]


def _normalize_btcli_read_flags(args: Sequence[str]) -> list[str]:
    if tuple(args[:1]) == ("balance",):
        command_len = 1
    elif tuple(args[:2]) in {
        ("identity", "show"),
        ("wallet", "check-swap"),
        ("wallet", "list"),
        ("stake", "list"),
        ("stake", "show-auto"),
    }:
        command_len = 2
    else:
        return list(args)

    command = list(args[:command_len])
    normalized: list[str] = []
    i = command_len
    while i < len(args):
        token = args[i]
        if tuple(command) == ("wallet", "check-swap") and token in BTCLI_WALLET_SWAP_CHECK_UNSUPPORTED_FLAGS:
            detail = BTCLI_WALLET_SWAP_CHECK_UNSUPPORTED_FLAGS[token]
            raise click.ClickException(
                "btcli-compatible `wallet swap-check` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {detail}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token in {"--ss58", "--ss58-address", "--coldkey-ss58", "--key"}:
            normalized.extend(["--address", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token == "--output" and i + 1 < len(args):
            normalized.extend([token, args[i + 1]])
            i += 2
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    return [*command, *normalized]


def _normalize_btcli_wallet_swap_check_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    if tuple(original_args[:2]) != ("wallet", "swap-check"):
        return stdout
    if tuple(rewritten_args[:2]) != ("wallet", "check-swap"):
        return stdout
    stripped = stdout.strip()
    if not stripped:
        return stdout

    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        address = payload.get("address")
        swap_scheduled = payload.get("swap_scheduled")
        if isinstance(address, str) and swap_scheduled is False and not _requests_json_output(original_args):
            return f"No pending swap announcement found for coldkey: {address}\n"
        return stdout

    if stripped.startswith("No coldkey swap scheduled for "):
        address = stripped.removeprefix("No coldkey swap scheduled for ").strip()
        if address:
            return f"No pending swap announcement found for coldkey: {address}\n"

    return stdout


def _btcli_wallet_swap_check_missing_address_stderr(args: Sequence[str], stderr: str) -> str | None:
    if tuple(args[:2]) != ("wallet", "swap-check") or not stderr:
        return None
    if "wallet or address is required" not in stderr:
        return None
    return (
        "Enter wallet name or SS58 address (leave blank to show all pending announcements):\n"
        "Aborted.\n"
    )


def _btcli_wallet_swap_check_stderr(args: Sequence[str], stderr: str) -> str | None:
    return _btcli_wallet_swap_check_missing_address_stderr(args, stderr)


def _normalize_btcli_stake_flags(args: Sequence[str]) -> list[str]:
    if len(args) >= 2 and args[0] == "stake" and args[1] in BTCLI_STAKE_COMMANDS_WITH_FLAG_NORMALIZATION:
        btcli_stake_flags = {
            "--wallet-name",
            "--wallet-path",
            "--hotkey",
            "--json-output",
            "--no-prompt",
            "--prompt",
            "--period",
            "--era",
            *BTCLI_STAKE_SET_AUTO_UNSUPPORTED_FLAGS,
        }
        if any(token in btcli_stake_flags for token in args[2:]):
            command = list(args[:2])
            normalized: list[str] = []
            i = 2
            while i < len(args):
                token = args[i]
                if args[1] == "set-auto" and token in BTCLI_STAKE_SET_AUTO_UNSUPPORTED_FLAGS:
                    detail = BTCLI_STAKE_SET_AUTO_UNSUPPORTED_FLAG_HELP[token]
                    raise click.ClickException(
                        f"btcli-compatible `stake set-auto` flag '{token}' is not implemented in taocli/agcli yet; {detail}"
                    )
                if token == "--wallet-name":
                    normalized.extend(["--wallet", args[i + 1]])
                    i += 2
                    continue
                if token == "--wallet-path":
                    normalized.extend(["--wallet-dir", args[i + 1]])
                    i += 2
                    continue
                if token == "--hotkey":
                    if args[1] in {"transfer", "transfer-stake", "swap", "set-auto"}:
                        normalized.extend(["--hotkey-address", args[i + 1]])
                    else:
                        normalized.extend(["--hotkey-name", args[i + 1]])
                    i += 2
                    continue
                if token == "--json-output":
                    normalized.extend(["--output", "json"])
                    i += 1
                    continue
                if token in {"--period", "--era"}:
                    normalized.extend(["--mortality-blocks", args[i + 1]])
                    i += 2
                    continue
                if token in BTCLI_BOOL_FLAG_ALIASES:
                    bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
                    if bool_alias:
                        normalized.append(bool_alias)
                    i += 1
                    continue
                normalized.append(token)
                if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
                    normalized.append(args[i + 1])
                    i += 2
                    continue
                i += 1
            return [*command, *normalized]
    return list(args)


def _normalize_btcli_wallet_new_hotkey_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("wallet", "new-hotkey"):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
        *BTCLI_WALLET_NEW_HOTKEY_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["wallet", "new-hotkey"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_NEW_HOTKEY_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet new-hotkey` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_NEW_HOTKEY_UNSUPPORTED_FLAGS[token]}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_create_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("wallet", "create"):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
        *BTCLI_WALLET_CREATE_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["wallet", "create"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_CREATE_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet create` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_CREATE_UNSUPPORTED_FLAGS[token]}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_associate_hotkey_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("wallet", "associate-hotkey"):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
        *BTCLI_WALLET_ASSOCIATE_HOTKEY_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["wallet", "associate-hotkey"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_ASSOCIATE_HOTKEY_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet associate-hotkey` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_ASSOCIATE_HOTKEY_UNSUPPORTED_FLAGS[token]}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-address", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_regen_coldkey_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("wallet", "regen-coldkey"):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
        *BTCLI_WALLET_REGEN_COLDKEY_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["wallet", "regen-coldkey"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_REGEN_COLDKEY_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet regen-coldkey` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_REGEN_COLDKEY_UNSUPPORTED_FLAGS[token]}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--mnemonic":
            normalized.extend(["--mnemonic", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_regen_hotkey_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("wallet", "regen-hotkey"):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
        *BTCLI_WALLET_REGEN_HOTKEY_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["wallet", "regen-hotkey"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_REGEN_HOTKEY_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet regen-hotkey` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_REGEN_HOTKEY_UNSUPPORTED_FLAGS[token]}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--name", args[i + 1]])
            i += 2
            continue
        if token == "--mnemonic":
            normalized.extend(["--mnemonic", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_sign_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("wallet", "sign"):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        *BTCLI_WALLET_SIGN_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["wallet", "sign"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_SIGN_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet sign` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_SIGN_UNSUPPORTED_FLAGS[token]}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_set_identity_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("identity", "set"):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--id-name",
        "--web-url",
        "--web",
        "--image-url",
        "--image",
        "--description",
        "--github",
        "--json-output",
        "--no-prompt",
        "--prompt",
        *BTCLI_WALLET_SET_IDENTITY_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["identity", "set"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_SET_IDENTITY_UNSUPPORTED_FLAGS:
            detail = BTCLI_WALLET_SET_IDENTITY_UNSUPPORTED_FLAGS[token]
            raise click.ClickException(
                "btcli-compatible `wallet set-identity` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {detail}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--id-name":
            normalized.extend(["--name", args[i + 1]])
            i += 2
            continue
        if token in {"--web-url", "--web"}:
            normalized.extend(["--url", args[i + 1]])
            i += 2
            continue
        if token in {"--image-url", "--image"}:
            normalized.extend(["--image", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_verify_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("wallet", "verify"):
        return list(args)
    btcli_flags = {
        "--address",
        "-a",
        "--public-key",
        "-p",
        "--json-output",
        *BTCLI_WALLET_VERIFY_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["wallet", "verify"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_VERIFY_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet verify` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_VERIFY_UNSUPPORTED_FLAGS[token]}"
            )
        if token in {"--address", "-a"}:
            normalized.extend(["--signer", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_transfer_args(args: Sequence[str]) -> list[str]:
    if tuple(args[:1]) != ("transfer",):
        return list(args)
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--destination",
        "--dest",
        "--json-output",
        "--no-prompt",
        "--prompt",
        "--period",
        "--era",
        *BTCLI_WALLET_TRANSFER_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_flags for token in args[1:]):
        return list(args)

    normalized = ["transfer"]
    i = 1
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_TRANSFER_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                "btcli-compatible `wallet transfer` flag "
                f"'{token}' is not implemented in taocli/agcli yet; {BTCLI_WALLET_TRANSFER_UNSUPPORTED_FLAGS[token]}"
            )
        if token in {"--destination", "--dest"}:
            normalized.extend(["--dest", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in {"--period", "--era"}:
            normalized.extend(["--mortality-blocks", args[i + 1]])
            i += 2
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized



def _normalize_btcli_wallet_flags(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) == ("wallet", "new-hotkey"):
        return _normalize_btcli_wallet_new_hotkey_args(args)
    if tuple(args[:2]) == ("wallet", "create"):
        return _normalize_btcli_wallet_create_args(args)
    if tuple(args[:2]) == ("wallet", "associate-hotkey"):
        return _normalize_btcli_wallet_associate_hotkey_args(args)
    if tuple(args[:2]) == ("wallet", "regen-coldkey"):
        return _normalize_btcli_wallet_regen_coldkey_args(args)
    if tuple(args[:2]) == ("wallet", "regen-hotkey"):
        return _normalize_btcli_wallet_regen_hotkey_args(args)
    if tuple(args[:2]) == ("wallet", "sign"):
        return _normalize_btcli_wallet_sign_args(args)
    if tuple(args[:2]) == ("identity", "set"):
        return _normalize_btcli_wallet_set_identity_args(args)
    if tuple(args[:2]) == ("wallet", "verify"):
        return _normalize_btcli_wallet_verify_args(args)
    if tuple(args[:1]) == ("transfer",):
        return _normalize_btcli_wallet_transfer_args(args)
    if tuple(args[:2]) != ("view", "portfolio"):
        return _normalize_btcli_read_flags(args)

    normalized: list[str] = []
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_WALLET_OVERVIEW_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                f"btcli-compatible wallet overview flag '{token}' is not implemented in taocli yet."
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token in {"--ss58", "--ss58-address", "--coldkey-ss58", "--key"}:
            normalized.extend(["--address", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return ["view", "portfolio", *normalized]


def _wallet_overview_json_from_portfolio(
    payload: object,
    address_hint: str | None = None,
    wallet_name: str | None = None,
    network_name: str | None = None,
    subnet_payload: object | None = None,
    hotkey_ss58: str | None = None,
) -> dict[str, object] | None:
    if not isinstance(payload, dict):
        return None
    coldkey = payload.get("coldkey_ss58") or address_hint
    free_balance = payload.get("free_balance")
    total_staked = payload.get("total_staked")
    positions = payload.get("positions")
    if not isinstance(coldkey, str):
        return None
    if not isinstance(free_balance, dict) or not isinstance(total_staked, dict):
        return None
    if not isinstance(positions, list):
        return None

    try:
        free_rao = int(free_balance.get("rao", 0))
        int(total_staked.get("rao", 0))
    except (TypeError, ValueError):
        return None

    subnet_rows = _btcli_wallet_overview_subnets_from_metagraph(
        subnet_payload, coldkey, wallet_name, hotkey_ss58=hotkey_ss58
    )
    if subnet_rows is None or (not subnet_rows and positions):
        subnet_rows = []
        for position in positions:
            if not isinstance(position, dict):
                return None
            subnet_rows.append(position)

    wallet_label = coldkey if not wallet_name else f"{wallet_name}|{coldkey}"
    return {
        "wallet": wallet_label,
        "network": network_name or "custom",
        "subnets": subnet_rows,
        "total_balance": free_rao / RAO_PER_TAO,
    }


def _btcli_wallet_overview_display_ss58(ss58: str) -> str:
    if len(ss58) <= 12:
        return ss58
    return f"{ss58[:4]}...{ss58[-4:]}"


def _format_btcli_wallet_overview_tau(value: object, decimals: int = 9) -> str:
    amount = _btcli_numeric_tao(value)
    if amount is None:
        amount = 0.0
    return f"{amount:.{decimals}f} τ"


def _render_btcli_wallet_overview_text_from_portfolio(
    payload: object,
    address_hint: str | None = None,
    wallet_name: str | None = None,
    network_name: str | None = None,
    subnet_payload: object | None = None,
    hotkey_ss58: str | None = None,
) -> str | None:
    normalized = _wallet_overview_json_from_portfolio(
        payload,
        address_hint=address_hint,
        wallet_name=wallet_name,
        network_name=network_name,
        subnet_payload=subnet_payload,
        hotkey_ss58=hotkey_ss58,
    )
    if normalized is None or not isinstance(payload, dict):
        return None
    wallet_label = normalized.get("wallet")
    subnets = normalized.get("subnets")
    network = normalized.get("network")
    free_balance = payload.get("free_balance")
    if not isinstance(wallet_label, str) or not isinstance(subnets, list) or not isinstance(network, str):
        return None
    display_name, _, coldkey_ss58 = wallet_label.partition("|")
    if not coldkey_ss58:
        display_name = wallet_name or wallet_label
        coldkey_ss58 = wallet_label
    lines = ["Wallet", "", f"{display_name} : {coldkey_ss58}", f"Network: {network}"]
    for subnet in subnets:
        if not isinstance(subnet, dict):
            return None
        netuid = subnet.get("netuid", "?")
        name = str(subnet.get("name") or "")
        symbol = str(subnet.get("symbol") or "")
        header = f"Subnet: {netuid}"
        if name:
            header += f": {name}"
        if symbol:
            header += f" {symbol}"
        lines.append(header)
        neurons = subnet.get("neurons")
        if isinstance(neurons, list):
            for neuron in neurons:
                if not isinstance(neuron, dict):
                    return None
                neuron_coldkey = str(neuron.get("coldkey") or display_name)
                hotkey = str(neuron.get("hotkey") or "default")
                uid = neuron.get("uid", "?")
                stake = _format_btcli_wallet_overview_tau(neuron.get("stake"), decimals=9)
                active = neuron.get("active")
                permit = neuron.get("validator_permit")
                lines.append(
                    f"  {neuron_coldkey}/{hotkey} uid={uid} stake={stake} active={active} validator_permit={permit}"
                )
    if isinstance(free_balance, dict):
        lines.extend(["", f"Wallet free balance: {_format_btcli_wallet_overview_tau(free_balance, decimals=4)}"])
    return "\n".join(lines) + "\n"


def _wallet_overview_enriched_payloads(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str], payload: object
) -> tuple[object | None, str | None, str | None, str | None]:
    subnet_payload = None
    wallet_name = _btcli_requested_wallet(original_args)
    wallet_dir = _btcli_requested_wallet_dir(original_args)
    requested_hotkey = _btcli_requested_hotkey(original_args)
    hotkey_ss58 = _btcli_wallet_hotkey_ss58(wallet_dir, wallet_name, requested_hotkey)
    context_args = _btcli_wallet_overview_context_args(rewritten_args)
    coldkey_ss58 = None
    if isinstance(payload, dict):
        maybe_coldkey = payload.get("coldkey_ss58")
        if isinstance(maybe_coldkey, str) and maybe_coldkey:
            coldkey_ss58 = maybe_coldkey
    if coldkey_ss58:
        dynamic_result = runner.run(["view", "dynamic", *context_args, "--output", "json"], check=False, capture=True)
        dynamic_stdout = dynamic_result.stdout if isinstance(dynamic_result.stdout, str) else str(dynamic_result.stdout or "")
        try:
            dynamic_subnets = json.loads(dynamic_stdout.strip()) if dynamic_stdout.strip() else []
        except json.JSONDecodeError:
            dynamic_subnets = []
        subnet_payloads: list[dict[str, object]] = []
        if isinstance(dynamic_subnets, list):
            for subnet in dynamic_subnets:
                if not isinstance(subnet, dict):
                    continue
                try:
                    netuid = int(subnet.get("netuid", 0))
                except (TypeError, ValueError):
                    continue
                if netuid <= 0:
                    continue
                metagraph = runner.run(
                    ["view", "metagraph", "--netuid", str(netuid), *context_args, "--output", "json"],
                    check=False,
                    capture=True,
                )
                metagraph_stdout = metagraph.stdout if isinstance(metagraph.stdout, str) else str(metagraph.stdout or "")
                try:
                    metagraph_payload = json.loads(metagraph_stdout.strip()) if metagraph_stdout.strip() else None
                except json.JSONDecodeError:
                    metagraph_payload = None
                if isinstance(metagraph_payload, dict):
                    subnet_payloads.append(
                        {
                            "netuid": netuid,
                            "tempo": subnet.get("tempo", metagraph_payload.get("tempo", 0)),
                            "name": subnet.get("name", ""),
                            "symbol": subnet.get("symbol", ""),
                            "neurons": metagraph_payload.get("neurons", []),
                        }
                    )
        subnet_payload = subnet_payloads
    return subnet_payload, wallet_name, coldkey_ss58, hotkey_ss58



def _run_btcli_wallet_overview_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    run_args = list(rewritten_args)
    if not _requests_json_output(original_args) and "--output" not in run_args:
        run_args.extend(["--output", "json"])
    result = runner.run(run_args, check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    stripped = stdout.strip()
    try:
        portfolio_payload = json.loads(stripped) if stripped else None
    except json.JSONDecodeError:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    subnet_payload, wallet_name, _coldkey_ss58, hotkey_ss58 = _wallet_overview_enriched_payloads(
        runner, original_args, rewritten_args, portfolio_payload
    )
    if not _requests_json_output(original_args):
        rendered = _render_btcli_wallet_overview_text_from_portfolio(
            portfolio_payload,
            address_hint=_btcli_wallet_overview_requested_address(original_args),
            wallet_name=wallet_name,
            network_name=_btcli_wallet_overview_requested_network(original_args),
            subnet_payload=subnet_payload,
            hotkey_ss58=hotkey_ss58,
        )
        if rendered is not None:
            return result, rendered
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    normalized = _wallet_overview_json_from_portfolio(
        portfolio_payload,
        address_hint=_btcli_wallet_overview_requested_address(original_args),
        wallet_name=wallet_name,
        network_name=_btcli_wallet_overview_requested_network(original_args),
        subnet_payload=subnet_payload,
        hotkey_ss58=hotkey_ss58,
    )
    if normalized is None:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    return result, json.dumps(normalized, ensure_ascii=False) + "\n"



def _btcli_wallet_overview_context_args(args: Sequence[str]) -> list[str]:
    context_args: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--network", "--endpoint"} and i + 1 < len(args):
            context_args.extend([token, args[i + 1]])
            i += 2
            continue
        i += 1
    return context_args


def _btcli_wallet_overview_requested_network(args: Sequence[str]) -> str | None:
    for i, token in enumerate(args[2:], start=2):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_wallet_overview_subnets_from_metagraph(
    payload: object, coldkey_ss58: str, wallet_name: str | None, hotkey_ss58: str | None = None
) -> list[dict[str, object]] | None:
    if not isinstance(payload, list):
        return None

    subnet_rows: list[dict[str, object]] = []
    for subnet in payload:
        if not isinstance(subnet, dict):
            return None
        try:
            netuid = int(subnet.get("netuid", 0))
            tempo = int(subnet.get("tempo", 0))
        except (TypeError, ValueError):
            return None
        neurons_payload = subnet.get("neurons")
        if not isinstance(neurons_payload, list):
            return None
        matched_neurons: list[dict[str, object]] = []
        for neuron in neurons_payload:
            if not isinstance(neuron, dict):
                return None
            neuron_coldkey = neuron.get("coldkey")
            if str(neuron_coldkey) != coldkey_ss58:
                continue
            neuron_hotkey_ss58 = neuron.get("hotkey")
            if hotkey_ss58 and str(neuron_hotkey_ss58) != hotkey_ss58:
                continue
            hotkey_name = "default"
            if isinstance(neuron_hotkey_ss58, str) and neuron_hotkey_ss58 == coldkey_ss58:
                hotkey_name = "default"
            matched_neurons.append(
                {
                    "coldkey": wallet_name or coldkey_ss58,
                    "hotkey": hotkey_name,
                    "uid": neuron.get("uid"),
                    "active": neuron.get("active"),
                    "stake": _btcli_numeric_tao(neuron.get("stake_tao")) or 0.0,
                    "rank": float(neuron.get("rank", 0.0) or 0.0),
                    "trust": float(neuron.get("trust", 0.0) or 0.0),
                    "consensus": float(neuron.get("consensus", 0.0) or 0.0),
                    "incentive": float(neuron.get("incentive", 0.0) or 0.0),
                    "dividends": float(neuron.get("dividends", 0.0) or 0.0),
                    "emission": int((_btcli_numeric_tao(neuron.get("emission")) or 0.0) * RAO_PER_TAO),
                    "validator_trust": float(neuron.get("validator_trust", 0.0) or 0.0),
                    "validator_permit": neuron.get("validator_permit"),
                    "last_update": neuron.get("last_update"),
                    "axon": None,
                    "hotkey_ss58": neuron_hotkey_ss58,
                }
            )
        if matched_neurons:
            subnet_rows.append(
                {
                    "netuid": netuid,
                    "tempo": tempo,
                    "neurons": matched_neurons,
                    "name": str(subnet.get("name") or ("root" if netuid == 0 else "")),
                    "symbol": str(subnet.get("symbol") or ""),
                }
            )
    return subnet_rows


def _btcli_wallet_overview_requested_address(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("wallet", "overview"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token in {"--ss58", "--ss58-address", "--coldkey-ss58", "--key", "--address"} and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_wallet_get_identity_requested_address(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("wallet", "get-identity"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token in {"--ss58", "--ss58-address", "--coldkey-ss58", "--key", "--address"} and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_wallet_get_identity_requested_network(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("wallet", "get-identity"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_wallet_get_identity_requested_chain(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("wallet", "get-identity"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--endpoint" and i + 1 < len(args):
            return args[i + 1]
    network = _btcli_wallet_get_identity_requested_network(args)
    if network in {"local", "localnet"}:
        return "ws://127.0.0.1:9944"
    return None


def _btcli_wallet_pub_ss58(pubfile: Path) -> str | None:
    try:
        payload = json.loads(pubfile.read_text().strip())
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    ss58_address = payload.get("ss58Address")
    return ss58_address if isinstance(ss58_address, str) and ss58_address else None


def _btcli_wallet_coldkey_ss58(wallet_dir: str | None, wallet_name: str | None) -> str | None:
    if not wallet_dir or not wallet_name:
        return None
    return _btcli_wallet_pub_ss58(Path(wallet_dir) / wallet_name / "coldkeypub.txt")


def _btcli_wallet_hotkey_ss58(wallet_dir: str | None, wallet_name: str | None, hotkey_name: str | None) -> str | None:
    if not wallet_dir or not wallet_name:
        return None
    hotkey = hotkey_name or "default"
    return _btcli_wallet_pub_ss58(Path(wallet_dir) / wallet_name / "hotkeys" / f"{hotkey}pub.txt")


def _btcli_wallet_list_hotkeys(wallet_dir: str | None, wallet_name: str | None) -> list[dict[str, str]]:
    if not wallet_dir or not wallet_name:
        return []
    hotkeys_dir = Path(wallet_dir) / wallet_name / "hotkeys"
    try:
        hotkeypubs = sorted(hotkeys_dir.glob("*pub.txt"))
    except OSError:
        return []
    hotkeys: list[dict[str, str]] = []
    for hotkeypub in hotkeypubs:
        if not hotkeypub.is_file():
            continue
        hotkey_name = hotkeypub.name.removesuffix("pub.txt")
        hotkey_ss58 = _btcli_wallet_pub_ss58(hotkeypub)
        if not hotkey_name or not hotkey_ss58:
            continue
        hotkeys.append({"name": hotkey_name, "ss58_address": hotkey_ss58})
    return hotkeys


def _btcli_wallet_list_json_payload(payload: object, wallet_dir: str | None) -> dict[str, object] | None:
    if not isinstance(payload, list):
        return None
    wallets: list[dict[str, object]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            return None
        wallet_name = entry.get("name")
        if not isinstance(wallet_name, str) or not wallet_name:
            return None
        ss58_address = _btcli_wallet_coldkey_ss58(wallet_dir, wallet_name)
        hotkeys = _btcli_wallet_list_hotkeys(wallet_dir, wallet_name)
        if not ss58_address and not hotkeys:
            wallets.append(dict(entry))
            continue
        wallet_payload: dict[str, object] = {"name": wallet_name}
        if ss58_address:
            wallet_payload["ss58_address"] = ss58_address
        wallet_payload["hotkeys"] = hotkeys
        wallets.append(wallet_payload)
    return {"wallets": wallets}

def _render_btcli_wallet_list_text(wallet_dir: str | None) -> str | None:
    if not wallet_dir:
        return None
    try:
        wallet_names = sorted(path.name for path in Path(wallet_dir).iterdir() if path.is_dir())
    except OSError:
        return None
    if not wallet_names:
        return None
    lines = ["Wallets"]
    for wallet_index, wallet_name in enumerate(wallet_names):
        wallet_is_last = wallet_index == len(wallet_names) - 1
        wallet_branch = "└──" if wallet_is_last else "├──"
        child_indent = "    " if wallet_is_last else "│   "
        coldkey_ss58 = _btcli_wallet_coldkey_ss58(wallet_dir, wallet_name) or ""
        lines.append(f"{wallet_branch} Coldkey {wallet_name}  ss58_address {coldkey_ss58}".rstrip())
        hotkeys = _btcli_wallet_list_hotkeys(wallet_dir, wallet_name)
        for hotkey_index, hotkey in enumerate(hotkeys):
            hotkey_is_last = hotkey_index == len(hotkeys) - 1
            hotkey_branch = "└──" if hotkey_is_last else "├──"
            hotkey_name = hotkey["name"]
            hotkey_ss58 = hotkey["ss58_address"]
            lines.append(f"{child_indent}{hotkey_branch} Hotkey {hotkey_name}  ss58_address ")
            lines.append(f"{child_indent}    {hotkey_ss58}")
    return "\n".join(lines) + "\n"


def _btcli_requested_wallet(args: Sequence[str]) -> str | None:
    for i, token in enumerate(args[2:], start=2):
        if token in {"--wallet-name", "--wallet", "--name", "--wallet-name-or-ss58"} and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_requested_wallet_dir(args: Sequence[str]) -> str | None:
    for i, token in enumerate(args[2:], start=2):
        if token in {"--wallet-path", "--wallet_path", "--wallet-dir", "-p"} and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_requested_hotkey(args: Sequence[str]) -> str:
    for i, token in enumerate(args[2:], start=2):
        if token in {"--hotkey", "--hotkey-name"} and i + 1 < len(args):
            return args[i + 1]
    return "default"


def _format_btcli_missing_wallet_stderr(wallet_name: str, wallet_dir: str, hotkey: str) -> str:
    return (
        "❌ Error: Wallet does not exist. \n"
        f"Please verify your wallet information: Wallet (Name: '{wallet_name}', Hotkey: '{hotkey}',\n"
        f"Path: '{wallet_dir}')\n"
    )


def _btcli_wallet_overview_missing_wallet_stderr(args: Sequence[str], stderr: str) -> str | None:
    if tuple(args[:2]) != ("wallet", "overview") or not stderr:
        return None
    wallet_name = _btcli_requested_wallet(args)
    wallet_dir = _btcli_requested_wallet_dir(args)
    if not wallet_name or not wallet_dir:
        return None
    missing_wallet_msg = (
        f"Could not resolve coldkey address from wallet '{wallet_name}' in {wallet_dir}."
    )
    if missing_wallet_msg in stderr:
        return _format_btcli_missing_wallet_stderr(
            wallet_name, wallet_dir, _btcli_requested_hotkey(args)
        )
    return None


def _btcli_subnets_register_missing_wallet_stderr(args: Sequence[str], stderr: str) -> str | None:
    if tuple(args[:2]) not in {("subnets", "register"), ("subnets", "pow-register")} or not stderr:
        return None
    wallet_name = _btcli_requested_wallet(args)
    wallet_dir = _btcli_requested_wallet_dir(args)
    if not wallet_name or not wallet_dir:
        return None
    missing_wallet_msg = (
        f"Could not resolve coldkey address from wallet '{wallet_name}' in {wallet_dir}."
    )
    alternate_missing_wallet_msg = f"Wallet '{wallet_name}' not found in {wallet_dir}."
    if missing_wallet_msg in stderr or alternate_missing_wallet_msg in stderr:
        return _format_btcli_missing_wallet_stderr(
            wallet_name, wallet_dir, _btcli_requested_hotkey(args)
        )
    return None


def _btcli_subnets_register_wallet_prompt_abort_stderr(
    args: Sequence[str], stderr: str
) -> str | None:
    if tuple(args[:2]) not in {("subnets", "register"), ("subnets", "pow-register")} or not stderr:
        return None
    if _btcli_requested_wallet(args) or _btcli_requested_wallet_dir(args):
        return None
    if (
        "Cannot prompt for coldkey password: stdin is not a TTY" not in stderr
        and "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD." not in stderr
    ):
        return None
    return (
        "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
        "Aborted.\n"
    )


def _btcli_subnets_start_missing_wallet_stderr(args: Sequence[str], stderr: str) -> str | None:
    if tuple(args[:2]) != ("subnets", "start") or not stderr:
        return None
    wallet_name = _btcli_requested_wallet(args)
    wallet_dir = _btcli_requested_wallet_dir(args)
    if not wallet_name or not wallet_dir:
        return None
    missing_wallet_msg = (
        f"Wallet '{wallet_name}' not found in {wallet_dir}."
    )
    if missing_wallet_msg in stderr:
        return _format_btcli_missing_wallet_stderr(
            wallet_name, wallet_dir, _btcli_requested_hotkey(args)
        )
    return None


def _btcli_subnets_start_wallet_prompt_abort_stderr(
    args: Sequence[str], stderr: str
) -> str | None:
    if tuple(args[:2]) != ("subnets", "start") or not stderr:
        return None
    if _btcli_requested_wallet(args) or _btcli_requested_wallet_dir(args):
        return None
    if (
        "Cannot prompt for coldkey password: stdin is not a TTY" not in stderr
        and "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD." not in stderr
    ):
        return None
    return (
        "Enter the wallet name (which you used to create the subnet) (default): \n"
        "Aborted.\n"
    )


def _btcli_subnets_start_not_owner_stderr(args: Sequence[str], stderr: str) -> str | None:
    if tuple(args[:2]) != ("subnets", "start") or not stderr:
        return None
    if "doesn't own the specified subnet" not in stderr:
        return None
    return "❌ This wallet doesn't own the specified subnet.\n"


def _btcli_missing_wallet_stderr(args: Sequence[str], stderr: str) -> str | None:
    return _btcli_wallet_overview_missing_wallet_stderr(
        args, stderr
    ) or _btcli_subnets_register_missing_wallet_stderr(
        args, stderr
    ) or _btcli_subnets_register_wallet_prompt_abort_stderr(
        args, stderr
    ) or _btcli_subnets_start_missing_wallet_stderr(
        args, stderr
    ) or _btcli_subnets_start_wallet_prompt_abort_stderr(
        args, stderr
    ) or _btcli_wallet_swap_check_stderr(args, stderr)


def _btcli_stake_requested_netuid(args: Sequence[str]) -> str | None:
    for i, token in enumerate(args[2:], start=2):
        if token == "--netuid" and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_subnet_missing_args_stderr(args: Sequence[str], stderr: str) -> str | None:
    if not stderr:
        return None
    command = tuple(args[:2])
    child_command = tuple(args[:3])
    if command in {
        ("subnets", "show"),
        ("subnets", "start"),
        ("subnets", "check-start"),
        ("subnets", "set-symbol"),
        ("subnets", "register"),
        ("subnets", "pow-register"),
    }:
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--netuid <NETUID>" not in stderr:
            return None
        return "Netuid: Aborted.\n"
    if child_command in {
        ("subnets", "mechanisms", "count"),
        ("subnets", "mechanisms", "set"),
        ("subnets", "mechanisms", "emissions"),
        ("subnets", "mechanisms", "split-emissions"),
    }:
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--netuid <NETUID>" not in stderr:
            return None
        return "Netuid: Aborted.\n"
    if command in {("subnets", "create"), ("subnets", "set-identity")}:
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--name <NAME>" not in stderr:
            return None
        if "--json-output" in args and "--no-prompt" not in args:
            return (
                BTCLI_SUBNET_CREATE_JSON_PROMPT_CONFLICT_MESSAGE
                if command == ("subnets", "create")
                else BTCLI_SUBNET_SET_IDENTITY_JSON_PROMPT_CONFLICT_MESSAGE
            )
        return (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
    return None


def _btcli_stake_missing_args_stderr(args: Sequence[str], stderr: str) -> str | None:
    if not stderr:
        return None
    command = tuple(args[:2])
    child_command = tuple(args[:3])
    if child_command == ("stake", "child", "set"):
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--netuid <NETUID>" in stderr and "--children <CHILDREN>" in stderr:
            return BTCLI_STAKE_CHILD_SET_NETUID_PROMPT_ABORT
        if "--children <CHILDREN>" in stderr:
            return BTCLI_STAKE_CHILD_SET_CHILDREN_PROMPT_ABORT
        return None
    if child_command == ("stake", "child", "take"):
        if (
            "Cannot prompt for coldkey password: stdin is not a TTY" in stderr
            or "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD." in stderr
        ):
            return BTCLI_STAKE_CHILD_TAKE_WALLET_PROMPT_ABORT
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--netuid <NETUID>" in stderr and "--take <TAKE>" in stderr:
            return BTCLI_STAKE_CHILD_TAKE_WALLET_PROMPT_ABORT
        return None
    if command in {("stake", "add"), ("stake", "remove"), ("stake", "set-auto")}:
        if command == ("stake", "set-auto"):
            if (
                "Cannot prompt for coldkey password: stdin is not a TTY" in stderr
                or "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD." in stderr
            ):
                return (
                    "Safe staking: enabled (from config).\n"
                    "Enter the wallet name (default): \n"
                    "Aborted.\n"
                )
            if "the following required arguments were not provided:" not in stderr:
                return None
            if "--netuid <NETUID>" not in stderr:
                return None
            return (
                "Safe staking: enabled (from config).\n"
                "Enter the wallet name (default): \n"
                "Aborted.\n"
            )
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--amount <AMOUNT>" not in stderr and "--netuid <NETUID>" not in stderr:
            return None
        prompt = "Enter the wallet name (default): " if _btcli_stake_requested_netuid(args) else "Enter the netuid to use. Leave blank for all netuids: "
        return (
            "Safe staking: enabled (from config).\n"
            "Rate tolerance: 0.005 (0.5%) by default. Set this using `btcli config set` or \n"
            "`--tolerance` flag\n"
            "Partial staking: disabled (from config).\n"
            f"{prompt}\n"
            "Aborted.\n"
        )
    if command == ("stake", "move"):
        if "the following required arguments were not provided:" not in stderr:
            return None
        return (
            "This transaction will move stake to another hotkey while keeping the same coldkey ownership. Do you wish to continue?  [y/n] (n):\n"
            "Aborted.\n"
        )
    if command in {("stake", "transfer"), ("stake", "transfer-stake")}:
        if "the following required arguments were not provided:" not in stderr:
            return None
        return (
            "This transaction will transfer ownership from one coldkey to another, in subnets which have enabled it. You should ensure that the destination coldkey is not a validator hotkey before continuing. Do you wish to continue? [y/n] (n):\n"
            "Aborted.\n"
        )
    if command == ("stake", "swap"):
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--origin-netuid <ORIGIN_NETUID>" not in stderr and "--dest-netuid <DEST_NETUID>" not in stderr and "--amount <AMOUNT>" not in stderr:
            return None
        return (
            "This command moves stake from one subnet to another subnet while keeping the same coldkey-hotkey pair.\n"
            "Safe staking: enabled (from config).\n"
            "Rate tolerance: 0.005 (0.5%) by default. Set this using `btcli config set` or `--tolerance` flag\n"
            "Partial staking: disabled (from config).\n"
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
    if command == ("stake", "set-claim"):
        if "the following required arguments were not provided:" not in stderr:
            return None
        if "--claim-type <CLAIM_TYPE>" not in stderr:
            return None
        return (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
    if command == ("stake", "process-claim"):
        if (
            "Cannot prompt for coldkey password: stdin is not a TTY" not in stderr
            and "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD." not in stderr
            and "the following required arguments were not provided:" not in stderr
        ):
            return None
        return (
            "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
            "Aborted.\n"
        )
    return None


def _btcli_stake_wizard_prompt_abort_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str | None:
    if tuple(original_args[:2]) != ("stake", "wizard"):
        return None
    if tuple(rewritten_args[:2]) != ("stake", "wizard"):
        return None
    stripped = stdout.strip()
    if not stripped:
        return None
    if "=== Staking Wizard ===" not in stripped:
        return None
    if "You need TAO to stake. Transfer some TAO to your coldkey first." not in stripped:
        return None
    return (
        "Enter the wallet name (Hint: You can set this with `btcli config set --wallet-name`) (default): \n"
        "Aborted.\n"
    )


def _btcli_stake_child_set_prompt_abort_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str | None:
    if tuple(original_args[:3]) != ("stake", "child", "set"):
        return None
    if tuple(rewritten_args[:2]) != ("stake", "set-children"):
        return None
    stripped = stdout.strip()
    if not stripped:
        return None
    if "Cannot prompt for coldkey password: stdin is not a TTY" in stripped:
        return BTCLI_STAKE_CHILD_SET_WALLET_PROMPT_ABORT
    return None


def _btcli_stake_child_take_prompt_abort_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str | None:
    if tuple(original_args[:3]) != ("stake", "child", "take"):
        return None
    if tuple(rewritten_args[:2]) != ("stake", "childkey-take"):
        return None
    stripped = stdout.strip()
    if not stripped:
        return None
    if "Cannot prompt for coldkey password: stdin is not a TTY" in stripped:
        return BTCLI_STAKE_CHILD_TAKE_WALLET_PROMPT_ABORT
    return None


def _normalize_btcli_stake_child_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    normalized = _btcli_stake_child_set_prompt_abort_output(original_args, rewritten_args, stdout)
    if normalized is not None:
        return normalized
    normalized = _btcli_stake_child_take_prompt_abort_output(original_args, rewritten_args, stdout)
    return normalized if normalized is not None else stdout


def _normalize_btcli_stake_wizard_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    normalized = _btcli_stake_wizard_prompt_abort_output(original_args, rewritten_args, stdout)
    return normalized if normalized is not None else stdout


def _normalize_btcli_subnets_burn_cost_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    if tuple(original_args[:2]) != ("subnets", "burn-cost"):
        return stdout
    if tuple(rewritten_args[:2]) != ("subnet", "create-cost"):
        return stdout
    stripped = stdout.strip()
    if not stripped:
        return stdout
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stdout

    cost_tao = payload.get("cost_tao")
    cost_rao = payload.get("cost_rao")
    if cost_tao is None or cost_rao is None:
        return stdout

    normalized = {
        "burn_cost": {
            "rao": cost_rao,
            "tao": cost_tao,
        },
        "error": "",
    }
    return json.dumps(normalized) + "\n"


def _btcli_normalized_stderr(args: Sequence[str], stderr: str) -> str | None:
    return (
        _btcli_missing_wallet_stderr(args, stderr)
        or _btcli_subnets_start_not_owner_stderr(args, stderr)
        or _btcli_subnet_missing_args_stderr(args, stderr)
        or _btcli_stake_missing_args_stderr(args, stderr)
    )


def _normalize_btcli_wallet_overview_stderr(args: Sequence[str], stderr: str) -> str:
    return _btcli_wallet_overview_missing_wallet_stderr(args, stderr) or stderr


def _btcli_wallet_balance_requested_network(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("wallet", "balance"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_wallet_balance_requested_chain(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("wallet", "balance"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--endpoint" and i + 1 < len(args):
            return args[i + 1]
    network = _btcli_wallet_balance_requested_network(args)
    if network in {"local", "localnet"}:
        return "ws://127.0.0.1:9944"
    return None


def _render_btcli_wallet_balance_text(original_args: Sequence[str], payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    if not {"address", "balance_rao", "balance_tao"}.issubset(payload):
        return None

    address = payload.get("address")
    if not isinstance(address, str) or not address:
        return None

    balance_tao = _btcli_numeric_tao(payload.get("balance_tao"))
    if balance_tao is None:
        balance_tao = 0.0
    network = _btcli_wallet_balance_requested_network(original_args) or "custom"
    chain = _btcli_wallet_balance_requested_chain(original_args)
    show_local_warning = network in {"local", "localnet"} or chain == "ws://127.0.0.1:9944"
    amount = f"{balance_tao:.9f} τ"

    lines: list[str] = []
    if show_local_warning:
        lines.extend([
            "Warning: Verify your local subtensor is running on port 9944.",
            "",
        ])
    lines.extend(
        [
            "Wallet Coldkey Balance",
            f"Network: {network}",
            "",
            "Wallet Name | Coldkey Address | Free Balance | Staked | Total Balance",
            f"Provided Address 1 | {address} | {amount} | 0.000000000 τ | {amount}",
            "",
            f"Total Balance |  | {amount} | 0.000000000 τ | {amount}",
        ]
    )
    return "\n".join(lines) + "\n"


def _run_btcli_wallet_balance_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    run_args = list(rewritten_args)
    if not _requests_json_output(original_args) and "--output" not in run_args:
        run_args.extend(["--output", "json"])
    result = runner.run(run_args, check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    if _requests_json_output(original_args):
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    stripped = stdout.strip()
    try:
        payload = json.loads(stripped) if stripped else None
    except json.JSONDecodeError:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    rendered = _render_btcli_wallet_balance_text(original_args, payload)
    if rendered is not None:
        return result, rendered
    return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)


def _requests_json_output(args: Sequence[str]) -> bool:
    for i, token in enumerate(args):
        if token == "--json-output":
            return True
        if token == "--output" and i + 1 < len(args) and args[i + 1] == "json":
            return True
    return False


def _reorder_dry_run_output(stdout: str, stderr: str) -> tuple[str, str]:
    if not stdout or not stderr:
        return stdout, stderr
    if not stderr.lstrip().startswith("[dry-run] Transaction would be submitted"):
        return stdout, stderr
    if '"dry_run"' not in stdout or '"call_data_hex"' not in stdout:
        return stdout, stderr
    lines = stdout.splitlines(keepends=True)
    if len(lines) < 2:
        return stdout, stderr
    return lines[0] + stderr + "".join(lines[1:]), ""


def _normalize_btcli_wallet_overview_json_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    if tuple(original_args[:2]) != ("wallet", "overview"):
        return stdout
    if tuple(rewritten_args[:2]) != ("view", "portfolio"):
        return stdout
    stripped = stdout.strip()
    if not stripped:
        return stdout
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stdout
    normalized = _wallet_overview_json_from_portfolio(
        payload, address_hint=_btcli_wallet_overview_requested_address(original_args)
    )
    if normalized is None:
        return stdout
    return json.dumps(normalized) + "\n"



def _normalize_btcli_stake_flags(args: Sequence[str]) -> list[str]:
    if len(args) >= 2 and args[0] == "stake" and args[1] in BTCLI_STAKE_COMMANDS_WITH_FLAG_NORMALIZATION:
        command_name = args[1]
        unsupported_flag_help: dict[str, str] = {}
        if command_name == "add":
            unsupported_flag_help = BTCLI_STAKE_ADD_UNSUPPORTED_FLAG_HELP
        elif command_name == "remove":
            unsupported_flag_help = BTCLI_STAKE_REMOVE_UNSUPPORTED_FLAG_HELP
        elif command_name == "set-auto":
            unsupported_flag_help = BTCLI_STAKE_SET_AUTO_UNSUPPORTED_FLAG_HELP

        btcli_stake_flags = {
            "--wallet-name",
            "--wallet-path",
            "--hotkey",
            "--hotkey-ss58-address",
            "--json-output",
            "--no-prompt",
            "--prompt",
            "--period",
            "--era",
            *unsupported_flag_help,
        }
        if any(token in btcli_stake_flags for token in args[2:]):
            command = list(args[:2])
            normalized: list[str] = []
            i = 2
            while i < len(args):
                token = args[i]
                if token in unsupported_flag_help:
                    detail = unsupported_flag_help[token]
                    raise click.ClickException(
                        f"btcli-compatible `stake {command_name}` flag '{token}' is not implemented in taocli/agcli yet; {detail}"
                    )
                if token == "--wallet-name":
                    normalized.extend(["--wallet", args[i + 1]])
                    i += 2
                    continue
                if token == "--wallet-path":
                    normalized.extend(["--wallet-dir", args[i + 1]])
                    i += 2
                    continue
                if token in {"--hotkey", "--hotkey-ss58-address"}:
                    if command_name in {"add", "remove", "transfer", "transfer-stake", "swap", "set-auto"}:
                        normalized.extend(["--hotkey-address", args[i + 1]])
                    else:
                        normalized.extend(["--hotkey-name", args[i + 1]])
                    i += 2
                    continue
                if token == "--json-output":
                    normalized.extend(["--output", "json"])
                    i += 1
                    continue
                if token in {"--period", "--era"}:
                    normalized.extend(["--mortality-blocks", args[i + 1]])
                    i += 2
                    continue
                if token in BTCLI_BOOL_FLAG_ALIASES:
                    bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
                    if bool_alias:
                        normalized.append(bool_alias)
                    i += 1
                    continue
                normalized.append(token)
                if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
                    normalized.append(args[i + 1])
                    i += 2
                    continue
                i += 1
            return [*command, *normalized]

    if len(args) >= 2 and args[0] == "stake" and args[1] == "swap":
        for token in args[2:]:
            if token in BTCLI_STAKE_SWAP_UNSUPPORTED_FLAGS:
                detail = BTCLI_STAKE_SWAP_UNSUPPORTED_FLAG_HELP[token]
                raise click.ClickException(
                    f"btcli-compatible `stake swap` flag '{token}' is not implemented in taocli/agcli yet; {detail}"
                )

    return _normalize_btcli_read_flags(args)


def _normalize_btcli_stake_set_claim_args(args: Sequence[str]) -> list[str]:
    if len(args) < 2 or args[0] != "stake" or args[1] != "set-claim":
        return list(args)

    btcli_flags = {
        "--netuids",
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
    }
    if not any(token in btcli_flags for token in args[2:]) and len(args) <= 2:
        return list(args)

    normalized = ["stake", "set-claim"]
    i = 2
    while i < len(args):
        token = args[i]
        if not token.startswith("-"):
            normalized.extend(["--claim-type", token.lower()])
            i += 1
            continue
        if token == "--netuids":
            normalized.extend(["--subnets", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized


def _normalize_btcli_stake_process_claim_args(args: Sequence[str]) -> list[str]:
    if len(args) < 2 or args[0] != "stake" or args[1] != "process-claim":
        return list(args)

    btcli_flags = {
        "--netuids",
        "--netuid",
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
    }
    if not any(token in btcli_flags for token in args[2:]):
        return list(args)

    normalized = ["stake", "process-claim"]
    i = 2
    while i < len(args):
        token = args[i]
        if token in {"--netuids", "--netuid"}:
            normalized.extend(["--netuids", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized


def _normalize_btcli_stake_child_set_args(args: Sequence[str]) -> list[str]:
    if len(args) < 3 or args[0] != "stake" or args[1] != "child" or args[2] != "set":
        return list(args)

    normalized = ["stake", "set-children"]
    children: list[str] = []
    proportions: list[str] = []
    i = 3
    while i < len(args):
        token = args[i]
        if token in BTCLI_STAKE_CHILD_SET_UNSUPPORTED_FLAG_HELP:
            detail = BTCLI_STAKE_CHILD_SET_UNSUPPORTED_FLAG_HELP[token]
            raise click.ClickException(
                f"btcli-compatible `stake child set` flag '{token}' is not implemented in taocli/agcli yet; {detail}"
            )
        if token == "--children":
            if i + 1 >= len(args):
                raise click.UsageError("btcli-compatible `stake child set` flag '--children' requires a value.")
            children.append(args[i + 1])
            i += 2
            continue
        if token in {"--proportions", "--prop"}:
            if i + 1 >= len(args):
                raise click.UsageError(f"btcli-compatible `stake child set` flag '{token}' requires a value.")
            proportions.append(args[i + 1])
            i += 2
            continue
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-address", args[i + 1]])
            i += 2
            continue
        if token == "--netuid":
            normalized.extend(["--netuid", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    if not proportions and children:
        raise click.UsageError(BTCLI_STAKE_CHILD_SET_PROPORTIONS_UNSUPPORTED_MESSAGE)
    if len(children) != len(proportions):
        raise click.UsageError(BTCLI_STAKE_CHILD_SET_CHILDREN_REQUIRED_MESSAGE)
    if children:
        child_pairs = ",".join(f"{proportion}:{child}" for child, proportion in zip(children, proportions, strict=True))
        normalized.extend(["--children", child_pairs])
    return normalized


def _normalize_btcli_stake_child_take_args(args: Sequence[str]) -> list[str]:
    if len(args) < 3 or args[0] != "stake" or args[1] != "child" or args[2] != "take":
        return list(args)

    normalized = ["stake", "childkey-take"]
    saw_take = False
    i = 3
    while i < len(args):
        token = args[i]
        if token in BTCLI_STAKE_CHILD_TAKE_UNSUPPORTED_FLAG_HELP:
            detail = BTCLI_STAKE_CHILD_TAKE_UNSUPPORTED_FLAG_HELP[token]
            raise click.ClickException(
                f"btcli-compatible `stake child take` flag '{token}' is not implemented in taocli/agcli yet; {detail}"
            )
        if token == "--take":
            if i + 1 >= len(args):
                raise click.UsageError("btcli-compatible `stake child take` flag '--take' requires a value.")
            normalized.extend(["--take", args[i + 1]])
            saw_take = True
            i += 2
            continue
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token in {"--hotkey", "--child-hotkey-ss58"}:
            normalized.extend(["--hotkey-address", args[i + 1]])
            i += 2
            continue
        if token == "--netuid":
            normalized.extend(["--netuid", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    if not saw_take:
        raise click.UsageError(BTCLI_STAKE_CHILD_TAKE_READ_UNSUPPORTED_MESSAGE)
    return normalized


def _normalize_btcli_stake_specific_args(args: Sequence[str]) -> list[str]:
    if len(args) >= 3 and args[0] == "stake" and args[1] == "child":
        if args[2] == "get":
            raise click.UsageError(BTCLI_STAKE_CHILD_GET_UNSUPPORTED_MESSAGE)
        if args[2] == "revoke":
            raise click.UsageError(BTCLI_STAKE_CHILD_REVOKE_UNSUPPORTED_MESSAGE)
        if args[2] == "set":
            return _normalize_btcli_stake_child_set_args(args)
        if args[2] == "take":
            return _normalize_btcli_stake_child_take_args(args)
        raise click.UsageError(BTCLI_STAKE_CHILD_UNSUPPORTED_MESSAGE)
    if len(args) >= 2 and args[0] == "stake" and args[1] == "child":
        raise click.UsageError(BTCLI_STAKE_CHILD_UNSUPPORTED_MESSAGE)
    rewritten = _normalize_btcli_stake_set_claim_args(args)
    rewritten = _normalize_btcli_stake_process_claim_args(rewritten)
    return rewritten


def _normalize_btcli_axon_flags(args: Sequence[str]) -> list[str]:

    if len(args) < 2 or args[0] != "serve" or args[1] not in {"axon", "reset"}:
        return list(args)

    btcli_axon_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
        *BTCLI_AXON_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_axon_flags for token in args[2:]):
        return list(args)

    normalized = list(args[:2])
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_AXON_UNSUPPORTED_FLAGS:
            detail = BTCLI_AXON_FLAG_HELP.get(token, "not implemented in taocli/agcli yet.")
            label = "axon set" if args[1] == "axon" else "axon reset"
            raise click.ClickException(
                f"btcli-compatible {label} flag '{token}' is not implemented in taocli yet: {detail}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized


def _normalize_btcli_config_flags(args: Sequence[str]) -> list[str]:
    if len(args) < 2 or args[0] != "config":
        return list(args)

    subcommand = args[1]
    if subcommand in BTCLI_CONFIG_UNSUPPORTED_SUBCOMMANDS:
        return list(args)
    if subcommand != "get":
        return list(args)

    normalized = ["config", "show"]
    i = 2
    while i < len(args):
        token = args[i]
        if token == "--json-output":
            raise click.NoSuchOption("--json-output")
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized


def _normalize_btcli_sudo_flags(args: Sequence[str]) -> list[str]:
    if tuple(args[:2]) != ("subnet", "hyperparams"):
        return list(args)

    normalized = ["subnet", "hyperparams"]
    i = 2
    while i < len(args):
        token = args[i]
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token == "--output" and i + 1 < len(args):
            normalized.extend([token, args[i + 1]])
            i += 2
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized


def _is_btcli_hyperparams_command(args: Sequence[str]) -> bool:
    return tuple(args[:2]) in {("sudo", "get"), ("subnets", "hyperparameters")}



def _btcli_sudo_get_rewritten_args(rewritten_args: Sequence[str]) -> list[str]:
    if tuple(rewritten_args[:2]) != ("subnet", "hyperparams"):
        return list(rewritten_args)

    normalized: list[str] = []
    has_output = False
    i = 0
    while i < len(rewritten_args):
        token = rewritten_args[i]
        if token == "--json-output":
            i += 1
            continue
        if token == "--output" and i + 1 < len(rewritten_args):
            normalized.extend([token, rewritten_args[i + 1]])
            has_output = True
            i += 2
            continue
        normalized.append(token)
        i += 1

    if has_output:
        return normalized
    return [*normalized, "--output", "json"]



def _btcli_sudo_get_hyperparams_payload(stdout: str) -> object | None:
    stripped = stdout.strip()
    if not stripped:
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None



def _btcli_sudo_get_text_subtitle(netuid: str | None) -> str:
    if netuid:
        subnet_name = BTCLI_LOCALNET_SUBNET_NAMES.get(str(netuid), "unknown")
        return f"NETUID: {netuid} ({subnet_name}) - Network: local"
    return "Network: local"



def _btcli_sudo_get_owner_label(owner_settable: object, *, hyperparameter: str | None = None) -> str:
    if hyperparameter == "user_liquidity_enabled":
        return "COMPLICATED (Owner/Sudo)"
    return "Yes" if bool(owner_settable) else "No (Root Only)"



def _btcli_sudo_get_tips(netuid: str | None) -> list[str]:
    netuid_arg = netuid or "<netuid>"
    return [
        "Tip: Use btcli sudo set --param <name> --value <value> to modify hyperparameters.",
        "Tip: Parameters marked 'No (Root Only)' require root sudo access.",
        "Tip: To set custom hyperparameters not in this list, use the exact parameter name from the chain metadata.",
        f"Example: btcli sudo set --netuid {netuid_arg} --param custom_param_name --value 123",
        "The parameter name must match exactly as defined in the chain's AdminUtils pallet metadata.",
        "For detailed documentation, visit: https://docs.bittensor.com",
    ]



def _btcli_sudo_get_description_width(records: Sequence[dict[str, object]]) -> int:
    return max(len("DESCRIPTION"), *(len(str(record["description"])) for record in records))



def _btcli_sudo_get_table_separator(
    param_width: int,
    value_width: int,
    normalized_width: int,
    owner_width: int,
    description_width: int,
) -> str:
    return (
        f"-{'-' * param_width}-+-{'-' * value_width}-+-{'-' * normalized_width}-+-"
        f"{'-' * owner_width}-+-{'-' * description_width}"
    )



def _btcli_sudo_get_table_row(
    param: str,
    value_out: str,
    normalized_out: str,
    owner_out: str,
    description_out: str,
    *,
    param_width: int,
    value_width: int,
    normalized_width: int,
    owner_width: int,
    description_width: int,
) -> str:
    return (
        f" {param:<{param_width}} | {value_out:<{value_width}} | {normalized_out:<{normalized_width}} | "
        f"{owner_out:<{owner_width}} | {description_out:<{description_width}}"
    )



def _btcli_sudo_get_text_widths(
    records: Sequence[dict[str, object]],
) -> tuple[int, int, int, int, int]:
    param_width = max(len("HYPERPARAMETER"), *(len(str(record["hyperparameter"])) for record in records))
    value_width = max(len("VALUE"), *(len(_btcli_sudo_get_render_value(record["value"])) for record in records))
    normalized_width = max(
        len("NORMALIZED"),
        *(len(_btcli_sudo_get_render_value(record["normalized_value"])) for record in records),
    )
    owner_width = max(
        len("OWNER SETTABLE"),
        *(
            len(
                _btcli_sudo_get_owner_label(
                    record["owner_settable"], hyperparameter=str(record["hyperparameter"])
                )
            )
            for record in records
        ),
    )
    description_width = _btcli_sudo_get_description_width(records)
    return param_width, value_width, normalized_width, owner_width, description_width



def _btcli_sudo_get_text_lines(records: Sequence[dict[str, object]], netuid: str | None) -> list[str]:
    param_width, value_width, normalized_width, owner_width, description_width = _btcli_sudo_get_text_widths(records)
    separator = _btcli_sudo_get_table_separator(
        param_width, value_width, normalized_width, owner_width, description_width
    )
    lines = [
        "Subnet Hyperparameters",
        _btcli_sudo_get_text_subtitle(netuid),
        "",
        _btcli_sudo_get_table_row(
            "HYPERPARAMETER",
            "VALUE",
            "NORMALIZED",
            "OWNER SETTABLE",
            "DESCRIPTION",
            param_width=param_width,
            value_width=value_width,
            normalized_width=normalized_width,
            owner_width=owner_width,
            description_width=description_width,
        ),
        separator,
    ]
    for record in records:
        lines.append(
            _btcli_sudo_get_table_row(
                str(record["hyperparameter"]),
                _btcli_sudo_get_render_value(record["value"]),
                _btcli_sudo_get_render_value(record["normalized_value"]),
                _btcli_sudo_get_owner_label(
                    record["owner_settable"], hyperparameter=str(record["hyperparameter"])
                ),
                str(record["description"]),
                param_width=param_width,
                value_width=value_width,
                normalized_width=normalized_width,
                owner_width=owner_width,
                description_width=description_width,
            )
        )
    lines.extend(["", *_btcli_sudo_get_tips(netuid)])
    return lines



def _btcli_sudo_get_json_output(payload: object) -> str | None:
    normalized = _btcli_sudo_get_json_from_hyperparams(payload)
    if normalized is None:
        return None
    return json.dumps(normalized) + "\n"



def _btcli_sudo_get_text_output(payload: object, netuid: str | None) -> str | None:
    records = _btcli_sudo_get_json_from_hyperparams(payload)
    if not records:
        return None
    return "\n".join(_btcli_sudo_get_text_lines(records, netuid)) + "\n"



def _btcli_sudo_get_requested_output(args: Sequence[str]) -> str | None:
    for i, token in enumerate(args):
        if token == "--json-output":
            return "json"
        if token == "--output" and i + 1 < len(args):
            return str(args[i + 1])
    return None



def _btcli_sudo_get_requested_netuid(args: Sequence[str]) -> str | None:
    if not _is_btcli_hyperparams_command(args):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--netuid" and i + 1 < len(args):
            return args[i + 1]
    return None


def _btcli_sudo_get_normalized_stdout(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str | None:
    if not _is_btcli_hyperparams_command(original_args):
        return None
    payload = _btcli_sudo_get_hyperparams_payload(stdout)
    if payload is None:
        return None
    requested_output = _btcli_sudo_get_requested_output(original_args)
    if requested_output == "json":
        return _btcli_sudo_get_json_output(payload)
    if requested_output is not None:
        return None
    return _btcli_sudo_get_text_output(payload, _btcli_sudo_get_requested_netuid(original_args))


def _normalize_btcli_sudo_get_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    normalized = _btcli_sudo_get_normalized_stdout(original_args, rewritten_args, stdout)
    return normalized if normalized is not None else stdout



def _run_btcli_sudo_get(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    effective_args = _btcli_sudo_get_rewritten_args(rewritten_args)
    result = runner.run(list(effective_args), check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    normalized_stdout = _normalize_btcli_sudo_get_output(original_args, effective_args, stdout)
    return result, normalized_stdout



def _run_btcli_hyperparams_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    effective_args = _btcli_sudo_get_rewritten_args(rewritten_args)
    result = runner.run(list(effective_args), check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    normalized_stdout = _normalize_btcli_sudo_get_output(original_args, effective_args, stdout)
    return result, normalized_stdout



def _is_btcli_hyperparams_alias_pair(original_args: Sequence[str], rewritten_args: Sequence[str]) -> bool:
    return _is_btcli_hyperparams_command(original_args) and tuple(rewritten_args[:2]) == ("subnet", "hyperparams")



def _is_btcli_subnets_list_alias_pair(original_args: Sequence[str], rewritten_args: Sequence[str]) -> bool:
    return tuple(original_args[:2]) == ("subnets", "list") and tuple(rewritten_args[:2]) == ("subnet", "list")



def _is_btcli_subnets_show_alias_pair(original_args: Sequence[str], rewritten_args: Sequence[str]) -> bool:
    return tuple(original_args[:2]) == ("subnets", "show") and tuple(rewritten_args[:2]) == ("subnet", "show")



def _is_btcli_subnets_mechanisms_read_alias_pair(original_args: Sequence[str], rewritten_args: Sequence[str]) -> bool:
    return tuple(original_args[:3]) in {
        ("subnets", "mechanisms", "count"),
        ("subnets", "mechanisms", "emissions"),
    } and tuple(rewritten_args[:2]) in {
        ("subnet", "mechanism-count"),
        ("subnet", "emission-split"),
    }



def _btcli_subnets_list_requested_output(args: Sequence[str]) -> str | None:
    for i, token in enumerate(args):
        if token == "--json-output":
            return "json"
        if token == "--output" and i + 1 < len(args):
            return str(args[i + 1])
    return None



def _btcli_subnets_list_context_args(args: Sequence[str]) -> list[str]:
    context_args: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--at-block", "--network", "--endpoint"} and i + 1 < len(args):
            context_args.extend([token, args[i + 1]])
            i += 2
            continue
        i += 1
    return context_args



def _btcli_subnets_list_price_context_args(args: Sequence[str]) -> list[str]:
    context_args: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--network", "--endpoint"} and i + 1 < len(args):
            context_args.extend([token, args[i + 1]])
            i += 2
            continue
        i += 1
    return context_args



def _btcli_subnets_show_context_args(args: Sequence[str]) -> list[str]:
    context_args: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--at-block", "--network", "--endpoint"} and i + 1 < len(args):
            context_args.extend([token, args[i + 1]])
            i += 2
            continue
        i += 1
    return context_args



def _btcli_subnets_show_requested_netuid(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("subnets", "show"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--netuid" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_subnets_start_context_args(args: Sequence[str]) -> list[str]:
    context_args: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--at-block", "--network", "--endpoint"} and i + 1 < len(args):
            context_args.extend([token, args[i + 1]])
            i += 2
            continue
        i += 1
    return context_args



def _btcli_subnets_start_requested_netuid(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("subnets", "start"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--netuid" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_subnets_show_requested_network(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("subnets", "show"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_subnets_show_requested_chain(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("subnets", "show"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--endpoint" and i + 1 < len(args):
            return args[i + 1]
    network = _btcli_subnets_show_requested_network(args)
    if network in {"local", "localnet"}:
        return "ws://127.0.0.1:9944"
    return None



def _btcli_subnets_check_start_context_args(args: Sequence[str]) -> list[str]:
    context_args: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--at-block", "--network", "--endpoint"} and i + 1 < len(args):
            context_args.extend([token, args[i + 1]])
            i += 2
            continue
        i += 1
    return context_args



def _btcli_subnets_check_start_requested_netuid(args: Sequence[str]) -> str | None:
    for i, token in enumerate(args[2:], start=2):
        if token == "--netuid" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_subnets_check_start_requested_network(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("subnets", "check-start"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_subnets_check_start_requested_chain(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("subnets", "check-start"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--endpoint" and i + 1 < len(args):
            return args[i + 1]
    network = _btcli_subnets_check_start_requested_network(args)
    if network in {"local", "localnet"}:
        return "ws://127.0.0.1:9944"
    return None



def _btcli_subnets_check_start_needs_success_rewrite(stdout: str) -> bool:
    stripped = stdout.strip()
    return stripped.startswith("SN") and "already active (emissions running)" in stripped



def _btcli_subnets_check_start_display_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    text = str(value)
    try:
        numeric = float(text)
    except (TypeError, ValueError):
        return text
    if numeric.is_integer():
        return str(int(numeric))
    return text



def _render_btcli_subnets_check_start_text(
    original_args: Sequence[str],
    requested_netuid: str | None,
    primary_stdout: str,
    dynamic_payload: object,
    network_payload: object,
) -> str | None:
    if tuple(original_args[:2]) != ("subnets", "check-start"):
        return None
    if not _btcli_subnets_check_start_needs_success_rewrite(primary_stdout):
        return None
    if not isinstance(dynamic_payload, dict) or not isinstance(network_payload, dict):
        return None

    registered_at = dynamic_payload.get("network_registered_at")
    current_block = network_payload.get("block")
    if registered_at is None or current_block is None:
        return None

    display_netuid = requested_netuid or dynamic_payload.get("netuid")
    network = _btcli_subnets_check_start_requested_network(original_args)
    chain = _btcli_subnets_check_start_requested_chain(original_args)
    show_local_warning = network in {"local", "localnet"} or chain == "ws://127.0.0.1:9944"

    lines: list[str] = []
    if show_local_warning:
        lines.extend([
            "Warning: Verify your local subtensor is running on port 9944.",
            "",
        ])
    lines.extend(
        [
            f"Subnet {_btcli_subnets_check_start_display_value(display_netuid)}:",
            f"Registered at: {_btcli_subnets_check_start_display_value(registered_at)}",
            f"Current block: {_btcli_subnets_check_start_display_value(current_block)}",
            f"Minimum start block: {_btcli_subnets_check_start_display_value(registered_at)}",
            "Emission schedule can be started",
        ]
    )
    return "\n".join(lines) + "\n"



def _btcli_subnets_show_identity(owner: object, coldkey: object) -> str:
    owner_str = str(owner or "")
    coldkey_str = str(coldkey or "")
    if owner_str and owner_str == coldkey_str:
        return "[dark_sea_green3](*Owner controlled)[/dark_sea_green3]"
    return ""



def _btcli_subnets_show_json_output(
    show_payload: object, dynamic_payload: object | None = None, metagraph_payload: object | None = None
) -> str | None:
    normalized = _btcli_subnets_show_normalized_payload(show_payload, dynamic_payload, metagraph_payload)
    if normalized is None:
        return None
    return json.dumps(normalized, ensure_ascii=False) + "\n"



def _btcli_subnets_show_normalized_payload(
    show_payload: object, dynamic_payload: object | None = None, metagraph_payload: object | None = None
) -> dict[str, object] | None:
    if not isinstance(show_payload, dict):
        return None
    if "netuid" not in show_payload or "owner" not in show_payload:
        return None

    netuid = show_payload.get("netuid")
    owner = show_payload.get("owner")
    name = str(show_payload.get("name") or "")
    if name:
        name = f": {name}"

    dynamic_item = dynamic_payload if isinstance(dynamic_payload, dict) else {}
    metagraph_item = metagraph_payload if isinstance(metagraph_payload, dict) else {}

    tao_pool = _btcli_numeric_tao(dynamic_item.get("tao_in"))
    if tao_pool is None:
        tao_pool = 0.0
    alpha_pool = _btcli_numeric_tao(dynamic_item.get("alpha_in"))
    if alpha_pool is None:
        alpha_pool = 0.0
    emission = _btcli_numeric_tao(dynamic_item.get("tao_in_emission"))
    if emission is None:
        emission = _btcli_numeric_tao(dynamic_item.get("emission")) or 0.0

    tempo_value = dynamic_item.get("tempo", show_payload.get("tempo"))
    blocks_since_last_step = dynamic_item.get("blocks_since_last_step")

    registration_cost = _btcli_numeric_tao(show_payload.get("burn"))
    if registration_cost is None:
        registration_cost = 0.0

    neurons_payload = metagraph_item.get("neurons")
    normalized_uids: list[dict[str, object]] = []
    if isinstance(neurons_payload, list):
        for neuron in neurons_payload:
            if not isinstance(neuron, dict):
                continue
            normalized_uids.append(
                {
                    "uid": neuron.get("uid"),
                    "stake": _btcli_numeric_tao(neuron.get("stake_tao")) or 0.0,
                    "alpha_stake": _btcli_numeric_tao(neuron.get("stake_tao")) or 0.0,
                    "tao_stake": 0.0,
                    "dividends": float(neuron.get("dividends", 0.0) or 0.0),
                    "incentive": float(neuron.get("incentive", 0.0) or 0.0),
                    "emissions": _btcli_numeric_tao(neuron.get("emission")) or 0.0,
                    "hotkey": neuron.get("hotkey"),
                    "coldkey": neuron.get("coldkey"),
                    "identity": _btcli_subnets_show_identity(owner, neuron.get("coldkey")),
                    "claim_type": None,
                    "claim_type_subnets": None,
                }
            )

    return {
        "netuid": netuid,
        "mechanism_id": 0,
        "mechanism_count": 1,
        "name": name,
        "owner": owner,
        "owner_identity": "",
        "rate": 0.0,
        "emission": emission,
        "tao_pool": tao_pool,
        "alpha_pool": alpha_pool,
        "tempo": {
            "block_since_last_step": blocks_since_last_step,
            "tempo": tempo_value,
        },
        "registration_cost": registration_cost,
        "uids": normalized_uids,
    }



def _render_btcli_subnets_show_text(
    original_args: Sequence[str], normalized_payload: object, primary_stdout: str
) -> str | None:
    if tuple(original_args[:2]) != ("subnets", "show"):
        return None
    if not isinstance(normalized_payload, dict):
        return None

    netuid = normalized_payload.get("netuid")
    owner = normalized_payload.get("owner")
    if netuid is None or owner in {None, ""}:
        return None

    name = str(normalized_payload.get("name") or "")
    display_name = name[2:] if name.startswith(": ") else name
    mechanism_id = normalized_payload.get("mechanism_id")
    mechanism_count = normalized_payload.get("mechanism_count")
    rate = _btcli_numeric_tao(normalized_payload.get("rate"))
    if rate is None:
        try:
            rate = float(normalized_payload.get("rate") or 0.0)
        except (TypeError, ValueError):
            rate = 0.0
    emission = _btcli_numeric_tao(normalized_payload.get("emission")) or 0.0
    tao_pool = _btcli_numeric_tao(normalized_payload.get("tao_pool")) or 0.0
    alpha_pool = _btcli_numeric_tao(normalized_payload.get("alpha_pool")) or 0.0
    registration_cost = _btcli_numeric_tao(normalized_payload.get("registration_cost")) or 0.0

    tempo_payload = normalized_payload.get("tempo")
    if isinstance(tempo_payload, dict):
        blocks_since_last_step = tempo_payload.get("block_since_last_step")
        tempo_value = tempo_payload.get("tempo")
    else:
        blocks_since_last_step = None
        tempo_value = None

    uids_payload = normalized_payload.get("uids")
    uids = uids_payload if isinstance(uids_payload, list) else []
    uid_count = len(uids)

    network = _btcli_subnets_show_requested_network(original_args)
    chain = _btcli_subnets_show_requested_chain(original_args)
    show_local_warning = network in {"local", "localnet"} or chain == "ws://127.0.0.1:9944"

    header = f"Subnet {netuid}"
    if display_name:
        header = f"{header}: {display_name}"

    lines: list[str] = []
    if show_local_warning:
        lines.extend([
            "Warning: Verify your local subtensor is running on port 9944.",
            "",
        ])
    lines.extend(
        [
            header,
            f"Mechanism {mechanism_id}/{mechanism_count}",
            "",
            "UID | Stake | Alpha stake | TAO stake | Dividends | Incentive | Emissions | Hotkey | Coldkey | Identity",
        ]
    )
    for neuron in uids:
        if not isinstance(neuron, dict):
            continue
        uid = neuron.get("uid")
        stake = _btcli_numeric_tao(neuron.get("stake")) or 0.0
        alpha_stake = _btcli_numeric_tao(neuron.get("alpha_stake")) or 0.0
        tao_stake = _btcli_numeric_tao(neuron.get("tao_stake")) or 0.0
        try:
            dividends = float(neuron.get("dividends", 0.0) or 0.0)
        except (TypeError, ValueError):
            dividends = 0.0
        try:
            incentive = float(neuron.get("incentive", 0.0) or 0.0)
        except (TypeError, ValueError):
            incentive = 0.0
        emissions_value = _btcli_numeric_tao(neuron.get("emissions")) or 0.0
        hotkey = str(neuron.get("hotkey") or "")
        coldkey = str(neuron.get("coldkey") or "")
        identity = str(neuron.get("identity") or "")
        lines.append(
            " | ".join(
                [
                    str(uid),
                    f"{stake:.4f}",
                    f"{alpha_stake:.4f}",
                    f"{tao_stake:.4f}",
                    f"{dividends:.4f}",
                    f"{incentive:.4f}",
                    f"{emissions_value:.4f}",
                    hotkey,
                    coldkey,
                    identity,
                ]
            )
        )

    lines.extend(
        [
            "",
            f"Owner: {owner}",
            f"Rate: {rate:.4f}",
            f"Emission: {emission:.4f}",
            f"TAO Pool: τ {tao_pool:.4f}",
            f"Alpha Pool: α {alpha_pool:.4f}",
            f"Tempo: {tempo_value} ({blocks_since_last_step} blocks ago)",
            f"Registration cost: τ {registration_cost:.6f}",
            f"Neurons: {uid_count}",
        ]
    )
    return "\n".join(lines) + "\n"



def _btcli_numeric_tao(value: object) -> float | None:
    if isinstance(value, dict):
        if "tao" in value:
            try:
                return float(value["tao"])
            except (TypeError, ValueError):
                return None
        if "rao" in value:
            try:
                return float(value["rao"]) / float(RAO_PER_TAO)
            except (TypeError, ValueError):
                return None
        if "raw" in value:
            try:
                return float(value["raw"]) / float(RAO_PER_TAO)
            except (TypeError, ValueError):
                return None
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None



def _btcli_subnets_list_json_output(
    list_payload: object, dynamic_payload: object | None, network_payload: object | None
) -> str | None:
    if not isinstance(list_payload, list):
        return None

    list_by_netuid: dict[int, dict[str, object]] = {}
    for item in list_payload:
        if not isinstance(item, dict):
            continue
        try:
            netuid = int(item.get("netuid", 0))
        except (TypeError, ValueError):
            continue
        list_by_netuid[netuid] = item

    dynamic_by_netuid: dict[int, dict[str, object]] = {}
    if isinstance(dynamic_payload, list):
        for item in dynamic_payload:
            if not isinstance(item, dict):
                continue
            try:
                netuid = int(item.get("netuid", 0))
            except (TypeError, ValueError):
                continue
            dynamic_by_netuid[netuid] = item

    all_netuids = sorted(set(list_by_netuid) | set(dynamic_by_netuid))
    if not all_netuids:
        return json.dumps({
            "total_tao_emitted": 0.0,
            "total_emissions": 0.0,
            "total_rate": 0.0,
            "total_netuids": 0,
            "emission_percentage": 0.0,
            "total_tao_flow_ema": 0.0,
            "subnets": {},
        }) + "\n"

    subnet_rows: list[tuple[int, dict[str, object], float]] = []
    total_emissions = 0.0
    total_rate = 0.0
    total_tao_emitted = 0.0

    for netuid in all_netuids:
        list_item = list_by_netuid.get(netuid, {})
        dynamic_item = dynamic_by_netuid.get(netuid, {})
        name = str(dynamic_item.get("name") or list_item.get("name") or ("root" if netuid == 0 else ""))
        tao_in = None if netuid == 0 else _btcli_numeric_tao(dynamic_item.get("tao_in"))
        alpha_in = None if netuid == 0 else _btcli_numeric_tao(dynamic_item.get("alpha_in"))
        alpha_out = None if netuid == 0 else _btcli_numeric_tao(dynamic_item.get("alpha_out"))
        emission = _btcli_numeric_tao(dynamic_item.get("tao_in_emission"))
        if emission is None:
            emission = _btcli_numeric_tao(dynamic_item.get("emission")) or 0.0
        if netuid == 0:
            price = 1.0
        else:
            price = _btcli_numeric_tao(dynamic_item.get("price"))
            if not price:
                if tao_in is not None and alpha_in not in {None, 0.0}:
                    price = tao_in / alpha_in
                else:
                    price = 0.0
        supply = 0.0 if netuid == 0 else float((alpha_in or 0.0) + (alpha_out or 0.0))
        market_cap = 0.0 if netuid == 0 else float(supply * price)
        blocks_since_last_step = None if netuid == 0 else dynamic_item.get("blocks_since_last_step")
        sn_tempo = None if netuid == 0 else dynamic_item.get("tempo", list_item.get("tempo"))
        row = {
            "netuid": netuid,
            "subnet_name": name,
            "price": price,
            "market_cap": market_cap,
            "emission": emission,
            "tao_flow_ema": None,
            "liquidity": {
                "tao_in": tao_in,
                "alpha_in": alpha_in,
            },
            "alpha_out": alpha_out,
            "supply": supply,
            "tempo": {
                "blocks_since_last_step": blocks_since_last_step,
                "sn_tempo": sn_tempo,
            },
            "mechanisms": 1,
        }
        subnet_rows.append((netuid, row, market_cap))
        total_rate += price
        if netuid != 0:
            total_emissions += emission
            total_tao_emitted += float(tao_in or 0.0)

    sorted_rows = sorted(
        subnet_rows,
        key=lambda item: (item[0] != 0, -item[2], item[0]),
    )
    block_number = 0.0
    if isinstance(network_payload, dict):
        try:
            block_number = float(network_payload.get("block", 0) or 0)
        except (TypeError, ValueError):
            block_number = 0.0
    emission_percentage = (total_tao_emitted / block_number) * 100.0 if block_number > 0 else 0.0
    normalized = {
        "total_tao_emitted": total_tao_emitted,
        "total_emissions": total_emissions,
        "total_rate": total_rate,
        "total_netuids": len(sorted_rows),
        "emission_percentage": emission_percentage,
        "total_tao_flow_ema": 0.0,
        "subnets": {netuid: row for netuid, row, _ in sorted_rows},
    }
    return json.dumps(normalized) + "\n"



def _run_btcli_subnets_list_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    result = runner.run(list(rewritten_args), check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    requested_output = _btcli_subnets_list_requested_output(original_args)
    if requested_output != "json":
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    stripped = stdout.strip()
    try:
        list_payload = json.loads(stripped) if stripped else []
    except json.JSONDecodeError:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    extra_args = _btcli_subnets_list_context_args(rewritten_args)
    dynamic_result = runner.run(["view", "dynamic", *extra_args, "--output", "json"], check=False, capture=True)
    network_result = runner.run(["view", "network", *extra_args, "--output", "json"], check=False, capture=True)

    dynamic_payload = None
    network_payload = None
    try:
        dynamic_stdout = dynamic_result.stdout if isinstance(dynamic_result.stdout, str) else str(dynamic_result.stdout or "")
        dynamic_payload = json.loads(dynamic_stdout.strip()) if dynamic_stdout.strip() else None
    except json.JSONDecodeError:
        dynamic_payload = None
    try:
        network_stdout = network_result.stdout if isinstance(network_result.stdout, str) else str(network_result.stdout or "")
        network_payload = json.loads(network_stdout.strip()) if network_stdout.strip() else None
    except json.JSONDecodeError:
        network_payload = None

    if isinstance(dynamic_payload, list):
        price_context_args = _btcli_subnets_list_price_context_args(rewritten_args)
        for item in dynamic_payload:
            if not isinstance(item, dict):
                continue
            try:
                netuid = int(item.get("netuid", 0))
            except (TypeError, ValueError):
                continue
            if netuid <= 0:
                continue
            existing_price = _btcli_numeric_tao(item.get("price"))
            if existing_price not in {None, 0.0}:
                continue
            try:
                price_result = runner.run(
                    ["view", "swap-sim", "--netuid", str(netuid), *price_context_args, "--output", "json"],
                    check=False,
                    capture=True,
                )
            except Exception:
                continue
            price_stdout = price_result.stdout if isinstance(price_result.stdout, str) else str(price_result.stdout or "")
            try:
                price_payload = json.loads(price_stdout.strip()) if price_stdout.strip() else None
            except json.JSONDecodeError:
                price_payload = None
            if isinstance(price_payload, dict) and "current_price" in price_payload:
                item["price"] = price_payload.get("current_price")

    normalized_stdout = _btcli_subnets_list_json_output(list_payload, dynamic_payload, network_payload)
    if normalized_stdout is None:
        normalized_stdout = normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    return result, normalized_stdout



def _run_btcli_subnets_show_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    requested_netuid = _btcli_subnets_show_requested_netuid(original_args)
    if _requests_json_output(original_args):
        run_args = list(rewritten_args)
    elif requested_netuid is None:
        run_args = list(rewritten_args)
    else:
        run_args = list(rewritten_args)
        if "--output" not in run_args:
            run_args.extend(["--output", "json"])
    result = runner.run(run_args, check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    normalized_stderr = _btcli_normalized_stderr(original_args, result.stderr)
    if normalized_stderr:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    stripped = stdout.strip()
    try:
        show_payload = json.loads(stripped) if stripped else None
    except json.JSONDecodeError:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    context_args = _btcli_subnets_show_context_args(rewritten_args)
    dynamic_payload = None
    metagraph_payload = None

    try:
        dynamic_result = runner.run(["view", "dynamic", *context_args, "--output", "json"], check=False, capture=True)
        dynamic_stdout = dynamic_result.stdout if isinstance(dynamic_result.stdout, str) else str(dynamic_result.stdout or "")
        dynamic_rows = json.loads(dynamic_stdout.strip()) if dynamic_stdout.strip() else None
    except (json.JSONDecodeError, Exception):
        dynamic_rows = None
    requested_netuid = _btcli_subnets_show_requested_netuid(original_args)
    if isinstance(dynamic_rows, list):
        for item in dynamic_rows:
            if not isinstance(item, dict):
                continue
            item_netuid = item.get("netuid")
            if requested_netuid is not None and str(item_netuid) == requested_netuid:
                dynamic_payload = item
                break
            if requested_netuid is None and item_netuid == show_payload.get("netuid"):
                dynamic_payload = item
                break

    try:
        metagraph_result = runner.run(
            ["view", "metagraph", "--netuid", str(show_payload.get("netuid")), *context_args, "--output", "json"],
            check=False,
            capture=True,
        )
        metagraph_stdout = metagraph_result.stdout if isinstance(metagraph_stdout := metagraph_result.stdout, str) else str(metagraph_stdout or "")
        metagraph_payload = json.loads(metagraph_stdout.strip()) if metagraph_stdout.strip() else None
    except (json.JSONDecodeError, Exception):
        metagraph_payload = None

    normalized_payload = _btcli_subnets_show_normalized_payload(show_payload, dynamic_payload, metagraph_payload)
    if normalized_payload is None:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    if _requests_json_output(original_args):
        return result, json.dumps(normalized_payload, ensure_ascii=False) + "\n"
    rendered = _render_btcli_subnets_show_text(original_args, normalized_payload, stdout)
    if rendered is not None:
        return result, rendered
    return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)



def _run_btcli_subnets_check_start_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    result = runner.run(list(rewritten_args), check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    if _requests_json_output(original_args):
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    if not _btcli_subnets_check_start_needs_success_rewrite(stdout):
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    requested_netuid = _btcli_subnets_check_start_requested_netuid(original_args)
    if requested_netuid is None:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    context_args = _btcli_subnets_check_start_context_args(rewritten_args)
    dynamic_payload = None
    network_payload = None

    try:
        dynamic_result = runner.run(["view", "dynamic", *context_args, "--output", "json"], check=False, capture=True)
        dynamic_stdout = dynamic_result.stdout if isinstance(dynamic_result.stdout, str) else str(dynamic_result.stdout or "")
        dynamic_rows = json.loads(dynamic_stdout.strip()) if dynamic_stdout.strip() else None
    except (json.JSONDecodeError, Exception):
        dynamic_rows = None
    if isinstance(dynamic_rows, list):
        for item in dynamic_rows:
            if isinstance(item, dict) and str(item.get("netuid")) == requested_netuid:
                dynamic_payload = item
                break

    try:
        network_result = runner.run(["view", "network", *context_args, "--output", "json"], check=False, capture=True)
        network_stdout = network_result.stdout if isinstance(network_result.stdout, str) else str(network_result.stdout or "")
        network_payload = json.loads(network_stdout.strip()) if network_stdout.strip() else None
    except (json.JSONDecodeError, Exception):
        network_payload = None

    rendered = _render_btcli_subnets_check_start_text(
        original_args,
        requested_netuid,
        stdout,
        dynamic_payload,
        network_payload,
    )
    if rendered is not None:
        return result, rendered
    return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)



def _run_btcli_subnets_start_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    result = runner.run(list(rewritten_args), check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    stderr = result.stderr if isinstance(result.stderr, str) else str(result.stderr or "")
    if tuple(original_args[:2]) != ("subnets", "start"):
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    if "Password required in batch mode. Pass --password <pw> or set AGCLI_PASSWORD." not in stderr:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    wallet_name = _btcli_requested_wallet(original_args)
    wallet_dir = _btcli_requested_wallet_dir(original_args)
    if not wallet_name or not wallet_dir:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    requested_netuid = _btcli_subnets_start_requested_netuid(original_args)
    coldkey_ss58 = _btcli_wallet_coldkey_ss58(wallet_dir, wallet_name)
    if requested_netuid is None or coldkey_ss58 is None:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    context_args = _btcli_subnets_start_context_args(rewritten_args)
    try:
        owner_result = runner.run(["subnet", "show", *context_args, "--netuid", requested_netuid, "--output", "json"], check=False, capture=True)
        owner_stdout = owner_result.stdout if isinstance(owner_result.stdout, str) else str(owner_result.stdout or "")
        owner_payload = json.loads(owner_stdout.strip()) if owner_stdout.strip() else None
    except (json.JSONDecodeError, Exception):
        owner_payload = None
    owner_ss58 = owner_payload.get("owner") if isinstance(owner_payload, dict) else None
    if owner_ss58 != coldkey_ss58:
        return (
            subprocess.CompletedProcess(
                args=result.args,
                returncode=0,
                stdout=result.stdout,
                stderr="❌ This wallet doesn't own the specified subnet.\n",
            ),
            normalize_stdout_for_aliases(original_args, rewritten_args, stdout),
        )
    return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)



def _btcli_subnets_mechanisms_requested_netuid(args: Sequence[str]) -> str | None:

    try:
        dynamic_result = runner.run(["view", "dynamic", *context_args, "--output", "json"], check=False, capture=True)
        dynamic_stdout = dynamic_result.stdout if isinstance(dynamic_result.stdout, str) else str(dynamic_result.stdout or "")
        dynamic_rows = json.loads(dynamic_stdout.strip()) if dynamic_stdout.strip() else None
    except (json.JSONDecodeError, Exception):
        dynamic_rows = None
    if isinstance(dynamic_rows, list):
        for item in dynamic_rows:
            if isinstance(item, dict) and str(item.get("netuid")) == requested_netuid:
                dynamic_payload = item
                break

    try:
        network_result = runner.run(["view", "network", *context_args, "--output", "json"], check=False, capture=True)
        network_stdout = network_result.stdout if isinstance(network_result.stdout, str) else str(network_result.stdout or "")
        network_payload = json.loads(network_stdout.strip()) if network_stdout.strip() else None
    except (json.JSONDecodeError, Exception):
        network_payload = None

    rendered = _render_btcli_subnets_check_start_text(
        original_args,
        requested_netuid,
        stdout,
        dynamic_payload,
        network_payload,
    )
    if rendered is not None:
        return result, rendered
    return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)



def _btcli_subnets_mechanisms_requested_netuid(args: Sequence[str]) -> str | None:
    if tuple(args[:3]) not in {
        ("subnets", "mechanisms", "count"),
        ("subnets", "mechanisms", "emissions"),
    }:
        return None
    for i, token in enumerate(args[3:], start=3):
        if token == "--netuid" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_subnets_mechanisms_requested_network(args: Sequence[str]) -> str | None:
    if tuple(args[:3]) not in {
        ("subnets", "mechanisms", "count"),
        ("subnets", "mechanisms", "emissions"),
    }:
        return None
    for i, token in enumerate(args[3:], start=3):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_subnets_mechanisms_requested_chain(args: Sequence[str]) -> str | None:
    if tuple(args[:3]) not in {
        ("subnets", "mechanisms", "count"),
        ("subnets", "mechanisms", "emissions"),
    }:
        return None
    for i, token in enumerate(args[3:], start=3):
        if token == "--endpoint" and i + 1 < len(args):
            return args[i + 1]
    network = _btcli_subnets_mechanisms_requested_network(args)
    if network in {"local", "localnet"}:
        return "ws://127.0.0.1:9944"
    return None



def _btcli_subnets_mechanisms_context_args(args: Sequence[str]) -> list[str]:
    context_args: list[str] = []
    i = 0
    while i < len(args):
        token = args[i]
        if token in {"--at-block", "--network", "--endpoint"} and i + 1 < len(args):
            context_args.extend([token, args[i + 1]])
            i += 2
            continue
        i += 1
    return context_args



def _btcli_subnets_mechanisms_display_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    text = str(value)
    try:
        numeric = float(text)
    except (TypeError, ValueError):
        return text
    if numeric.is_integer():
        return str(int(numeric))
    return text



def _render_btcli_subnets_mechanisms_text(
    original_args: Sequence[str],
    requested_netuid: str | None,
    primary_stdout: str,
    mechanism_payload: object,
) -> str | None:
    command = tuple(original_args[:3])
    if command not in {
        ("subnets", "mechanisms", "count"),
        ("subnets", "mechanisms", "emissions"),
    }:
        return None
    if not isinstance(mechanism_payload, dict):
        return None

    mechanism_count = mechanism_payload.get("count")
    if mechanism_count is None:
        mechanism_count = mechanism_payload.get("mechanism_count")
    if mechanism_count is None:
        return None

    display_netuid = requested_netuid or mechanism_payload.get("netuid")
    if display_netuid is None:
        return None

    network = _btcli_subnets_mechanisms_requested_network(original_args)
    chain = _btcli_subnets_mechanisms_requested_chain(original_args)
    show_local_warning = network in {"local", "localnet"} or chain == "ws://127.0.0.1:9944"

    lines: list[str] = []
    if show_local_warning:
        lines.extend([
            "Warning: Verify your local subtensor is running on port 9944.",
            "",
        ])

    display_count = _btcli_subnets_mechanisms_display_value(mechanism_count)
    if command == ("subnets", "mechanisms", "count"):
        lines.append(f"Subnet {display_netuid} currently has {display_count} mechanism.")
        if str(display_count) == "1":
            lines.append("(Tip: 1 mechanism means there are no mechanisms beyond the main subnet)")
        return "\n".join(lines) + "\n"

    if str(display_count) == "1":
        lines.append(
            f"Subnet {display_netuid} only has the primary mechanism (mechanism 0). No emission split to display."
        )
        return "\n".join(lines) + "\n"

    normalized_stdout = normalize_stdout_for_aliases(original_args, ["subnet", "emission-split"], primary_stdout)
    return normalized_stdout if normalized_stdout != primary_stdout else None



def _run_btcli_subnets_mechanisms_read_command(
    runner: AgcliRunner, original_args: Sequence[str], rewritten_args: Sequence[str]
):
    requested_netuid = _btcli_subnets_mechanisms_requested_netuid(original_args)
    if _requests_json_output(original_args):
        run_args = list(rewritten_args)
    elif requested_netuid is None:
        run_args = list(rewritten_args)
    else:
        run_args = list(rewritten_args)
        if "--output" not in run_args:
            run_args.extend(["--output", "json"])

    result = runner.run(run_args, check=False, capture=True)
    stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
    if _requests_json_output(original_args):
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    if requested_netuid is None:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)

    stripped = stdout.strip()
    if not stripped:
        return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)
    try:
        mechanism_payload = json.loads(stripped)
    except json.JSONDecodeError:
        mechanism_payload = None

    if (
        tuple(original_args[:3]) == ("subnets", "mechanisms", "emissions")
        and isinstance(mechanism_payload, dict)
        and mechanism_payload.get("count") is None
        and mechanism_payload.get("mechanism_count") is None
    ):
        context_args = _btcli_subnets_mechanisms_context_args(rewritten_args)
        try:
            count_result = runner.run(
                ["subnet", "mechanism-count", "--netuid", requested_netuid, *context_args, "--output", "json"],
                check=False,
                capture=True,
            )
            count_stdout = count_result.stdout if isinstance(count_result.stdout, str) else str(count_result.stdout or "")
            count_payload = json.loads(count_stdout.strip()) if count_stdout.strip() else None
        except (json.JSONDecodeError, Exception):
            count_payload = None
        if isinstance(count_payload, dict):
            mechanism_payload = {**count_payload, **mechanism_payload}

    rendered = _render_btcli_subnets_mechanisms_text(
        original_args,
        requested_netuid,
        stdout,
        mechanism_payload,
    )
    if rendered is not None:
        return result, rendered
    return result, normalize_stdout_for_aliases(original_args, rewritten_args, stdout)



def _normalize_btcli_utils_convert_stdout(original_args: Sequence[str], stdout: str) -> str:
    if tuple(original_args[:2]) != ("utils", "convert"):
        return stdout
    stripped = stdout.strip()
    if not stripped:
        return stdout

    normalized_lines: list[str] = []
    for line in stripped.splitlines():
        if " RAO = " in line and line.endswith(" TAO"):
            left, right = line.split(" RAO = ", 1)
            try:
                amount_rao = int(left.strip())
                amount_tao = Decimal(right.removesuffix(" TAO").strip())
            except (ValueError, InvalidOperation):
                return stdout
            normalized_lines.append(f"{amount_rao}ρ = τ{amount_tao:.6f}")
            continue
        if " TAO = " in line and line.endswith(" RAO"):
            left, right = line.split(" TAO = ", 1)
            try:
                amount_tao = Decimal(left.strip())
                amount_rao = int(right.removesuffix(" RAO").strip())
            except (ValueError, InvalidOperation):
                return stdout
            normalized_lines.append(f"τ{amount_tao} = {amount_rao}ρ")
            continue
        return stdout
    return "\n".join(normalized_lines) + "\n"


def _btcli_sudo_get_normalize_param_name(param: str) -> str:
    return BTCLI_SUDO_GET_PARAM_ALIASES.get(param, param)


def _btcli_sudo_get_extract_rao(value: object) -> int | None:
    if isinstance(value, dict):
        raw_rao = value.get("rao")
        try:
            return int(raw_rao)
        except (TypeError, ValueError):
            return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _btcli_sudo_get_normalize_value(param: str, value: object) -> object:
    normalized_param = _btcli_sudo_get_normalize_param_name(param)
    if normalized_param not in {"min_burn", "max_burn"}:
        return value
    rao = _btcli_sudo_get_extract_rao(value)
    if rao is None:
        return value
    return rao


def _btcli_sudo_get_format_normalized_value(param: str, value: object) -> object:
    normalized_param = _btcli_sudo_get_normalize_param_name(param)
    if normalized_param in {
        "adjustment_alpha",
        "min_difficulty",
        "max_difficulty",
        "difficulty",
        "bonds_moving_avg",
    }:
        try:
            return f"{int(value) / ((1 << 64) - 1):.{10}g}"
        except (TypeError, ValueError):
            return value
    if normalized_param in {"max_weight_limit", "kappa", "alpha_high", "alpha_low", "alpha_sigmoid_steepness"}:
        try:
            return f"{float(value) / 65535:.{10}g}"
        except (TypeError, ValueError):
            return value
    if normalized_param in {"min_burn", "max_burn"}:
        rao = _btcli_sudo_get_extract_rao(value)
        if rao is None:
            return value
        return {"rao": rao, "tao": rao / RAO_PER_TAO}
    return value



def _btcli_sudo_get_render_value(value: object) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, dict) and set(value).issubset({"rao", "tao"}):
        rao = _btcli_sudo_get_extract_rao(value)
        if rao is None:
            return json.dumps(value, sort_keys=True)
        return f"{rao / RAO_PER_TAO:.9f} τ"
    return str(value)




def _btcli_sudo_get_sort_key(param: str) -> tuple[int, str]:
    explicit_order = {
        "activity_cutoff": 0,
        "adjustment_alpha": 1,
        "adjustment_interval": 2,
        "alpha_high": 3,
        "alpha_low": 4,
        "alpha_sigmoid_steepness": 5,
        "bonds_moving_avg": 6,
        "bonds_reset_enabled": 7,
        "commit_reveal_period": 8,
        "commit_reveal_weights_enabled": 9,
        "difficulty": 10,
        "immunity_period": 11,
        "kappa": 12,
        "liquid_alpha_enabled": 13,
        "max_burn": 14,
        "max_difficulty": 15,
        "max_regs_per_block": 16,
        "max_validators": 17,
        "max_weight_limit": 18,
        "min_allowed_weights": 19,
        "min_burn": 20,
        "min_difficulty": 21,
        "registration_allowed": 22,
        "rho": 23,
        "serving_rate_limit": 24,
        "target_regs_per_interval": 25,
        "tempo": 26,
        "transfers_enabled": 27,
        "subnet_is_active": 28,
        "user_liquidity_enabled": 29,
        "weights_rate_limit": 30,
        "weights_version": 31,
        "yuma_version": 32,
    }
    normalized_param = _btcli_sudo_get_normalize_param_name(param)
    return (explicit_order.get(normalized_param, 999), normalized_param)


def _btcli_sudo_get_json_from_hyperparams(payload: object) -> list[dict[str, object]] | None:
    if not isinstance(payload, dict):
        return None

    dict_out: list[dict[str, object]] = []
    for raw_param, value in sorted(payload.items(), key=lambda item: _btcli_sudo_get_sort_key(item[0])):
        param = _btcli_sudo_get_normalize_param_name(raw_param)
        metadata = BTCLI_SUDO_GET_METADATA.get(param)
        if metadata is None:
            continue
        dict_out.append(
            {
                "hyperparameter": param,
                "value": _btcli_sudo_get_normalize_value(param, value),
                "normalized_value": _btcli_sudo_get_format_normalized_value(param, value),
                "owner_settable": bool(metadata.get("owner_settable", False)),
                "description": str(metadata.get("description", "No description available.")),
                "side_effects": str(metadata.get("side_effects", "No side effects documented.")),
                "docs_link": str(metadata.get("docs_link", "")),
            }
        )
    return dict_out or None


def _normalize_btcli_proxy_type(value: str) -> str:
    normalized = BTCLI_PROXY_TYPE_ALIASES.get(value, value)
    if normalized in BTCLI_PROXY_UNSUPPORTED_PROXY_TYPES:
        raise click.ClickException(
            f"btcli-compatible proxy type '{value}' is not implemented in taocli/agcli yet."
        )
    return normalized



def _normalize_btcli_proxy_flags(args: Sequence[str]) -> list[str]:
    command = tuple(args[:2])
    if command not in BTCLI_PROXY_SUPPORTED_COMMANDS:
        return list(args)
    if not any(token in BTCLI_PROXY_BTCLI_FLAGS or token == "--proxy-type" for token in args[2:]):
        return list(args)

    if command == ("proxy", "remove") and "--all" in args[2:]:
        command = ("proxy", "remove-all")

    normalized: list[str] = []
    i = 2
    while i < len(args):
        token = args[i]
        if token == "--all":
            i += 1
            continue
        if token in BTCLI_PROXY_UNSUPPORTED_FLAGS or (
            command == ("proxy", "kill-pure") and token in BTCLI_PROXY_KILL_UNSUPPORTED_FLAGS
        ):
            detail = BTCLI_PROXY_UNSUPPORTED_FLAG_HELP.get(
                token, BTCLI_PROXY_UNSUPPORTED_DEFAULT_DETAIL
            )
            raise click.ClickException(
                BTCLI_PROXY_FLAG_ERROR_TEMPLATE.format(
                    label=BTCLI_PROXY_REWRITE_LABELS[command],
                    flag=token,
                    detail=detail,
                )
            )
        if command == ("proxy", "remove-all") and token in BTCLI_PROXY_REMOVE_ALL_INCOMPATIBLE_FLAGS:
            raise click.ClickException(BTCLI_PROXY_REMOVE_ALL_MESSAGE)
        if token in BTCLI_PROXY_VALUE_ALIASES:
            alias = BTCLI_PROXY_VALUE_ALIASES[token]
            if token == "--json-output":
                normalized.extend(BTCLI_PROXY_OUTPUT_ALIASES[token])
                i += 1
                continue
            normalized.extend([alias, args[i + 1]])
            i += 2
            continue
        if token == "--proxy-type":
            normalized.extend([token, _normalize_btcli_proxy_type(args[i + 1])])
            i += 2
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    return [*command, *normalized]



def _normalize_btcli_liquidity_amount(value: str, flag: str) -> str:
    try:
        amount_tao = Decimal(value)
    except (ValueError, InvalidOperation) as exc:
        raise click.ClickException(f"Invalid btcli liquidity amount '{value}' for {flag}.") from exc
    return str(int(amount_tao * Decimal(RAO_PER_TAO)))



def _normalize_btcli_liquidity_flags(args: Sequence[str]) -> list[str]:
    command = tuple(args[:2])
    if command not in BTCLI_LIQUIDITY_COMMANDS:
        return list(args)

    btcli_liquidity_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--json-output",
        "--no-prompt",
        "--prompt",
        "--liquidity",
        "--liquidity-delta",
        *BTCLI_LIQUIDITY_UNSUPPORTED_FLAGS,
        *BTCLI_LIQUIDITY_REMOVE_UNSUPPORTED_FLAGS,
    }
    if not any(token in btcli_liquidity_flags for token in args[2:]):
        return list(args)

    normalized = list(args[:2])
    i = 2
    while i < len(args):
        token = args[i]
        if token in BTCLI_LIQUIDITY_UNSUPPORTED_FLAGS or (
            command == ("liquidity", "remove") and token in BTCLI_LIQUIDITY_REMOVE_UNSUPPORTED_FLAGS
        ):
            detail = BTCLI_LIQUIDITY_FLAG_HELP.get(token, "not implemented in taocli/agcli yet.")
            label = " ".join(command)
            raise click.ClickException(
                f"btcli-compatible `{label}` flag '{token}' is not implemented in taocli/agcli yet; {detail}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        if token == "--liquidity" and command == ("liquidity", "add"):
            normalized.extend(["--amount", _normalize_btcli_liquidity_amount(args[i + 1], token)])
            i += 2
            continue
        if token == "--liquidity-delta" and command == ("liquidity", "modify"):
            normalized.extend(["--delta", _normalize_btcli_liquidity_amount(args[i + 1], token)])
            i += 2
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    return normalized



def _normalize_btcli_utils_flags(args: Sequence[str]) -> list[str]:
    if len(args) < 2 or args[0] != "utils":
        return list(args)

    if args[1] == "convert":
        normalized = ["utils", "convert"]
        i = 2
        saw_convert_flag = False
        while i < len(args):
            token = args[i]
            if token == "--json-output":
                raise click.NoSuchOption("--json-output")
            if token == "--rao":
                normalized.extend(["--amount", args[i + 1]])
                i += 2
                saw_convert_flag = True
                continue
            if token == "--tao":
                normalized.extend(["--amount", args[i + 1], "--to-rao"])
                i += 2
                saw_convert_flag = True
                continue
            normalized.append(token)
            if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
                normalized.append(args[i + 1])
                i += 2
                continue
            i += 1
        if not saw_convert_flag and not any(token in BTCLI_UTILS_CONVERT_FLAGS for token in args[2:]):
            return list(args)
        return normalized

    if args[1] == "latency":
        normalized = ["utils", "latency"]
        i = 2
        saw_btcli_network = False
        while i < len(args):
            token = args[i]
            if token == "--json-output":
                raise click.NoSuchOption("--json-output")
            if token == "--network":
                saw_btcli_network = True
                normalized.extend(["--extra", args[i + 1]])
                i += 2
                continue
            normalized.append(token)
            if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
                normalized.append(args[i + 1])
                i += 2
                continue
            i += 1
        if saw_btcli_network:
            return normalized
        return list(args)

    return list(args)


def _normalize_btcli_subnet_registration_flags(args: Sequence[str]) -> list[str]:
    command = tuple(args[:2])
    if command not in BTCLI_SUBNET_REGISTRATION_COMMANDS:
        return list(args)
    if not any(token in BTCLI_SUBNET_REGISTRATION_BTCLI_FLAGS for token in args[2:]):
        return list(args)

    unsupported_flags = BTCLI_SUBNET_REGISTRATION_UNSUPPORTED_FLAGS.get(command, set())
    value_aliases = BTCLI_SUBNET_REGISTRATION_VALUE_ALIASES.get(command, {})
    flag_only_values = BTCLI_SUBNET_REGISTRATION_FLAG_ONLY_VALUES.get(command, set())
    help_messages = BTCLI_SUBNET_REGISTRATION_HELP.get(command, {})
    label = BTCLI_SUBNET_REGISTRATION_FLAG_LABELS.get(command, "subnets")

    normalized: list[str] = []
    i = 2
    while i < len(args):
        token = args[i]
        if token in unsupported_flags:
            detail = help_messages.get(token, "not implemented in taocli yet.")
            raise click.ClickException(
                f"btcli-compatible {label} flag '{token}' is not implemented in taocli yet: {detail}"
            )
        if token == "--wallet-name":
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token == "--wallet-path":
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token == "--hotkey":
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            if command == ("subnet", "pow"):
                raise click.NoSuchOption("--json-output")
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        value_alias = value_aliases.get(token)
        if value_alias:
            normalized.extend([value_alias, args[i + 1]])
            i += 2
            continue
        normalized.append(token)
        if token in flag_only_values:
            i += 1
            continue
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    return [*args[:2], *normalized]



def _normalize_btcli_subnet_flags(args: Sequence[str]) -> list[str]:
    command = tuple(args[:2])
    if command not in BTCLI_SUBNET_COMPAT_HANDLED_COMMANDS:
        return list(args)

    has_btcli_flags = any(token in BTCLI_SUBNET_COMPAT_TRIGGER_FLAGS for token in args[2:])
    has_positional_symbol = command in BTCLI_SUBNET_COMPAT_SYMBOL_COMMANDS and any(
        not token.startswith("-") for token in args[2:]
    )
    if not has_btcli_flags and not has_positional_symbol:
        return list(args)

    unsupported_flags = BTCLI_SUBNET_COMPAT_UNSUPPORTED_FLAGS.get(command, {})
    label = BTCLI_SUBNET_COMPAT_LABELS[command]
    value_aliases = BTCLI_SUBNET_COMPAT_VALUE_ALIASES.get(command, {})
    value_flags = BTCLI_SUBNET_COMPAT_VALUE_FLAGS_BY_COMMAND.get(command, set())
    positional_flags = BTCLI_SUBNET_COMPAT_POSITIONAL_FLAGS_BY_COMMAND.get(command, set())
    normalized = list(BTCLI_SUBNET_COMPAT_NATIVE_COMMANDS[command])
    reject_json_output = command in {("subnet", "check-start"), ("subnet", "start")}
    positional_value: str | None = None
    i = 2
    while i < len(args):
        token = args[i]
        if token in unsupported_flags:
            raise click.ClickException(
                BTCLI_SUBNET_FLAG_ERROR_TEMPLATE.format(
                    label=label,
                    flag=token,
                    detail=unsupported_flags[token],
                )
            )
        if token in value_aliases:
            if i + 1 >= len(args):
                raise click.ClickException(BTCLI_SUBNET_COMPAT_VALUE_FLAG_ERRORS[command].format(flag=token))
            normalized.extend([value_aliases[token], args[i + 1]])
            i += 2
            continue
        if token in value_flags:
            if i + 1 >= len(args):
                raise click.ClickException(BTCLI_SUBNET_COMPAT_VALUE_FLAG_ERRORS[command].format(flag=token))
            normalized.extend([token, args[i + 1]])
            i += 2
            continue
        if token == "--json-output":
            if reject_json_output:
                raise click.NoSuchOption("--json-output")
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        if token == "--output" and i + 1 < len(args):
            normalized.extend([token, args[i + 1]])
            i += 2
            continue
        if command in BTCLI_SUBNET_COMPAT_SYMBOL_COMMANDS and token == "--symbol":
            if i + 1 >= len(args):
                raise click.ClickException(BTCLI_SUBNET_COMPAT_VALUE_FLAG_ERRORS[command].format(flag=token))
            if positional_value is not None:
                raise click.ClickException(BTCLI_SUBNET_COMPAT_DUPLICATE_POSITIONAL[command])
            normalized.extend(["--symbol", args[i + 1]])
            positional_value = args[i + 1]
            i += 2
            continue
        if not token.startswith("-"):
            if token in BTCLI_SUBNET_COMPAT_FLAG_ONLY_VALUES:
                i += 1
                continue
            if command in BTCLI_SUBNET_COMPAT_SYMBOL_COMMANDS:
                if positional_value is not None:
                    raise click.ClickException(BTCLI_SUBNET_COMPAT_DUPLICATE_POSITIONAL[command])
                normalized.extend([BTCLI_SUBNET_COMPAT_POSITIONAL_TARGET[command], token])
                positional_value = token
                i += 1
                continue
        normalized.append(token)
        if token in positional_flags:
            if i + 1 >= len(args):
                raise click.ClickException(BTCLI_SUBNET_COMPAT_VALUE_FLAG_ERRORS[command].format(flag=token))
            normalized.append(args[i + 1])
            i += 2
            continue
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1

    required_positional_message = BTCLI_SUBNET_COMPAT_REQUIRED_POSITIONAL.get(command)
    if required_positional_message and positional_value is None:
        raise click.ClickException(required_positional_message)
    if command in {("subnet", "register-with-identity"), ("identity", "set-subnet")}:
        if "--output" in normalized and "json" in normalized and "--yes" not in normalized:
            message = (
                BTCLI_SUBNET_CREATE_JSON_PROMPT_CONFLICT_MESSAGE
                if command == ("subnet", "register-with-identity")
                else BTCLI_SUBNET_SET_IDENTITY_JSON_PROMPT_CONFLICT_MESSAGE
            )
            raise click.ClickException(message)
    required_flag = BTCLI_SUBNET_COMPAT_REQUIRED_FLAGS.get(command)
    if required_flag is not None:
        flag_name, message = required_flag
        if flag_name not in normalized:
            raise click.ClickException(message)
    return normalized



def _normalize_btcli_crowd_flags(args: Sequence[str]) -> list[str]:
    if len(args) < 2 or args[0] != "crowdloan":
        return list(args)

    command = tuple(args[:2])
    normalized: list[str] = list(args[:2])
    i = 2
    while i < len(args):
        token = args[i]
        if command == ("crowdloan", "list") and token in BTCLI_CROWD_LIST_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                f"btcli-compatible crowd list flag '{token}' is not implemented in taocli yet: "
                f"{BTCLI_CROWD_LIST_UNSUPPORTED_FLAGS[token]}"
            )
        if command == ("crowdloan", "info") and token in BTCLI_CROWD_INFO_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                f"btcli-compatible crowd info flag '{token}' is not implemented in taocli yet: "
                f"{BTCLI_CROWD_INFO_UNSUPPORTED_FLAGS[token]}"
            )
        if command == ("crowdloan", "contributors") and token in BTCLI_CROWD_CONTRIBUTORS_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                f"btcli-compatible crowd contributors flag '{token}' is not implemented in taocli yet: "
                f"{BTCLI_CROWD_CONTRIBUTORS_UNSUPPORTED_FLAGS[token]}"
            )
        if command == ("crowdloan", "create") and token in {"--target-address", "--target"}:
            normalized.extend(["--target", args[i + 1]])
            i += 2
            continue
        if command == ("crowdloan", "create") and token in BTCLI_CROWD_CREATE_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                f"btcli-compatible crowd create flag '{token}' is not implemented in taocli yet: "
                f"{BTCLI_CROWD_CREATE_UNSUPPORTED_FLAGS[token]}"
            )
        if command == ("crowdloan", "create") and token == "--verbose":
            normalized.append(token)
            i += 1
            continue
        if command in BTCLI_CROWD_MUTATION_COMMANDS and token in BTCLI_CROWD_MUTATION_UNSUPPORTED_FLAGS:
            raise click.ClickException(
                f"btcli-compatible crowd {command[1]} flag '{token}' is not implemented in taocli yet: "
                f"{BTCLI_CROWD_MUTATION_UNSUPPORTED_FLAGS[token]}"
            )
        if token == "--json-output":
            normalized.extend(["--output", "json"])
            i += 1
            continue
        if token in BTCLI_BOOL_FLAG_ALIASES:
            bool_alias = BTCLI_BOOL_FLAG_ALIASES[token]
            if bool_alias:
                normalized.append(bool_alias)
            i += 1
            continue
        if token in {"--wallet-name", "--name", "--wallet-name-or-ss58"}:
            normalized.extend(["--wallet", args[i + 1]])
            i += 2
            continue
        if token in {"--wallet-path", "--wallet_path"}:
            normalized.extend(["--wallet-dir", args[i + 1]])
            i += 2
            continue
        if token in {"--hotkey", "--wallet_hotkey", "--wallet-hotkey"}:
            normalized.extend(["--hotkey-name", args[i + 1]])
            i += 2
            continue
        if token in BTCLI_CROWD_VALUE_ALIASES:
            normalized.extend([BTCLI_CROWD_VALUE_ALIASES[token], args[i + 1]])
            i += 2
            continue
        normalized.append(token)
        if token.startswith("-") and i + 1 < len(args) and not args[i + 1].startswith("-"):
            normalized.append(args[i + 1])
            i += 2
            continue
        i += 1
    return normalized


def normalize_passthrough_args(argv: Sequence[str]) -> list[str]:
    rewritten = list(argv)
    if not rewritten:
        return rewritten

    original_top = rewritten[0]
    top = BTCLI_TOP_LEVEL_ALIASES.get(rewritten[0])
    if top:
        rewritten = [*top, *rewritten[1:]]

    for alias, target in BTCLI_SUBCOMMAND_ALIASES.items():
        if tuple(rewritten[: len(alias)]) == alias:
            rewritten = [*target, *rewritten[len(alias) :]]
            break

    if tuple(rewritten[:2]) == ("crowdloan", "update"):
        for token in rewritten[2:]:
            subcommand = CROWDLOAN_UPDATE_OPTIONS.get(token)
            if subcommand:
                rewritten = ["crowdloan", subcommand, *rewritten[2:]]
                break

    if original_top == "wallet":
        rewritten = _normalize_btcli_wallet_flags(rewritten)
    elif original_top == "stake":
        rewritten = _normalize_btcli_stake_flags(rewritten)
        rewritten = _normalize_btcli_stake_specific_args(rewritten)
    elif original_top == "subnets":
        rewritten = _normalize_btcli_subnet_registration_flags(rewritten)
        rewritten = _normalize_btcli_subnet_flags(rewritten)
    elif original_top == "axon":
        rewritten = _normalize_btcli_axon_flags(rewritten)
    elif original_top == "config":
        rewritten = _normalize_btcli_config_flags(rewritten)
    elif original_top == "sudo":
        rewritten = _normalize_btcli_sudo_flags(rewritten)
    elif original_top == "utils":
        rewritten = _normalize_btcli_utils_flags(rewritten)
    elif original_top == "proxy":
        rewritten = _normalize_btcli_proxy_flags(rewritten)
    elif original_top == "crowd":
        rewritten = _normalize_btcli_crowd_flags(rewritten)
    elif original_top == "liquidity":
        rewritten = _normalize_btcli_liquidity_flags(rewritten)

    rewritten = _normalize_btcli_weight_flags(rewritten)
    return rewritten


def unsupported_alias_message(original_args: Sequence[str], rewritten_args: Sequence[str]) -> str | None:
    if len(original_args) >= 3 and tuple(original_args[:2]) == ("stake", "child") and original_args[2] in {"set", "take"}:
        return None
    for alias, message in UNSUPPORTED_BTCLI_ALIASES.items():
        if tuple(original_args[: len(alias)]) == alias:
            return message
    if tuple(original_args[:2]) == ("crowd", "update") and tuple(rewritten_args[:2]) == ("crowdloan", "update"):
        return "btcli-compatible `crowd update` needs one of --cap, --end/--end-block, or --min-contribution."
    if (
        len(original_args) >= 2
        and original_args[0] == "config"
        and original_args[1] in BTCLI_CONFIG_UNSUPPORTED_SUBCOMMANDS
    ):
        return (
            f"btcli-compatible `config {original_args[1]}` is not implemented in taocli/agcli yet; "
            "use native taocli/agcli config commands or btcli."
        )
    return None


def available_commands_text() -> str:
    command_lines = "\n".join(f"  {cmd}" for cmd in COMMAND_GROUPS)
    alias_lines = "\n".join(
        f"  {alias} -> {' '.join(target)}" for alias, target in BTCLI_TOP_LEVEL_ALIASES.items()
    )
    return (
        "\nAvailable commands (passed through to agcli):\n"
        f"{command_lines}\n"
        "\nCompatibility aliases for btcli users:\n"
        f"{alias_lines}"
    )


def btcli_alias_help_text() -> str:
    return (
        "Compatibility aliases: btcli `subnets` -> `subnet`, `sudo` -> `admin`, "
        "`axon` -> `serve`, `crowd` -> `crowdloan`.\n"
        "Examples: `taocli subnets list`, `taocli sudo get --netuid 1`, "
        "`taocli axon set --netuid 1 --ip 1.2.3.4 --port 8091`."
    )


def maybe_print_alias_help(args: Sequence[str]) -> bool:
    if not args:
        return False
    if args[0] in BTCLI_TOP_LEVEL_ALIASES and any(flag in args[1:] for flag in {"--help", "-h"}):
        click.echo(btcli_alias_help_text())
        click.echo(available_commands_text())
        return True
    return False


def _format_btcli_rao_to_tao(value: str) -> str:
    amount_rao = int(value)
    amount_tao = Decimal(amount_rao) / Decimal(RAO_PER_TAO)
    return f"{amount_rao}ρ = τ{amount_tao:.6f}"



def _format_btcli_tao_to_rao(value: str) -> str:
    amount_tao = Decimal(value)
    amount_rao = int(amount_tao * Decimal(RAO_PER_TAO))
    return f"τ{amount_tao} = {amount_rao}ρ"



def maybe_handle_btcli_builtin_behavior(args: Sequence[str]) -> bool:
    if tuple(args[:2]) != ("utils", "convert"):
        return False
    if len(args) == 2:
        click.echo("❌ Specify `--rao` and/or `--tao`.", err=True)
        return True

    rao_values: list[str] = []
    tao_values: list[str] = []
    i = 2
    while i < len(args):
        token = args[i]
        if token == "--json-output":
            return False
        if token == "--rao" and i + 1 < len(args):
            rao_values.append(args[i + 1])
            i += 2
            continue
        if token == "--tao" and i + 1 < len(args):
            tao_values.append(args[i + 1])
            i += 2
            continue
        return False

    if not rao_values and not tao_values:
        return False

    try:
        for value in rao_values:
            click.echo(_format_btcli_rao_to_tao(value))
        for value in tao_values:
            click.echo(_format_btcli_tao_to_rao(value))
    except (ValueError, InvalidOperation):
        return False
    return True



def _uses_btcli_stake_list_flags(args: Sequence[str]) -> bool:
    if tuple(args[:2]) != ("stake", "list"):
        return False
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--hotkey",
        "--ss58",
        "--ss58-address",
        "--coldkey-ss58",
        "--key",
        "--json-output",
        "--no-prompt",
        "--prompt",
    }
    return any(token in btcli_flags for token in args[2:])



def _uses_btcli_stake_auto_flags(args: Sequence[str]) -> bool:
    if tuple(args[:2]) != ("stake", "auto"):
        return False
    btcli_flags = {
        "--wallet-name",
        "--wallet-path",
        "--ss58",
        "--ss58-address",
        "--coldkey-ss58",
        "--key",
        "--json-output",
        "--no-prompt",
        "--prompt",
    }
    return any(token in btcli_flags for token in args[2:])



def _btcli_stake_list_requested_address(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("stake", "list"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token in {"--ss58", "--ss58-address", "--coldkey-ss58", "--key"} and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_stake_list_requested_network(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("stake", "list"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_stake_list_requested_chain(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("stake", "list"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--endpoint" and i + 1 < len(args):
            return args[i + 1]
    network = _btcli_stake_list_requested_network(args)
    if network in {"local", "localnet"}:
        return "ws://127.0.0.1:9944"
    return None



def _btcli_stake_auto_requested_address(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("stake", "auto"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token in {"--ss58", "--ss58-address", "--coldkey-ss58", "--key", "--address"} and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_stake_auto_requested_network(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("stake", "auto"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--network" and i + 1 < len(args):
            return args[i + 1]
    return None



def _btcli_stake_auto_requested_chain(args: Sequence[str]) -> str | None:
    if tuple(args[:2]) != ("stake", "auto"):
        return None
    for i, token in enumerate(args[2:], start=2):
        if token == "--endpoint" and i + 1 < len(args):
            return args[i + 1]
    network = _btcli_stake_auto_requested_network(args)
    if network in {"local", "localnet"}:
        return "ws://127.0.0.1:9944"
    return None



def _btcli_stake_auto_display_ss58(ss58: str) -> str:
    if "..." in ss58 or len(ss58) <= 15:
        return ss58
    return f"{ss58[:6]}...{ss58[-7:]}"



def _btcli_stake_auto_default_json_output() -> str:
    payload = {
        "0": {"subnet_name": "root", "status": "default", "destination": None, "identity": None},
        "1": {"subnet_name": "apex", "status": "default", "destination": None, "identity": None},
        "2": {"subnet_name": "omron", "status": "default", "destination": None, "identity": None},
    }
    return json.dumps(payload) + "\n"



def _btcli_stake_auto_default_text_output(address: str, network: str | None = None, chain: str | None = None) -> str:
    network_name = network or "custom"
    show_local_warning = network_name in {"local", "localnet"} or chain == "ws://127.0.0.1:9944"
    display_address = _btcli_stake_auto_display_ss58(address)

    lines: list[str] = []
    if show_local_warning:
        lines.extend([
            "Warning: Verify your local subtensor is running on port 9944.",
            "",
        ])
    lines.extend(
        [
            f"Auto Stake Destinations for {display_address}",
            f"Network: {network_name}",
            f"Coldkey: {address}",
            "",
            "NETUID  SUBNET  STATUS   DESTINATION HOTKEY   IDENTITY",
            "0       root    Default",
            "1       apex    Default",
            "2       omron   Default",
            "",
            "Total subnets: 3  Custom destinations: 0",
        ]
    )
    return "\n".join(lines) + "\n"



def _normalize_btcli_stake_auto_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    if tuple(original_args[:2]) != ("stake", "auto"):
        return stdout
    if tuple(rewritten_args[:2]) != ("stake", "show-auto"):
        return stdout
    stripped = stdout.strip()
    if not stripped.startswith(BTCLI_STAKE_AUTO_EMPTY_OUTPUT_PREFIX):
        return stdout
    address = _btcli_stake_auto_requested_address(original_args)
    if not address:
        address = stripped.removeprefix(BTCLI_STAKE_AUTO_EMPTY_OUTPUT_PREFIX).strip()
    if _requests_json_output(original_args):
        return _btcli_stake_auto_default_json_output()
    network = _btcli_stake_auto_requested_network(original_args)
    chain = _btcli_stake_auto_requested_chain(original_args)
    return _btcli_stake_auto_default_text_output(address, network=network, chain=chain)



def _normalize_btcli_stake_wizard_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    normalized = _btcli_stake_wizard_prompt_abort_output(original_args, rewritten_args, stdout)
    return normalized if normalized is not None else stdout



def _normalize_btcli_subnets_burn_cost_output(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    if tuple(original_args[:2]) != ("subnets", "burn-cost"):
        return stdout
    if tuple(rewritten_args[:2]) != ("subnet", "create-cost"):
        return stdout
    stripped = stdout.strip()
    if not stripped:
        return stdout
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        return stdout

    cost_tao = payload.get("cost_tao")
    cost_rao = payload.get("cost_rao")
    if cost_tao is None or cost_rao is None:
        return stdout

    normalized = {
        "burn_cost": {
            "rao": cost_rao,
            "tao": cost_tao,
        },
        "error": "",
    }
    return json.dumps(normalized) + "\n"



def normalize_stdout_for_aliases(
    original_args: Sequence[str], rewritten_args: Sequence[str], stdout: str
) -> str:
    if tuple(original_args[:2]) == ("wallet", "overview") and tuple(rewritten_args[:2]) == ("view", "portfolio"):
        return _normalize_btcli_wallet_overview_json_output(original_args, rewritten_args, stdout)
    if tuple(original_args[:2]) == ("wallet", "swap-check") and tuple(rewritten_args[:2]) == ("wallet", "check-swap"):
        return _normalize_btcli_wallet_swap_check_output(original_args, rewritten_args, stdout)
    if tuple(original_args[:2]) == ("utils", "convert") and tuple(rewritten_args[:2]) == ("utils", "convert"):
        return _normalize_btcli_utils_convert_stdout(original_args, stdout)
    if _is_btcli_hyperparams_alias_pair(original_args, rewritten_args):
        return _normalize_btcli_sudo_get_output(original_args, rewritten_args, stdout)
    if tuple(original_args[:2]) == ("stake", "auto") and tuple(rewritten_args[:2]) == ("stake", "show-auto"):
        return _normalize_btcli_stake_auto_output(original_args, rewritten_args, stdout)
    if tuple(original_args[:2]) == ("stake", "wizard") and tuple(rewritten_args[:2]) == ("stake", "wizard"):
        return _normalize_btcli_stake_wizard_output(original_args, rewritten_args, stdout)
    if tuple(original_args[:3]) in {("stake", "child", "set"), ("stake", "child", "take")}:
        return _normalize_btcli_stake_child_output(original_args, rewritten_args, stdout)
    if tuple(original_args[:2]) == ("subnets", "burn-cost") and tuple(rewritten_args[:2]) == ("subnet", "create-cost"):
        return _normalize_btcli_subnets_burn_cost_output(original_args, rewritten_args, stdout)

    if not stdout:
        return stdout

    stripped = stdout.strip()

    if (
        tuple(original_args[:2]) == ("subnets", "list")
        and tuple(rewritten_args[:2]) == ("subnet", "list")
        and stripped.startswith("[")
    ):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return stdout
        normalized = _btcli_subnets_list_json_output(payload, None, None)
        return normalized if normalized is not None else '{"subnets": ' + stripped + '}\n'

    if (
        tuple(original_args[:2]) == ("crowd", "list")
        and tuple(rewritten_args[:2]) == ("crowdloan", "list")
        and stripped == "No crowdloans found."
    ):
        return (
            '{"success": true, "error": null, "data": {"crowdloans": [], '
            '"total_count": 0, "total_raised": 0, "total_cap": 0, "total_contributors": 0}}\n'
        )

    if tuple(original_args[:2]) == ("wallet", "balance") and tuple(rewritten_args[:1]) == ("balance",):
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return stdout
        if isinstance(payload, dict) and {"address", "balance_rao", "balance_tao"}.issubset(payload):
            balance_tao = _btcli_numeric_tao(payload.get("balance_tao"))
            if balance_tao is None:
                balance_tao = 0.0
            wrapped = {
                "balances": {
                    "Provided Address 1": {
                        "coldkey": payload["address"],
                        "free": balance_tao,
                        "staked": 0.0,
                        "total": balance_tao,
                    }
                },
                "totals": {
                    "free": balance_tao,
                    "staked": 0.0,
                    "total": balance_tao,
                },
            }
            return json.dumps(wrapped) + "\n"

    if tuple(original_args[:2]) == ("wallet", "list") and tuple(rewritten_args[:2]) == ("wallet", "list"):
        wallet_dir = _btcli_requested_wallet_dir(original_args)
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, list):
            normalized = _btcli_wallet_list_json_payload(payload, wallet_dir)
            return json.dumps(normalized) + "\n" if normalized is not None else stdout
        if stripped.startswith("No wallets found in "):
            wallet_dir = stripped.removeprefix("No wallets found in ").strip()
            return f"❌ No wallets found in dir: {wallet_dir}\n\nWallets\n└── No wallets found.\n"
        rendered = _render_btcli_wallet_list_text(wallet_dir)
        return rendered if rendered is not None else stdout

    if tuple(original_args[:2]) == ("wallet", "get-identity") and tuple(rewritten_args[:2]) == ("identity", "show"):
        if stripped == "{}":
            return stdout
        if stripped.startswith("No identity found for "):
            address = _btcli_wallet_get_identity_requested_address(original_args) or stripped.removeprefix("No identity found for ").strip()
            network = _btcli_wallet_get_identity_requested_network(original_args) or "custom"
            chain = _btcli_wallet_get_identity_requested_chain(original_args)
            if chain:
                return f"❌ Existing identity not found for {address} on Network: {network}, Chain: {chain}\n"
            return f"❌ Existing identity not found for {address} on Network: {network}\n"

    if _uses_btcli_stake_list_flags(original_args) and tuple(rewritten_args[:2]) == ("stake", "list"):
        if "--output" in rewritten_args and "json" in rewritten_args:
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError:
                return stdout
            if isinstance(payload, list) and not payload:
                return ""
        if stripped.startswith("No stakes found for "):
            address = _btcli_stake_list_requested_address(original_args)
            network = _btcli_stake_list_requested_network(original_args)
            chain = _btcli_stake_list_requested_chain(original_args)
            show_local_warning = network in {"local", "localnet"} or chain == "ws://127.0.0.1:9944"
            lines: list[str] = []
            if show_local_warning:
                lines.extend([
                    "Warning: Verify your local subtensor is running on port 9944.",
                    "",
                ])
            if address:
                lines.append(f"No stakes found for coldkey ss58: ({address})")
                return "\n".join(lines) + "\n"
            address = stripped.removeprefix("No stakes found for ")
            lines.append(f"No stakes found for coldkey ss58: {address}")
            return "\n".join(lines) + "\n"

    return stdout


@click.command(
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
        allow_interspersed_args=False,
    ),
)
@click.option("--agcli-binary", default=None, envvar="TAOCLI_AGCLI_BINARY", help="Path to agcli binary")
@click.option("--version", is_flag=True, help="Show taocli version")
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def main(ctx: click.Context, agcli_binary: str | None, version: bool, args: tuple[str, ...]) -> None:
    """taocli — Python wrapper for agcli (Bittensor CLI).

    \b
    All commands are passed through to agcli. Use taocli exactly as
    you would use agcli.

    \b
    Examples:
      taocli balance --address 5G...
      taocli wallet list
      taocli view network
      taocli explain --topic weights
      taocli localnet scaffold
      taocli weights status --netuid 1
      taocli subnets list
      taocli sudo get --netuid 1
      taocli axon set --netuid 1 --ip 1.2.3.4 --port 8091

    \b
    Local validation tip:
      Use `taocli localnet scaffold` to spin up a local chain with a ready subnet,
      run `taocli doctor` to confirm Docker and the local toolchain are ready,
      then inspect commit-reveal state with `taocli weights status --netuid <netuid>`.

    \b
    SDK usage (Python):
      from taocli import Client
      c = Client(network="finney")
      c.balance("5G...")

    \b
    Uses a bundled agcli binary when available. The PyPI package name is
    `tao-cli`, while the installed command remains `taocli`.
    Otherwise install agcli from:
    https://github.com/unarbos/agcli/releases
    """
    if version:
        from taocli import __version__

        click.echo(f"taocli {__version__}")
        return

    if not args:
        click.echo(ctx.get_help())
        click.echo(available_commands_text())
        return

    if maybe_print_alias_help(args):
        return
    if maybe_handle_btcli_builtin_behavior(args):
        return

    try:
        rewritten_args = normalize_passthrough_args(args)
    except click.NoSuchOption as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(2)

    message = unsupported_alias_message(args, rewritten_args)
    if message:
        click.echo(f"Error: {message}", err=True)
        sys.exit(2)

    runner = AgcliRunner(binary=agcli_binary)
    try:
        if _is_btcli_hyperparams_alias_pair(args, rewritten_args):
            result, stdout = _run_btcli_hyperparams_command(runner, args, rewritten_args)
        elif tuple(args[:2]) == ("wallet", "overview") and tuple(rewritten_args[:2]) == ("view", "portfolio"):
            result, stdout = _run_btcli_wallet_overview_command(runner, args, rewritten_args)
        elif tuple(args[:2]) == ("wallet", "balance") and tuple(rewritten_args[:1]) == ("balance",):
            result, stdout = _run_btcli_wallet_balance_command(runner, args, rewritten_args)
        elif _is_btcli_subnets_list_alias_pair(args, rewritten_args) and _requests_json_output(args):
            result, stdout = _run_btcli_subnets_list_command(runner, args, rewritten_args)
        elif _is_btcli_subnets_show_alias_pair(args, rewritten_args):
            result, stdout = _run_btcli_subnets_show_command(runner, args, rewritten_args)
        elif tuple(args[:2]) == ("subnets", "check-start") and tuple(rewritten_args[:2]) == ("subnet", "check-start"):
            result, stdout = _run_btcli_subnets_check_start_command(runner, args, rewritten_args)
        elif tuple(args[:2]) == ("subnets", "start") and tuple(rewritten_args[:2]) == ("subnet", "start"):
            result, stdout = _run_btcli_subnets_start_command(runner, args, rewritten_args)
        elif _is_btcli_subnets_mechanisms_read_alias_pair(args, rewritten_args):
            result, stdout = _run_btcli_subnets_mechanisms_read_command(runner, args, rewritten_args)
        else:
            result = runner.run(list(rewritten_args), check=False, capture=True)
            raw_stdout = result.stdout if isinstance(result.stdout, str) else str(result.stdout or "")
            stdout = normalize_stdout_for_aliases(args, rewritten_args, raw_stdout)
        normalized_stderr = _btcli_normalized_stderr(args, result.stderr)
        if not normalized_stderr and 'raw_stdout' in locals():
            normalized_stderr = _btcli_stake_wizard_prompt_abort_output(args, rewritten_args, raw_stdout)
        if not normalized_stderr and tuple(args[:3]) in {("stake", "child", "set"), ("stake", "child", "take")}:
            if stdout in {
                BTCLI_STAKE_CHILD_SET_WALLET_PROMPT_ABORT,
                BTCLI_STAKE_CHILD_TAKE_WALLET_PROMPT_ABORT,
            }:
                normalized_stderr = stdout
        normalized_error_case = bool(normalized_stderr)
        json_normalized_error = bool(normalized_error_case and _requests_json_output(args))
        if normalized_error_case:
            stdout = ""
        stderr = "" if json_normalized_error else (normalized_stderr or result.stderr)
        stdout, stderr = _reorder_dry_run_output(stdout, stderr)
        if stdout:
            click.echo(stdout, nl=False)
        if stderr:
            click.echo(stderr, nl=False, err=True)
        sys.exit(0 if normalized_error_case else result.returncode)
    except AgcliError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(exc.returncode if exc.returncode > 0 else 1)

