"""Tests for the taocli package init."""

from __future__ import annotations


def test_imports():
    from taocli import (
        AgcliError,
        AgcliRunner,
        Client,
        Delegate,
        Root,
        Stake,
        Subnet,
        Transfer,
        View,
        Wallet,
        Weights,
        __version__,
    )

    assert __version__ == "0.1.0"
    assert Client is not None
    assert Wallet is not None
    assert Stake is not None
    assert Transfer is not None
    assert Subnet is not None
    assert Weights is not None
    assert Delegate is not None
    assert Root is not None
    assert View is not None
    assert AgcliRunner is not None
    assert AgcliError is not None


def test_sdk_init_imports():
    from taocli.sdk import Client

    assert Client is not None


def test_cli_init_imports():
    from taocli.cli import main

    assert main is not None
