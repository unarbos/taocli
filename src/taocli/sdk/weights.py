"""Weights SDK module."""

from __future__ import annotations

import hashlib
import json
import re
import secrets
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from taocli.sdk.base import SdkModule

WeightsInput = str | Mapping[Any, Any] | Iterable[tuple[Any, Any]]
CommitSaltInput = str | bytes
HashInput = str | bytes


class CommitRevealState(dict[str, Any]):
    """Structured commit-reveal state record used for durable operator recovery."""


class Weights(SdkModule):
    """Weight-setting operations — set, commit, reveal, show, etc."""

    _WALLET_SELECTION_NOTE = (
        "These commands use agcli's global wallet selectors before the subcommand: "
        "--wallet chooses the coldkey and --hotkey-name chooses the hotkey file name."
    )

    @staticmethod
    def _normalize_uid(uid: object) -> int:
        """Normalize a single UID value."""
        if isinstance(uid, bool):
            raise ValueError("weight uids must be integers")
        if isinstance(uid, int):
            return uid
        if isinstance(uid, str):
            normalized = uid.strip()
            if not normalized:
                raise ValueError("weight uids must be integers")
            try:
                return int(normalized)
            except ValueError as exc:
                raise ValueError("weight uids must be integers") from exc
        raise ValueError("weight uids must be integers")

    @staticmethod
    def _normalize_value(value: object) -> str:
        """Normalize a single weight value."""
        if isinstance(value, bool):
            raise ValueError("weight values must be numbers")
        if isinstance(value, int | float):
            return str(value)
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                raise ValueError("weight values must be numbers")
            try:
                float(normalized)
            except ValueError as exc:
                raise ValueError("weight values must be numbers") from exc
            return normalized
        raise ValueError("weight values must be numbers")

    @classmethod
    def _validated_weights_arg(cls, weights: WeightsInput) -> str:
        """Normalize weights and reject integer values outside the on-chain u16 range."""
        normalized = cls._weights_arg(weights)
        if normalized == "-" or normalized.startswith("@"):
            return normalized
        for entry in normalized.split(","):
            _, _, value_text = entry.partition(":")
            try:
                numeric_value = float(value_text)
            except ValueError as exc:
                raise ValueError("weight values must be numbers") from exc
            if numeric_value.is_integer() and (numeric_value < 0 or numeric_value > 65535):
                raise ValueError(f"weight value out of range: {int(numeric_value)}")
        return normalized

    @classmethod
    def _validated_explicit_weights_arg(cls, weights: WeightsInput) -> str:
        """Normalize explicit weights and reject stdin/file indirection markers."""
        normalized = cls._weights_arg(weights)
        if normalized == "-" or normalized.startswith("@"):
            raise ValueError("weights hash generation requires explicit weights, not stdin or @file inputs")
        return normalized

    @classmethod
    def _string_weights_arg(cls, weights: str) -> str:
        """Validate and normalize a raw CSV weights string."""
        normalized = weights.strip()
        if not normalized:
            raise ValueError("weights cannot be empty")

        entries = [entry.strip() for entry in normalized.split(",")]
        if any(not entry for entry in entries):
            raise ValueError("weights entries must use uid:value format")

        seen_uids: set[int] = set()
        parts: list[str] = []
        for entry in entries:
            uid, separator, value = entry.partition(":")
            if separator != ":" or not uid.strip() or not value.strip():
                raise ValueError("weights entries must use uid:value format")
            normalized_uid = cls._normalize_uid(uid)
            if normalized_uid in seen_uids:
                raise ValueError(f"duplicate uid in weights: {normalized_uid}")
            seen_uids.add(normalized_uid)
            parts.append(f"{normalized_uid}:{cls._normalize_value(value)}")
        return ",".join(parts)

    @classmethod
    def _weights_from_json_string(cls, weights: str) -> str:
        """Normalize agcli-compatible JSON weight inputs into CSV form."""
        try:
            parsed = json.loads(weights)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON weights input: {exc.msg}") from exc

        if isinstance(parsed, Mapping):
            return cls._weights_arg(dict(parsed))
        if isinstance(parsed, list):
            normalized_entries: list[tuple[Any, Any]] = []
            for item in parsed:
                if not isinstance(item, Mapping):
                    raise ValueError("JSON weights must be an object map or array of {uid, weight} entries")
                normalized_entries.append((item.get("uid"), item.get("weight")))
            return cls._weights_arg(normalized_entries)
        raise ValueError("JSON weights must be an object map or array of {uid, weight} entries")

    @classmethod
    def _weights_arg(cls, weights: WeightsInput) -> str:
        """Normalize weights into an agcli-compatible format."""
        if isinstance(weights, str):
            normalized = weights.strip()
            if not normalized:
                raise ValueError("weights cannot be empty")
            if normalized == "-" or normalized.startswith("@"):
                return normalized
            if normalized.startswith("{") or normalized.startswith("["):
                return cls._weights_from_json_string(normalized)
            return cls._string_weights_arg(normalized)

        items = list(weights.items()) if isinstance(weights, Mapping) else list(weights)
        if not items:
            raise ValueError("weights cannot be empty")

        seen_uids: set[int] = set()
        parts: list[str] = []
        for item in items:
            try:
                uid, value = item
            except (TypeError, ValueError) as exc:
                raise ValueError("weights entries must be (uid, value) pairs") from exc
            normalized_uid = cls._normalize_uid(uid)
            if normalized_uid in seen_uids:
                raise ValueError(f"duplicate uid in weights: {normalized_uid}")
            seen_uids.add(normalized_uid)
            parts.append(f"{normalized_uid}:{cls._normalize_value(value)}")
        return ",".join(parts)

    @staticmethod
    def _salt_arg(salt: CommitSaltInput) -> str:
        """Normalize a commit/reveal salt value."""
        if isinstance(salt, bytes):
            if not salt:
                raise ValueError("salt cannot be empty")
            try:
                return salt.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise ValueError("salt bytes must decode as UTF-8") from exc
        if isinstance(salt, str):
            normalized = salt.strip()
            if not normalized:
                raise ValueError("salt cannot be empty")
            return normalized
        raise ValueError("salt must be a string or bytes")

    @staticmethod
    def _hash_arg(hash_value: HashInput) -> str:
        """Normalize a precomputed mechanism commit hash."""
        if isinstance(hash_value, bytes):
            if len(hash_value) != 32:
                raise ValueError(f"hash must be exactly 32 bytes, got {len(hash_value)} bytes")
            return f"0x{hash_value.hex()}"
        if isinstance(hash_value, str):
            normalized = hash_value.strip()
            if not normalized:
                raise ValueError("hash cannot be empty")
            raw = normalized[2:] if normalized.startswith("0x") else normalized
            try:
                decoded = bytes.fromhex(raw)
            except ValueError as exc:
                raise ValueError("hash must be valid hex") from exc
            if len(decoded) != 32:
                raise ValueError(f"hash must be exactly 32 bytes, got {len(decoded)} bytes")
            return normalized
        raise ValueError("hash must be a hex string or 32-byte value")

    @classmethod
    def _salt_bytes(cls, salt: CommitSaltInput) -> bytes:
        """Normalize a salt into the raw bytes used for commit hashing."""
        return cls._salt_arg(salt).encode("utf-8")

    @classmethod
    def _salt_u16_arg(cls, salt: CommitSaltInput) -> list[int]:
        """Normalize a salt into the u16 chunks used by reveal calls."""
        raw = cls._salt_bytes(salt)
        return [
            ((chunk[1] << 8) | chunk[0]) if len(chunk) == 2 else chunk[0]
            for chunk in (raw[index : index + 2] for index in range(0, len(raw), 2))
        ]

    @classmethod
    def _weights_vectors(cls, weights: WeightsInput) -> tuple[list[int], list[int]]:
        """Normalize weights into u16 UID and value vectors for commit hashing."""
        normalized = cls._validated_explicit_weights_arg(weights)

        uids: list[int] = []
        values: list[int] = []
        for entry in normalized.split(","):
            uid_text, _, value_text = entry.partition(":")
            uid = cls._normalize_uid(uid_text)
            try:
                numeric_value = float(value_text)
            except ValueError as exc:
                raise ValueError("weight values must be numbers") from exc
            if not numeric_value.is_integer():
                raise ValueError("weights hash generation requires integer weight values")
            value = int(numeric_value)
            if uid < 0 or uid > 65535:
                raise ValueError(f"uid out of range for weight hash generation: {uid}")
            if value < 0 or value > 65535:
                raise ValueError(f"weight value out of range for weight hash generation: {value}")
            uids.append(uid)
            values.append(value)
        return uids, values

    @classmethod
    def _compute_commit_hash(cls, weights: WeightsInput, salt: CommitSaltInput) -> str:
        """Compute the agcli-compatible Blake2b commit hash for weights and salt."""
        uids, values = cls._weights_vectors(weights)
        hasher = hashlib.blake2b(digest_size=32)
        for uid in uids:
            hasher.update(uid.to_bytes(2, byteorder="little", signed=False))
        for value in values:
            hasher.update(value.to_bytes(2, byteorder="little", signed=False))
        hasher.update(cls._salt_bytes(salt))
        return f"0x{hasher.hexdigest()}"

    @classmethod
    def _optional_text(cls, name: str, value: str | None) -> str | None:
        """Normalize optional text arguments used in workflow helpers."""
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{name} cannot be empty")
        return normalized

    @classmethod
    def _command_prefix(cls, *, wallet: str | None = None, hotkey: str | None = None) -> tuple[str, dict[str, Any]]:
        """Build a workflow command prefix for weight helpers."""
        prefix = "agcli"
        context: dict[str, Any] = {}
        wallet_arg = cls._optional_text("wallet", wallet)
        hotkey_arg = cls._optional_text("hotkey", hotkey)
        if wallet_arg is not None:
            prefix = f"{prefix} --wallet {wallet_arg}"
            context["wallet"] = wallet_arg
        if hotkey_arg is not None:
            prefix = f"{prefix} --hotkey-name {hotkey_arg}"
            context["hotkey"] = hotkey_arg
        if wallet_arg is not None or hotkey_arg is not None:
            context["wallet_selection_note"] = cls._WALLET_SELECTION_NOTE
        return prefix, context

    @staticmethod
    def _status_note() -> str:
        """Return guidance for interpreting weights status."""
        return (
            "weights status resolves the current hotkey from agcli's global wallet selectors "
            "and inspects pending commits, reveal windows, and commit-reveal settings for "
            "that hotkey on the target subnet."
        )

    @staticmethod
    def _show_note() -> str:
        """Return guidance for on-chain weight inspection."""
        return (
            "Use weights show when you want the live on-chain weights map; use weights status "
            "when you want commit-reveal state for your hotkey."
        )

    @staticmethod
    def _hyperparams_note() -> str:
        """Return guidance for weights-related subnet configuration."""
        return (
            "Inspect subnet hyperparams before retrying failed set/reveal flows so "
            "version_key, commit-reveal, and rate-limit assumptions match the subnet."
        )

    @staticmethod
    def _pending_commits_note() -> str:
        """Return guidance for subnet-wide pending commit inspection."""
        return (
            "Use subnet commits when you need every on-chain pending commit for the subnet, "
            "especially when comparing saved reveal state against live status for one hotkey."
        )

    @staticmethod
    def _set_weights_note() -> str:
        """Return guidance for direct set vs commit-reveal."""
        return (
            "Use direct weights set only when the subnet allows it; otherwise follow "
            "commit-reveal or the saved-state recovery helpers instead of reformatting "
            "commands manually."
        )

    @staticmethod
    def _adjacent_workflows_note() -> str:
        """Return guidance for pivoting from weights into adjacent operator workflows."""
        return (
            "If the weights-specific path still looks wrong, pivot to show/metagraph and chain_data plus emissions for "
            "live weights, subnet UIDs/state, pending_commits for operator watch/reveal drift checks, "
            "inspect_neuron_command for per-UID member detail after metagraph/monitor checks, "
            "config_show plus wallet_show plus wallet_current plus wallet_associate plus wallet_derive plus "
            "wallet_sign plus wallet_verify plus balance plus validators/stake/stake_add/validator_requirements for "
            "wallet selector inspection, wallet inventory plus selected coldkey/hotkey identity confirmation, hotkey "
            "association recovery, manual address derivation checks, signature generation, signature verification, "
            "coldkey funding, "
            "validator readiness, stake top-ups, or validator threshold checks, hyperparams plus "
            "owner_param_list/set_param/admin_list/admin_raw/registration_cost/register_neuron/"
            "pow_register/snipe_register/health for subnet readiness, subnet entry, registration retries, "
            "root-only mutation escape hatches, or mutation discovery, "
            "serve_axon plus serve_axon_tls plus serve_prometheus plus serve_reset plus probe plus "
            "axon/miner_endpoints/validator_endpoints for serve retries, TLS serve recovery, prometheus recovery, "
            "endpoint recovery, or serve/endpoint verification, watch plus monitor for live UID/state drift, "
            "explain_weights/explain_commit_reveal for copy-pasteable concept refreshers, and subnets plus "
            "subnet for available netuid discovery and the current subnet summary."
        )

    @staticmethod
    def _adjacent_recovery_note() -> str:
        """Return guidance for pivoting from weights troubleshooting into adjacent discovery commands."""
        return (
            "If the weights-specific retry path still looks wrong, pivot to show_command for live on-chain weights, "
            "inspect_pending_commits_command for subnet-wide pending commit/watch drift checks, "
            "inspect_metagraph_command, inspect_chain_data_command, inspect_emissions_command, and "
            "inspect_monitor_command for live subnet UIDs/state drift, inspect_neuron_command for per-UID member "
            "detail after metagraph/monitor checks, inspect_config_show_command, inspect_wallet_show_command, "
            "inspect_wallet_current_command, inspect_wallet_associate_command, inspect_wallet_derive_command, "
            "inspect_wallet_sign_command, inspect_wallet_verify_command, inspect_balance_command, "
            "inspect_validators_command, inspect_stake_command, inspect_stake_add_command, and "
            "inspect_validator_requirements_command for wallet selector inspection, wallet inventory plus "
            "selected coldkey/hotkey identity confirmation, hotkey association recovery, manual address "
            "derivation checks, signature generation, signature verification, coldkey funding, validator readiness, "
            "stake top-ups, or validator threshold checks, "
            "inspect_hyperparams_command plus "
            "inspect_owner_param_list_command, inspect_set_param_command, inspect_admin_list_command, "
            "inspect_admin_raw_command, inspect_registration_cost_command, "
            "inspect_register_neuron_command, inspect_pow_register_command, "
            "inspect_snipe_register_command, and inspect_health_command for subnet readiness, "
            "subnet entry, registration retries, root-only mutation escape hatches, or mutation discovery, "
            "inspect_serve_axon_command plus inspect_serve_axon_tls_command plus "
            "inspect_serve_prometheus_command plus inspect_serve_reset_command plus inspect_probe_command plus "
            "inspect_axon_command, inspect_miner_endpoints_command, and inspect_validator_endpoints_command for "
            "serve retries, TLS serve recovery, prometheus recovery, endpoint recovery, or serve/endpoint "
            "verification, inspect_watch_command plus inspect_monitor_command for live UID/state drift, "
            "explain_weights_command plus explain_commit_reveal_command for copy-pasteable concept refreshers, "
            "inspect_subnets_command for available netuid discovery, and inspect_subnet_command for the current "
            "subnet summary."
        )

    @staticmethod
    def _error_arg(error: str) -> str:
        """Normalize an error string used for troubleshooting helpers."""
        if not isinstance(error, str):
            raise ValueError("error must be a string")
        normalized = error.strip()
        if not normalized:
            raise ValueError("error cannot be empty")
        return normalized

    @staticmethod
    def _state_path_arg(path: str | Path) -> Path:
        """Normalize a commit-reveal state path."""
        candidate = Path(path).expanduser() if isinstance(path, str | Path) else path
        if not isinstance(candidate, Path):
            raise ValueError("state path must be a string or Path")
        normalized = str(candidate).strip()
        if not normalized:
            raise ValueError("state path cannot be empty")
        return Path(normalized).expanduser()

    @classmethod
    def _state_record(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
        *,
        source: str,
        wait: bool = False,
        state_path: str | Path | None = None,
    ) -> CommitRevealState:
        """Build a durable commit-reveal recovery record."""
        normalized_weights = cls._weights_arg(weights)
        normalized_salt = cls._salt_arg(salt)
        normalized_version_key = cls._version_key_arg(version_key)
        record: CommitRevealState = CommitRevealState(
            netuid=int(cls._netuid_arg(netuid)),
            normalized_weights=normalized_weights,
            normalized_salt=normalized_salt,
            salt_u16=cls._salt_u16_arg(normalized_salt),
            hash=cls._compute_commit_hash(normalized_weights, normalized_salt),
            status_command=cls.status_help(netuid),
            inspect_status_command=cls.status_help(netuid),
            inspect_pending_commits_command=cls.inspect_pending_commits_help(netuid),
            inspect_version_key_command=cls.inspect_version_key_help(netuid),
            **cls._adjacent_recovery_fields(netuid),
            preflight_note=(
                "Inspect weights status and subnet hyperparams before commit/reveal so the reveal window, "
                "commit-reveal mode, and version_key still match the subnet."
            ),
            pending_commits_note=(
                "If wallet-specific status and this saved state drift apart, inspect subnet-wide pending commits "
                "before retrying the saved reveal_command."
            ),
            commit_command=cls.commit_help(netuid, normalized_weights, salt=normalized_salt),
            reveal_command=cls.reveal_help(
                netuid,
                normalized_weights,
                normalized_salt,
                version_key=version_key,
            ),
            commit_reveal_command=cls.commit_reveal_help(
                netuid,
                normalized_weights,
                version_key=version_key,
                wait=wait,
            ),
            source=source,
            wait=wait,
        )
        if normalized_version_key is not None:
            record["version_key"] = int(normalized_version_key)
        if state_path is not None:
            record["state_path"] = str(cls._state_path_arg(state_path))
        return record

    @classmethod
    def save_commit_reveal_state_help(
        cls,
        path: str | Path,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
        *,
        source: str = "manual_commit",
        wait: bool = False,
    ) -> CommitRevealState:
        """Write a durable commit-reveal recovery record to disk and return it."""
        state_path = cls._state_path_arg(path)
        record = cls._state_record(
            netuid,
            weights,
            salt,
            version_key,
            source=source,
            wait=wait,
            state_path=state_path,
        )
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return record

    @classmethod
    def load_commit_reveal_state_help(cls, path: str | Path) -> CommitRevealState:
        """Load and validate a previously saved commit-reveal recovery record."""
        state_path = cls._state_path_arg(path)
        try:
            payload = json.loads(state_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ValueError(f"commit-reveal state file not found: {state_path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid commit-reveal state JSON: {exc.msg}") from exc
        if not isinstance(payload, Mapping):
            raise ValueError("commit-reveal state must be a JSON object")

        netuid = payload.get("netuid")
        weights = payload.get("normalized_weights")
        salt = payload.get("normalized_salt")
        version_key_value = payload.get("version_key")
        if isinstance(netuid, bool) or not isinstance(netuid, int):
            raise ValueError("commit-reveal state netuid must be an integer")
        if not isinstance(weights, (str, Mapping)) and not isinstance(weights, Iterable):
            raise ValueError("commit-reveal state normalized_weights must be weights-compatible")
        if not isinstance(salt, (str, bytes)):
            raise ValueError("commit-reveal state normalized_salt must be a string or bytes")
        if version_key_value is not None and (
            isinstance(version_key_value, bool) or not isinstance(version_key_value, int)
        ):
            raise ValueError("commit-reveal state version_key must be an integer")
        version_key_arg = cls._version_key_arg(version_key_value)
        version_key = None if version_key_arg is None else int(version_key_arg)
        state_record = cls._state_record(
            netuid,
            cls._weights_arg(weights),
            cls._salt_arg(salt),
            version_key,
            source=str(payload.get("source") or "saved_state"),
            wait=bool(payload.get("wait", False)),
            state_path=state_path,
        )
        return state_record

    @classmethod
    def create_commit_reveal_state_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
        *,
        salt: CommitSaltInput | None = None,
        state_path: str | Path | None = None,
        wait: bool = False,
    ) -> CommitRevealState:
        """Create a recoverable commit-reveal state record, optionally persisting it to disk."""
        resolved_salt = salt if salt is not None else secrets.token_hex(16)
        if state_path is not None:
            return cls.save_commit_reveal_state_help(
                state_path,
                netuid,
                weights,
                resolved_salt,
                version_key,
                source="generated_commit_reveal_state",
                wait=wait,
            )
        return cls._state_record(
            netuid,
            weights,
            resolved_salt,
            version_key,
            source="generated_commit_reveal_state",
            wait=wait,
        )

    @classmethod
    def recover_reveal_from_state_help(
        cls,
        path: str | Path,
        *,
        version_key: int | None = None,
    ) -> CommitRevealState:
        """Load a saved state record and optionally override its reveal version key."""
        record = cls.load_commit_reveal_state_help(path)
        saved_version_key = record.get("version_key")
        resolved_version_key = saved_version_key if version_key is None else version_key
        record["reveal_command"] = cls.reveal_help(
            record["netuid"],
            record["normalized_weights"],
            record["normalized_salt"],
            version_key=resolved_version_key,
        )
        if version_key is not None:
            version_key_arg = cls._version_key_arg(version_key)
            assert version_key_arg is not None
            if saved_version_key is not None:
                record["saved_version_key"] = saved_version_key
            record["version_key"] = int(version_key_arg)
            record["version_key_override_applied"] = True
        return record

    @staticmethod
    def _is_version_key_mismatch_error(error: str) -> bool:
        """Return whether an error indicates the wrong commit-reveal version key."""
        return "IncorrectCommitRevealVersion" in error or "Custom error: 111" in error

    @staticmethod
    def _is_commit_state_error(error: str) -> bool:
        """Return whether an error points to on-chain commit state that should be inspected directly."""
        return any(
            needle in error
            for needle in (
                "RevealTooEarly",
                "NotInRevealPeriod",
                "RevealTooLate",
                "ExpiredWeightCommit",
                "Custom error: 77",
                "NoWeightsCommitFound",
                "Custom error: 50",
                "InvalidRevealCommitHashNotMatch",
                "Custom error: 51",
                "TooManyUnrevealedCommits",
                "Custom error: 76",
                "Custom error: 16",
            )
        )

    @staticmethod
    def _is_validator_permit_error(error: str) -> bool:
        """Return whether an error indicates missing validator permit on the target subnet."""
        return "NeuronNoValidatorPermit" in error or "Custom error: 15" in error

    @staticmethod
    def _is_insufficient_stake_error(error: str) -> bool:
        """Return whether an error indicates the hotkey stake is too low to set weights."""
        return "NotEnoughStakeToSetWeights" in error

    @staticmethod
    def _is_weights_not_settable_error(error: str) -> bool:
        """Return whether an error indicates direct weight setting is blocked by subnet rules or timing."""
        return any(
            needle in error
            for needle in (
                "WeightsNotSettable",
                "WeightsWindow",
                "AdminActionProhibitedDuringWeightsWindow",
            )
        )

    @staticmethod
    def _is_commit_reveal_disabled_error(error: str) -> bool:
        """Return whether an error indicates commit-reveal is disabled on the target subnet."""
        return "CommitRevealDisabled" in error or "Custom error: 53" in error

    @staticmethod
    def _is_commit_reveal_required_error(error: str) -> bool:
        """Return whether an error indicates the subnet requires commit-reveal instead of direct set."""
        return "CommitRevealEnabled" in error

    @staticmethod
    def _saved_state_next_step(error: str, *, version_key_overridden: bool = False) -> str | None:
        """Return saved-state-specific recovery guidance for common reveal failures."""
        if Weights._is_version_key_mismatch_error(error):
            if version_key_overridden:
                return (
                    "Retry reveal with the saved state record and the overridden version_key shown in reveal_command."
                )
            return "Retry reveal with the saved state record after updating reveal_command to the matching version_key."
        if any(needle in error for needle in ("InvalidRevealCommitHashNotMatch", "Custom error: 51")):
            return "Retry reveal with the exact saved reveal_command from this state record."
        if any(needle in error for needle in ("NoWeightsCommitFound", "Custom error: 50")):
            return (
                "Retry reveal with the exact saved reveal_command from this state record, or create a fresh commit "
                "if the original one no longer exists on-chain."
            )
        return None

    @classmethod
    def _version_key_recovery_fields(cls, netuid: int, *, saved_state: bool = False) -> dict[str, str]:
        """Attach a concrete hyperparameters command for version-key mismatch recovery."""
        inspect_command = cls.inspect_version_key_help(netuid)
        note = (
            "Run inspect_version_key_command to inspect the subnet hyperparameters and find the expected "
            "version_key before retrying."
        )
        if saved_state:
            note = (
                "Run inspect_version_key_command to inspect the subnet hyperparameters and find the expected "
                "version_key before retrying the saved reveal_command."
            )
        return {
            "inspect_version_key_command": inspect_command,
            "version_key_recovery_note": note,
        }

    @classmethod
    def _commit_state_recovery_fields(cls, netuid: int, *, saved_state: bool = False) -> dict[str, str]:
        """Attach concrete on-chain inspection commands for commit-state recovery."""
        status_command = cls.status_help(netuid)
        commits_command = cls.inspect_pending_commits_help(netuid)
        note = (
            "Run inspect_pending_commits_command to inspect the current pending commits on-chain, then compare that "
            "output with inspect_status_command before retrying."
        )
        if saved_state:
            note = (
                "Run inspect_pending_commits_command to inspect the current pending commits on-chain, then compare "
                "that output with the saved state record and inspect_status_command before retrying the saved "
                "reveal_command."
            )
        return {
            "inspect_status_command": status_command,
            "inspect_pending_commits_command": commits_command,
            "commit_state_recovery_note": note,
        }

    @classmethod
    def _validator_permit_recovery_fields(cls, netuid: int) -> dict[str, str]:
        """Attach inspection commands for validator-permit failures."""
        validators_command = cls.inspect_validators_help(netuid)
        stake_command = cls.inspect_stake_help(netuid)
        hyperparams_command = cls.inspect_validator_requirements_help(netuid)
        return {
            "inspect_validators_command": validators_command,
            "inspect_stake_command": stake_command,
            "inspect_stake_add_command": cls.inspect_stake_add_help(netuid),
            "inspect_validator_requirements_command": hyperparams_command,
            "validator_permit_recovery_note": (
                "Run inspect_validators_command to confirm the hotkey currently has validator permit, then compare "
                "its stake with inspect_stake_command and inspect_validator_requirements_command before retrying. "
                "Use inspect_stake_add_command when the hotkey needs a stake top-up first."
            ),
        }

    @classmethod
    def _insufficient_stake_recovery_fields(cls, netuid: int) -> dict[str, str]:
        """Attach inspection commands for insufficient-stake failures."""
        stake_command = cls.inspect_stake_help(netuid)
        hyperparams_command = cls.inspect_validator_requirements_help(netuid)
        return {
            "inspect_stake_command": stake_command,
            "inspect_config_show_command": cls.inspect_config_show_help(),
            "inspect_wallet_show_command": cls.inspect_wallet_show_help(),
            "inspect_wallet_current_command": cls.inspect_wallet_current_help(),
            "inspect_wallet_associate_command": cls.inspect_wallet_associate_help(),
            "inspect_wallet_derive_command": cls.inspect_wallet_derive_help(),
            "inspect_wallet_sign_command": cls.inspect_wallet_sign_help(),
            "inspect_wallet_verify_command": cls.inspect_wallet_verify_help(),
            "inspect_balance_command": cls.inspect_balance_help(),
            "inspect_stake_add_command": cls.inspect_stake_add_help(netuid),
            "inspect_validator_requirements_command": hyperparams_command,
            "stake_recovery_note": (
                "Run inspect_stake_command to confirm the hotkey stake on this subnet, then compare it with "
                "inspect_validator_requirements_command before retrying. Use inspect_config_show_command when the "
                "wrong wallet or hotkey may be selected, inspect_wallet_show_command to inspect wallet inventory, "
                "inspect_wallet_current_command to confirm the selected coldkey/hotkey identity, "
                "inspect_wallet_associate_command when the hotkey may need to be re-associated to the coldkey, "
                "inspect_wallet_derive_command for manual address confirmation from a pubkey or mnemonic, "
                "inspect_wallet_sign_command when you need to generate a fresh confirmation signature, "
                "inspect_wallet_verify_command when you need explicit signer/signature confirmation, and "
                "inspect_balance_command when the coldkey may need more TAO before staking."
            ),
        }

    @classmethod
    def _weights_not_settable_recovery_fields(cls, netuid: int) -> dict[str, str]:
        """Attach inspection commands for protected-window or temporarily blocked direct-set failures."""
        return {
            "inspect_status_command": cls.status_help(netuid),
            "inspect_subnet_rules_command": cls.inspect_subnet_rules_help(netuid),
            "weights_not_settable_recovery_note": (
                "Run inspect_status_command to see whether commit-reveal is enabled or a protected weights window is "
                "active, then compare it with inspect_subnet_rules_command before retrying."
            ),
        }

    @classmethod
    def _commit_reveal_disabled_recovery_fields(cls, netuid: int) -> dict[str, str]:
        """Attach inspection commands for commit flows used against direct-set subnets."""
        return {
            "inspect_status_command": cls.status_help(netuid),
            "inspect_subnet_rules_command": cls.inspect_subnet_rules_help(netuid),
            "commit_reveal_disabled_recovery_note": (
                "Run inspect_status_command to confirm commit-reveal is disabled, then use "
                "inspect_subnet_rules_command to verify the subnet settings before retrying with a direct set "
                "command."
            ),
        }

    @classmethod
    def _commit_reveal_required_recovery_fields(cls, netuid: int) -> dict[str, str]:
        """Attach inspection commands for direct-set flows used against commit-reveal subnets."""
        return {
            "inspect_status_command": cls.status_help(netuid),
            "inspect_subnet_rules_command": cls.inspect_subnet_rules_help(netuid),
            "commit_reveal_required_recovery_note": (
                "Run inspect_status_command to confirm commit-reveal is enabled, then use "
                "inspect_subnet_rules_command to verify the subnet settings before retrying with commit/reveal "
                "commands."
            ),
        }

    @classmethod
    def _direct_set_recovery_fields(cls, netuid: int, error: str) -> dict[str, str]:
        """Attach targeted inspection commands for direct set_weights failures."""
        if cls._is_validator_permit_error(error):
            return cls._validator_permit_recovery_fields(netuid)
        if cls._is_insufficient_stake_error(error):
            return cls._insufficient_stake_recovery_fields(netuid)
        if cls._is_weights_not_settable_error(error):
            return cls._weights_not_settable_recovery_fields(netuid)
        if cls._is_commit_reveal_disabled_error(error):
            return cls._commit_reveal_disabled_recovery_fields(netuid)
        if cls._is_commit_reveal_required_error(error):
            return cls._commit_reveal_required_recovery_fields(netuid)
        return {}

    @classmethod
    def inspect_validators_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready validators view command for permit recovery."""
        return " ".join(["agcli", "view", "validators", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_stake_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready stake inspection command for the current hotkey."""
        return " ".join(["agcli", "stake", "list", "--netuid", cls._netuid_arg(netuid)])

    @staticmethod
    def inspect_config_show_help() -> str:
        """Return a copy-paste-ready config inspection command for wallet selector recovery."""
        return " ".join(["agcli", "config", "show"])

    @staticmethod
    def inspect_wallet_show_help() -> str:
        """Return a copy-paste-ready wallet inspection command for coldkey/hotkey identity recovery."""
        return " ".join(["agcli", "wallet", "show", "--all"])

    @staticmethod
    def inspect_wallet_current_help() -> str:
        """Return a copy-paste-ready selected wallet command for coldkey/hotkey confirmation."""
        return " ".join(["agcli", "wallet", "show"])

    @staticmethod
    def inspect_wallet_associate_help() -> str:
        """Return a copy-paste-ready wallet association command for coldkey/hotkey pairing recovery."""
        return " ".join(["agcli", "wallet", "associate-hotkey"])

    @staticmethod
    def inspect_wallet_derive_help() -> str:
        """Return a copy-paste-ready wallet derive command for manual address confirmation."""
        return " ".join(["agcli", "wallet", "derive", "--input", "<pubkey-or-mnemonic>"])

    @staticmethod
    def inspect_wallet_verify_help() -> str:
        """Return a copy-paste-ready wallet verify command for signer/signature confirmation."""
        return " ".join(
            [
                "agcli",
                "wallet",
                "verify",
                "--message",
                "<message>",
                "--signature",
                "<signature>",
                "--signer",
                "<ss58>",
            ]
        )

    @staticmethod
    def inspect_wallet_sign_help() -> str:
        """Return a copy-paste-ready wallet sign command for generating a confirmation signature."""
        return " ".join(["agcli", "wallet", "sign", "--message", "<message>"])

    @staticmethod
    def inspect_balance_help() -> str:
        """Return a copy-paste-ready coldkey balance command for funding recovery."""
        return " ".join(["agcli", "balance"])

    @classmethod
    def inspect_stake_add_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready stake top-up command stub for validator-readiness recovery."""
        return " ".join(["agcli", "stake", "add", "--netuid", cls._netuid_arg(netuid), "--amount", "<amount>"])

    @classmethod
    def inspect_validator_requirements_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet hyperparameters command for stake/permit recovery."""
        return " ".join(["agcli", "subnet", "hyperparams", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_subnet_rules_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet hyperparameters command for weights rule recovery."""
        return " ".join(["agcli", "subnet", "hyperparams", "--netuid", cls._netuid_arg(netuid)])

    @staticmethod
    def inspect_subnets_help() -> str:
        """Return a copy-paste-ready command to list available subnets."""
        return " ".join(["agcli", "subnet", "list"])

    @classmethod
    def inspect_metagraph_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready metagraph command for UID/payload recovery."""
        return " ".join(["agcli", "subnet", "metagraph", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_chain_data_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready chain-data entrypoint for adjacent subnet inspection."""
        return " ".join(["agcli", "subnet", "show", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_subnet_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet summary command for adjacent troubleshooting."""
        return cls.inspect_chain_data_help(netuid)

    @classmethod
    def inspect_registration_cost_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet registration-cost command for readiness checks."""
        return " ".join(["agcli", "subnet", "cost", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_register_neuron_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet registration command for operator entry pivots."""
        return " ".join(["agcli", "subnet", "register-neuron", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_health_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet health command for readiness checks."""
        return " ".join(["agcli", "subnet", "health", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_serve_reset_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready serve reset command for clearing stale endpoint metadata."""
        return " ".join(["agcli", "serve", "reset", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_serve_axon_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready serve axon command stub for re-serving endpoint metadata."""
        return " ".join(
            ["agcli", "serve", "axon", "--netuid", cls._netuid_arg(netuid), "--ip", "<ip>", "--port", "<port>"]
        )

    @classmethod
    def inspect_serve_axon_tls_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready TLS serve command stub for re-serving encrypted endpoint metadata."""
        return " ".join(
            [
                "agcli",
                "serve",
                "axon-tls",
                "--netuid",
                cls._netuid_arg(netuid),
                "--ip",
                "<ip>",
                "--port",
                "<port>",
                "--cert",
                "<cert>",
            ]
        )

    @classmethod
    def inspect_serve_prometheus_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready serve prometheus command stub for re-serving monitoring metadata."""
        return " ".join(
            ["agcli", "serve", "prometheus", "--netuid", cls._netuid_arg(netuid), "--ip", "<ip>", "--port", "<port>"]
        )

    @classmethod
    def inspect_pow_register_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready proof-of-work registration command for retry pivots."""
        return " ".join(["agcli", "subnet", "pow", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_snipe_register_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready snipe registration command for retry pivots."""
        return " ".join(["agcli", "subnet", "snipe", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_axon_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready axon inspection command for serve verification."""
        return " ".join(["agcli", "view", "axon", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_miner_endpoints_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready miner-endpoint command for chain-data pivots."""
        return cls.inspect_axon_help(netuid)

    @classmethod
    def inspect_validator_endpoints_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready validator-endpoint command for chain-data pivots."""
        return cls.inspect_axon_help(netuid)

    @classmethod
    def inspect_probe_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet probe command for serve reachability verification."""
        return " ".join(["agcli", "subnet", "probe", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_watch_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet watch command for live subnet drift checks."""
        return " ".join(["agcli", "subnet", "watch", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_monitor_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet monitor command for live metagraph/state drift checks."""
        return " ".join(["agcli", "subnet", "monitor", "--netuid", cls._netuid_arg(netuid), "--json"])

    @classmethod
    def inspect_neuron_help(cls, netuid: int, uid: int = 0) -> str:
        """Return a copy-paste-ready per-UID neuron command for member-detail recovery."""
        return " ".join(["agcli", "view", "neuron", "--netuid", cls._netuid_arg(netuid), "--uid", cls._uid_arg(uid)])

    @classmethod
    def inspect_emissions_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready emissions inspection command for adjacent chain-data checks."""
        return " ".join(["agcli", "view", "emissions", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_owner_param_list_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready owner-visible hyperparameter list command."""
        return " ".join(["agcli", "subnet", "set-param", "--netuid", cls._netuid_arg(netuid), "--param", "list"])

    @classmethod
    def inspect_set_param_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet parameter mutation entrypoint for owner workflows."""
        return " ".join(["agcli", "subnet", "set-param", "--netuid", cls._netuid_arg(netuid)])

    @staticmethod
    def inspect_admin_list_help() -> str:
        """Return a copy-paste-ready admin command list for root-only hyperparameter discovery."""
        return " ".join(["agcli", "admin", "list"])

    @staticmethod
    def inspect_admin_raw_help() -> str:
        """Return a copy-paste-ready raw admin entrypoint for root-only mutation fallback."""
        return " ".join(["agcli", "admin", "raw", "--call", "<sudo-call>"])

    @staticmethod
    def explain_weights_help() -> str:
        """Return a copy-paste-ready weights explainer command for operator refreshers."""
        return " ".join(["agcli", "explain", "weights"])

    @staticmethod
    def explain_commit_reveal_help() -> str:
        """Return a copy-paste-ready commit-reveal explainer command for operator refreshers."""
        return " ".join(["agcli", "explain", "commit-reveal"])

    @classmethod
    def _adjacent_workflows_fields(cls, netuid: int) -> dict[str, str]:
        """Attach adjacent operator workflow entrypoints for weights runbooks and troubleshooting."""
        return {
            "show_command": cls.show_help(netuid),
            "inspect_metagraph_command": cls.inspect_metagraph_help(netuid),
            "inspect_chain_data_command": cls.inspect_chain_data_help(netuid),
            "inspect_subnets_command": cls.inspect_subnets_help(),
            "inspect_subnet_command": cls.inspect_subnet_help(netuid),
            "inspect_hyperparams_command": cls.inspect_hyperparams_help(netuid),
            "inspect_emissions_command": cls.inspect_emissions_help(netuid),
            "inspect_neuron_command": cls.inspect_neuron_help(netuid),
            "inspect_validators_command": cls.inspect_validators_help(netuid),
            "inspect_stake_command": cls.inspect_stake_help(netuid),
            "inspect_config_show_command": cls.inspect_config_show_help(),
            "inspect_wallet_show_command": cls.inspect_wallet_show_help(),
            "inspect_wallet_current_command": cls.inspect_wallet_current_help(),
            "inspect_wallet_associate_command": cls.inspect_wallet_associate_help(),
            "inspect_wallet_derive_command": cls.inspect_wallet_derive_help(),
            "inspect_wallet_sign_command": cls.inspect_wallet_sign_help(),
            "inspect_wallet_verify_command": cls.inspect_wallet_verify_help(),
            "inspect_balance_command": cls.inspect_balance_help(),
            "inspect_stake_add_command": cls.inspect_stake_add_help(netuid),
            "inspect_validator_requirements_command": cls.inspect_validator_requirements_help(netuid),
            "inspect_owner_param_list_command": cls.inspect_owner_param_list_help(netuid),
            "inspect_set_param_command": cls.inspect_set_param_help(netuid),
            "inspect_admin_list_command": cls.inspect_admin_list_help(),
            "inspect_admin_raw_command": cls.inspect_admin_raw_help(),
            "explain_weights_command": cls.explain_weights_help(),
            "explain_commit_reveal_command": cls.explain_commit_reveal_help(),
            "inspect_registration_cost_command": cls.inspect_registration_cost_help(netuid),
            "inspect_register_neuron_command": cls.inspect_register_neuron_help(netuid),
            "inspect_pow_register_command": cls.inspect_pow_register_help(netuid),
            "inspect_snipe_register_command": cls.inspect_snipe_register_help(netuid),
            "inspect_health_command": cls.inspect_health_help(netuid),
            "inspect_serve_axon_command": cls.inspect_serve_axon_help(netuid),
            "inspect_serve_axon_tls_command": cls.inspect_serve_axon_tls_help(netuid),
            "inspect_serve_prometheus_command": cls.inspect_serve_prometheus_help(netuid),
            "inspect_serve_reset_command": cls.inspect_serve_reset_help(netuid),
            "inspect_probe_command": cls.inspect_probe_help(netuid),
            "inspect_axon_command": cls.inspect_axon_help(netuid),
            "inspect_miner_endpoints_command": cls.inspect_miner_endpoints_help(netuid),
            "inspect_validator_endpoints_command": cls.inspect_validator_endpoints_help(netuid),
            "inspect_watch_command": cls.inspect_watch_help(netuid),
            "inspect_monitor_command": cls.inspect_monitor_help(netuid),
            "adjacent_workflows_note": cls._adjacent_workflows_note(),
        }

    @classmethod
    def _adjacent_recovery_fields(cls, netuid: int) -> dict[str, str]:
        """Attach adjacent discovery commands for weights recovery pivots."""
        return {
            **cls._adjacent_workflows_fields(netuid),
            "adjacent_recovery_note": cls._adjacent_recovery_note(),
        }

    @staticmethod
    def _metagraph_weights_examples() -> dict[str, str]:
        """Return copy-paste-ready examples for rebuilding payloads from metagraph UIDs."""
        return {
            "csv": "<uid>:100,<uid>:200",
            "json_object": '{"<uid>": 100, "<uid>": 200}',
            "json_array": '[{"uid": <uid>, "weight": 100}, {"uid": <uid>, "weight": 200}]',
        }

    @classmethod
    def _uid_payload_recovery_fields(cls, netuid: int) -> dict[str, Any]:
        """Attach inspection commands for invalid-UID or duplicate-UID failures."""
        return {
            "inspect_metagraph_command": cls.inspect_metagraph_help(netuid),
            "uid_payload_recovery_note": (
                "Run inspect_metagraph_command to fetch the latest subnet UIDs, then rebuild the weights payload from "
                "the metagraph uid column so each destination UID appears once and still exists on-chain."
            ),
            "uid_payload_examples": cls._metagraph_weights_examples(),
        }

    @classmethod
    def _payload_shape_recovery_fields(cls, netuid: int) -> dict[str, Any]:
        """Attach inspection commands for general payload-shape failures."""
        return {
            "inspect_metagraph_command": cls.inspect_metagraph_help(netuid),
            "inspect_subnet_rules_command": cls.inspect_subnet_rules_help(netuid),
            "payload_shape_recovery_note": (
                "Run inspect_metagraph_command to confirm the latest destination UIDs and "
                "inspect_subnet_rules_command to confirm subnet weight limits, then rebuild the payload from the "
                "metagraph uid column so the UID and value vectors match the subnet requirements before retrying."
            ),
            "uid_payload_examples": cls._metagraph_weights_examples(),
        }

    @staticmethod
    def _is_rate_limit_error(error: str) -> bool:
        """Return whether an error indicates subnet or network rate limiting for weights flows."""
        return any(
            needle in error
            for needle in (
                "CommittingWeightsTooFast",
                "SettingWeightsTooFast",
                "TxRateLimitExceeded",
                "NetworkTxRateLimitExceeded",
            )
        )

    @classmethod
    def _rate_limit_recovery_fields(cls, netuid: int) -> dict[str, str]:
        """Attach inspection commands for weight update rate-limit failures."""
        return {
            "inspect_status_command": cls.status_help(netuid),
            "inspect_subnet_rules_command": cls.inspect_subnet_rules_help(netuid),
            "rate_limit_recovery_note": (
                "Run inspect_status_command to confirm whether a commit is already pending, then use "
                "inspect_subnet_rules_command to inspect this subnet's weight update limits before retrying after "
                "the rate-limit window passes."
            ),
        }

    @classmethod
    def _subnet_missing_recovery_fields(cls) -> dict[str, str]:
        """Attach inspection commands for missing or inactive subnet failures."""
        return {
            "inspect_subnets_command": cls.inspect_subnets_help(),
            "subnet_missing_recovery_note": (
                "Run inspect_subnets_command to confirm the target netuid exists and is active before retrying."
            ),
        }

    @classmethod
    def _payload_recovery_fields(cls, netuid: int, error: str) -> dict[str, str]:
        """Attach targeted inspection commands for payload-format failures."""
        if any(needle in error for needle in ("InvalidUid", "UidVecContainInvalidOne", "DuplicateUids")):
            return cls._uid_payload_recovery_fields(netuid)
        if any(
            needle in error
            for needle in (
                "WeightVecNotEqualSize",
                "InputLengthsUnequal",
                "WeightVecLengthIsLow",
                "UidsLengthExceedUidsInSubNet",
            )
        ):
            return cls._payload_shape_recovery_fields(netuid)
        return {}

    @classmethod
    def _troubleshoot_recovery_fields(cls, netuid: int, error: str) -> dict[str, str]:
        """Attach the highest-signal recovery commands for a troubleshooting error."""
        fields = cls._direct_set_recovery_fields(netuid, error)
        if fields:
            return fields
        if cls._is_version_key_mismatch_error(error):
            return cls._version_key_recovery_fields(netuid)
        if cls._is_commit_state_error(error):
            return cls._commit_state_recovery_fields(netuid)
        if cls._is_rate_limit_error(error):
            return cls._rate_limit_recovery_fields(netuid)
        if any(needle in error for needle in ("SubnetworkDoesNotExist", "SubnetNotExists", "Subnet 0 not found")):
            return cls._subnet_missing_recovery_fields()
        return cls._payload_recovery_fields(netuid, error)

    @classmethod
    def _saved_state_recovery_fields(cls, netuid: int, error: str) -> dict[str, str]:
        """Attach the highest-signal saved-state recovery commands for a troubleshooting error."""
        if cls._is_version_key_mismatch_error(error):
            return cls._version_key_recovery_fields(netuid, saved_state=True)
        if cls._is_commit_state_error(error):
            return cls._commit_state_recovery_fields(netuid, saved_state=True)
        return {}

    @classmethod
    def _status_aware_recovery_fields(cls, error: str, status_summary: Mapping[str, Any]) -> dict[str, Any]:
        """Attach reconciliation notes when status context changes the safest operator move."""
        next_action = status_summary.get("next_action")
        if not isinstance(next_action, str):
            return {}

        commit_reveal_enabled = status_summary.get("commit_reveal_enabled")
        if not isinstance(commit_reveal_enabled, bool):
            return {}

        result: dict[str, Any] = {}

        if cls._is_commit_reveal_required_error(error) and not commit_reveal_enabled:
            result["status_error_conflict_detected"] = True
            result["status_error_reconciliation_note"] = (
                "The error says this subnet required commit-reveal, but the provided status snapshot says direct "
                "weight setting is available. Refresh inspect_status_command and inspect_subnet_rules_command before "
                "retrying because the subnet mode may have changed or the status snapshot may be stale."
            )
        elif cls._is_commit_reveal_disabled_error(error) and commit_reveal_enabled:
            result["status_error_conflict_detected"] = True
            result["status_error_reconciliation_note"] = (
                "The error says commit-reveal was disabled, but the provided status snapshot says commit-reveal is "
                "enabled. Refresh inspect_status_command and inspect_subnet_rules_command before retrying because "
                "the subnet mode may have changed or the status snapshot may be stale."
            )

        if (
            cls._pending_commit_window(status_summary) is not None
            and next_action in {"WAIT", "REVEAL"}
            and (
                cls._is_rate_limit_error(error)
                or cls._is_commit_reveal_required_error(error)
                or cls._is_commit_reveal_disabled_error(error)
            )
        ):
            result["already_pending_recovery_note"] = (
                "Status already shows a pending commit on-chain, so resubmitting now is unlikely to help. Follow "
                "recommended_action/recommended_command instead of submitting another direct set or commit until "
                "that pending commit is revealed or expires."
            )

        return result

    @staticmethod
    def _weights_input_recovery_fields(validation_error: str) -> dict[str, Any]:
        """Attach local input guidance when weights fail to normalize before any chain call."""
        return {
            "weights_input_error": validation_error,
            "weights_input_recovery_note": (
                "Use weights as uid:value CSV, a JSON object/array, stdin '-', or an @file input before retrying."
            ),
            "weights_examples": {
                "csv": "0:100,1:200",
                "json_object": '{"0": 100, "1": 200}',
                "json_array": '[{"uid": 0, "weight": 100}, {"uid": 1, "weight": 200}]',
                "file": "@weights.json",
            },
        }

    @classmethod
    def commit_reveal_runbook_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
        *,
        salt: CommitSaltInput | None = None,
        state_path: str | Path | None = None,
        wait: bool = False,
    ) -> CommitRevealState:
        """Return a recoverable commit-reveal runbook with generated or provided salt."""
        return cls.create_commit_reveal_state_help(
            netuid,
            weights,
            version_key,
            salt=salt,
            state_path=state_path,
            wait=wait,
        )

    @classmethod
    def _saved_state_status_fields(
        cls,
        record: Mapping[str, Any],
        status: object,
        *,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Attach on-chain status context to a saved commit-reveal recovery record."""
        summary = cls._extract_status_summary(status)
        result: dict[str, Any] = {"status_summary": summary}
        result = cls._attach_pending_commit_context(result, summary)
        result = cls._attach_raw_status(result, status)

        pending_commit = result.get("pending_commit")
        saved_hash = record.get("hash")
        pending_hash = pending_commit.get("hash") if isinstance(pending_commit, Mapping) else None
        saved_hash_matches_pending_commit = False
        if isinstance(saved_hash, str) and isinstance(pending_hash, str):
            saved_hash_matches_pending_commit = saved_hash == pending_hash
            result["saved_hash_matches_pending_commit"] = saved_hash_matches_pending_commit

        commit_windows = summary.get("commit_windows")
        matching_pending_commits: list[dict[str, Any]] = []
        if isinstance(saved_hash, str) and isinstance(commit_windows, list):
            for entry in commit_windows:
                if not isinstance(entry, Mapping):
                    continue
                entry_hash = entry.get("hash")
                if isinstance(entry_hash, str) and entry_hash == saved_hash:
                    matching_pending_commits.append(dict(entry))

        promoted_matching_pending_commit = False
        if matching_pending_commits:
            result["matching_pending_commits"] = matching_pending_commits
            result["matching_pending_commit_count"] = len(matching_pending_commits)
            matching_indexes = [
                entry_index
                for entry in matching_pending_commits
                if isinstance((entry_index := entry.get("index")), int)
            ]
            if matching_indexes:
                result["matching_pending_commit_indexes"] = matching_indexes
            if not saved_hash_matches_pending_commit:
                chosen_pending_commit = matching_pending_commits[0]
                result = cls._apply_pending_commit_context(result, chosen_pending_commit)
                pending_commit = chosen_pending_commit
                pending_hash = pending_commit.get("hash") if isinstance(pending_commit, Mapping) else None
                saved_hash_matches_pending_commit = True
                promoted_matching_pending_commit = True
                result["saved_hash_matches_pending_commit"] = True

        pending_commits = summary.get("pending_commits")
        next_action = summary.get("next_action")
        pending_action = cls._pending_commit_action(pending_commit) if isinstance(pending_commit, Mapping) else None
        effective_next_action = pending_action or next_action
        if isinstance(pending_commits, int) and pending_commits == 0:
            result["on_chain_state_note"] = "No pending commit is currently visible on-chain for this saved state."
        elif len(matching_pending_commits) > 1:
            result["matching_pending_commit_note"] = (
                "Multiple on-chain pending commits share the saved hash. "
                "The top-level pending_commit context now shows the first "
                "matching entry so you can inspect its reveal window before "
                "retrying the saved reveal_command. Use matching_pending_commit_count "
                "and matching_pending_commit_indexes to review every matching entry in "
                "matching_pending_commits."
            )
        elif promoted_matching_pending_commit:
            result["matching_pending_commit_note"] = (
                "Several pending commits exist on-chain; the top-level pending_commit context now points to the one "
                "whose hash matches the saved reveal state instead of a different commit that happened to drive the "
                "global next_action summary."
            )

        if saved_hash_matches_pending_commit and effective_next_action == "REVEAL":
            result["on_chain_match_note"] = (
                "The saved commit hash matches the current pending commit on-chain. Reuse the saved reveal_command "
                "instead of creating a fresh commit."
            )
            if error is None:
                result["next_step"] = (
                    "Use the saved reveal_command now; the saved commit still matches the current on-chain pending "
                    "commit."
                )
        elif saved_hash_matches_pending_commit and effective_next_action == "WAIT":
            result["on_chain_match_note"] = (
                "The saved commit hash matches the current pending commit on-chain. No recommit is needed yet; wait "
                "for the reveal window, then reuse the saved reveal_command."
            )
            if error is None:
                result["next_step"] = (
                    "Wait for the reveal window, then use the saved reveal_command instead of creating a fresh commit."
                )

        if error is None:
            return result

        missing_commit_error = any(needle in error for needle in ("NoWeightsCommitFound", "Custom error: 50"))
        hash_mismatch_error = any(needle in error for needle in ("InvalidRevealCommitHashNotMatch", "Custom error: 51"))
        expired_commit_error = any(
            needle in error for needle in ("RevealTooLate", "ExpiredWeightCommit", "Custom error: 77")
        )

        if expired_commit_error or (
            (missing_commit_error or hash_mismatch_error) and not saved_hash_matches_pending_commit
        ):
            result["stale_state_detected"] = True

        if missing_commit_error:
            if saved_hash_matches_pending_commit:
                result["next_step"] = (
                    "The saved hash already matches the live pending commit. Refresh weights status if needed, then "
                    "follow the saved reveal_command when the reveal window opens."
                )
            elif (
                isinstance(saved_hash, str) and isinstance(pending_hash, str) and not saved_hash_matches_pending_commit
            ):
                result["on_chain_drift_note"] = (
                    "The saved commit hash differs from the current pending commit on-chain. Compare the saved state "
                    "record with pending_commit before retrying, or create a fresh commit if they should match."
                )
                result["next_step"] = (
                    "Compare the saved hash with pending_commit.hash before retrying the saved reveal_command, or "
                    "create a fresh commit if the on-chain pending commit belongs to different weights."
                )
            elif pending_commits == 0:
                result["on_chain_drift_note"] = (
                    "No pending commit is visible on-chain for this saved state. The original commit may have "
                    "expired, been revealed already, or been replaced."
                )
                result["next_step"] = (
                    "Refresh weights status to confirm the commit is gone, then create a fresh commit and save its "
                    "new reveal state before retrying."
                )
            else:
                result["on_chain_drift_note"] = (
                    "A pending commit still exists on-chain, but the saved state did not match it. Compare the saved "
                    "hash, weights, salt, and version_key against pending_commit before retrying."
                )
                result["next_step"] = (
                    "Compare the saved weights, salt, version_key, and hash with pending_commit before retrying the "
                    "saved reveal_command."
                )
        elif hash_mismatch_error:
            if saved_hash_matches_pending_commit:
                if effective_next_action == "WAIT":
                    result["next_step"] = (
                        "The saved hash already matches the live pending commit. Wait for the reveal window, then "
                        "retry the saved reveal_command instead of creating a fresh commit."
                    )
                else:
                    result["next_step"] = (
                        "The saved hash already matches the live pending commit. Retry the exact saved reveal_command "
                        "instead of creating a fresh commit."
                    )
            elif (
                isinstance(saved_hash, str) and isinstance(pending_hash, str) and not saved_hash_matches_pending_commit
            ):
                result["on_chain_drift_note"] = (
                    "The saved reveal inputs drifted from the current on-chain pending commit. Compare the saved hash "
                    "with pending_commit.hash before retrying the saved reveal_command."
                )
                result["next_step"] = (
                    "Compare the saved hash with pending_commit.hash before retrying the saved reveal_command. If the "
                    "pending hash belongs to a different commit, create a fresh commit and save its reveal state."
                )
            elif pending_commits == 0:
                result["on_chain_drift_note"] = (
                    "No pending commit is visible on-chain, so the saved reveal inputs likely belong to an expired, "
                    "already-revealed, or replaced commit."
                )
                result["next_step"] = (
                    "Refresh weights status to confirm there is still no pending commit, then create a fresh commit "
                    "and save its reveal state before retrying."
                )
            else:
                result["on_chain_drift_note"] = (
                    "A pending commit still exists on-chain, so compare the saved weights, salt, and version_key with "
                    "pending_commit before retrying the saved reveal_command."
                )
                result["next_step"] = (
                    "Compare the saved weights, salt, version_key, and hash with pending_commit before retrying the "
                    "saved reveal_command."
                )
        elif expired_commit_error:
            result["on_chain_drift_note"] = (
                "The saved commit is no longer revealable on-chain. Create a fresh commit and save its new reveal "
                "state before waiting for the next reveal window."
            )
            result["next_step"] = (
                "Create a fresh commit, save its new reveal state, and wait for the next reveal window before retrying."
            )

        return result

    @classmethod
    def troubleshoot_unrevealed_commit_help(
        cls,
        path: str | Path,
        error: str | None = None,
        *,
        version_key: int | None = None,
        status: object | None = None,
    ) -> dict[str, Any]:
        """Load saved commit state and return recovery guidance for stuck unrevealed commits."""
        record = cls.recover_reveal_from_state_help(path, version_key=version_key)
        result: dict[str, Any] = {
            **record,
            "recovery_reason": (
                "A previous commit can still be revealed if its original weights and salt are preserved."
            ),
        }
        error_text: str | None = None
        if error is not None:
            error_text = cls._error_arg(error)
            likely_cause, next_step = cls._troubleshooting_guidance(error_text)
            saved_state_next_step = cls._saved_state_next_step(
                error_text,
                version_key_overridden=bool(result.get("version_key_override_applied", False)),
            )
            result.update(
                {
                    "error": error_text,
                    "likely_cause": likely_cause,
                    "next_step": saved_state_next_step or next_step,
                }
            )
            result.update(cls._saved_state_recovery_fields(record["netuid"], error_text))
        elif status is not None:
            result.update(cls._commit_state_recovery_fields(record["netuid"], saved_state=True))
        if status is not None:
            result.update(cls._saved_state_status_fields(record, status, error=error_text))
        return result

    @classmethod
    def operator_note_for_atomic_commit_reveal_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
        *,
        salt: CommitSaltInput | None = None,
        state_path: str | Path | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        """Return operator-facing guidance that atomic commit-reveal should preserve reveal state."""
        record = cls.commit_reveal_runbook_help(
            netuid,
            weights,
            version_key,
            salt=salt,
            state_path=state_path,
            wait=wait,
        )
        return {
            **record,
            "operator_note": (
                "If atomic commit-reveal stalls after commit, keep this state record so the same commit can be "
                "revealed manually later."
            ),
        }

    @staticmethod
    def _status_int(field_name: str, value: object) -> int:
        """Normalize a required integer field from status payloads."""
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"status {field_name} must be an integer")
        return value

    @classmethod
    def _commit_status_from_text(
        cls,
        index: int,
        status_text: str,
        hash_value: str | None = None,
    ) -> dict[str, Any]:
        """Parse a human-readable `weights status` block into a normalized commit entry."""
        normalized_status = status_text.strip() or "UNKNOWN"
        entry: dict[str, Any] = {"index": index, "status": normalized_status}
        if hash_value is not None:
            entry["hash"] = hash_value

        commit_match = re.search(r"Commit:\s*block\s+(\d+)", status_text)
        if commit_match is not None:
            entry["commit_block"] = int(commit_match.group(1))

        reveal_match = re.search(r"Reveal:\s*blocks\s+(\d+)\.\.(\d+)", status_text)
        if reveal_match is not None:
            entry["first_reveal"] = int(reveal_match.group(1))
            entry["last_reveal"] = int(reveal_match.group(2))

        blocks_match = re.search(r"\((\d+)\s+blocks?\s+(?:until reveal window|remaining)\)", normalized_status)
        if blocks_match is not None:
            entry["blocks_until_action"] = int(blocks_match.group(1))

        return entry

    @classmethod
    def _status_mapping_from_text(cls, status_text: str) -> dict[str, Any]:
        """Parse raw text from `agcli weights status` into a normalized status mapping."""
        current_block_match = re.search(r"Current block:\s*(\d+)", status_text)
        if current_block_match is None:
            raise ValueError("weights status output must be a mapping or recognizable status text")

        commit_reveal_match = re.search(r"Commit-reveal:\s*(ENABLED|disabled)", status_text)
        if commit_reveal_match is None:
            raise ValueError("weights status output must be a mapping or recognizable status text")

        reveal_period_match = re.search(r"Reveal period:\s*(\d+)\s+epochs", status_text)
        if reveal_period_match is None:
            raise ValueError("weights status output must be a mapping or recognizable status text")

        commits: list[dict[str, Any]] = []
        if "No pending commits." not in status_text:
            commit_pattern = re.compile(
                r"\[(\d+)\]\s+Hash:\s+(0x[0-9a-fA-F]+)\s+"
                r"Commit:\s*block\s+(\d+)\s+"
                r"Reveal:\s*blocks\s+(\d+)\.\.(\d+)\s+"
                r"Status:\s*(.*?)(?=\n\s*\[\d+\]\s+Hash:|\Z)",
                re.DOTALL,
            )
            for match in commit_pattern.finditer(status_text):
                commits.append(
                    cls._commit_status_from_text(
                        int(match.group(1)),
                        match.group(6),
                        hash_value=match.group(2),
                    )
                    | {
                        "commit_block": int(match.group(3)),
                        "first_reveal": int(match.group(4)),
                        "last_reveal": int(match.group(5)),
                    }
                )

        return {
            "block": int(current_block_match.group(1)),
            "commit_reveal_enabled": commit_reveal_match.group(1) == "ENABLED",
            "reveal_period_epochs": int(reveal_period_match.group(1)),
            "commits": commits,
        }

    @classmethod
    def _status_mapping(cls, status: object) -> Mapping[str, Any]:
        """Accept either structured JSON or human-readable status text."""
        if isinstance(status, Mapping):
            return status
        if isinstance(status, str):
            return cls._status_mapping_from_text(status)
        raise ValueError("status must be a mapping")

    @staticmethod
    def _status_raw_text(status: object) -> str | None:
        """Return stripped raw status text when the original status input was textual."""
        if not isinstance(status, str):
            return None
        return status.strip()

    @classmethod
    def _attach_raw_status(cls, result: dict[str, Any], status: object) -> dict[str, Any]:
        """Attach stripped raw status text to helper output when available."""
        raw_status = cls._status_raw_text(status)
        if raw_status is not None:
            result["raw_status"] = raw_status
        return result

    @classmethod
    def _extract_status_summary(cls, status: object) -> dict[str, Any]:
        """Normalize key commit-reveal status fields for helper output."""
        status_mapping = cls._status_mapping(status)

        block = cls._status_int("block", status_mapping.get("block"))

        commit_reveal_enabled = status_mapping.get("commit_reveal_enabled")
        if not isinstance(commit_reveal_enabled, bool):
            raise ValueError("status commit_reveal_enabled must be a boolean")

        reveal_period_epochs = cls._status_int("reveal_period_epochs", status_mapping.get("reveal_period_epochs"))

        raw_commits = status_mapping.get("commits")
        if raw_commits is None:
            raw_commits = status_mapping.get("pending_commits")

        commit_entries: list[dict[str, Any]] = []
        if raw_commits is None:
            pass
        elif isinstance(raw_commits, list):
            for index, entry in enumerate(raw_commits, start=1):
                if not isinstance(entry, Mapping):
                    raise ValueError(f"status commits[{index}] must be a mapping")
                status_value = entry.get("status")
                if not isinstance(status_value, str):
                    raise ValueError(f"status commits[{index}].status must be a string")
                normalized_entry: dict[str, Any] = {
                    "index": index,
                    "status": status_value.strip() or "UNKNOWN",
                }
                for field in ("commit_block", "first_reveal", "last_reveal", "blocks_until_action"):
                    value = entry.get(field)
                    if value is None:
                        continue
                    if isinstance(value, bool) or not isinstance(value, int):
                        raise ValueError(f"status commits[{index}].{field} must be an integer when present")
                    normalized_entry[field] = value
                hash_value = entry.get("hash")
                if hash_value is not None:
                    if not isinstance(hash_value, str):
                        raise ValueError(f"status commits[{index}].hash must be a string when present")
                    normalized_entry["hash"] = hash_value
                commit_entries.append(normalized_entry)
        elif isinstance(raw_commits, int) and not isinstance(raw_commits, bool):
            commit_entries = [{"index": idx + 1, "status": "UNKNOWN"} for idx in range(raw_commits)]
        else:
            raise ValueError("status commits must be a list when present")

        pending_statuses = [entry["status"] for entry in commit_entries]
        if any(status_value.startswith("READY TO REVEAL") for status_value in pending_statuses):
            next_action = "REVEAL"
        elif any(status_value.startswith("EXPIRED") for status_value in pending_statuses):
            next_action = "RECOMMIT"
        elif commit_entries:
            next_action = "WAIT"
        else:
            next_action = "NO_PENDING_COMMITS"

        return {
            "current_block": block,
            "commit_reveal_enabled": commit_reveal_enabled,
            "reveal_period_epochs": reveal_period_epochs,
            "pending_commits": len(commit_entries),
            "pending_statuses": pending_statuses,
            "next_action": next_action,
            "commit_windows": [
                {
                    key: entry[key]
                    for key in (
                        "index",
                        "status",
                        "commit_block",
                        "first_reveal",
                        "last_reveal",
                        "blocks_until_action",
                        "hash",
                    )
                    if key in entry
                }
                for entry in commit_entries
            ],
        }

    @staticmethod
    def _pending_commit_action(commit_window: Mapping[str, Any]) -> str | None:
        """Infer the operator action for a specific pending commit window."""
        status_value = commit_window.get("status")
        if not isinstance(status_value, str):
            return None
        if status_value.startswith("READY TO REVEAL"):
            return "REVEAL"
        if status_value.startswith("EXPIRED"):
            return "RECOMMIT"
        if status_value:
            return "WAIT"
        return None

    @staticmethod
    def _apply_pending_commit_context(result: dict[str, Any], pending_commit: Mapping[str, Any]) -> dict[str, Any]:
        """Attach one chosen pending commit window as top-level operator context."""
        result.pop("pending_commit", None)
        result.pop("blocks_until_action", None)
        result.pop("reveal_window", None)

        normalized_pending_commit = dict(pending_commit)
        result["pending_commit"] = normalized_pending_commit

        blocks_until_action = normalized_pending_commit.get("blocks_until_action")
        if isinstance(blocks_until_action, int):
            result["blocks_until_action"] = blocks_until_action
        first_reveal = normalized_pending_commit.get("first_reveal")
        last_reveal = normalized_pending_commit.get("last_reveal")
        if isinstance(first_reveal, int) and isinstance(last_reveal, int):
            result["reveal_window"] = {
                "first_block": first_reveal,
                "last_block": last_reveal,
            }
        return result

    @classmethod
    def _pending_commit_window(
        cls,
        status_summary: Mapping[str, Any],
    ) -> dict[str, Any] | None:
        """Return the most relevant pending commit window for the current next action."""
        next_action = status_summary.get("next_action")
        if not isinstance(next_action, str):
            raise ValueError("status summary next_action must be a string")

        commit_windows = status_summary.get("commit_windows")
        if not isinstance(commit_windows, list):
            return None

        prefixes = {
            "REVEAL": "READY TO REVEAL",
            "RECOMMIT": "EXPIRED",
            "WAIT": "WAITING",
        }
        prefix = prefixes.get(next_action)
        for entry in commit_windows:
            if not isinstance(entry, Mapping):
                continue
            status_value = entry.get("status")
            if prefix is not None and isinstance(status_value, str) and status_value.startswith(prefix):
                return dict(entry)

        if len(commit_windows) == 1 and isinstance(commit_windows[0], Mapping):
            return dict(commit_windows[0])
        return None

    @classmethod
    def _attach_pending_commit_context(
        cls,
        result: dict[str, Any],
        status_summary: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Attach the most relevant pending commit window as top-level operator context."""
        pending_commit = cls._pending_commit_window(status_summary)
        if pending_commit is None:
            return result

        return cls._apply_pending_commit_context(result, pending_commit)

    @classmethod
    def _next_action_guidance(
        cls,
        netuid: int,
        status_summary: Mapping[str, Any],
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        """Turn a normalized status summary into the next recommended operator action."""
        next_action = status_summary.get("next_action")
        if not isinstance(next_action, str):
            raise ValueError("status summary next_action must be a string")

        commit_reveal_enabled = status_summary.get("commit_reveal_enabled")
        if not isinstance(commit_reveal_enabled, bool):
            raise ValueError("status summary commit_reveal_enabled must be a boolean")

        result: dict[str, Any] = cls._attach_pending_commit_context(
            {
                "recommended_action": next_action,
                "recommended_command": cls.status_help(netuid),
            },
            status_summary,
        )

        blocks_until_action = result.get("blocks_until_action")

        normalized_weights: str | None = None
        if weights is not None:
            normalized_weights = cls._weights_arg(weights)
            result["normalized_weights"] = normalized_weights

        normalized_salt: str | None = None
        if salt is not None:
            normalized_salt = cls._salt_arg(salt)

        if next_action == "REVEAL":
            if normalized_weights is not None and normalized_salt is not None:
                result["recommended_command"] = cls.reveal_help(
                    netuid,
                    normalized_weights,
                    normalized_salt,
                    version_key=version_key,
                )
                result["reason"] = "A pending commit is ready to reveal now."
            else:
                result["reason"] = (
                    "A pending commit is ready to reveal now; provide the original weights and salt "
                    "to build the reveal command."
                )
            if isinstance(blocks_until_action, int):
                result["timing_note"] = (
                    f"Reveal is ready now; current status reports {blocks_until_action} blocks remaining."
                )
            return result

        if next_action == "RECOMMIT":
            result["reason"] = "A previous pending commit expired, so fresh weights are required."
            if normalized_weights is None:
                return result
            if commit_reveal_enabled and wait:
                result["recommended_command"] = cls.commit_reveal_help(
                    netuid,
                    normalized_weights,
                    version_key=version_key,
                    wait=True,
                )
            elif commit_reveal_enabled and normalized_salt is not None:
                result["recommended_command"] = cls.commit_help(netuid, normalized_weights, salt=normalized_salt)
            elif commit_reveal_enabled:
                result["recommended_command"] = cls.commit_reveal_help(
                    netuid,
                    normalized_weights,
                    version_key=version_key,
                )
            else:
                result["recommended_command"] = cls.set_help(netuid, normalized_weights, version_key=version_key)
            return result

        if next_action == "NO_PENDING_COMMITS":
            if commit_reveal_enabled:
                result["reason"] = "No commit is pending and this subnet uses commit-reveal."
                if normalized_weights is None:
                    return result
                if wait or normalized_salt is None:
                    result["recommended_command"] = cls.commit_reveal_help(
                        netuid,
                        normalized_weights,
                        version_key=version_key,
                        wait=wait,
                    )
                else:
                    result["recommended_command"] = cls.commit_help(netuid, normalized_weights, salt=normalized_salt)
            else:
                result["reason"] = "No commit is pending and direct weight setting is available."
                if normalized_weights is not None:
                    result["recommended_command"] = cls.set_help(netuid, normalized_weights, version_key=version_key)
            return result

        result["reason"] = "A pending commit exists but the reveal window is not open yet."
        if isinstance(blocks_until_action, int):
            result["timing_note"] = f"Wait about {blocks_until_action} more blocks, then check status again."
        return result

    @classmethod
    def _mechanism_next_action_guidance(
        cls,
        netuid: int,
        mechanism_id: int,
        status_summary: Mapping[str, Any],
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Turn a normalized status summary into the next recommended mechanism action."""
        next_action = status_summary.get("next_action")
        if not isinstance(next_action, str):
            raise ValueError("status summary next_action must be a string")

        commit_reveal_enabled = status_summary.get("commit_reveal_enabled")
        if not isinstance(commit_reveal_enabled, bool):
            raise ValueError("status summary commit_reveal_enabled must be a boolean")

        result: dict[str, Any] = cls._attach_pending_commit_context(
            {
                "recommended_action": next_action,
                "recommended_command": cls.status_help(netuid),
            },
            status_summary,
        )

        blocks_until_action = result.get("blocks_until_action")

        normalized_weights: str | None = None
        if weights is not None:
            normalized_weights = cls._weights_arg(weights)
            result["normalized_weights"] = normalized_weights

        normalized_salt: str | None = None
        if salt is not None:
            normalized_salt = cls._salt_arg(salt)

        normalized_hash: str | None = None
        if hash_value is not None:
            normalized_hash = cls._hash_arg(hash_value)
        elif normalized_weights is not None and normalized_salt is not None:
            normalized_hash = cls._compute_commit_hash(normalized_weights, normalized_salt)
        if normalized_hash is not None:
            result["normalized_hash"] = normalized_hash

        if next_action == "REVEAL":
            if normalized_weights is not None and normalized_salt is not None:
                result["recommended_command"] = cls.reveal_mechanism_help(
                    netuid,
                    mechanism_id,
                    normalized_weights,
                    normalized_salt,
                    version_key=version_key,
                )
                result["reason"] = "A pending mechanism commit is ready to reveal now."
            else:
                result["reason"] = (
                    "A pending mechanism commit is ready to reveal now; provide the original weights and salt "
                    "to build the reveal command."
                )
            if isinstance(blocks_until_action, int):
                result["timing_note"] = (
                    f"Reveal is ready now; current status reports {blocks_until_action} blocks remaining."
                )
            return result

        if next_action == "RECOMMIT":
            if commit_reveal_enabled:
                if normalized_hash is not None:
                    result["recommended_command"] = cls.commit_mechanism_help(netuid, mechanism_id, normalized_hash)
                    result["reason"] = (
                        "A previous pending mechanism commit expired, so a fresh mechanism commit is required."
                    )
                else:
                    result["reason"] = (
                        "A previous pending mechanism commit expired, so a fresh precomputed mechanism hash is "
                        "required before retrying."
                    )
            else:
                result["reason"] = (
                    "The previous mechanism commit expired and direct mechanism weight setting is available."
                )
                if normalized_weights is not None:
                    result["recommended_command"] = cls.set_mechanism_help(
                        netuid,
                        mechanism_id,
                        normalized_weights,
                        version_key=version_key,
                    )
            return result

        if next_action == "NO_PENDING_COMMITS":
            if commit_reveal_enabled:
                if normalized_hash is not None:
                    result["recommended_command"] = cls.commit_mechanism_help(netuid, mechanism_id, normalized_hash)
                    result["reason"] = "No mechanism commit is pending and this subnet uses commit-reveal."
                else:
                    result["reason"] = (
                        "No mechanism commit is pending and this subnet uses commit-reveal; provide the precomputed "
                        "mechanism hash to build the commit command."
                    )
            else:
                result["reason"] = "No mechanism commit is pending and direct mechanism weight setting is available."
                if normalized_weights is not None:
                    result["recommended_command"] = cls.set_mechanism_help(
                        netuid,
                        mechanism_id,
                        normalized_weights,
                        version_key=version_key,
                    )
            return result

        result["reason"] = "A pending mechanism commit exists but the reveal window is not open yet."
        if isinstance(blocks_until_action, int):
            result["timing_note"] = f"Wait about {blocks_until_action} more blocks, then check status again."
        return result

    @classmethod
    def _timelocked_next_action_guidance(
        cls,
        netuid: int,
        status_summary: Mapping[str, Any],
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Turn a normalized status summary into the next recommended timelocked action."""
        next_action = status_summary.get("next_action")
        if not isinstance(next_action, str):
            raise ValueError("status summary next_action must be a string")

        commit_reveal_enabled = status_summary.get("commit_reveal_enabled")
        if not isinstance(commit_reveal_enabled, bool):
            raise ValueError("status summary commit_reveal_enabled must be a boolean")

        result: dict[str, Any] = cls._attach_pending_commit_context(
            {
                "recommended_action": next_action,
                "recommended_command": cls.status_help(netuid),
            },
            status_summary,
        )

        blocks_until_action = result.get("blocks_until_action")

        normalized_weights: str | None = None
        if weights is not None:
            normalized_weights = cls._weights_arg(weights)
            result["normalized_weights"] = normalized_weights

        normalized_round: int | None = None
        if round is not None:
            normalized_round = int(cls._round_arg(round))
            result["round"] = normalized_round

        normalized_salt: str | None = None
        if salt is not None:
            normalized_salt = cls._salt_arg(salt)

        if next_action == "REVEAL":
            if normalized_weights is not None and normalized_salt is not None:
                result["recommended_command"] = cls.reveal_help(
                    netuid,
                    normalized_weights,
                    normalized_salt,
                    version_key=version_key,
                )
                result["reason"] = "A pending timelocked commit is ready to reveal now."
            else:
                result["reason"] = (
                    "A pending timelocked commit is ready to reveal now; provide the original weights and salt "
                    "to build the reveal command."
                )
            if isinstance(blocks_until_action, int):
                result["timing_note"] = (
                    f"Reveal is ready now; current status reports {blocks_until_action} blocks remaining."
                )
            return result

        if next_action == "RECOMMIT":
            if commit_reveal_enabled:
                if normalized_weights is not None and normalized_round is not None:
                    result["recommended_command"] = cls.commit_timelocked_help(
                        netuid,
                        normalized_weights,
                        normalized_round,
                        salt=normalized_salt,
                    )
                    result["reason"] = (
                        "A previous pending timelocked commit expired, so a fresh timelocked commit is required."
                    )
                else:
                    result["reason"] = (
                        "A previous pending timelocked commit expired, so fresh weights and a drand round are "
                        "required before retrying."
                    )
            else:
                result["reason"] = "The previous timelocked commit expired and direct weight setting is available."
                if normalized_weights is not None:
                    result["recommended_command"] = cls.set_help(netuid, normalized_weights, version_key=version_key)
            return result

        if next_action == "NO_PENDING_COMMITS":
            if commit_reveal_enabled:
                if normalized_weights is not None and normalized_round is not None:
                    result["recommended_command"] = cls.commit_timelocked_help(
                        netuid,
                        normalized_weights,
                        normalized_round,
                        salt=normalized_salt,
                    )
                    result["reason"] = "No timelocked commit is pending and this subnet uses commit-reveal."
                else:
                    result["reason"] = (
                        "No timelocked commit is pending and this subnet uses commit-reveal; provide weights and a "
                        "drand round to build the next commit command."
                    )
            else:
                result["reason"] = "No timelocked commit is pending and direct weight setting is available."
                if normalized_weights is not None:
                    result["recommended_command"] = cls.set_help(netuid, normalized_weights, version_key=version_key)
            return result

        result["reason"] = "A pending timelocked commit exists but the reveal window is not open yet."
        if isinstance(blocks_until_action, int):
            result["timing_note"] = f"Wait about {blocks_until_action} more blocks, then check status again."
        return result

    @classmethod
    def _troubleshooting_guidance(cls, error: str) -> tuple[str, str]:
        """Return likely-cause guidance for common weight-setting failures."""
        normalized = cls._error_arg(error)
        rules = [
            (
                ("RevealTooLate",),
                "The reveal was submitted after the valid reveal window closed.",
                "Create a fresh commit, then reveal again before the commit expires.",
            ),
            (
                ("TooManyUnrevealedCommits", "Custom error: 76"),
                "There are too many pending commits waiting to be revealed for this hotkey.",
                "Reveal or let old commits expire, then retry with a fresh commit.",
            ),
            (
                (
                    "CommittingWeightsTooFast",
                    "SettingWeightsTooFast",
                    "TxRateLimitExceeded",
                    "NetworkTxRateLimitExceeded",
                ),
                "A subnet or network rate limit is blocking this weights update.",
                "Check weights status to see whether a commit is already pending, then wait for the rate-limit "
                "window to pass before retrying the same normalized command.",
            ),
            (
                ("InvalidUid", "UidVecContainInvalidOne", "DuplicateUids"),
                "The weights payload includes invalid or repeated destination UIDs.",
                "Regenerate the weights payload from the latest metagraph and ensure each UID appears once.",
            ),
            (
                ("NeuronNoValidatorPermit", "Custom error: 15"),
                "The hotkey is not currently allowed to set weights on this subnet.",
                "Check validator permit, stake, and subnet validator settings before retrying.",
            ),
            (
                ("SubnetworkDoesNotExist", "SubnetNotExists", "Subnet 0 not found"),
                "The target subnet does not exist or is not currently active.",
                "Verify the netuid first, then retry against an existing subnet.",
            ),
            (
                ("NotEnoughStakeToSetWeights",),
                "The hotkey does not have enough stake to set weights.",
                "Increase stake or use a hotkey that already meets the subnet stake requirement.",
            ),
            (
                ("WeightsNotSettable", "WeightsWindow", "AdminActionProhibitedDuringWeightsWindow"),
                "Direct weight setting is temporarily blocked by the subnet's current window or rules.",
                "Check weights status and subnet hyperparameters, then retry after the protected window or use "
                "the required workflow.",
            ),
            (
                ("CommitRevealDisabled", "Custom error: 53"),
                "This subnet does not accept commit-reveal submissions right now.",
                "Use a direct set command instead of commit/reveal after confirming the subnet status.",
            ),
            (
                ("IncorrectCommitRevealVersion", "Custom error: 111"),
                "The subnet expects a different version_key than the one provided.",
                "Inspect the subnet hyperparameters, then retry with the matching version_key.",
            ),
            (
                ("RevealTooEarly", "NotInRevealPeriod"),
                "The reveal window has not opened yet for the pending commit.",
                "Check weights status and retry when the subnet enters the reveal period.",
            ),
            (
                ("ExpiredWeightCommit", "Custom error: 77"),
                "The previous commit expired before it was revealed.",
                "Commit again, then reveal inside the next valid reveal window.",
            ),
            (
                ("NoWeightsCommitFound", "Custom error: 50"),
                "There is no matching pending commit for this subnet and hotkey.",
                "Create a fresh commit first, then reveal the exact same weights and salt.",
            ),
            (
                ("InvalidRevealCommitHashNotMatch", "Custom error: 51"),
                "The reveal payload does not match the previously committed hash.",
                "Reuse the exact normalized weights, salt, and version_key from the original commit.",
            ),
            (
                ("CommitRevealEnabled",),
                "This subnet expects commit-reveal instead of a direct set call.",
                "Use commit-reveal or a manual commit followed by reveal for this subnet.",
            ),
            (
                ("Custom error: 16",),
                "The runtime returned a generic reveal-side custom error.",
                "Check pending commits, reveal timing, and that weights, salt, and version_key match the commit.",
            ),
        ]
        for needles, likely_cause, next_step in rules:
            if any(needle in normalized for needle in needles):
                return likely_cause, next_step
        return (
            "The runtime returned an unrecognized weights error.",
            "Check weights status, confirm netuid and payload inputs, then retry with the normalized command preview.",
        )

    @staticmethod
    def _netuid_arg(netuid: int) -> str:
        """Normalize a subnet id."""
        if isinstance(netuid, bool) or not isinstance(netuid, int):
            raise ValueError("netuid must be an integer")
        if netuid <= 0:
            raise ValueError("netuid must be greater than 0")
        return str(netuid)

    @staticmethod
    def _uid_arg(uid: int) -> str:
        """Normalize a neuron uid."""
        if isinstance(uid, bool) or not isinstance(uid, int):
            raise ValueError("uid must be an integer")
        if uid < 0:
            raise ValueError("uid must be greater than or equal to 0")
        return str(uid)

    @staticmethod
    def _mechanism_id_arg(mechanism_id: int) -> str:
        """Normalize a mechanism id."""
        if isinstance(mechanism_id, bool) or not isinstance(mechanism_id, int):
            raise ValueError("mechanism_id must be an integer")
        if mechanism_id < 0:
            raise ValueError("mechanism_id must be greater than or equal to 0")
        return str(mechanism_id)

    @staticmethod
    def _version_key_arg(version_key: int | None) -> str | None:
        """Normalize an optional version key."""
        if version_key is None:
            return None
        if isinstance(version_key, bool) or not isinstance(version_key, int):
            raise ValueError("version_key must be an integer")
        if version_key < 0:
            raise ValueError("version_key must be greater than or equal to 0")
        return str(version_key)

    @staticmethod
    def _round_arg(round: int) -> str:
        """Normalize a drand round value."""
        if isinstance(round, bool) or not isinstance(round, int):
            raise ValueError("round must be an integer")
        if round < 0:
            raise ValueError("round must be greater than or equal to 0")
        return str(round)

    @classmethod
    def _set_args(cls, netuid: int, weights: WeightsInput, version_key: int | None = None) -> list[str]:
        args = ["--netuid", cls._netuid_arg(netuid), "--weights", cls._validated_weights_arg(weights)]
        args += cls._opt("--version-key", cls._version_key_arg(version_key))
        return args

    @classmethod
    def _commit_args(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput | None = None,
    ) -> list[str]:
        args = ["--netuid", cls._netuid_arg(netuid), "--weights", cls._validated_weights_arg(weights)]
        if salt is not None:
            args += ["--salt", cls._salt_arg(salt)]
        return args

    @classmethod
    def _reveal_args(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> list[str]:
        args = [
            "--netuid",
            cls._netuid_arg(netuid),
            "--weights",
            cls._weights_arg(weights),
            "--salt",
            cls._salt_arg(salt),
        ]
        args += cls._opt("--version-key", cls._version_key_arg(version_key))
        return args

    @classmethod
    def _commit_reveal_args(
        cls,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
        wait: bool = False,
    ) -> list[str]:
        args = ["--netuid", cls._netuid_arg(netuid), "--weights", cls._validated_weights_arg(weights)]
        args += cls._opt("--version-key", cls._version_key_arg(version_key))
        args += cls._flag("--wait", wait)
        return args

    @classmethod
    def _set_mechanism_args(
        cls,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        version_key: int | None = None,
    ) -> list[str]:
        args = [
            "--netuid",
            cls._netuid_arg(netuid),
            "--mechanism-id",
            cls._mechanism_id_arg(mechanism_id),
            "--weights",
            cls._weights_arg(weights),
        ]
        args += cls._opt("--version-key", cls._version_key_arg(version_key))
        return args

    @classmethod
    def _commit_mechanism_args(cls, netuid: int, mechanism_id: int, hash_value: HashInput) -> list[str]:
        return [
            "--netuid",
            cls._netuid_arg(netuid),
            "--mechanism-id",
            cls._mechanism_id_arg(mechanism_id),
            "--hash",
            cls._hash_arg(hash_value),
        ]

    @classmethod
    def _reveal_mechanism_args(
        cls,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> list[str]:
        args = [
            "--netuid",
            cls._netuid_arg(netuid),
            "--mechanism-id",
            cls._mechanism_id_arg(mechanism_id),
            "--weights",
            cls._weights_arg(weights),
            "--salt",
            cls._salt_arg(salt),
        ]
        args += cls._opt("--version-key", cls._version_key_arg(version_key))
        return args

    @classmethod
    def _commit_timelocked_args(
        cls,
        netuid: int,
        weights: WeightsInput,
        round: int,
        salt: CommitSaltInput | None = None,
    ) -> list[str]:
        args = [
            "--netuid",
            cls._netuid_arg(netuid),
            "--weights",
            cls._weights_arg(weights),
            "--round",
            cls._round_arg(round),
        ]
        if salt is not None:
            args += ["--salt", cls._salt_arg(salt)]
        return args

    @classmethod
    def commit_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput | None = None,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
    ) -> str:
        """Return a copy-paste-ready commit command preview."""
        prefix, _ = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        return " ".join([prefix, "weights", "commit", *cls._commit_args(netuid, weights, salt=salt)])

    @classmethod
    def set_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
    ) -> str:
        """Return a copy-paste-ready set command preview."""
        prefix, _ = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        return " ".join([prefix, "weights", "set", *cls._set_args(netuid, weights, version_key=version_key)])

    @classmethod
    def reveal_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
    ) -> str:
        """Return a copy-paste-ready reveal command preview."""
        prefix, _ = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        return " ".join(
            [prefix, "weights", "reveal", *cls._reveal_args(netuid, weights, salt, version_key=version_key)]
        )

    @classmethod
    def set_mechanism_help(
        cls,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        version_key: int | None = None,
    ) -> str:
        """Return a copy-paste-ready mechanism set command preview."""
        return " ".join(
            [
                "agcli",
                "weights",
                "set-mechanism",
                *cls._set_mechanism_args(netuid, mechanism_id, weights, version_key=version_key),
            ]
        )

    @classmethod
    def commit_mechanism_help(cls, netuid: int, mechanism_id: int, hash_value: HashInput) -> str:
        """Return a copy-paste-ready mechanism commit command preview."""
        return " ".join(
            ["agcli", "weights", "commit-mechanism", *cls._commit_mechanism_args(netuid, mechanism_id, hash_value)]
        )

    @classmethod
    def reveal_mechanism_help(
        cls,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> str:
        """Return a copy-paste-ready mechanism reveal command preview."""
        return " ".join(
            [
                "agcli",
                "weights",
                "reveal-mechanism",
                *cls._reveal_mechanism_args(netuid, mechanism_id, weights, salt, version_key=version_key),
            ]
        )

    @classmethod
    def commit_timelocked_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        round: int,
        salt: CommitSaltInput | None = None,
    ) -> str:
        """Return a copy-paste-ready timelocked commit command preview."""
        return " ".join(
            ["agcli", "weights", "commit-timelocked", *cls._commit_timelocked_args(netuid, weights, round, salt=salt)]
        )

    @classmethod
    def commit_reveal_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
        wait: bool = False,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
    ) -> str:
        """Return a copy-paste-ready commit-reveal command preview."""
        prefix, _ = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        return " ".join(
            [
                prefix,
                "weights",
                "commit-reveal",
                *cls._commit_reveal_args(netuid, weights, version_key=version_key, wait=wait),
            ]
        )

    @classmethod
    def workflow_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
        wait: bool = False,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
    ) -> dict[str, Any]:
        """Return copy-paste-ready helpers for common weights workflows."""
        normalized_weights = cls._weights_arg(weights)
        normalized_salt = cls._salt_arg(salt)
        _, context = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        return {
            "normalized_weights": normalized_weights,
            **context,
            "status": cls.status_help(netuid, wallet=wallet, hotkey=hotkey),
            "show": cls.show_help(netuid),
            "pending_commits": cls.inspect_pending_commits_help(netuid),
            "hyperparams": cls.inspect_version_key_help(netuid),
            "set": cls.set_help(netuid, normalized_weights, version_key=version_key, wallet=wallet, hotkey=hotkey),
            "commit_reveal": cls.commit_reveal_help(
                netuid,
                normalized_weights,
                version_key=version_key,
                wait=wait,
                wallet=wallet,
                hotkey=hotkey,
            ),
            "commit": cls.commit_help(netuid, normalized_weights, salt=normalized_salt, wallet=wallet, hotkey=hotkey),
            "reveal": cls.reveal_help(
                netuid,
                normalized_weights,
                normalized_salt,
                version_key=version_key,
                wallet=wallet,
                hotkey=hotkey,
            ),
            **cls._adjacent_workflows_fields(netuid),
            "status_note": cls._status_note(),
            "show_note": cls._show_note(),
            "pending_commits_note": cls._pending_commits_note(),
            "hyperparams_note": cls._hyperparams_note(),
            "set_weights_note": cls._set_weights_note(),
        }

    @classmethod
    def status_help(cls, netuid: int, *, wallet: str | None = None, hotkey: str | None = None) -> str:
        """Return a copy-paste-ready status command preview."""
        prefix, _ = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        return " ".join([prefix, "weights", "status", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def show_help(cls, netuid: int, hotkey_address: str | None = None, limit: int | None = None) -> str:
        """Return a copy-paste-ready weights show command preview."""
        args = ["agcli", "weights", "show", "--netuid", cls._netuid_arg(netuid)]
        if hotkey_address is not None:
            normalized_hotkey = cls._optional_text("hotkey_address", hotkey_address)
            args += ["--hotkey-address", normalized_hotkey]
        if limit is not None:
            if isinstance(limit, bool) or not isinstance(limit, int):
                raise ValueError("limit must be an integer")
            if limit <= 0:
                raise ValueError("limit must be greater than 0")
            args += ["--limit", str(limit)]
        return " ".join(args)

    @classmethod
    def inspect_pending_commits_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready pending-commits command for reveal recovery."""
        return " ".join(["agcli", "subnet", "commits", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def operator_workflow_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
        wait: bool = False,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
    ) -> dict[str, Any]:
        """Return an operator-facing weights runbook with wallet-aware commands and notes."""
        return cls.workflow_help(
            netuid,
            weights,
            salt,
            version_key=version_key,
            wait=wait,
            wallet=wallet,
            hotkey=hotkey,
        )

    @classmethod
    def serve_prerequisite_help(
        cls,
        netuid: int,
        *,
        wallet: str | None = None,
        hotkey: str | None = None,
    ) -> dict[str, Any]:
        """Return the weight-related checks operators should run before or after serving a validator hotkey."""
        _, context = cls._command_prefix(wallet=wallet, hotkey=hotkey)
        return {
            "netuid": int(cls._netuid_arg(netuid)),
            **context,
            "status": cls.status_help(netuid, wallet=wallet, hotkey=hotkey),
            "show": cls.show_help(netuid),
            "pending_commits": cls.inspect_pending_commits_help(netuid),
            "hyperparams": cls.inspect_version_key_help(netuid),
            **cls._adjacent_workflows_fields(netuid),
            "status_note": cls._status_note(),
            "show_note": cls._show_note(),
            "pending_commits_note": cls._pending_commits_note(),
            "hyperparams_note": cls._hyperparams_note(),
        }

    @classmethod
    def inspect_version_key_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready subnet hyperparameters command for version-key recovery."""
        return " ".join(["agcli", "subnet", "hyperparams", "--netuid", cls._netuid_arg(netuid)])

    @classmethod
    def inspect_version_key_help_old(cls, netuid: int) -> str:
        """Backward-compatible alias for inspect_version_key_help."""
        return cls.inspect_version_key_help(netuid)

    @classmethod
    def inspect_hyperparams_help(cls, netuid: int) -> str:
        """Backward-compatible alias for inspect_version_key_help with clearer wording."""
        return cls.inspect_version_key_help(netuid)

    @classmethod
    def commit_reveal_flow_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> dict[str, str]:
        """Return normalized helpers for a manual commit/reveal workflow."""
        helpers = cls.workflow_help(netuid, weights, salt, version_key=version_key)
        return {
            "normalized_weights": helpers["normalized_weights"],
            "commit": helpers["commit"],
            "reveal": helpers["reveal"],
            "status": helpers["status"],
        }

    @classmethod
    def mechanism_commit_hash_help(
        cls,
        weights: WeightsInput,
        salt: CommitSaltInput,
    ) -> dict[str, str]:
        """Return a normalized mechanism commit hash plus reusable reveal inputs."""
        normalized_weights = cls._validated_explicit_weights_arg(weights)
        normalized_salt = cls._salt_arg(salt)
        return {
            "normalized_weights": normalized_weights,
            "normalized_salt": normalized_salt,
            "hash": cls._compute_commit_hash(normalized_weights, normalized_salt),
        }

    @classmethod
    def timelocked_commit_hash_help(
        cls,
        weights: WeightsInput,
        salt: CommitSaltInput,
    ) -> dict[str, str]:
        """Return a normalized timelocked commit hash plus reusable reveal inputs."""
        return cls.mechanism_commit_hash_help(weights, salt)

    @classmethod
    def commit_reveal_payload_help(
        cls,
        weights: WeightsInput,
        salt: CommitSaltInput,
    ) -> dict[str, Any]:
        """Return normalized payload details shared by direct, mechanism, and timelocked flows."""
        normalized_weights = cls._validated_explicit_weights_arg(weights)
        normalized_salt = cls._salt_arg(salt)
        return {
            "normalized_weights": normalized_weights,
            "normalized_salt": normalized_salt,
            "salt_u16": cls._salt_u16_arg(normalized_salt),
            "hash": cls._compute_commit_hash(normalized_weights, normalized_salt),
        }

    @classmethod
    def reveal_payload_help(
        cls,
        weights: WeightsInput,
        salt: CommitSaltInput,
    ) -> dict[str, Any]:
        """Return normalized reveal payload details, including the derived salt_u16 vector."""
        return cls.commit_reveal_payload_help(weights, salt)

    @classmethod
    def mechanism_reveal_payload_help(
        cls,
        weights: WeightsInput,
        salt: CommitSaltInput,
    ) -> dict[str, Any]:
        """Return normalized mechanism reveal payload details."""
        return cls.commit_reveal_payload_help(weights, salt)

    @classmethod
    def timelocked_reveal_payload_help(
        cls,
        weights: WeightsInput,
        salt: CommitSaltInput,
        round: int,
    ) -> dict[str, Any]:
        """Return normalized timelocked reveal payload details."""
        payload = cls.commit_reveal_payload_help(weights, salt)
        payload["round"] = int(cls._round_arg(round))
        return payload

    @classmethod
    def reveal_salt_help(cls, salt: CommitSaltInput) -> dict[str, Any]:
        """Return normalized reveal salt forms used by agcli commit/reveal flows."""
        normalized_salt = cls._salt_arg(salt)
        return {
            "normalized_salt": normalized_salt,
            "salt_u16": cls._salt_u16_arg(normalized_salt),
        }

    @classmethod
    def drand_round_help(cls, round: int) -> dict[str, int]:
        """Return a normalized drand round for timelocked flows."""
        return {"round": int(cls._round_arg(round))}

    @classmethod
    def drand_status_help(cls, netuid: int, round: int) -> dict[str, str | int]:
        """Return a minimal timelocked runbook anchored on subnet status plus normalized round."""
        return {
            "status": cls.status_help(netuid),
            "round": int(cls._round_arg(round)),
        }

    @classmethod
    def mechanism_commit_runbook_help(
        cls,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> dict[str, str]:
        """Return a full mechanism commit/reveal runbook without requiring a precomputed hash."""
        hash_help = cls.mechanism_commit_hash_help(weights, salt)
        return {
            **hash_help,
            "status": cls.status_help(netuid),
            "commit_mechanism": cls.commit_mechanism_help(netuid, mechanism_id, hash_help["hash"]),
            "reveal_mechanism": cls.reveal_mechanism_help(
                netuid,
                mechanism_id,
                hash_help["normalized_weights"],
                hash_help["normalized_salt"],
                version_key=version_key,
            ),
        }

    @classmethod
    def timelocked_commit_runbook_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        round: int,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> dict[str, str | int]:
        """Return a full timelocked commit/reveal runbook with hash, round, and reveal inputs."""
        hash_help = cls.timelocked_commit_hash_help(weights, salt)
        normalized_round = int(cls._round_arg(round))
        return {
            **hash_help,
            "round": normalized_round,
            "status": cls.status_help(netuid),
            "commit_timelocked": cls.commit_timelocked_help(
                netuid,
                hash_help["normalized_weights"],
                normalized_round,
                salt=hash_help["normalized_salt"],
            ),
            "reveal": cls.reveal_help(
                netuid,
                hash_help["normalized_weights"],
                hash_help["normalized_salt"],
                version_key=version_key,
            ),
        }

    @classmethod
    def mechanism_workflow_help(
        cls,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, str]:
        """Return copy-paste-ready helpers for mechanism-specific weights workflows."""
        if hash_value is None:
            return cls.mechanism_commit_runbook_help(
                netuid,
                mechanism_id,
                weights,
                salt,
                version_key=version_key,
            )

        normalized_weights = cls._weights_arg(weights)
        normalized_salt = cls._salt_arg(salt)
        normalized_hash = cls._hash_arg(hash_value)
        return {
            "normalized_weights": normalized_weights,
            "normalized_salt": normalized_salt,
            "hash": normalized_hash,
            "status": cls.status_help(netuid),
            "set_mechanism": cls.set_mechanism_help(
                netuid,
                mechanism_id,
                normalized_weights,
                version_key=version_key,
            ),
            "commit_mechanism": cls.commit_mechanism_help(netuid, mechanism_id, normalized_hash),
            "reveal_mechanism": cls.reveal_mechanism_help(
                netuid,
                mechanism_id,
                normalized_weights,
                normalized_salt,
                version_key=version_key,
            ),
        }

    @classmethod
    def timelocked_workflow_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        round: int,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, str | int]:
        """Return copy-paste-ready helpers for timelocked weights workflows."""
        normalized_weights = cls._weights_arg(weights)
        helpers: dict[str, str | int] = {
            "normalized_weights": normalized_weights,
            "status": cls.status_help(netuid),
            "set": cls.set_help(netuid, normalized_weights, version_key=version_key),
            "round": int(cls._round_arg(round)),
        }
        if salt is None:
            return helpers

        return {
            **helpers,
            **cls.timelocked_commit_runbook_help(
                netuid,
                normalized_weights,
                round,
                salt,
                version_key=version_key,
            ),
        }

    @classmethod
    def troubleshoot_mechanism_help(
        cls,
        netuid: int,
        mechanism_id: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
        status: object | None = None,
    ) -> dict[str, Any]:
        """Return a compact troubleshooting runbook for mechanism-specific failures."""
        error_text = cls._error_arg(error)
        result: dict[str, Any] = {
            "error": error_text,
            "likely_cause": cls._troubleshooting_guidance(error_text)[0],
            "next_step": cls._troubleshooting_guidance(error_text)[1],
            "status": cls.status_help(netuid),
        }
        summary: dict[str, Any] | None = None
        if status is not None:
            summary = cls._extract_status_summary(status)
            result["status_summary"] = summary
        if weights is not None:
            normalized_weights = cls._weights_arg(weights)
            result["normalized_weights"] = normalized_weights
            result["set_mechanism"] = cls.set_mechanism_help(
                netuid,
                mechanism_id,
                normalized_weights,
                version_key=version_key,
            )
            if salt is not None:
                normalized_salt = cls._salt_arg(salt)
                result["reveal_mechanism"] = cls.reveal_mechanism_help(
                    netuid,
                    mechanism_id,
                    normalized_weights,
                    normalized_salt,
                    version_key=version_key,
                )
        normalized_hash: str | None = None
        if hash_value is not None:
            normalized_hash = cls._hash_arg(hash_value)
        elif weights is not None and salt is not None:
            normalized_hash = cls._compute_commit_hash(cls._weights_arg(weights), cls._salt_arg(salt))
        if normalized_hash is not None:
            result["normalized_hash"] = normalized_hash
            result["commit_mechanism"] = cls.commit_mechanism_help(netuid, mechanism_id, normalized_hash)
        if summary is not None:
            result.update(
                cls._mechanism_next_action_guidance(
                    netuid,
                    mechanism_id,
                    summary,
                    weights,
                    salt=salt,
                    hash_value=hash_value,
                    version_key=version_key,
                )
            )
        return result

    @classmethod
    def next_mechanism_action_help(
        cls,
        netuid: int,
        mechanism_id: int,
        status: Mapping[str, Any] | str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Return the next recommended mechanism command from a provided status payload."""
        summary = cls._extract_status_summary(status)
        return {
            "status": cls.status_help(netuid),
            "status_summary": summary,
            **cls._mechanism_next_action_guidance(
                netuid,
                mechanism_id,
                summary,
                weights,
                salt=salt,
                hash_value=hash_value,
                version_key=version_key,
            ),
        }

    @classmethod
    def troubleshoot_timelocked_help(
        cls,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
        status: object | None = None,
    ) -> dict[str, Any]:
        """Return a compact troubleshooting runbook for timelocked failures."""
        error_text = cls._error_arg(error)
        result: dict[str, Any] = {
            "error": error_text,
            "likely_cause": cls._troubleshooting_guidance(error_text)[0],
            "next_step": cls._troubleshooting_guidance(error_text)[1],
            "status": cls.status_help(netuid),
        }
        summary: dict[str, Any] | None = None
        if status is not None:
            summary = cls._extract_status_summary(status)
            result["status_summary"] = summary
        if weights is not None:
            normalized_weights = cls._weights_arg(weights)
            result["normalized_weights"] = normalized_weights
            result["set"] = cls.set_help(netuid, normalized_weights, version_key=version_key)
            if salt is not None:
                normalized_salt = cls._salt_arg(salt)
                result["reveal"] = cls.reveal_help(
                    netuid,
                    normalized_weights,
                    normalized_salt,
                    version_key=version_key,
                )
        if round is not None:
            normalized_round = int(cls._round_arg(round))
            result["round"] = normalized_round
            if weights is not None:
                result["commit_timelocked"] = cls.commit_timelocked_help(
                    netuid,
                    cls._weights_arg(weights),
                    normalized_round,
                    salt=salt,
                )
        if summary is not None:
            result.update(
                cls._timelocked_next_action_guidance(
                    netuid,
                    summary,
                    weights,
                    round=round,
                    salt=salt,
                    version_key=version_key,
                )
            )
        return result

    @classmethod
    def next_timelocked_action_help(
        cls,
        netuid: int,
        status: Mapping[str, Any] | str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Return the next recommended timelocked command from a provided status payload."""
        summary = cls._extract_status_summary(status)
        return {
            "status": cls.status_help(netuid),
            "status_summary": summary,
            **cls._timelocked_next_action_guidance(
                netuid,
                summary,
                weights,
                round=round,
                salt=salt,
                version_key=version_key,
            ),
        }

    @classmethod
    def troubleshoot_help(
        cls,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
        status: object | None = None,
    ) -> dict[str, Any]:
        """Return a compact troubleshooting runbook for common weights failures."""
        status_command = cls.status_help(netuid)
        error_text = cls._error_arg(error)
        likely_cause, next_step = cls._troubleshooting_guidance(error_text)
        result: dict[str, Any] = {
            "error": error_text,
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": status_command,
        }
        summary: dict[str, Any] | None = None
        if status is not None:
            summary = cls._extract_status_summary(status)
            result["status_summary"] = summary
            result = cls._attach_raw_status(result, status)
        normalized_weights: str | None = None
        normalized_salt: str | None = None
        if weights is not None:
            try:
                normalized_weights = cls._weights_arg(weights)
            except ValueError as exc:
                if summary is not None:
                    result.update(
                        cls._next_action_guidance(
                            netuid,
                            summary,
                            version_key=version_key,
                        )
                    )
                result.update(cls._weights_input_recovery_fields(str(exc)))
                return result
            result["normalized_weights"] = normalized_weights
            result["set"] = cls.set_help(netuid, normalized_weights, version_key=version_key)
            if salt is not None:
                normalized_salt = cls._salt_arg(salt)
                result["commit"] = cls.commit_help(netuid, normalized_weights, salt=normalized_salt)
                result["reveal"] = cls.reveal_help(
                    netuid,
                    normalized_weights,
                    normalized_salt,
                    version_key=version_key,
                )
                result["commit_reveal"] = cls.commit_reveal_help(
                    netuid,
                    normalized_weights,
                    version_key=version_key,
                )
        if summary is not None:
            result.update(
                cls._next_action_guidance(
                    netuid,
                    summary,
                    normalized_weights,
                    salt=normalized_salt,
                    version_key=version_key,
                )
            )
        result.update(cls._troubleshoot_recovery_fields(netuid, error_text))
        result.update(cls._adjacent_recovery_fields(netuid))
        if summary is not None:
            result.update(cls._status_aware_recovery_fields(error_text, summary))
        return result

    def _live_status_input(self, netuid: int) -> Mapping[str, Any] | str:
        """Fetch live status, falling back to raw text when JSON status is unavailable."""
        try:
            status = self.status(netuid)
        except json.JSONDecodeError:
            return self.status_text(netuid)
        if isinstance(status, Mapping):
            return status
        return self.status_text(netuid)

    def status_summary(self, netuid: int) -> dict[str, Any]:
        """Run `weights status` and return a normalized summary for agents/operators."""
        status = self._live_status_input(netuid)
        return {
            "status": self.status_help(netuid),
            **self._extract_status_summary(status),
        }

    def status_text(self, netuid: int) -> str:
        """Return raw human-readable `weights status` output for operator-facing runbooks."""
        return self._run_raw(["weights", "status", "--netuid", self._netuid_arg(netuid)])

    def status_summary_text(self, netuid: int) -> dict[str, Any]:
        """Run human-readable `weights status` and normalize it into a structured summary."""
        status_text = self.status_text(netuid)
        return {
            "status": self.status_help(netuid),
            **self._extract_status_summary(status_text),
        }

    def status_runbook(self, netuid: int) -> dict[str, Any]:
        """Return raw status text together with a normalized machine-friendly summary."""
        status_text = self.status_text(netuid)
        return {
            "status": self.status_help(netuid),
            "raw_status": status_text,
            "summary": self._extract_status_summary(status_text),
        }

    def status_runbook_json(self, netuid: int) -> dict[str, Any]:
        """Return JSON status plus a normalized summary when machine-readable output is preferred."""
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        return {
            "status": self.status_help(netuid),
            "raw_status": status,
            "summary": self._extract_status_summary(status),
        }

    @classmethod
    def status_summary_help(cls, status: Mapping[str, Any] | str) -> dict[str, Any]:
        """Normalize a provided status payload or raw status text without making subprocess calls."""
        return cls._extract_status_summary(status)

    @classmethod
    def status_runbook_help(cls, netuid: int, status: Mapping[str, Any] | str) -> dict[str, Any]:
        """Build a reusable runbook from provided status payloads or status text."""
        return {
            "status": cls.status_help(netuid),
            "raw_status": status,
            "summary": cls._extract_status_summary(status),
        }

    @classmethod
    def status_text_help(cls, status: str) -> dict[str, Any]:
        """Normalize raw human-readable status text into a structured summary."""
        if not isinstance(status, str):
            raise ValueError("status text must be a string")
        normalized_status = status.strip()
        if not normalized_status:
            raise ValueError("status text cannot be empty")
        return cls._extract_status_summary(normalized_status)

    @classmethod
    def status_text_runbook_help(cls, netuid: int, status: str) -> dict[str, Any]:
        """Build a reusable runbook from raw human-readable status text."""
        if not isinstance(status, str):
            raise ValueError("status text must be a string")
        normalized_status = status.strip()
        if not normalized_status:
            raise ValueError("status text cannot be empty")
        return {
            "status": cls.status_help(netuid),
            "raw_status": normalized_status,
            "summary": cls._extract_status_summary(normalized_status),
        }

    @classmethod
    def status_text_next_action_help(
        cls,
        netuid: int,
        status: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        """Return the next recommended command from raw human-readable status text."""
        summary = cls.status_text_help(status)
        return {
            "status": cls.status_help(netuid),
            "raw_status": status.strip(),
            "status_summary": summary,
            **cls._next_action_guidance(
                netuid,
                summary,
                weights,
                salt=salt,
                version_key=version_key,
                wait=wait,
            ),
        }

    @classmethod
    def status_text_troubleshoot_help(
        cls,
        netuid: int,
        status: str,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Return troubleshooting guidance from raw human-readable status text."""
        normalized_status = status.strip() if isinstance(status, str) else status
        return cls.troubleshoot_help(
            netuid,
            error,
            weights,
            salt=salt,
            version_key=version_key,
            status=normalized_status,
        )

    @classmethod
    def status_text_next_mechanism_action_help(
        cls,
        netuid: int,
        mechanism_id: int,
        status: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Return mechanism guidance from raw human-readable status text."""
        summary = cls.status_text_help(status)
        return {
            "status": cls.status_help(netuid),
            "raw_status": status.strip(),
            "status_summary": summary,
            **cls._mechanism_next_action_guidance(
                netuid,
                mechanism_id,
                summary,
                weights,
                salt=salt,
                hash_value=hash_value,
                version_key=version_key,
            ),
        }

    @classmethod
    def status_text_troubleshoot_mechanism_help(
        cls,
        netuid: int,
        mechanism_id: int,
        status: str,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Return mechanism troubleshooting guidance from raw human-readable status text."""
        normalized_status = status.strip() if isinstance(status, str) else status
        return cls.troubleshoot_mechanism_help(
            netuid,
            mechanism_id,
            error,
            weights,
            salt=salt,
            hash_value=hash_value,
            version_key=version_key,
            status=normalized_status,
        )

    @classmethod
    def status_text_next_timelocked_action_help(
        cls,
        netuid: int,
        status: str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Return timelocked guidance from raw human-readable status text."""
        summary = cls.status_text_help(status)
        return {
            "status": cls.status_help(netuid),
            "raw_status": status.strip(),
            "status_summary": summary,
            **cls._timelocked_next_action_guidance(
                netuid,
                summary,
                weights,
                round=round,
                salt=salt,
                version_key=version_key,
            ),
        }

    @classmethod
    def status_text_troubleshoot_timelocked_help(
        cls,
        netuid: int,
        status: str,
        error: str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Return timelocked troubleshooting guidance from raw human-readable status text."""
        normalized_status = status.strip() if isinstance(status, str) else status
        return cls.troubleshoot_timelocked_help(
            netuid,
            error,
            weights,
            round=round,
            salt=salt,
            version_key=version_key,
            status=normalized_status,
        )

    def next_action_text(
        self,
        netuid: int,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and return the next recommended weights command."""
        status_text = self.status_text(netuid)
        return self.status_text_next_action_help(
            netuid,
            status_text,
            weights,
            salt=salt,
            version_key=version_key,
            wait=wait,
        )

    def troubleshoot_text(
        self,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and merge it into the troubleshooting runbook."""
        status_text = self.status_text(netuid)
        return self.status_text_troubleshoot_help(
            netuid,
            status_text,
            error,
            weights,
            salt=salt,
            version_key=version_key,
        )

    def next_mechanism_action_text(
        self,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and return the next recommended mechanism command."""
        status_text = self.status_text(netuid)
        return self.status_text_next_mechanism_action_help(
            netuid,
            mechanism_id,
            status_text,
            weights,
            salt=salt,
            hash_value=hash_value,
            version_key=version_key,
        )

    def troubleshoot_mechanism_text(
        self,
        netuid: int,
        mechanism_id: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and merge it into the mechanism troubleshooting runbook."""
        status_text = self.status_text(netuid)
        return self.status_text_troubleshoot_mechanism_help(
            netuid,
            mechanism_id,
            status_text,
            error,
            weights,
            salt=salt,
            hash_value=hash_value,
            version_key=version_key,
        )

    def next_timelocked_action_text(
        self,
        netuid: int,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and return the next recommended timelocked command."""
        status_text = self.status_text(netuid)
        return self.status_text_next_timelocked_action_help(
            netuid,
            status_text,
            weights,
            round=round,
            salt=salt,
            version_key=version_key,
        )

    def troubleshoot_timelocked_text(
        self,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and merge it into the timelocked troubleshooting runbook."""
        status_text = self.status_text(netuid)
        return self.status_text_troubleshoot_timelocked_help(
            netuid,
            status_text,
            error,
            weights,
            round=round,
            salt=salt,
            version_key=version_key,
        )

    def diagnose_text(self, netuid: int, error: str) -> dict[str, Any]:
        """Fetch human-readable status text and return compact error plus status guidance."""
        status_text = self.status_text(netuid)
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self.status_text_help(status_text)
        return {
            "error": self._error_arg(error),
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": self.status_help(netuid),
            "raw_status": status_text,
            "status_summary": summary,
            **self._next_action_guidance(netuid, summary),
        }

    def diagnose_mechanism_text(
        self,
        netuid: int,
        mechanism_id: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and return compact mechanism error plus status guidance."""
        status_text = self.status_text(netuid)
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self.status_text_help(status_text)
        return {
            "error": self._error_arg(error),
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": self.status_help(netuid),
            "raw_status": status_text,
            "status_summary": summary,
            **self._mechanism_next_action_guidance(
                netuid,
                mechanism_id,
                summary,
                weights,
                salt=salt,
                hash_value=hash_value,
                version_key=version_key,
            ),
        }

    def diagnose_timelocked_text(
        self,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch human-readable status text and return compact timelocked error plus status guidance."""
        status_text = self.status_text(netuid)
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self.status_text_help(status_text)
        return {
            "error": self._error_arg(error),
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": self.status_help(netuid),
            "raw_status": status_text,
            "status_summary": summary,
            **self._timelocked_next_action_guidance(
                netuid,
                summary,
                weights,
                round=round,
                salt=salt,
                version_key=version_key,
            ),
        }

    @classmethod
    def next_action_help(
        cls,
        netuid: int,
        status: Mapping[str, Any] | str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        """Return the next recommended command from a provided status payload."""
        summary = cls._extract_status_summary(status)
        return {
            "status": cls.status_help(netuid),
            "status_summary": summary,
            **cls._next_action_guidance(
                netuid,
                summary,
                weights,
                salt=salt,
                version_key=version_key,
                wait=wait,
            ),
        }

    def next_action(
        self,
        netuid: int,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
        wait: bool = False,
    ) -> dict[str, Any]:
        """Fetch live status and return the next recommended weights command."""
        status = self._live_status_input(netuid)
        result = self.next_action_help(
            netuid,
            status,
            weights,
            salt=salt,
            version_key=version_key,
            wait=wait,
        )
        return self._attach_raw_status(result, status)

    def troubleshoot(
        self,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and merge it into the troubleshooting runbook."""
        status = self._live_status_input(netuid)
        result = self.troubleshoot_help(
            netuid,
            error,
            weights,
            salt=salt,
            version_key=version_key,
            status=status,
        )
        return self._attach_raw_status(result, status)

    def diagnose(self, netuid: int, error: str) -> dict[str, Any]:
        """Fetch live status and return compact error plus status guidance."""
        status = self._live_status_input(netuid)
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self._extract_status_summary(status)
        result = {
            "error": self._error_arg(error),
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": self.status_help(netuid),
            "status_summary": summary,
            **self._next_action_guidance(netuid, summary),
        }
        return self._attach_raw_status(result, status)

    def diagnose_mechanism(
        self,
        netuid: int,
        mechanism_id: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and return compact mechanism error plus status guidance."""
        status = self._live_status_input(netuid)
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self._extract_status_summary(status)
        result = {
            "error": self._error_arg(error),
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": self.status_help(netuid),
            "status_summary": summary,
            **self._mechanism_next_action_guidance(
                netuid,
                mechanism_id,
                summary,
                weights,
                salt=salt,
                hash_value=hash_value,
                version_key=version_key,
            ),
        }
        return self._attach_raw_status(result, status)

    def diagnose_timelocked(
        self,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and return compact timelocked error plus status guidance."""
        status = self._live_status_input(netuid)
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self._extract_status_summary(status)
        result = {
            "error": self._error_arg(error),
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": self.status_help(netuid),
            "status_summary": summary,
            **self._timelocked_next_action_guidance(
                netuid,
                summary,
                weights,
                round=round,
                salt=salt,
                version_key=version_key,
            ),
        }
        return self._attach_raw_status(result, status)

    def next_mechanism_action(
        self,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and return the next recommended mechanism command."""
        status = self._live_status_input(netuid)
        result = self.next_mechanism_action_help(
            netuid,
            mechanism_id,
            status,
            weights,
            salt=salt,
            hash_value=hash_value,
            version_key=version_key,
        )
        return self._attach_raw_status(result, status)

    def troubleshoot_mechanism(
        self,
        netuid: int,
        mechanism_id: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        hash_value: HashInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and merge it into the mechanism troubleshooting runbook."""
        status = self._live_status_input(netuid)
        result = self.troubleshoot_mechanism_help(
            netuid,
            mechanism_id,
            error,
            weights,
            salt=salt,
            hash_value=hash_value,
            version_key=version_key,
            status=status,
        )
        return self._attach_raw_status(result, status)

    def next_timelocked_action(
        self,
        netuid: int,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and return the next recommended timelocked command."""
        status = self._live_status_input(netuid)
        result = self.next_timelocked_action_help(
            netuid,
            status,
            weights,
            round=round,
            salt=salt,
            version_key=version_key,
        )
        return self._attach_raw_status(result, status)

    def troubleshoot_timelocked(
        self,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and merge it into the timelocked troubleshooting runbook."""
        status = self._live_status_input(netuid)
        result = self.troubleshoot_timelocked_help(
            netuid,
            error,
            weights,
            round=round,
            salt=salt,
            version_key=version_key,
            status=status,
        )
        return self._attach_raw_status(result, status)

    def show(self, netuid: int, hotkey_address: str | None = None, limit: int | None = None) -> Any:
        """Show current weights set by a hotkey on a subnet."""
        args = ["weights", "show", "--netuid", self._netuid_arg(netuid)]
        args += self._opt("--hotkey-address", hotkey_address)
        args += self._opt("--limit", limit)
        return self._run(args)

    def set(self, netuid: int, weights: WeightsInput, version_key: int | None = None) -> Any:
        """Set weights on a subnet."""
        return self._run(["weights", "set", *self._set_args(netuid, weights, version_key=version_key)])

    def commit(
        self,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput | None = None,
    ) -> Any:
        """Commit weights (hash) for later reveal."""
        return self._run(["weights", "commit", *self._commit_args(netuid, weights, salt=salt)])

    def reveal(
        self,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> Any:
        """Reveal previously committed weights."""
        return self._run(["weights", "reveal", *self._reveal_args(netuid, weights, salt, version_key=version_key)])

    def status(self, netuid: int) -> Any:
        """Show commit/reveal status for a subnet."""
        return self._run(["weights", "status", "--netuid", self._netuid_arg(netuid)])

    def commit_reveal(
        self,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
        wait: bool = False,
    ) -> Any:
        """Commit and auto-reveal weights in one operation."""
        return self._run(
            ["weights", "commit-reveal", *self._commit_reveal_args(netuid, weights, version_key=version_key, wait=wait)]
        )

    def set_mechanism(
        self,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        version_key: int | None = None,
    ) -> Any:
        """Set mechanism-specific weights on a subnet."""
        return self._run(
            [
                "weights",
                "set-mechanism",
                *self._set_mechanism_args(netuid, mechanism_id, weights, version_key=version_key),
            ]
        )

    def commit_mechanism(self, netuid: int, mechanism_id: int, hash: HashInput) -> Any:
        """Commit a precomputed mechanism-specific weights hash."""
        return self._run(["weights", "commit-mechanism", *self._commit_mechanism_args(netuid, mechanism_id, hash)])

    def reveal_mechanism(
        self,
        netuid: int,
        mechanism_id: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> Any:
        """Reveal previously committed mechanism-specific weights."""
        return self._run(
            [
                "weights",
                "reveal-mechanism",
                *self._reveal_mechanism_args(
                    netuid,
                    mechanism_id,
                    weights,
                    salt,
                    version_key=version_key,
                ),
            ]
        )

    def commit_timelocked(
        self,
        netuid: int,
        weights: WeightsInput,
        round: int,
        salt: CommitSaltInput | None = None,
    ) -> Any:
        """Commit timelocked weights using drand randomness."""
        return self._run(
            ["weights", "commit-timelocked", *self._commit_timelocked_args(netuid, weights, round, salt=salt)]
        )
