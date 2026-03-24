"""Tests for the taocli package init."""

from __future__ import annotations


def test_imports():
    from taocli import (
        AgcliError,
        AgcliRunner,
        Client,
        Commitment,
        Config,
        Delegate,
        Identity,
        Proxy,
        Root,
        Serve,
        Stake,
        Subnet,
        Swap,
        Transfer,
        Utils,
        View,
        Wallet,
        Weights,
        __version__,
    )

    assert __version__ == "0.4.0"
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
    assert AgcliRunner is not None
    assert AgcliError is not None


def test_sdk_init_imports():
    from taocli.sdk import Client

    assert Client is not None


def test_cli_init_imports():
    from taocli.cli import main

    assert main is not None
