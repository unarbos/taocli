"""Tests for the taocli package init."""

from __future__ import annotations


def test_imports():
    from taocli import (
        Admin,
        AgcliError,
        AgcliRunner,
        Audit,
        Batch,
        Block,
        Client,
        Commitment,
        Config,
        Contracts,
        Crowdloan,
        Delegate,
        Diff,
        Drand,
        Evm,
        Explain,
        Identity,
        Liquidity,
        Localnet,
        Multisig,
        Preimage,
        Proxy,
        Root,
        SafeMode,
        Scheduler,
        Serve,
        Stake,
        Subnet,
        Subscribe,
        Swap,
        Transfer,
        Utils,
        View,
        Wallet,
        Weights,
        __version__,
    )

    assert __version__ == "0.6.0"
    assert Client is not None
    assert Wallet is not None
    assert Stake is not None
    assert Transfer is not None
    assert Subnet is not None
    assert Weights is not None
    assert Delegate is not None
    assert Root is not None
    assert View is not None
    assert Identity is not None
    assert Proxy is not None
    assert Serve is not None
    assert Commitment is not None
    assert Utils is not None
    assert Config is not None
    assert Swap is not None
    assert Admin is not None
    assert Audit is not None
    assert Batch is not None
    assert Block is not None
    assert Contracts is not None
    assert Crowdloan is not None
    assert Diff is not None
    assert Drand is not None
    assert Evm is not None
    assert Explain is not None
    assert Liquidity is not None
    assert Localnet is not None
    assert Multisig is not None
    assert Preimage is not None
    assert SafeMode is not None
    assert Scheduler is not None
    assert Subscribe is not None
    assert AgcliRunner is not None
    assert AgcliError is not None


def test_sdk_init_imports():
    from taocli.sdk import Client

    assert Client is not None


def test_cli_init_imports():
    from taocli.cli import main

    assert main is not None
