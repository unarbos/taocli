"""Main CLI entry point — passes all commands through to agcli."""

from __future__ import annotations

import sys

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

    \b
    SDK usage (Python):
      from taocli import Client
      c = Client(network="finney")
      c.balance("5G...")

    \b
    Uses a bundled agcli binary when available; otherwise install agcli from:
    https://github.com/unarbos/agcli/releases
    """
    if version:
        from taocli import __version__

        click.echo(f"taocli {__version__}")
        return

    if not args:
        # Show help with available commands
        click.echo(ctx.get_help())
        click.echo("\nAvailable commands (passed through to agcli):")
        for cmd in COMMAND_GROUPS:
            click.echo(f"  {cmd}")
        return

    runner = AgcliRunner(binary=agcli_binary)
    try:
        result = runner.run(list(args), check=False, capture=True)
        if result.stdout:
            click.echo(result.stdout, nl=False)
        if result.stderr:
            click.echo(result.stderr, nl=False, err=True)
        sys.exit(result.returncode)
    except AgcliError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(exc.returncode if exc.returncode > 0 else 1)
