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
        normalized = cls._weights_arg(weights)
        if normalized == "-" or normalized.startswith("@"):
            raise ValueError("weights hash generation requires explicit weights, not stdin or @file inputs")

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
        record["reveal_command"] = cls.reveal_help(
            record["netuid"],
            record["normalized_weights"],
            record["normalized_salt"],
            version_key=record.get("version_key") if version_key is None else version_key,
        )
        if version_key is not None:
            version_key_arg = cls._version_key_arg(version_key)
            assert version_key_arg is not None
            record["version_key"] = int(version_key_arg)
        return record

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
    def troubleshoot_unrevealed_commit_help(
        cls,
        path: str | Path,
        error: str | None = None,
    ) -> dict[str, Any]:
        """Load saved commit state and return recovery guidance for stuck unrevealed commits."""
        record = cls.load_commit_reveal_state_help(path)
        result: dict[str, Any] = {
            **record,
            "recovery_reason": (
                "A previous commit can still be revealed if its original weights and salt are preserved."
            ),
        }
        if error is not None:
            error_text = cls._error_arg(error)
            likely_cause, next_step = cls._troubleshooting_guidance(error_text)
            result.update(
                {
                    "error": error_text,
                    "likely_cause": likely_cause,
                    "next_step": next_step,
                }
            )
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

        result: dict[str, Any] = {
            "recommended_action": next_action,
            "recommended_command": cls.status_help(netuid),
        }

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

        result: dict[str, Any] = {
            "recommended_action": next_action,
            "recommended_command": cls.status_help(netuid),
        }

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

        result: dict[str, Any] = {
            "recommended_action": next_action,
            "recommended_command": cls.status_help(netuid),
        }

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
                ("CommittingWeightsTooFast", "SettingWeightsTooFast", "TxRateLimitExceeded"),
                "The subnet is rate limiting repeated weight updates.",
                "Wait for the rate limit window to pass, then retry the same normalized command.",
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
        args = ["--netuid", cls._netuid_arg(netuid), "--weights", cls._weights_arg(weights)]
        args += cls._opt("--version-key", cls._version_key_arg(version_key))
        return args

    @classmethod
    def _commit_args(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput | None = None,
    ) -> list[str]:
        args = ["--netuid", cls._netuid_arg(netuid), "--weights", cls._weights_arg(weights)]
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
        args = ["--netuid", cls._netuid_arg(netuid), "--weights", cls._weights_arg(weights)]
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
    ) -> str:
        """Return a copy-paste-ready commit command preview."""
        return " ".join(["agcli", "weights", "commit", *cls._commit_args(netuid, weights, salt=salt)])

    @classmethod
    def set_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        version_key: int | None = None,
    ) -> str:
        """Return a copy-paste-ready set command preview."""
        return " ".join(["agcli", "weights", "set", *cls._set_args(netuid, weights, version_key=version_key)])

    @classmethod
    def reveal_help(
        cls,
        netuid: int,
        weights: WeightsInput,
        salt: CommitSaltInput,
        version_key: int | None = None,
    ) -> str:
        """Return a copy-paste-ready reveal command preview."""
        return " ".join(
            ["agcli", "weights", "reveal", *cls._reveal_args(netuid, weights, salt, version_key=version_key)]
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
    ) -> str:
        """Return a copy-paste-ready commit-reveal command preview."""
        return " ".join(
            [
                "agcli",
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
    ) -> dict[str, str]:
        """Return copy-paste-ready helpers for common weights workflows."""
        normalized_weights = cls._weights_arg(weights)
        normalized_salt = cls._salt_arg(salt)
        return {
            "normalized_weights": normalized_weights,
            "status": cls.status_help(netuid),
            "set": cls.set_help(netuid, normalized_weights, version_key=version_key),
            "commit_reveal": cls.commit_reveal_help(
                netuid,
                normalized_weights,
                version_key=version_key,
                wait=wait,
            ),
            "commit": cls.commit_help(netuid, normalized_weights, salt=normalized_salt),
            "reveal": cls.reveal_help(netuid, normalized_weights, normalized_salt, version_key=version_key),
        }

    @classmethod
    def status_help(cls, netuid: int) -> str:
        """Return a copy-paste-ready status command preview."""
        return " ".join(["agcli", "weights", "status", "--netuid", cls._netuid_arg(netuid)])

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
        return {
            "normalized_weights": cls._weights_arg(weights),
            "normalized_salt": cls._salt_arg(salt),
            "hash": cls._compute_commit_hash(weights, salt),
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
        normalized_salt = cls._salt_arg(salt)
        return {
            "normalized_weights": cls._weights_arg(weights),
            "normalized_salt": normalized_salt,
            "salt_u16": cls._salt_u16_arg(normalized_salt),
            "hash": cls._compute_commit_hash(weights, normalized_salt),
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
        status: Mapping[str, Any],
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
        status: Mapping[str, Any],
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
        if weights is not None:
            normalized_weights = cls._weights_arg(weights)
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
                    weights,
                    salt=salt,
                    version_key=version_key,
                )
            )
        return result

    def status_summary(self, netuid: int) -> dict[str, Any]:
        """Run `weights status` and return a normalized summary for agents/operators."""
        status = self.status(netuid)
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
        status: Mapping[str, Any],
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
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        return self.next_action_help(
            netuid,
            status,
            weights,
            salt=salt,
            version_key=version_key,
            wait=wait,
        )

    def troubleshoot(
        self,
        netuid: int,
        error: str,
        weights: WeightsInput | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and merge it into the troubleshooting runbook."""
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        return self.troubleshoot_help(
            netuid,
            error,
            weights,
            salt=salt,
            version_key=version_key,
            status=status,
        )

    def diagnose(self, netuid: int, error: str) -> dict[str, Any]:
        """Fetch live status and return compact error plus status guidance."""
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self._extract_status_summary(status)
        return {
            "error": self._error_arg(error),
            "likely_cause": likely_cause,
            "next_step": next_step,
            "status": self.status_help(netuid),
            "status_summary": summary,
            **self._next_action_guidance(netuid, summary),
        }

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
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self._extract_status_summary(status)
        return {
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
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        likely_cause, next_step = self._troubleshooting_guidance(error)
        summary = self._extract_status_summary(status)
        return {
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
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        return self.next_mechanism_action_help(
            netuid,
            mechanism_id,
            status,
            weights,
            salt=salt,
            hash_value=hash_value,
            version_key=version_key,
        )

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
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        return self.troubleshoot_mechanism_help(
            netuid,
            mechanism_id,
            error,
            weights,
            salt=salt,
            hash_value=hash_value,
            version_key=version_key,
            status=status,
        )

    def next_timelocked_action(
        self,
        netuid: int,
        weights: WeightsInput | None = None,
        round: int | None = None,
        salt: CommitSaltInput | None = None,
        version_key: int | None = None,
    ) -> dict[str, Any]:
        """Fetch live status and return the next recommended timelocked command."""
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        return self.next_timelocked_action_help(
            netuid,
            status,
            weights,
            round=round,
            salt=salt,
            version_key=version_key,
        )

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
        status = self.status(netuid)
        if not isinstance(status, Mapping):
            raise ValueError("weights status output must be a mapping")
        return self.troubleshoot_timelocked_help(
            netuid,
            error,
            weights,
            round=round,
            salt=salt,
            version_key=version_key,
            status=status,
        )

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
