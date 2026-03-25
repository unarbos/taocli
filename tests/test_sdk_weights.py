"""Tests for the Weights SDK module."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from taocli.runner import AgcliRunner
from taocli.sdk.weights import Weights
from tests.conftest import make_completed_process

READY_STATUS_TEXT = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   125
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  Pending commits: 1

  [1] Hash:    0x1212
      Commit:  block 100
      Reveal:  blocks 120..130
      Status:  READY TO REVEAL (5 blocks remaining)
"""

NO_PENDING_STATUS_TEXT = """Weight Commit Status — SN7
  Hotkey:          5DAAnrj7VHTz5J4d7V7y9nGg8uXx2z
  Current block:   140
  Commit-reveal:   ENABLED
  Reveal period:   4 epochs

  No pending commits.
"""

WAITING_STATUS_TEXT = """Weight Commit Status — SN8
  Hotkey:          5FHneW46xGXgs5mUiveU4sbTyGBzm
  Current block:   100
  Commit-reveal:   ENABLED
  Reveal period:   2 epochs

  Pending commits: 1

  [1] Hash:    0x3434
      Commit:  block 90
      Reveal:  blocks 110..120
      Status:  WAITING (10 blocks until reveal window)
"""

EXPIRED_STATUS_TEXT = """Weight Commit Status — SN9
  Hotkey:          5GrwvaEF5zXb26Fz9rcQpDWS57CtE
  Current block:   140
  Commit-reveal:   ENABLED
  Reveal period:   4 epochs

  Pending commits: 1

  [1] Hash:    0x5656
      Commit:  block 100
      Reveal:  blocks 110..130
      Status:  EXPIRED
"""

DIRECT_SET_STATUS_TEXT = """Weight Commit Status — SN4
  Hotkey:          5C62Ck4U8QnF5wC7W9U4Lw8Bz2r4g
  Current block:   200
  Commit-reveal:   disabled
  Reveal period:   0 epochs

  No pending commits.
"""

BAD_STATUS_TEXT = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
"""

NON_MAPPING_STATUS_ERROR = "weights status output must be a mapping"
NON_MAPPING_OR_TEXT_STATUS_ERROR = "weights status output must be a mapping or recognizable status text"
STATUS_TEXT_TYPE_ERROR = "status text must be a string"
STATUS_TEXT_EMPTY_ERROR = "status text cannot be empty"
STATUS_MAPPING_ERROR = "status must be a mapping"


@pytest.fixture
def weights(mock_subprocess: Any) -> Weights:
    return Weights(AgcliRunner())


class TestWeights:
    def test_show(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.show(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "weights" in cmd and "show" in cmd

    def test_show_with_options(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.show(1, hotkey_address="5G...", limit=10)
        cmd = mock_subprocess.call_args[0][0]
        assert "--hotkey-address" in cmd and "--limit" in cmd

    def test_set(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, "0:100,1:200")
        cmd = mock_subprocess.call_args[0][0]
        assert "set" in cmd and "--weights" in cmd

    def test_set_accepts_mapping(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, {0: 100, 1: 200})
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200" in cmd

    def test_set_accepts_pairs(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, [(0, 100), (1, 200)])
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200" in cmd

    def test_set_normalizes_string_weights(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, " 0 : 100 , 1 : 200 ")
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200" in cmd

    def test_set_accepts_string_uids_and_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, {"0": "100", "1": "200.5"})
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200.5" in cmd

    def test_set_accepts_json_mapping_string(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, '{"0": 100, "1": 200}')
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200" in cmd

    def test_set_accepts_json_list_string(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, '[{"uid": 0, "weight": 100}, {"uid": 1, "weight": 200}]')
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200" in cmd

    def test_set_accepts_stdin_weights_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, "-")
        cmd = mock_subprocess.call_args[0][0]
        assert "-" in cmd

    def test_set_accepts_file_weights_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, "@weights.json")
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_set_rejects_invalid_json_weights_string(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="invalid JSON weights input"):
            weights.set(1, '{"0": }')

    def test_set_rejects_invalid_json_weights_shape(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=r"JSON weights must be an object map or array of \{uid, weight\} entries"):
            weights.set(1, "[1, 2, 3]")

    def test_set_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.set(0, "0:100")

    def test_set_rejects_boolean_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be an integer"):
            weights.set(True, "0:100")

    def test_set_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.set(1, "0:100", version_key=-1)

    def test_set_rejects_boolean_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be an integer"):
            weights.set(1, "0:100", version_key=True)

    def test_commit_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.commit_help(1, {0: 100}, salt=b"abc")
        assert command == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"

    def test_set_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.set_help(1, {0: 100}, version_key=2)
        assert command == "agcli weights set --netuid 1 --weights 0:100 --version-key 2"

    def test_reveal_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.reveal_help(1, {0: 100}, b"abc", version_key=2)
        assert command == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 2"

    def test_commit_reveal_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.commit_reveal_help(1, {0: 100}, version_key=2, wait=True)
        assert command == "agcli weights commit-reveal --netuid 1 --weights 0:100 --version-key 2 --wait"

    def test_set_mechanism_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.set_mechanism_help(1, 4, {0: 100}, version_key=2)
        assert command == "agcli weights set-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --version-key 2"

    def test_commit_mechanism_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.commit_mechanism_help(1, 4, b"\x11" * 32)
        assert command == ("agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash 0x" + "11" * 32)

    def test_reveal_mechanism_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.reveal_mechanism_help(1, 4, {0: 100}, b"abc", version_key=2)
        assert command == (
            "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 2"
        )

    def test_commit_timelocked_help_returns_copy_paste_command(self, weights: Weights) -> None:
        command = weights.commit_timelocked_help(1, {0: 100}, 42, salt=b"abc")
        assert command == "agcli weights commit-timelocked --netuid 1 --weights 0:100 --round 42 --salt abc"

    def test_status_help_returns_copy_paste_command(self, weights: Weights) -> None:
        assert weights.status_help(1) == "agcli weights status --netuid 1"

    def test_status_text_help_parses_ready_status_text(self, weights: Weights) -> None:
        summary = weights.status_text_help(READY_STATUS_TEXT)
        assert summary == {
            "current_block": 125,
            "commit_reveal_enabled": True,
            "reveal_period_epochs": 3,
            "pending_commits": 1,
            "pending_statuses": ["READY TO REVEAL (5 blocks remaining)"],
            "next_action": "REVEAL",
            "commit_windows": [
                {
                    "index": 1,
                    "status": "READY TO REVEAL (5 blocks remaining)",
                    "commit_block": 100,
                    "first_reveal": 120,
                    "last_reveal": 130,
                    "blocks_until_action": 5,
                    "hash": "0x1212",
                }
            ],
        }

    def test_status_text_help_parses_no_pending_commits_text(self, weights: Weights) -> None:
        summary = weights.status_text_help(NO_PENDING_STATUS_TEXT)
        assert summary == {
            "current_block": 140,
            "commit_reveal_enabled": True,
            "reveal_period_epochs": 4,
            "pending_commits": 0,
            "pending_statuses": [],
            "next_action": "NO_PENDING_COMMITS",
            "commit_windows": [],
        }

    def test_status_text_help_rejects_non_string_input(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_TEXT_TYPE_ERROR):
            weights.status_text_help(123)  # type: ignore[arg-type]

    def test_status_text_help_rejects_empty_input(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_TEXT_EMPTY_ERROR):
            weights.status_text_help("   ")

    def test_status_text_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_help(BAD_STATUS_TEXT)

    def test_status_summary_help_accepts_text_input(self, weights: Weights) -> None:
        summary = weights.status_summary_help(NO_PENDING_STATUS_TEXT)
        assert summary["next_action"] == "NO_PENDING_COMMITS"
        assert summary["pending_commits"] == 0

    def test_status_runbook_help_accepts_text_input(self, weights: Weights) -> None:
        runbook = weights.status_runbook_help(5, READY_STATUS_TEXT)
        assert runbook["status"] == "agcli weights status --netuid 5"
        assert runbook["raw_status"] == READY_STATUS_TEXT
        assert runbook["summary"]["next_action"] == "REVEAL"

    def test_status_text_runbook_help_returns_status_and_summary(self, weights: Weights) -> None:
        runbook = weights.status_text_runbook_help(7, NO_PENDING_STATUS_TEXT)
        assert runbook == {
            "status": "agcli weights status --netuid 7",
            "raw_status": NO_PENDING_STATUS_TEXT.strip(),
            "summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
        }

    def test_status_text_runbook_help_rejects_non_string_input(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_TEXT_TYPE_ERROR):
            weights.status_text_runbook_help(1, 123)  # type: ignore[arg-type]

    def test_status_text_runbook_help_rejects_empty_input(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_TEXT_EMPTY_ERROR):
            weights.status_text_runbook_help(1, "   ")

    def test_status_summary_help_rejects_non_mapping_non_string_input(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_MAPPING_ERROR):
            weights.status_summary_help(123)  # type: ignore[arg-type]

    def test_mechanism_workflow_help_returns_common_weight_helpers(self, weights: Weights) -> None:
        helpers = weights.mechanism_workflow_help(1, 4, " 0 : 100 , 1 : 200 ", b"abc", b"\x11" * 32, version_key=2)
        assert helpers == {
            "normalized_weights": "0:100,1:200",
            "normalized_salt": "abc",
            "hash": "0x" + "11" * 32,
            "status": "agcli weights status --netuid 1",
            "set_mechanism": (
                "agcli weights set-mechanism --netuid 1 --mechanism-id 4 --weights 0:100,1:200 --version-key 2"
            ),
            "commit_mechanism": ("agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash 0x" + "11" * 32),
            "reveal_mechanism": (
                "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100,1:200 --salt abc "
                "--version-key 2"
            ),
        }

    def test_mechanism_workflow_help_derives_hash_when_missing(self, weights: Weights) -> None:
        helpers = weights.mechanism_workflow_help(1, 4, "0:100", "abc")
        expected_hash = hashlib.blake2b(
            (0).to_bytes(2, byteorder="little", signed=False)
            + (100).to_bytes(2, byteorder="little", signed=False)
            + b"abc",
            digest_size=32,
        ).hexdigest()
        assert helpers == {
            "normalized_weights": "0:100",
            "normalized_salt": "abc",
            "hash": f"0x{expected_hash}",
            "status": "agcli weights status --netuid 1",
            "commit_mechanism": (
                "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash 0x" + expected_hash
            ),
            "reveal_mechanism": (
                "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc"
            ),
        }

    def test_timelocked_workflow_help_returns_common_weight_helpers(self, weights: Weights) -> None:
        helpers = weights.timelocked_workflow_help(1, " 0 : 100 , 1 : 200 ", 42, b"abc", version_key=2)
        expected_hash = hashlib.blake2b(
            (0).to_bytes(2, byteorder="little", signed=False)
            + (1).to_bytes(2, byteorder="little", signed=False)
            + (100).to_bytes(2, byteorder="little", signed=False)
            + (200).to_bytes(2, byteorder="little", signed=False)
            + b"abc",
            digest_size=32,
        ).hexdigest()
        assert helpers == {
            "normalized_weights": "0:100,1:200",
            "normalized_salt": "abc",
            "hash": f"0x{expected_hash}",
            "round": 42,
            "status": "agcli weights status --netuid 1",
            "set": "agcli weights set --netuid 1 --weights 0:100,1:200 --version-key 2",
            "commit_timelocked": (
                "agcli weights commit-timelocked --netuid 1 --weights 0:100,1:200 --round 42 --salt abc"
            ),
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100,1:200 --salt abc --version-key 2",
        }

    def test_timelocked_workflow_help_omits_hash_when_salt_missing(self, weights: Weights) -> None:
        helpers = weights.timelocked_workflow_help(1, "0:100", 42)
        assert helpers == {
            "normalized_weights": "0:100",
            "status": "agcli weights status --netuid 1",
            "set": "agcli weights set --netuid 1 --weights 0:100",
            "round": 42,
        }

    def test_commit_reveal_payload_help_returns_hash_and_salt_u16(self, weights: Weights) -> None:
        payload = weights.commit_reveal_payload_help("0:100,1:200", "abc")
        expected_hash = hashlib.blake2b(
            (0).to_bytes(2, byteorder="little", signed=False)
            + (1).to_bytes(2, byteorder="little", signed=False)
            + (100).to_bytes(2, byteorder="little", signed=False)
            + (200).to_bytes(2, byteorder="little", signed=False)
            + b"abc",
            digest_size=32,
        ).hexdigest()
        assert payload == {
            "normalized_weights": "0:100,1:200",
            "normalized_salt": "abc",
            "salt_u16": [25185, 99],
            "hash": f"0x{expected_hash}",
        }

    def test_commit_reveal_runbook_help_generates_recoverable_state(self, weights: Weights) -> None:
        runbook = weights.commit_reveal_runbook_help(7, {0: 100, 1: 200}, version_key=9, salt="tempo-42", wait=True)
        assert runbook == {
            "netuid": 7,
            "normalized_weights": "0:100,1:200",
            "normalized_salt": "tempo-42",
            "salt_u16": [25972, 28781, 11631, 12852],
            "hash": weights.commit_reveal_payload_help({0: 100, 1: 200}, "tempo-42")["hash"],
            "status_command": "agcli weights status --netuid 7",
            "commit_command": "agcli weights commit --netuid 7 --weights 0:100,1:200 --salt tempo-42",
            "reveal_command": ("agcli weights reveal --netuid 7 --weights 0:100,1:200 --salt tempo-42 --version-key 9"),
            "commit_reveal_command": (
                "agcli weights commit-reveal --netuid 7 --weights 0:100,1:200 --version-key 9 --wait"
            ),
            "source": "generated_commit_reveal_state",
            "wait": True,
            "version_key": 9,
        }

    def test_commit_reveal_runbook_help_generates_random_salt_when_missing(self, weights: Weights) -> None:
        runbook = weights.commit_reveal_runbook_help(5, "0:100")
        assert runbook["netuid"] == 5
        assert runbook["normalized_weights"] == "0:100"
        assert isinstance(runbook["normalized_salt"], str)
        assert len(runbook["normalized_salt"]) == 32
        assert runbook["source"] == "generated_commit_reveal_state"
        assert runbook["wait"] is False
        assert runbook["commit_command"].endswith(f"--salt {runbook['normalized_salt']}")
        assert runbook["reveal_command"].endswith(f"--salt {runbook['normalized_salt']}")

    def test_save_and_load_commit_reveal_state_help_round_trip(self, weights: Weights, tmp_path: Path) -> None:
        path = tmp_path / "weights-state.json"
        saved = weights.save_commit_reveal_state_help(
            path,
            11,
            "0:100,1:200",
            "abc",
            version_key=4,
            source="manual_commit",
            wait=True,
        )
        assert saved["state_path"] == str(path)
        on_disk = json.loads(path.read_text(encoding="utf-8"))
        assert on_disk == saved
        loaded = weights.load_commit_reveal_state_help(path)
        assert loaded == saved

    def test_load_commit_reveal_state_help_recomputes_commands_after_version_override(
        self, weights: Weights, tmp_path: Path
    ) -> None:
        path = tmp_path / "weights-state.json"
        weights.save_commit_reveal_state_help(path, 3, "0:100", "abc", version_key=2)
        recovered = weights.recover_reveal_from_state_help(path, version_key=7)
        assert recovered["version_key"] == 7
        assert recovered["reveal_command"] == (
            "agcli weights reveal --netuid 3 --weights 0:100 --salt abc --version-key 7"
        )
        assert recovered["commit_command"] == "agcli weights commit --netuid 3 --weights 0:100 --salt abc"

    def test_load_commit_reveal_state_help_rejects_missing_file(self, weights: Weights, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="commit-reveal state file not found"):
            weights.load_commit_reveal_state_help(tmp_path / "missing.json")

    def test_load_commit_reveal_state_help_rejects_invalid_json(self, weights: Weights, tmp_path: Path) -> None:
        path = tmp_path / "weights-state.json"
        path.write_text("{not json}\n", encoding="utf-8")
        with pytest.raises(ValueError, match="invalid commit-reveal state JSON"):
            weights.load_commit_reveal_state_help(path)

    def test_load_commit_reveal_state_help_rejects_non_object_json(self, weights: Weights, tmp_path: Path) -> None:
        path = tmp_path / "weights-state.json"
        path.write_text("[]\n", encoding="utf-8")
        with pytest.raises(ValueError, match="commit-reveal state must be a JSON object"):
            weights.load_commit_reveal_state_help(path)

    def test_troubleshoot_unrevealed_commit_help_returns_saved_recovery_runbook(
        self, weights: Weights, tmp_path: Path
    ) -> None:
        path = tmp_path / "weights-state.json"
        weights.save_commit_reveal_state_help(path, 97, "0:100", "stuck-salt", version_key=6)
        helpers = weights.troubleshoot_unrevealed_commit_help(path, error="Custom error: 16")
        assert helpers["netuid"] == 97
        assert helpers["normalized_salt"] == "stuck-salt"
        assert helpers["reveal_command"] == (
            "agcli weights reveal --netuid 97 --weights 0:100 --salt stuck-salt --version-key 6"
        )
        assert helpers["likely_cause"] == "The runtime returned a generic reveal-side custom error."
        assert helpers["recovery_reason"] == (
            "A previous commit can still be revealed if its original weights and salt are preserved."
        )

    def test_operator_note_for_atomic_commit_reveal_help_mentions_saved_state(self, weights: Weights) -> None:
        note = weights.operator_note_for_atomic_commit_reveal_help(97, "0:100", version_key=6, salt="abc")
        assert note["operator_note"] == (
            "If atomic commit-reveal stalls after commit, keep this state record so the same commit can be "
            "revealed manually later."
        )
        assert note["reveal_command"] == ("agcli weights reveal --netuid 97 --weights 0:100 --salt abc --version-key 6")

    def test_save_commit_reveal_state_help_rejects_empty_path(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="state path cannot be empty"):
            weights.save_commit_reveal_state_help("   ", 1, "0:100", "abc")

    def test_save_commit_reveal_state_help_rejects_invalid_path_type(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="state path must be a string or Path"):
            weights.save_commit_reveal_state_help(123, 1, "0:100", "abc")  # type: ignore[arg-type]

    def test_load_commit_reveal_state_help_rejects_invalid_saved_version_key(
        self, weights: Weights, tmp_path: Path
    ) -> None:
        path = tmp_path / "weights-state.json"
        path.write_text(
            json.dumps({"netuid": 1, "normalized_weights": "0:100", "normalized_salt": "abc", "version_key": -1}),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.load_commit_reveal_state_help(path)

    def test_load_commit_reveal_state_help_rejects_invalid_saved_netuid(self, weights: Weights, tmp_path: Path) -> None:
        path = tmp_path / "weights-state.json"
        path.write_text(
            json.dumps({"netuid": 0, "normalized_weights": "0:100", "normalized_salt": "abc"}),
            encoding="utf-8",
        )
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.load_commit_reveal_state_help(path)

    def test_recover_reveal_from_state_help_reuses_saved_version_when_override_missing(
        self, weights: Weights, tmp_path: Path
    ) -> None:
        path = tmp_path / "weights-state.json"
        weights.save_commit_reveal_state_help(path, 3, "0:100", "abc", version_key=2)
        recovered = weights.recover_reveal_from_state_help(path)
        assert recovered["version_key"] == 2
        assert recovered["reveal_command"] == (
            "agcli weights reveal --netuid 3 --weights 0:100 --salt abc --version-key 2"
        )

    def test_commit_reveal_runbook_help_persists_state_when_path_is_provided(
        self, weights: Weights, tmp_path: Path
    ) -> None:
        path = tmp_path / "weights-state.json"
        record = weights.commit_reveal_runbook_help(1, "0:100", salt="abc", state_path=path)
        assert path.exists()
        assert record["state_path"] == str(path)
        assert json.loads(path.read_text(encoding="utf-8"))["normalized_salt"] == "abc"

    def test_create_commit_reveal_state_help_accepts_path_objects(self, weights: Weights, tmp_path: Path) -> None:
        path = tmp_path / "weights-state.json"
        record = weights.create_commit_reveal_state_help(1, "0:100", salt="abc", state_path=path)
        assert record["state_path"] == str(path)
        assert record["normalized_weights"] == "0:100"

    def test_load_commit_reveal_state_help_normalizes_saved_weights(self, weights: Weights, tmp_path: Path) -> None:
        path = tmp_path / "weights-state.json"
        path.write_text(
            json.dumps({"netuid": 4, "normalized_weights": {"1": "200", "0": "100"}, "normalized_salt": "abc"}),
            encoding="utf-8",
        )
        loaded = weights.load_commit_reveal_state_help(path)
        assert loaded["normalized_weights"] == "1:200,0:100"
        assert loaded["commit_command"] == "agcli weights commit --netuid 4 --weights 1:200,0:100 --salt abc"

    def test_troubleshoot_unrevealed_commit_help_without_error_keeps_recovery_fields(
        self, weights: Weights, tmp_path: Path
    ) -> None:
        path = tmp_path / "weights-state.json"
        weights.save_commit_reveal_state_help(path, 2, "0:100", "abc")
        helpers = weights.troubleshoot_unrevealed_commit_help(path)
        assert "likely_cause" not in helpers
        assert helpers["recovery_reason"] == (
            "A previous commit can still be revealed if its original weights and salt are preserved."
        )
        assert helpers["reveal_command"] == "agcli weights reveal --netuid 2 --weights 0:100 --salt abc"

    def test_mechanism_commit_runbook_help_returns_derived_hash_and_commands(self, weights: Weights) -> None:
        runbook = weights.mechanism_commit_runbook_help(1, 4, "0:100", "abc", version_key=7)
        expected_hash = hashlib.blake2b(
            (0).to_bytes(2, byteorder="little", signed=False)
            + (100).to_bytes(2, byteorder="little", signed=False)
            + b"abc",
            digest_size=32,
        ).hexdigest()
        assert runbook == {
            "normalized_weights": "0:100",
            "normalized_salt": "abc",
            "hash": f"0x{expected_hash}",
            "status": "agcli weights status --netuid 1",
            "commit_mechanism": (
                "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash 0x" + expected_hash
            ),
            "reveal_mechanism": (
                "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 7"
            ),
        }

    def test_timelocked_commit_runbook_help_returns_round_hash_and_reveal(self, weights: Weights) -> None:
        runbook = weights.timelocked_commit_runbook_help(1, "0:100", 42, "abc", version_key=7)
        expected_hash = hashlib.blake2b(
            (0).to_bytes(2, byteorder="little", signed=False)
            + (100).to_bytes(2, byteorder="little", signed=False)
            + b"abc",
            digest_size=32,
        ).hexdigest()
        assert runbook == {
            "normalized_weights": "0:100",
            "normalized_salt": "abc",
            "hash": f"0x{expected_hash}",
            "round": 42,
            "status": "agcli weights status --netuid 1",
            "commit_timelocked": ("agcli weights commit-timelocked --netuid 1 --weights 0:100 --round 42 --salt abc"),
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7",
        }

    def test_reveal_salt_help_returns_normalized_salt_and_u16_vector(self, weights: Weights) -> None:
        assert weights.reveal_salt_help("abc") == {"normalized_salt": "abc", "salt_u16": [25185, 99]}

    def test_drand_status_help_returns_status_and_normalized_round(self, weights: Weights) -> None:
        assert weights.drand_status_help(1, 42) == {"status": "agcli weights status --netuid 1", "round": 42}

    def test_mechanism_commit_hash_help_rejects_non_integer_weight_values(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights hash generation requires integer weight values"):
            weights.mechanism_commit_hash_help("0:1.5", "abc")

    def test_mechanism_commit_hash_help_rejects_file_marker_weights(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights hash generation requires explicit weights"):
            weights.mechanism_commit_hash_help("@weights.json", "abc")

    def test_mechanism_commit_hash_help_rejects_uid_out_of_range(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="uid out of range for weight hash generation: 70000"):
            weights.mechanism_commit_hash_help("70000:1", "abc")

    def test_mechanism_commit_hash_help_rejects_weight_out_of_range(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight value out of range for weight hash generation: 70000"):
            weights.mechanism_commit_hash_help("0:70000", "abc")

    def test_timelocked_reveal_payload_help_includes_round(self, weights: Weights) -> None:
        payload = weights.timelocked_reveal_payload_help("0:100", "abc", 42)
        assert payload["round"] == 42
        assert payload["salt_u16"] == [25185, 99]
        assert isinstance(payload["hash"], str)
        assert payload["hash"].startswith("0x")

    def test_timelocked_commit_hash_help_reuses_mechanism_hash_logic(self, weights: Weights) -> None:
        assert weights.timelocked_commit_hash_help("0:100", "abc") == weights.mechanism_commit_hash_help("0:100", "abc")

    def test_timelocked_workflow_help_keeps_round_without_salt(self, weights: Weights) -> None:
        helpers = weights.timelocked_workflow_help(3, "0:100", 7)
        assert helpers == {
            "normalized_weights": "0:100",
            "status": "agcli weights status --netuid 3",
            "set": "agcli weights set --netuid 3 --weights 0:100",
            "round": 7,
        }

    def test_timelocked_workflow_help_with_salt_returns_reveal_hash_and_round(self, weights: Weights) -> None:
        helpers = weights.timelocked_workflow_help(3, "0:100", 7, "abc", version_key=9)
        assert helpers["round"] == 7
        assert helpers["normalized_salt"] == "abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 3 --weights 0:100 --salt abc --version-key 9"
        assert isinstance(helpers["hash"], str)
        assert helpers["hash"].startswith("0x")
        assert helpers["commit_timelocked"] == (
            "agcli weights commit-timelocked --netuid 3 --weights 0:100 --round 7 --salt abc"
        )

    def test_timelocked_reveal_payload_help_rejects_invalid_round(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="round must be greater than or equal to 0"):
            weights.timelocked_reveal_payload_help("0:100", "abc", -1)

    def test_commit_reveal_payload_help_rejects_non_utf8_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt bytes must decode as UTF-8"):
            weights.commit_reveal_payload_help("0:100", b"\xff")

    def test_mechanism_commit_hash_help_rejects_boolean_weight_value(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight values must be numbers"):
            weights.mechanism_commit_hash_help({0: True}, "abc")

    def test_mechanism_commit_hash_help_rejects_boolean_uid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight uids must be integers"):
            weights.mechanism_commit_hash_help({True: 1}, "abc")

    def test_mechanism_commit_hash_help_rejects_empty_weights(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights cannot be empty"):
            weights.mechanism_commit_hash_help({}, "abc")

    def test_commit_reveal_payload_help_rejects_stdin_weights(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights hash generation requires explicit weights"):
            weights.commit_reveal_payload_help("-", "abc")

    def test_reveal_payload_help_reuses_commit_reveal_payload(self, weights: Weights) -> None:
        assert weights.reveal_payload_help("0:100", "abc") == weights.commit_reveal_payload_help("0:100", "abc")

    def test_mechanism_reveal_payload_help_reuses_commit_reveal_payload(self, weights: Weights) -> None:
        assert weights.mechanism_reveal_payload_help("0:100", "abc") == weights.commit_reveal_payload_help(
            "0:100", "abc"
        )

    def test_drand_round_help_rejects_invalid_round(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="round must be greater than or equal to 0"):
            weights.drand_round_help(-1)

    def test_reveal_salt_help_rejects_invalid_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.reveal_salt_help("   ")

    def test_mechanism_commit_runbook_help_rejects_non_explicit_weights(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights hash generation requires explicit weights"):
            weights.mechanism_commit_runbook_help(1, 4, "-", "abc")

    def test_timelocked_commit_runbook_help_rejects_invalid_round(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="round must be greater than or equal to 0"):
            weights.timelocked_commit_runbook_help(1, "0:100", -1, "abc")

    def test_mechanism_workflow_help_reuses_normalized_hash_input(self, weights: Weights) -> None:
        helpers = weights.mechanism_workflow_help(1, 4, "0:100", "abc", "11" * 32)
        assert helpers["hash"] == "11" * 32
        assert helpers["normalized_salt"] == "abc"
        assert helpers["commit_mechanism"] == (
            "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash " + "11" * 32
        )

    def test_drand_status_help_rejects_invalid_round(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="round must be greater than or equal to 0"):
            weights.drand_status_help(1, -1)

    def test_drand_status_help_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.drand_status_help(0, 7)

    def test_commit_reveal_payload_help_uses_explicit_normalized_salt_for_hash(self, weights: Weights) -> None:
        payload = weights.commit_reveal_payload_help("0:100", " abc ")
        expected = hashlib.blake2b(
            (0).to_bytes(2, byteorder="little", signed=False)
            + (100).to_bytes(2, byteorder="little", signed=False)
            + b"abc",
            digest_size=32,
        ).hexdigest()
        assert payload == {
            "normalized_weights": "0:100",
            "normalized_salt": "abc",
            "salt_u16": [25185, 99],
            "hash": f"0x{expected}",
        }

    def test_reveal_salt_help_accepts_bytes(self, weights: Weights) -> None:
        assert weights.reveal_salt_help(b"abc") == {"normalized_salt": "abc", "salt_u16": [25185, 99]}

    def test_commit_reveal_payload_help_rejects_non_integer_float_like_weight(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights hash generation requires integer weight values"):
            weights.commit_reveal_payload_help({0: 1.25}, "abc")

    def test_commit_reveal_payload_help_rejects_negative_weight(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight value out of range for weight hash generation: -1"):
            weights.commit_reveal_payload_help({0: -1}, "abc")

    def test_commit_reveal_payload_help_rejects_negative_uid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="uid out of range for weight hash generation: -1"):
            weights.commit_reveal_payload_help({-1: 1}, "abc")

    def test_mechanism_commit_hash_help_matches_expected_blake2b(self, weights: Weights) -> None:
        payload = weights.mechanism_commit_hash_help({1: 2, 3: 4}, "salt42")
        expected = hashlib.blake2b(digest_size=32)
        expected.update((1).to_bytes(2, byteorder="little", signed=False))
        expected.update((3).to_bytes(2, byteorder="little", signed=False))
        expected.update((2).to_bytes(2, byteorder="little", signed=False))
        expected.update((4).to_bytes(2, byteorder="little", signed=False))
        expected.update(b"salt42")
        assert payload == {
            "normalized_weights": "1:2,3:4",
            "normalized_salt": "salt42",
            "hash": f"0x{expected.hexdigest()}",
        }

    def test_commit_reveal_payload_help_accepts_bytes_salt(self, weights: Weights) -> None:
        payload = weights.commit_reveal_payload_help("0:100", b"abc")
        assert payload["normalized_salt"] == "abc"
        assert payload["salt_u16"] == [25185, 99]
        assert payload["hash"].startswith("0x")

    def test_workflow_help_returns_common_weight_helpers(self, weights: Weights) -> None:
        helpers = weights.workflow_help(1, " 0 : 100 , 1 : 200 ", b"abc", version_key=2, wait=True)
        assert helpers == {
            "normalized_weights": "0:100,1:200",
            "status": "agcli weights status --netuid 1",
            "set": "agcli weights set --netuid 1 --weights 0:100,1:200 --version-key 2",
            "commit_reveal": "agcli weights commit-reveal --netuid 1 --weights 0:100,1:200 --version-key 2 --wait",
            "commit": "agcli weights commit --netuid 1 --weights 0:100,1:200 --salt abc",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100,1:200 --salt abc --version-key 2",
        }

    def test_commit_reveal_flow_help_returns_normalized_helpers(self, weights: Weights) -> None:
        helpers = weights.commit_reveal_flow_help(1, " 0 : 100 , 1 : 200 ", b"abc", version_key=2)
        assert helpers == {
            "normalized_weights": "0:100,1:200",
            "commit": "agcli weights commit --netuid 1 --weights 0:100,1:200 --salt abc",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100,1:200 --salt abc --version-key 2",
            "status": "agcli weights status --netuid 1",
        }

    def test_commit_reveal_flow_help_is_subset_of_workflow_help(self, weights: Weights) -> None:
        workflow = weights.workflow_help(1, "0:100", "abc", version_key=2)
        flow = weights.commit_reveal_flow_help(1, "0:100", "abc", version_key=2)
        assert flow == {
            "normalized_weights": workflow["normalized_weights"],
            "commit": workflow["commit"],
            "reveal": workflow["reveal"],
            "status": workflow["status"],
        }

    def test_workflow_help_rejects_invalid_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.workflow_help(1, "0:100", "   ")

    def test_set_help_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.set_help(1, "0:100", version_key=-1)

    def test_commit_reveal_help_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.commit_reveal_help(1, "0:100", version_key=-1)

    def test_commit_reveal_help_accepts_file_marker(self, weights: Weights) -> None:
        command = weights.commit_reveal_help(1, "@weights.json", wait=True)
        assert command == "agcli weights commit-reveal --netuid 1 --weights @weights.json --wait"

    def test_workflow_help_accepts_json_weights(self, weights: Weights) -> None:
        helpers = weights.workflow_help(1, '{"0": 100}', "abc")
        assert helpers["normalized_weights"] == "0:100"
        assert helpers["set"] == "agcli weights set --netuid 1 --weights 0:100"
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc"
        assert helpers["status"] == "agcli weights status --netuid 1"

    def test_workflow_help_accepts_file_marker(self, weights: Weights) -> None:
        helpers = weights.workflow_help(1, "@weights.json", "abc", wait=True)
        assert helpers["normalized_weights"] == "@weights.json"
        assert helpers["set"] == "agcli weights set --netuid 1 --weights @weights.json"
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights @weights.json --wait"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights @weights.json --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights @weights.json --salt abc"
        assert helpers["status"] == "agcli weights status --netuid 1"

    def test_workflow_help_accepts_bytes_salt(self, weights: Weights) -> None:
        helpers = weights.workflow_help(1, "0:100", b"salt")
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt salt"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100 --salt salt"
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100"

    def test_workflow_help_reuses_normalized_weights(self, weights: Weights) -> None:
        helpers = weights.workflow_help(1, {"0": "100", "1": "200"}, "abc")
        assert helpers["normalized_weights"] == "0:100,1:200"
        assert "0:100,1:200" in helpers["set"]
        assert "0:100,1:200" in helpers["commit_reveal"]
        assert "0:100,1:200" in helpers["commit"]
        assert "0:100,1:200" in helpers["reveal"]

    def test_workflow_help_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.workflow_help(1, "0:100", "abc", version_key=-1)

    def test_workflow_help_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.workflow_help(0, "0:100", "abc")

    def test_workflow_help_preserves_wait_flag_when_false(self, weights: Weights) -> None:
        helpers = weights.workflow_help(1, "0:100", "abc", wait=False)
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100"

    def test_workflow_help_preserves_wait_flag_when_true(self, weights: Weights) -> None:
        helpers = weights.workflow_help(1, "0:100", "abc", wait=True)
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100 --wait"

    def test_commit_reveal_flow_help_rejects_invalid_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.commit_reveal_flow_help(1, "0:100", "   ")

    def test_commit_rejects_non_utf8_salt_bytes(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt bytes must decode as UTF-8"):
            weights.commit(1, "0:100", salt=b"\xff")

    def test_commit_rejects_empty_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.commit(1, "0:100", salt="   ")

    def test_commit_mechanism_accepts_hash_bytes(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_mechanism(1, 0, b"\x11" * 32)
        cmd = mock_subprocess.call_args[0][0]
        assert "0x" + "11" * 32 in cmd

    def test_commit_mechanism_rejects_invalid_hash_bytes_length(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="hash must be exactly 32 bytes, got 31 bytes"):
            weights.commit_mechanism(1, 0, b"\x11" * 31)

    def test_commit_mechanism_rejects_invalid_hash_hex(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="hash must be valid hex"):
            weights.commit_mechanism(1, 0, "xyz")

    def test_commit_timelocked_rejects_invalid_round(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="round must be greater than or equal to 0"):
            weights.commit_timelocked(1, "0:100", -1)

    def test_set_mechanism_rejects_invalid_mechanism_id(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="mechanism_id must be greater than or equal to 0"):
            weights.set_mechanism(1, -1, "0:100")

    def test_set_mechanism_rejects_boolean_mechanism_id(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="mechanism_id must be an integer"):
            weights.set_mechanism(1, True, "0:100")

    def test_reveal_accepts_salt_bytes(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal(1, "0:100", b"abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "--salt" in cmd and "abc" in cmd

    def test_commit_accepts_salt_bytes(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit(1, "0:100", salt=b"abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "--salt" in cmd and "abc" in cmd

    def test_commit_timelocked_accepts_salt_bytes(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_timelocked(1, "0:100", 42, salt=b"abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "--salt" in cmd and "abc" in cmd

    def test_reveal_mechanism_accepts_salt_bytes(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal_mechanism(1, 0, "0:100", b"abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "--salt" in cmd and "abc" in cmd

    def test_show_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.show(0)

    def test_status_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.status(0)

    def test_show_rejects_boolean_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be an integer"):
            weights.show(True)

    def test_status_rejects_boolean_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be an integer"):
            weights.status(True)

    def test_show_normalizes_netuid(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.show(1)
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[cmd.index("--netuid") + 1] == "1"

    def test_status_normalizes_netuid(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.status(1)
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[cmd.index("--netuid") + 1] == "1"

    def test_reveal_help_rejects_invalid_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.reveal_help(1, "0:100", "   ")

    def test_status_help_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.status_help(0)

    def test_set_preserves_order_from_json_list(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, '[{"uid": 2, "weight": 5}, {"uid": 1, "weight": 7}]')
        cmd = mock_subprocess.call_args[0][0]
        assert "2:5,1:7" in cmd

    def test_set_rejects_duplicate_uids_in_json_string(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="duplicate uid in weights: 0"):
            weights.set(1, '[{"uid": 0, "weight": 1}, {"uid": 0, "weight": 2}]')

    def test_set_rejects_missing_uid_in_json_string(self, weights: Weights) -> None:
        with pytest.raises(
            ValueError,
            match=r"weights entries must be \(uid, value\) pairs|weight uids must be integers",
        ):
            weights.set(1, '[{"weight": 1}]')

    def test_set_rejects_missing_weight_in_json_string(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight values must be numbers"):
            weights.set(1, '[{"uid": 0}]')

    def test_set_rejects_empty_file_marker(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights cannot be empty"):
            weights.set(1, "   ")

    def test_commit_reveal_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.commit_reveal(1, "0:100", version_key=-1)

    def test_reveal_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.reveal(1, "0:100", "abc", version_key=-1)

    def test_set_mechanism_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.set_mechanism(1, 0, "0:100", version_key=-1)

    def test_reveal_mechanism_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.reveal_mechanism(1, 0, "0:100", "abc", version_key=-1)

    def test_reveal_rejects_empty_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.reveal(1, "0:100", "   ")

    def test_reveal_mechanism_rejects_empty_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.reveal_mechanism(1, 0, "0:100", "   ")

    def test_commit_timelocked_rejects_empty_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.commit_timelocked(1, "0:100", 1, salt="   ")

    def test_commit_mechanism_rejects_empty_hash(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="hash cannot be empty"):
            weights.commit_mechanism(1, 0, "   ")

    def test_commit_mechanism_rejects_short_hash_hex(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="hash must be exactly 32 bytes, got 2 bytes"):
            weights.commit_mechanism(1, 0, "0x1111")

    def test_commit_help_accepts_json_weights(self, weights: Weights) -> None:
        command = weights.commit_help(1, '{"0": 100}', "abc")
        assert command == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"

    def test_reveal_help_accepts_json_weights(self, weights: Weights) -> None:
        command = weights.reveal_help(1, '{"0": 100}', "abc")
        assert command == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc"

    def test_status_help_normalizes_netuid(self, weights: Weights) -> None:
        assert weights.status_help(5) == "agcli weights status --netuid 5"

    def test_show_accepts_file_weights_not_applicable(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.show(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "show" in cmd

    def test_set_accepts_json_mapping_string_with_spaces(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, ' { "0" : 100 , "1" : 200 } ')
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200" in cmd

    def test_set_accepts_json_list_string_with_spaces(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, ' [ { "uid" : 0 , "weight" : 100 } ] ')
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd

    def test_commit_reveal_accepts_json_weights(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_reveal(1, '{"0": 100}', wait=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd and "--wait" in cmd

    def test_set_mechanism_accepts_json_weights(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set_mechanism(1, 0, '{"0": 100}')
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd and "--mechanism-id" in cmd

    def test_reveal_mechanism_accepts_json_weights(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal_mechanism(1, 0, '{"0": 100}', "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd and "--salt" in cmd

    def test_commit_timelocked_accepts_json_weights(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_timelocked(1, '{"0": 100}', 42)
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd and "--round" in cmd

    def test_commit_accepts_json_weights(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit(1, '{"0": 100}', salt="abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd and "--salt" in cmd

    def test_reveal_accepts_json_weights(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal(1, '{"0": 100}', "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd and "--salt" in cmd

    def test_set_rejects_non_object_json_scalar(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights entries must use uid:value format"):
            weights.set(1, "123")

    def test_set_rejects_invalid_json_array_entry_shape(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=r"JSON weights must be an object map or array of \{uid, weight\} entries"):
            weights.set(1, '[{"uid": 0, "weight": 1}, 2]')

    def test_commit_mechanism_accepts_plain_hex_without_prefix(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_mechanism(1, 0, "11" * 32)
        cmd = mock_subprocess.call_args[0][0]
        assert "11" * 32 in cmd

    def test_commit_mechanism_rejects_invalid_mechanism_id(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="mechanism_id must be greater than or equal to 0"):
            weights.commit_mechanism(1, -1, "11" * 32)

    def test_commit_mechanism_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.commit_mechanism(0, 0, "11" * 32)

    def test_commit_timelocked_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.commit_timelocked(0, "0:100", 1)

    def test_reveal_mechanism_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.reveal_mechanism(0, 0, "0:100", "abc")

    def test_set_mechanism_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.set_mechanism(0, 0, "0:100")

    def test_commit_reveal_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.commit_reveal(0, "0:100")

    def test_reveal_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.reveal(0, "0:100", "abc")

    def test_commit_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.commit(0, "0:100")

    def test_set_accepts_json_map_stringified_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, '{"0": "100", "1": "200"}')
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100,1:200" in cmd

    def test_set_rejects_json_map_non_numeric_value(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight values must be numbers"):
            weights.set(1, '{"0": "abc"}')

    def test_set_rejects_json_map_non_numeric_uid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight uids must be integers"):
            weights.set(1, '{"abc": 1}')

    def test_commit_help_accepts_bytes_salt(self, weights: Weights) -> None:
        command = weights.commit_help(1, "0:100", b"salt")
        assert command == "agcli weights commit --netuid 1 --weights 0:100 --salt salt"

    def test_reveal_help_accepts_bytes_salt(self, weights: Weights) -> None:
        command = weights.reveal_help(1, "0:100", b"salt")
        assert command == "agcli weights reveal --netuid 1 --weights 0:100 --salt salt"

    def test_commit_timelocked_rejects_boolean_round(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="round must be an integer"):
            weights.commit_timelocked(1, "0:100", True)

    def test_commit_reveal_accepts_file_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_reveal(1, "@weights.json")
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_commit_accepts_file_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit(1, "@weights.json")
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_reveal_accepts_file_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal(1, "@weights.json", "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_commit_timelocked_accepts_file_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_timelocked(1, "@weights.json", 42)
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_set_mechanism_accepts_file_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set_mechanism(1, 0, "@weights.json")
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_reveal_mechanism_accepts_file_marker(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal_mechanism(1, 0, "@weights.json", "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_set_accepts_stdin_marker_with_spaces(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, "  -  ")
        cmd = mock_subprocess.call_args[0][0]
        assert "-" in cmd

    def test_set_accepts_file_marker_with_spaces(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, "  @weights.json  ")
        cmd = mock_subprocess.call_args[0][0]
        assert "@weights.json" in cmd

    def test_commit_mechanism_rejects_boolean_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be an integer"):
            weights.commit_mechanism(True, 0, "11" * 32)

    def test_commit_mechanism_rejects_boolean_mechanism_id(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="mechanism_id must be an integer"):
            weights.commit_mechanism(1, True, "11" * 32)

    def test_reveal_mechanism_rejects_boolean_mechanism_id(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="mechanism_id must be an integer"):
            weights.reveal_mechanism(1, True, "0:100", "abc")

    def test_set_mechanism_accepts_stringified_numeric_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set_mechanism(1, 0, {"0": "100"})
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd

    def test_reveal_mechanism_accepts_stringified_numeric_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal_mechanism(1, 0, {"0": "100"}, "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd

    def test_commit_timelocked_accepts_stringified_numeric_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_timelocked(1, {"0": "100"}, 42)
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd

    def test_commit_accepts_stringified_numeric_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit(1, {"0": "100"})
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd

    def test_reveal_accepts_stringified_numeric_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal(1, {"0": "100"}, "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd

    def test_commit_reveal_accepts_stringified_numeric_values(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_reveal(1, {"0": "100"})
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd

    def test_show_with_options_keeps_flags(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.show(1, hotkey_address="5G...", limit=3)
        cmd = mock_subprocess.call_args[0][0]
        assert cmd[cmd.index("--limit") + 1] == "3"

    def test_status_help_returns_normalized_string(self, weights: Weights) -> None:
        assert weights.status_help(1) == "agcli weights status --netuid 1"

    def test_commit_help_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.commit_help(0, "0:100")

    def test_reveal_help_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.reveal_help(0, "0:100", "abc")

    def test_commit_help_rejects_invalid_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.commit_help(1, "0:100", "   ")

    def test_reveal_help_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.reveal_help(1, "0:100", "abc", version_key=-1)

    def test_commit_reveal_flow_help_rejects_invalid_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be greater than 0"):
            weights.commit_reveal_flow_help(0, "0:100", "abc")

    def test_commit_reveal_flow_help_rejects_invalid_version_key(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="version_key must be greater than or equal to 0"):
            weights.commit_reveal_flow_help(1, "0:100", "abc", version_key=-1)

    def test_commit_reveal_flow_help_accepts_json_weights(self, weights: Weights) -> None:
        helpers = weights.commit_reveal_flow_help(1, '{"0": 100}', "abc")
        assert helpers["normalized_weights"] == "0:100"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc"
        assert helpers["status"] == "agcli weights status --netuid 1"

    def test_commit_reveal_flow_help_accepts_file_marker(self, weights: Weights) -> None:
        helpers = weights.commit_reveal_flow_help(1, "@weights.json", "abc")
        assert helpers["normalized_weights"] == "@weights.json"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights @weights.json --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights @weights.json --salt abc"
        assert helpers["status"] == "agcli weights status --netuid 1"

    def test_commit_reveal_flow_help_accepts_bytes_salt(self, weights: Weights) -> None:
        helpers = weights.commit_reveal_flow_help(1, "0:100", b"salt")
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt salt"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100 --salt salt"

    def test_commit_reveal_flow_help_reuses_normalized_weights(self, weights: Weights) -> None:
        helpers = weights.commit_reveal_flow_help(1, {"0": "100", "1": "200"}, "abc")
        assert helpers["normalized_weights"] == "0:100,1:200"
        assert "0:100,1:200" in helpers["commit"]
        assert "0:100,1:200" in helpers["reveal"]

    def test_mechanism_workflow_help_rejects_invalid_salt(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="salt cannot be empty"):
            weights.mechanism_workflow_help(1, 4, "0:100", "   ")

    def test_mechanism_workflow_help_rejects_invalid_hash(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="hash must be valid hex"):
            weights.mechanism_workflow_help(1, 4, "0:100", "abc", "xyz")

    def test_timelocked_workflow_help_rejects_invalid_round(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="round must be greater than or equal to 0"):
            weights.timelocked_workflow_help(1, "0:100", -1)

    def test_troubleshoot_mechanism_help_includes_live_reveal_guidance(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_mechanism_help(
            1,
            4,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            hash_value="11" * 32,
            version_key=7,
            status={
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                        "blocks_until_action": 5,
                    }
                ],
            },
        )
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending mechanism commit is ready to reveal now."
        assert helpers["normalized_hash"] == "11" * 32
        assert helpers["commit_mechanism"] == (
            "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash " + "11" * 32
        )

    def test_troubleshoot_mechanism_help_derives_hash_from_weights_and_salt(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_mechanism_help(
            1,
            4,
            "NoWeightsCommitFound",
            "0:100",
            salt="abc",
            status={
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [],
            },
        )
        assert helpers["normalized_hash"] == "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339"
        assert helpers["commit_mechanism"] == (
            "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash "
            "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339"
        )
        assert helpers["recommended_command"] == (
            "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash "
            "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339"
        )
        assert helpers["reason"] == "No mechanism commit is pending and this subnet uses commit-reveal."
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["normalized_weights"] == "0:100"

    def test_next_mechanism_action_help_recommends_commit_when_no_pending_commit(self, weights: Weights) -> None:
        helpers = weights.next_mechanism_action_help(
            3,
            4,
            {
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [],
            },
            "0:100",
            hash_value="11" * 32,
            version_key=9,
        )
        assert helpers == {
            "status": "agcli weights status --netuid 3",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
            "recommended_action": "NO_PENDING_COMMITS",
            "recommended_command": ("agcli weights commit-mechanism --netuid 3 --mechanism-id 4 --hash " + "11" * 32),
            "reason": "No mechanism commit is pending and this subnet uses commit-reveal.",
            "normalized_weights": "0:100",
            "normalized_hash": "11" * 32,
        }

    def test_troubleshoot_timelocked_help_includes_live_recommit_guidance(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_timelocked_help(
            7,
            "ExpiredWeightCommit",
            "0:100",
            round=42,
            salt="abc",
            version_key=8,
            status={
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [{"commit_block": 100, "first_reveal": 110, "last_reveal": 130, "status": "EXPIRED"}],
            },
        )
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == (
            "agcli weights commit-timelocked --netuid 7 --weights 0:100 --round 42 --salt abc"
        )
        assert helpers["reason"] == (
            "A previous pending timelocked commit expired, so a fresh timelocked commit is required."
        )
        assert helpers["round"] == 42
        assert helpers["commit_timelocked"] == (
            "agcli weights commit-timelocked --netuid 7 --weights 0:100 --round 42 --salt abc"
        )

    def test_next_timelocked_action_help_recommends_set_when_commit_reveal_disabled(self, weights: Weights) -> None:
        helpers = weights.next_timelocked_action_help(
            4,
            {
                "block": 200,
                "commit_reveal_enabled": False,
                "reveal_period_epochs": 0,
                "commits": [],
            },
            {0: 100},
            round=42,
            version_key=2,
        )
        assert helpers == {
            "status": "agcli weights status --netuid 4",
            "status_summary": {
                "current_block": 200,
                "commit_reveal_enabled": False,
                "reveal_period_epochs": 0,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
            "recommended_action": "NO_PENDING_COMMITS",
            "recommended_command": "agcli weights set --netuid 4 --weights 0:100 --version-key 2",
            "reason": "No timelocked commit is pending and direct weight setting is available.",
            "normalized_weights": "0:100",
            "round": 42,
        }

    def test_troubleshoot_help_returns_guidance_for_validator_permit_errors(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_help(
            1,
            "NeuronNoValidatorPermit",
            {"0": "100", "1": "200"},
            salt="tempo-12",
            version_key=9,
        )
        assert helpers == {
            "error": "NeuronNoValidatorPermit",
            "likely_cause": "The hotkey is not currently allowed to set weights on this subnet.",
            "next_step": "Check validator permit, stake, and subnet validator settings before retrying.",
            "status": "agcli weights status --netuid 1",
            "normalized_weights": "0:100,1:200",
            "set": "agcli weights set --netuid 1 --weights 0:100,1:200 --version-key 9",
            "commit": "agcli weights commit --netuid 1 --weights 0:100,1:200 --salt tempo-12",
            "reveal": "agcli weights reveal --netuid 1 --weights 0:100,1:200 --salt tempo-12 --version-key 9",
            "commit_reveal": "agcli weights commit-reveal --netuid 1 --weights 0:100,1:200 --version-key 9",
        }

    def test_troubleshoot_help_returns_generic_guidance_without_weights(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_help(3, "unexpected runtime error")
        assert helpers == {
            "error": "unexpected runtime error",
            "likely_cause": "The runtime returned an unrecognized weights error.",
            "next_step": (
                "Check weights status, confirm netuid and payload inputs, then retry with the "
                "normalized command preview."
            ),
            "status": "agcli weights status --netuid 3",
        }

    def test_troubleshoot_help_handles_custom_error_16(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_help(1, "Custom error: 16", "0:100", salt="abc", version_key=2)
        assert helpers["likely_cause"] == "The runtime returned a generic reveal-side custom error."
        assert helpers["next_step"] == (
            "Check pending commits, reveal timing, and that weights, salt, and version_key match the commit."
        )
        assert helpers["normalized_weights"] == "0:100"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"
        assert helpers["reveal"] == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 2"

    def test_troubleshoot_help_rejects_empty_error(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="error cannot be empty"):
            weights.troubleshoot_help(1, "   ")

    def test_troubleshoot_help_rejects_non_string_error(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="error must be a string"):
            weights.troubleshoot_help(1, 16)  # type: ignore[arg-type]

    def test_troubleshoot_help_includes_status_summary_when_status_is_provided(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_help(
            1,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            version_key=7,
            status={
                "block": 100,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 2,
                "commits": [
                    {
                        "hash": "0x" + "11" * 32,
                        "commit_block": 90,
                        "first_reveal": 110,
                        "last_reveal": 120,
                        "status": "WAITING (10 blocks until reveal window)",
                        "blocks_until_action": 10,
                    }
                ],
            },
        )
        assert helpers["status_summary"] == {
            "current_block": 100,
            "commit_reveal_enabled": True,
            "reveal_period_epochs": 2,
            "pending_commits": 1,
            "pending_statuses": ["WAITING (10 blocks until reveal window)"],
            "next_action": "WAIT",
            "commit_windows": [
                {
                    "index": 1,
                    "status": "WAITING (10 blocks until reveal window)",
                    "commit_block": 90,
                    "first_reveal": 110,
                    "last_reveal": 120,
                    "blocks_until_action": 10,
                    "hash": "0x" + "11" * 32,
                }
            ],
        }
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 1"
        assert helpers["reason"] == "A pending commit exists but the reveal window is not open yet."

    def test_troubleshoot_help_includes_reveal_recommendation_when_status_is_ready(self, weights: Weights) -> None:
        helpers = weights.troubleshoot_help(
            1,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            version_key=7,
            status={
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                        "blocks_until_action": 5,
                    }
                ],
            },
        )
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending commit is ready to reveal now."

    def test_status_text_next_action_help_recommends_reveal_for_ready_text(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(5, READY_STATUS_TEXT, "0:100", salt="abc", version_key=7)
        assert helpers["raw_status"] == READY_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "REVEAL"
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 5 --weights 0:100 --salt abc --version-key 7"
        )

    def test_status_text_troubleshoot_help_returns_guidance(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(
            8,
            WAITING_STATUS_TEXT,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            version_key=7,
        )
        assert helpers["status_summary"]["next_action"] == "WAIT"
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 8"
        assert helpers["reason"] == "A pending commit exists but the reveal window is not open yet."

    def test_status_text_next_action_help_recommends_commit_reveal_for_no_pending_text(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(
            7,
            NO_PENDING_STATUS_TEXT,
            "0:100",
            version_key=9,
            wait=True,
        )
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == (
            "agcli weights commit-reveal --netuid 7 --weights 0:100 --version-key 9 --wait"
        )

    def test_status_text_next_action_help_recommends_set_for_direct_set_text(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(4, DIRECT_SET_STATUS_TEXT, "0:100", version_key=2)
        assert helpers["status_summary"]["commit_reveal_enabled"] is False
        assert helpers["recommended_command"] == "agcli weights set --netuid 4 --weights 0:100 --version-key 2"

    def test_status_text_next_mechanism_action_help_recommends_commit(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(
            7,
            4,
            NO_PENDING_STATUS_TEXT,
            "0:100",
            hash_value="11" * 32,
        )
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == (
            "agcli weights commit-mechanism --netuid 7 --mechanism-id 4 --hash " + "11" * 32
        )

    def test_status_text_troubleshoot_mechanism_help_reuses_text_summary(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_mechanism_help(
            5,
            4,
            READY_STATUS_TEXT,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            hash_value="11" * 32,
            version_key=7,
        )
        assert helpers["status_summary"]["next_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal-mechanism --netuid 5 --mechanism-id 4 --weights 0:100 --salt abc --version-key 7"
        )

    def test_status_text_next_timelocked_action_help_recommends_recommit(self, weights: Weights) -> None:
        helpers = weights.status_text_next_timelocked_action_help(
            9,
            EXPIRED_STATUS_TEXT,
            "0:100",
            round=42,
            salt="abc",
        )
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == (
            "agcli weights commit-timelocked --netuid 9 --weights 0:100 --round 42 --salt abc"
        )

    def test_status_text_troubleshoot_timelocked_help_reuses_text_summary(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_timelocked_help(
            9,
            EXPIRED_STATUS_TEXT,
            "ExpiredWeightCommit",
            "0:100",
            round=42,
            salt="abc",
        )
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"
        assert helpers["recommended_action"] == "RECOMMIT"
        assert (
            helpers["reason"]
            == "A previous pending timelocked commit expired, so a fresh timelocked commit is required."
        )

    def test_status_text_troubleshoot_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_troubleshoot_help(1, BAD_STATUS_TEXT, "RevealTooEarly")

    def test_status_text_next_action_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_next_action_help(1, BAD_STATUS_TEXT)

    def test_status_text_next_mechanism_action_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_next_mechanism_action_help(1, 0, BAD_STATUS_TEXT)

    def test_status_text_next_timelocked_action_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_next_timelocked_action_help(1, BAD_STATUS_TEXT)

    def test_status_text_troubleshoot_mechanism_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_troubleshoot_mechanism_help(1, 0, BAD_STATUS_TEXT, "RevealTooEarly")

    def test_status_text_troubleshoot_timelocked_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_troubleshoot_timelocked_help(1, BAD_STATUS_TEXT, "RevealTooEarly")

    def test_status_summary_text_fetches_and_parses_raw_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        summary = weights.status_summary_text(5)
        assert summary["status"] == "agcli weights status --netuid 5"
        assert summary["next_action"] == "REVEAL"

    def test_status_runbook_fetches_raw_text_and_summary(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        runbook = weights.status_runbook(7)
        assert runbook["status"] == "agcli weights status --netuid 7"
        assert runbook["raw_status"] == NO_PENDING_STATUS_TEXT.strip()
        assert runbook["summary"]["next_action"] == "NO_PENDING_COMMITS"

    def test_status_runbook_json_fetches_json_status_and_summary(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        runbook = weights.status_runbook_json(7)
        assert runbook == {
            "status": "agcli weights status --netuid 7",
            "raw_status": {
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [],
            },
            "summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
        }

    def test_status_runbook_json_rejects_non_mapping_status_output(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout="[1, 2, 3]")
        with pytest.raises(ValueError, match=NON_MAPPING_STATUS_ERROR):
            weights.status_runbook_json(7)

    def test_status_text_fetches_raw_output(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        assert weights.status_text(5) == READY_STATUS_TEXT.strip()
        cmd = mock_subprocess.call_args[0][0]
        assert "weights" in cmd and "status" in cmd and "5" in cmd

    def test_next_action_text_fetches_raw_status_and_recommends_action(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        helpers = weights.next_action_text(5, "0:100", salt="abc", version_key=7)
        assert helpers["raw_status"] == READY_STATUS_TEXT.strip()
        assert helpers["recommended_action"] == "REVEAL"

    def test_troubleshoot_text_fetches_raw_status_and_recommends_action(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=WAITING_STATUS_TEXT)
        helpers = weights.troubleshoot_text(8, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers["status_summary"]["next_action"] == "WAIT"
        assert helpers["recommended_action"] == "WAIT"

    def test_next_mechanism_action_text_fetches_raw_status_and_recommends_action(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.next_mechanism_action_text(7, 4, "0:100", hash_value="11" * 32)
        assert helpers["raw_status"] == NO_PENDING_STATUS_TEXT.strip()
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"

    def test_troubleshoot_mechanism_text_fetches_raw_status_and_recommends_action(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        helpers = weights.troubleshoot_mechanism_text(
            5,
            4,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            hash_value="11" * 32,
            version_key=7,
        )
        assert helpers["status_summary"]["next_action"] == "REVEAL"
        assert helpers["recommended_action"] == "REVEAL"

    def test_next_timelocked_action_text_fetches_raw_status_and_recommends_action(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.next_timelocked_action_text(9, "0:100", round=42, salt="abc")
        assert helpers["raw_status"] == EXPIRED_STATUS_TEXT.strip()
        assert helpers["recommended_action"] == "RECOMMIT"

    def test_troubleshoot_timelocked_text_fetches_raw_status_and_recommends_action(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.troubleshoot_timelocked_text(9, "ExpiredWeightCommit", "0:100", round=42, salt="abc")
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"
        assert helpers["recommended_action"] == "RECOMMIT"

    def test_diagnose_text_fetches_raw_status_and_summary(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_text(9, "ExpiredWeightCommit")
        assert helpers["raw_status"] == EXPIRED_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"
        assert helpers["recommended_action"] == "RECOMMIT"

    def test_diagnose_text_includes_status_command(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_text(9, "ExpiredWeightCommit")
        assert helpers["status"] == "agcli weights status --netuid 9"

    def test_diagnose_text_preserves_error_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_text(9, "ExpiredWeightCommit")
        assert helpers["likely_cause"] == "The previous commit expired before it was revealed."
        assert helpers["next_step"] == "Commit again, then reveal inside the next valid reveal window."

    def test_diagnose_text_without_payload_inputs_keeps_status_command(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=WAITING_STATUS_TEXT)
        helpers = weights.diagnose_text(8, "RevealTooEarly")
        assert helpers["recommended_command"] == "agcli weights status --netuid 8"
        assert helpers["recommended_action"] == "WAIT"

    def test_diagnose_text_parses_waiting_status_text(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=WAITING_STATUS_TEXT)
        helpers = weights.diagnose_text(8, "RevealTooEarly")
        assert helpers["status_summary"]["next_action"] == "WAIT"
        assert helpers["status_summary"]["commit_windows"][0]["blocks_until_action"] == 10

    def test_diagnose_text_reuses_stripped_raw_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_text(9, "ExpiredWeightCommit")
        assert helpers["raw_status"].endswith("EXPIRED")
        assert not helpers["raw_status"].endswith("EXPIRED\n")

    def test_diagnose_text_handles_no_pending_commits_text(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.diagnose_text(7, "NoWeightsCommitFound")
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"

    def test_diagnose_text_handles_direct_set_status_text(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=DIRECT_SET_STATUS_TEXT)
        helpers = weights.diagnose_text(4, "SettingWeightsTooFast")
        assert helpers["status_summary"]["commit_reveal_enabled"] is False
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"

    def test_diagnose_text_rejects_unrecognized_status_text(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=BAD_STATUS_TEXT)
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.diagnose_text(5, "RevealTooEarly")

    def test_diagnose_text_uses_raw_runner_path(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        weights.diagnose_text(9, "ExpiredWeightCommit")
        cmd = mock_subprocess.call_args[0][0]
        assert "weights" in cmd and "status" in cmd and "9" in cmd
        assert "--output" not in cmd

    def test_diagnose_mechanism_text_fetches_raw_status_and_summary(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.diagnose_mechanism_text(7, 4, "NoWeightsCommitFound", "0:100", hash_value="11" * 32)
        assert helpers["raw_status"] == NO_PENDING_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"

    def test_diagnose_mechanism_text_preserves_hash_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.diagnose_mechanism_text(7, 4, "NoWeightsCommitFound", "0:100", hash_value="11" * 32)
        assert helpers["normalized_hash"] == "11" * 32
        assert "commit-mechanism" in helpers["recommended_command"]

    def test_diagnose_mechanism_text_rejects_unrecognized_status_text(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=BAD_STATUS_TEXT)
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.diagnose_mechanism_text(5, 4, "RevealTooEarly")

    def test_diagnose_timelocked_text_fetches_raw_status_and_summary(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_timelocked_text(9, "ExpiredWeightCommit", "0:100", round=42, salt="abc")
        assert helpers["raw_status"] == EXPIRED_STATUS_TEXT.strip()
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"
        assert helpers["recommended_action"] == "RECOMMIT"

    def test_diagnose_timelocked_text_preserves_round(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_timelocked_text(9, "ExpiredWeightCommit", "0:100", round=42, salt="abc")
        assert helpers["round"] == 42

    def test_diagnose_timelocked_text_rejects_unrecognized_status_text(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=BAD_STATUS_TEXT)
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.diagnose_timelocked_text(5, "RevealTooEarly")

    def test_diagnose_timelocked_text_without_round_uses_status_command(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_timelocked_text(9, "ExpiredWeightCommit")
        assert helpers["recommended_command"] == "agcli weights status --netuid 9"

    def test_diagnose_mechanism_text_without_hash_uses_status_command(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.diagnose_mechanism_text(7, 4, "NoWeightsCommitFound")
        assert helpers["recommended_command"] == "agcli weights status --netuid 7"

    def test_diagnose_text_handles_ready_status_text(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        helpers = weights.diagnose_text(5, "RevealTooEarly")
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == "agcli weights status --netuid 5"

    def test_diagnose_mechanism_text_handles_ready_status_text(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        helpers = weights.diagnose_mechanism_text(5, 4, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers["recommended_action"] == "REVEAL"
        assert "reveal-mechanism" in helpers["recommended_command"]

    def test_diagnose_timelocked_text_handles_ready_status_text(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        helpers = weights.diagnose_timelocked_text(5, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers["recommended_action"] == "REVEAL"
        assert "reveal" in helpers["recommended_command"]

    def test_diagnose_text_handles_no_pending_direct_set_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=DIRECT_SET_STATUS_TEXT)
        helpers = weights.diagnose_text(4, "SettingWeightsTooFast")
        assert helpers["reason"] == "No commit is pending and direct weight setting is available."

    def test_diagnose_mechanism_text_handles_no_pending_without_hash(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.diagnose_mechanism_text(7, 4, "NoWeightsCommitFound")
        assert helpers["reason"] == (
            "No mechanism commit is pending and this subnet uses commit-reveal; "
            "provide the precomputed mechanism hash to build the commit command."
        )

    def test_diagnose_timelocked_text_handles_no_pending_without_round(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.diagnose_timelocked_text(7, "NoWeightsCommitFound")
        assert helpers["reason"] == (
            "No timelocked commit is pending and this subnet uses commit-reveal; "
            "provide weights and a drand round to build the next commit command."
        )

    def test_status_text_parsing_accepts_trailing_whitespace(self, weights: Weights) -> None:
        summary = weights.status_text_help(READY_STATUS_TEXT + "\n\n")
        assert summary["next_action"] == "REVEAL"

    def test_status_text_parsing_handles_expired_text(self, weights: Weights) -> None:
        summary = weights.status_text_help(EXPIRED_STATUS_TEXT)
        assert summary["next_action"] == "RECOMMIT"
        assert summary["commit_windows"][0]["hash"] == "0x5656"

    def test_status_text_parsing_handles_waiting_text(self, weights: Weights) -> None:
        summary = weights.status_text_help(WAITING_STATUS_TEXT)
        assert summary["next_action"] == "WAIT"
        assert summary["commit_windows"][0]["blocks_until_action"] == 10

    def test_status_text_parsing_handles_disabled_commit_reveal(self, weights: Weights) -> None:
        summary = weights.status_text_help(DIRECT_SET_STATUS_TEXT)
        assert summary["commit_reveal_enabled"] is False
        assert summary["next_action"] == "NO_PENDING_COMMITS"

    def test_status_summary_help_accepts_text_with_whitespace(self, weights: Weights) -> None:
        summary = weights.status_summary_help("\n" + NO_PENDING_STATUS_TEXT + "\n")
        assert summary["next_action"] == "NO_PENDING_COMMITS"

    def test_status_runbook_help_accepts_mapping_input(self, weights: Weights) -> None:
        runbook = weights.status_runbook_help(
            3,
            {
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [],
            },
        )
        assert runbook["status"] == "agcli weights status --netuid 3"
        assert runbook["summary"]["next_action"] == "NO_PENDING_COMMITS"

    def test_status_text_troubleshoot_help_preserves_likely_cause(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(9, EXPIRED_STATUS_TEXT, "ExpiredWeightCommit")
        assert helpers["likely_cause"] == "The previous commit expired before it was revealed."
        assert helpers["next_step"] == "Commit again, then reveal inside the next valid reveal window."

    def test_status_text_next_action_help_includes_normalized_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(7, NO_PENDING_STATUS_TEXT, {0: 100}, wait=True)
        assert helpers["normalized_weights"] == "0:100"

    def test_status_text_next_mechanism_action_help_derives_hash_from_weights_and_salt(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(7, 4, NO_PENDING_STATUS_TEXT, "0:100", salt="abc")
        assert helpers["normalized_hash"].startswith("0x")
        assert "commit-mechanism" in helpers["recommended_command"]

    def test_status_text_next_timelocked_action_help_requires_round_for_recommit_command(
        self, weights: Weights
    ) -> None:
        helpers = weights.status_text_next_timelocked_action_help(9, EXPIRED_STATUS_TEXT, "0:100", salt="abc")
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 9"
        assert helpers["reason"] == (
            "A previous pending timelocked commit expired, so fresh weights and a drand round "
            "are required before retrying."
        )

    def test_status_text_runbook_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_runbook_help(1, BAD_STATUS_TEXT)

    def test_status_runbook_help_rejects_unrecognized_text(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_runbook_help(1, BAD_STATUS_TEXT)

    def test_status_text_summary_parsing_keeps_hashes(self, weights: Weights) -> None:
        summary = weights.status_text_help(READY_STATUS_TEXT)
        assert summary["commit_windows"][0]["hash"] == "0x1212"

    def test_status_text_summary_parsing_keeps_commit_window_bounds(self, weights: Weights) -> None:
        summary = weights.status_text_help(EXPIRED_STATUS_TEXT)
        assert summary["commit_windows"][0]["commit_block"] == 100
        assert summary["commit_windows"][0]["first_reveal"] == 110
        assert summary["commit_windows"][0]["last_reveal"] == 130

    def test_status_text_summary_parsing_keeps_pending_statuses(self, weights: Weights) -> None:
        summary = weights.status_text_help(WAITING_STATUS_TEXT)
        assert summary["pending_statuses"] == ["WAITING (10 blocks until reveal window)"]

    def test_status_text_summary_parsing_supports_direct_set_no_pending_text(self, weights: Weights) -> None:
        summary = weights.status_text_help(DIRECT_SET_STATUS_TEXT)
        assert summary["pending_commits"] == 0

    def test_status_text_runbook_help_strips_input(self, weights: Weights) -> None:
        runbook = weights.status_text_runbook_help(5, "\n" + READY_STATUS_TEXT + "\n")
        assert runbook["raw_status"] == READY_STATUS_TEXT.strip()

    def test_status_text_next_action_help_strips_raw_status(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(5, "\n" + READY_STATUS_TEXT + "\n", "0:100", salt="abc")
        assert helpers["raw_status"] == READY_STATUS_TEXT.strip()

    def test_status_text_next_mechanism_action_help_strips_raw_status(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(
            7, 4, "\n" + NO_PENDING_STATUS_TEXT + "\n", "0:100", hash_value="11" * 32
        )
        assert helpers["raw_status"] == NO_PENDING_STATUS_TEXT.strip()

    def test_status_text_next_timelocked_action_help_strips_raw_status(self, weights: Weights) -> None:
        helpers = weights.status_text_next_timelocked_action_help(
            9, "\n" + EXPIRED_STATUS_TEXT + "\n", "0:100", round=42, salt="abc"
        )
        assert helpers["raw_status"] == EXPIRED_STATUS_TEXT.strip()

    def test_status_text_troubleshoot_help_strips_raw_status(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(8, "\n" + WAITING_STATUS_TEXT + "\n", "RevealTooEarly")
        assert helpers["status_summary"]["next_action"] == "WAIT"

    def test_status_text_troubleshoot_mechanism_help_strips_raw_status(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_mechanism_help(
            5,
            4,
            "\n" + READY_STATUS_TEXT + "\n",
            "RevealTooEarly",
            "0:100",
            salt="abc",
            hash_value="11" * 32,
            version_key=7,
        )
        assert helpers["status_summary"]["next_action"] == "REVEAL"

    def test_status_text_troubleshoot_timelocked_help_strips_raw_status(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_timelocked_help(
            9,
            "\n" + EXPIRED_STATUS_TEXT + "\n",
            "ExpiredWeightCommit",
            "0:100",
            round=42,
            salt="abc",
        )
        assert helpers["status_summary"]["next_action"] == "RECOMMIT"

    def test_status_text_help_parses_ready_status_text_with_unicode_dash(self, weights: Weights) -> None:
        summary = weights.status_text_help(READY_STATUS_TEXT)
        assert summary["current_block"] == 125

    def test_status_text_next_action_help_rejects_non_string_status(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_TEXT_TYPE_ERROR):
            weights.status_text_next_action_help(1, 123)  # type: ignore[arg-type]

    def test_status_text_troubleshoot_help_rejects_non_string_status(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_MAPPING_ERROR):
            weights.status_text_troubleshoot_help(1, 123, "RevealTooEarly")  # type: ignore[arg-type]

    def test_status_text_next_mechanism_action_help_rejects_non_string_status(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_TEXT_TYPE_ERROR):
            weights.status_text_next_mechanism_action_help(1, 0, 123)  # type: ignore[arg-type]

    def test_status_text_troubleshoot_mechanism_help_rejects_non_string_status(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_MAPPING_ERROR):
            weights.status_text_troubleshoot_mechanism_help(1, 0, 123, "RevealTooEarly")  # type: ignore[arg-type]

    def test_status_text_next_timelocked_action_help_rejects_non_string_status(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_TEXT_TYPE_ERROR):
            weights.status_text_next_timelocked_action_help(1, 123)  # type: ignore[arg-type]

    def test_status_text_troubleshoot_timelocked_help_rejects_non_string_status(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_MAPPING_ERROR):
            weights.status_text_troubleshoot_timelocked_help(1, 123, "RevealTooEarly")  # type: ignore[arg-type]

    def test_status_runbook_help_rejects_non_mapping_non_string_status(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=STATUS_MAPPING_ERROR):
            weights.status_runbook_help(1, 123)  # type: ignore[arg-type]

    def test_diagnose_text_reuses_error_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_text(9, "ExpiredWeightCommit")
        assert helpers["likely_cause"] == "The previous commit expired before it was revealed."
        assert helpers["next_step"] == "Commit again, then reveal inside the next valid reveal window."

    def test_diagnose_mechanism_text_reuses_error_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=NO_PENDING_STATUS_TEXT)
        helpers = weights.diagnose_mechanism_text(7, 4, "NoWeightsCommitFound", "0:100", hash_value="11" * 32)
        assert helpers["likely_cause"] == "There is no matching pending commit for this subnet and hotkey."

    def test_diagnose_timelocked_text_reuses_error_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=EXPIRED_STATUS_TEXT)
        helpers = weights.diagnose_timelocked_text(9, "ExpiredWeightCommit", "0:100", round=42, salt="abc")
        assert helpers["likely_cause"] == "The previous commit expired before it was revealed."

    def test_status_text_parsing_handles_single_commit_without_blocks_until_action(self, weights: Weights) -> None:
        text = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   140
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  Pending commits: 1

  [1] Hash:    0xabcd
      Commit:  block 100
      Reveal:  blocks 110..130
      Status:  EXPIRED
"""
        summary = weights.status_text_help(text)
        assert summary["commit_windows"] == [
            {
                "index": 1,
                "status": "EXPIRED",
                "commit_block": 100,
                "first_reveal": 110,
                "last_reveal": 130,
                "hash": "0xabcd",
            }
        ]

    def test_status_text_parsing_handles_multiple_commits(self, weights: Weights) -> None:
        text = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   125
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  Pending commits: 2

  [1] Hash:    0x1111
      Commit:  block 100
      Reveal:  blocks 120..130
      Status:  READY TO REVEAL (5 blocks remaining)

  [2] Hash:    0x2222
      Commit:  block 110
      Reveal:  blocks 130..140
      Status:  WAITING (5 blocks until reveal window)
"""
        summary = weights.status_text_help(text)
        assert summary["pending_commits"] == 2
        assert summary["pending_statuses"] == [
            "READY TO REVEAL (5 blocks remaining)",
            "WAITING (5 blocks until reveal window)",
        ]
        assert summary["next_action"] == "REVEAL"

    def test_status_text_parsing_handles_no_pending_commits_with_whitespace(self, weights: Weights) -> None:
        summary = weights.status_text_help(NO_PENDING_STATUS_TEXT + "\n")
        assert summary["pending_commits"] == 0

    def test_status_text_parsing_handles_lowercase_disabled_flag(self, weights: Weights) -> None:
        summary = weights.status_text_help(DIRECT_SET_STATUS_TEXT)
        assert summary["commit_reveal_enabled"] is False

    def test_status_text_parsing_requires_current_block(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_help("Commit-reveal:   ENABLED\nReveal period:   3 epochs")

    def test_status_text_parsing_requires_commit_reveal_flag(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_help("Current block:   125\nReveal period:   3 epochs")

    def test_status_text_parsing_requires_reveal_period(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=NON_MAPPING_OR_TEXT_STATUS_ERROR):
            weights.status_text_help("Current block:   125\nCommit-reveal:   ENABLED")

    def test_status_text_parsing_ignores_pending_count_when_no_entries(self, weights: Weights) -> None:
        text = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   125
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  Pending commits: 1
"""
        summary = weights.status_text_help(text)
        assert summary["pending_commits"] == 0

    def test_status_text_parsing_ignores_non_matching_lines(self, weights: Weights) -> None:
        summary = weights.status_text_help(READY_STATUS_TEXT + "\nextra line")
        assert summary["next_action"] == "REVEAL"

    def test_status_text_parsing_uses_stripped_status_for_no_pending(self, weights: Weights) -> None:
        summary = weights.status_text_help("\n" + NO_PENDING_STATUS_TEXT + "\n")
        assert summary["pending_commits"] == 0

    def test_status_text_next_action_help_handles_wait_without_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(8, WAITING_STATUS_TEXT)
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 8"

    def test_status_text_troubleshoot_help_handles_no_inputs(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(7, NO_PENDING_STATUS_TEXT, "NoWeightsCommitFound")
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights status --netuid 7"

    def test_status_text_next_mechanism_action_help_handles_no_inputs(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(7, 4, NO_PENDING_STATUS_TEXT)
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights status --netuid 7"

    def test_status_text_next_timelocked_action_help_handles_no_inputs(self, weights: Weights) -> None:
        helpers = weights.status_text_next_timelocked_action_help(9, EXPIRED_STATUS_TEXT)
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 9"

    def test_status_text_troubleshoot_mechanism_help_handles_no_inputs(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_mechanism_help(7, 4, NO_PENDING_STATUS_TEXT, "NoWeightsCommitFound")
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights status --netuid 7"

    def test_status_text_troubleshoot_timelocked_help_handles_no_inputs(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_timelocked_help(9, EXPIRED_STATUS_TEXT, "ExpiredWeightCommit")
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 9"

    def test_status_text_next_action_help_allows_mapping_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(7, NO_PENDING_STATUS_TEXT, {0: 100})
        assert helpers["normalized_weights"] == "0:100"

    def test_status_text_next_mechanism_action_help_allows_mapping_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(
            7,
            4,
            NO_PENDING_STATUS_TEXT,
            {0: 100},
            hash_value="11" * 32,
        )
        assert helpers["normalized_weights"] == "0:100"

    def test_status_text_next_timelocked_action_help_allows_mapping_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_next_timelocked_action_help(
            9,
            EXPIRED_STATUS_TEXT,
            {0: 100},
            round=42,
            salt="abc",
        )
        assert helpers["normalized_weights"] == "0:100"

    def test_status_text_troubleshoot_help_allows_mapping_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(8, WAITING_STATUS_TEXT, "RevealTooEarly", {0: 100}, salt="abc")
        assert helpers["normalized_weights"] == "0:100"

    def test_status_text_troubleshoot_mechanism_help_allows_mapping_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_mechanism_help(
            5,
            4,
            READY_STATUS_TEXT,
            "RevealTooEarly",
            {0: 100},
            salt="abc",
            hash_value="11" * 32,
            version_key=7,
        )
        assert helpers["normalized_weights"] == "0:100"

    def test_status_text_troubleshoot_timelocked_help_allows_mapping_weights(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_timelocked_help(
            9,
            EXPIRED_STATUS_TEXT,
            "ExpiredWeightCommit",
            {0: 100},
            round=42,
            salt="abc",
        )
        assert helpers["normalized_weights"] == "0:100"

    def test_status_text_next_action_help_reuses_status_command(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(5, READY_STATUS_TEXT)
        assert helpers["status"] == "agcli weights status --netuid 5"

    def test_status_text_next_mechanism_action_help_reuses_status_command(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(7, 4, NO_PENDING_STATUS_TEXT)
        assert helpers["status"] == "agcli weights status --netuid 7"

    def test_status_text_next_timelocked_action_help_reuses_status_command(self, weights: Weights) -> None:
        helpers = weights.status_text_next_timelocked_action_help(9, EXPIRED_STATUS_TEXT)
        assert helpers["status"] == "agcli weights status --netuid 9"

    def test_status_text_troubleshoot_help_reuses_status_command(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(8, WAITING_STATUS_TEXT, "RevealTooEarly")
        assert helpers["status"] == "agcli weights status --netuid 8"

    def test_status_text_troubleshoot_mechanism_help_reuses_status_command(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_mechanism_help(7, 4, NO_PENDING_STATUS_TEXT, "NoWeightsCommitFound")
        assert helpers["status"] == "agcli weights status --netuid 7"

    def test_status_text_troubleshoot_timelocked_help_reuses_status_command(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_timelocked_help(9, EXPIRED_STATUS_TEXT, "ExpiredWeightCommit")
        assert helpers["status"] == "agcli weights status --netuid 9"

    def test_status_text_summary_help_returns_same_as_status_text_help(self, weights: Weights) -> None:
        assert weights.status_summary_help(READY_STATUS_TEXT) == weights.status_text_help(READY_STATUS_TEXT)

    def test_status_text_runbook_help_returns_same_summary_as_status_text_help(self, weights: Weights) -> None:
        runbook = weights.status_text_runbook_help(5, READY_STATUS_TEXT)
        assert runbook["summary"] == weights.status_text_help(READY_STATUS_TEXT)

    def test_status_runbook_help_returns_same_summary_as_status_summary_help(self, weights: Weights) -> None:
        runbook = weights.status_runbook_help(5, READY_STATUS_TEXT)
        assert runbook["summary"] == weights.status_summary_help(READY_STATUS_TEXT)

    def test_status_summary_text_uses_status_help_command(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        summary = weights.status_summary_text(5)
        assert summary["status"] == "agcli weights status --netuid 5"

    def test_status_runbook_json_uses_status_help_command(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        runbook = weights.status_runbook_json(7)
        assert runbook["status"] == "agcli weights status --netuid 7"

    def test_status_text_fetches_with_raw_runner(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout=READY_STATUS_TEXT)
        weights.status_text(5)
        cmd = mock_subprocess.call_args[0][0]
        assert "--output" not in cmd
        assert "--batch" not in cmd
        assert "--yes" not in cmd

    def test_status_text_troubleshoot_help_preserves_status_text_hash(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(5, READY_STATUS_TEXT, "RevealTooEarly")
        assert helpers["status_summary"]["commit_windows"][0]["hash"] == "0x1212"

    def test_status_text_next_mechanism_action_help_preserves_normalized_hash(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(
            7,
            4,
            NO_PENDING_STATUS_TEXT,
            "0:100",
            hash_value="11" * 32,
        )
        assert helpers["normalized_hash"] == "11" * 32

    def test_status_text_troubleshoot_mechanism_help_preserves_normalized_hash(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_mechanism_help(
            5,
            4,
            READY_STATUS_TEXT,
            "RevealTooEarly",
            "0:100",
            salt="abc",
            hash_value="11" * 32,
            version_key=7,
        )
        assert helpers["normalized_hash"] == "11" * 32

    def test_status_text_next_timelocked_action_help_preserves_round(self, weights: Weights) -> None:
        helpers = weights.status_text_next_timelocked_action_help(
            9,
            EXPIRED_STATUS_TEXT,
            "0:100",
            round=42,
            salt="abc",
        )
        assert helpers["round"] == 42

    def test_status_text_troubleshoot_timelocked_help_preserves_round(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_timelocked_help(
            9,
            EXPIRED_STATUS_TEXT,
            "ExpiredWeightCommit",
            "0:100",
            round=42,
            salt="abc",
        )
        assert helpers["round"] == 42

    def test_status_text_next_action_help_preserves_reason(self, weights: Weights) -> None:
        helpers = weights.status_text_next_action_help(5, READY_STATUS_TEXT, "0:100", salt="abc")
        assert helpers["reason"] == "A pending commit is ready to reveal now."

    def test_status_text_next_mechanism_action_help_preserves_reason(self, weights: Weights) -> None:
        helpers = weights.status_text_next_mechanism_action_help(7, 4, NO_PENDING_STATUS_TEXT)
        assert helpers["reason"] == (
            "No mechanism commit is pending and this subnet uses commit-reveal; "
            "provide the precomputed mechanism hash to build the commit command."
        )

    def test_status_text_next_timelocked_action_help_preserves_reason(self, weights: Weights) -> None:
        helpers = weights.status_text_next_timelocked_action_help(9, EXPIRED_STATUS_TEXT)
        assert helpers["reason"] == (
            "A previous pending timelocked commit expired, so fresh weights and a drand round "
            "are required before retrying."
        )

    def test_status_text_troubleshoot_help_preserves_reason(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_help(8, WAITING_STATUS_TEXT, "RevealTooEarly")
        assert helpers["reason"] == "A pending commit exists but the reveal window is not open yet."

    def test_status_text_troubleshoot_mechanism_help_preserves_reason(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_mechanism_help(
            7,
            4,
            NO_PENDING_STATUS_TEXT,
            "NoWeightsCommitFound",
        )
        assert helpers["reason"] == (
            "No mechanism commit is pending and this subnet uses commit-reveal; "
            "provide the precomputed mechanism hash to build the commit command."
        )

    def test_status_text_troubleshoot_timelocked_help_preserves_reason(self, weights: Weights) -> None:
        helpers = weights.status_text_troubleshoot_timelocked_help(
            9,
            EXPIRED_STATUS_TEXT,
            "ExpiredWeightCommit",
        )
        assert helpers["reason"] == (
            "A previous pending timelocked commit expired, so fresh weights and a drand round "
            "are required before retrying."
        )

    def test_status_text_help_parses_commit_reveal_disabled_text(self, weights: Weights) -> None:
        summary = weights.status_text_help(DIRECT_SET_STATUS_TEXT)
        assert summary["commit_reveal_enabled"] is False
        assert summary["reveal_period_epochs"] == 0

    def test_status_text_help_keeps_unknown_status_when_blank(self, weights: Weights) -> None:
        text = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   125
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  Pending commits: 1

  [1] Hash:    0x1111
      Commit:  block 100
      Reveal:  blocks 120..130
      Status:
"""
        summary = weights.status_text_help(text)
        assert summary["commit_windows"][0]["status"] == "UNKNOWN"

    def test_status_text_help_parses_hash_without_pending_count_line(self, weights: Weights) -> None:
        text = """Weight Commit Status — SN5
  Hotkey:          5F3sa2TJAWMqDhXG6jhV4N8ko9Y8Xr
  Current block:   125
  Commit-reveal:   ENABLED
  Reveal period:   3 epochs

  [1] Hash:    0x1111
      Commit:  block 100
      Reveal:  blocks 120..130
      Status:  READY TO REVEAL (5 blocks remaining)
"""
        summary = weights.status_text_help(text)
        assert summary["pending_commits"] == 1

    def test_status_summary_returns_normalized_ready_to_reveal_view(
        self,
        weights: Weights,
        mock_subprocess: Any,
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"hash": "0x1212", "commit_block": 100, "first_reveal": 120, '
                '"last_reveal": 130, "status": "READY TO REVEAL (5 blocks remaining)", '
                '"blocks_until_action": 5}]}'
            )
        )
        summary = weights.status_summary(5)
        assert summary == {
            "status": "agcli weights status --netuid 5",
            "current_block": 125,
            "commit_reveal_enabled": True,
            "reveal_period_epochs": 3,
            "pending_commits": 1,
            "pending_statuses": ["READY TO REVEAL (5 blocks remaining)"],
            "next_action": "REVEAL",
            "commit_windows": [
                {
                    "index": 1,
                    "status": "READY TO REVEAL (5 blocks remaining)",
                    "commit_block": 100,
                    "first_reveal": 120,
                    "last_reveal": 130,
                    "blocks_until_action": 5,
                    "hash": "0x1212",
                }
            ],
        }

    def test_next_action_help_recommends_reveal_for_ready_commit(self, weights: Weights) -> None:
        helpers = weights.next_action_help(
            1,
            {
                "block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "commits": [
                    {
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                        "blocks_until_action": 5,
                    }
                ],
            },
            "0:100",
            salt="abc",
            version_key=7,
        )
        assert helpers == {
            "status": "agcli weights status --netuid 1",
            "status_summary": {
                "current_block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "pending_commits": 1,
                "pending_statuses": ["READY TO REVEAL (5 blocks remaining)"],
                "next_action": "REVEAL",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "blocks_until_action": 5,
                    }
                ],
            },
            "recommended_action": "REVEAL",
            "recommended_command": "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7",
            "reason": "A pending commit is ready to reveal now.",
            "normalized_weights": "0:100",
        }

    def test_next_action_help_recommends_commit_reveal_when_no_pending_commits(self, weights: Weights) -> None:
        helpers = weights.next_action_help(
            3,
            {
                "block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "commits": [],
            },
            {0: 100},
            version_key=9,
            wait=True,
        )
        assert helpers == {
            "status": "agcli weights status --netuid 3",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
            "recommended_action": "NO_PENDING_COMMITS",
            "recommended_command": "agcli weights commit-reveal --netuid 3 --weights 0:100 --version-key 9 --wait",
            "reason": "No commit is pending and this subnet uses commit-reveal.",
            "normalized_weights": "0:100",
        }

    def test_next_action_help_recommends_set_when_commit_reveal_is_disabled(self, weights: Weights) -> None:
        helpers = weights.next_action_help(
            4,
            {
                "block": 200,
                "commit_reveal_enabled": False,
                "reveal_period_epochs": 0,
                "commits": [],
            },
            {0: 100},
            version_key=2,
        )
        assert helpers == {
            "status": "agcli weights status --netuid 4",
            "status_summary": {
                "current_block": 200,
                "commit_reveal_enabled": False,
                "reveal_period_epochs": 0,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
            "recommended_action": "NO_PENDING_COMMITS",
            "recommended_command": "agcli weights set --netuid 4 --weights 0:100 --version-key 2",
            "reason": "No commit is pending and direct weight setting is available.",
            "normalized_weights": "0:100",
        }

    def test_next_action_help_recommends_wait_when_pending_commit_is_not_ready(self, weights: Weights) -> None:
        helpers = weights.next_action_help(
            5,
            {
                "block": 100,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 2,
                "commits": [
                    {
                        "commit_block": 90,
                        "first_reveal": 110,
                        "last_reveal": 120,
                        "status": "WAITING (10 blocks until reveal window)",
                        "blocks_until_action": 10,
                    }
                ],
            },
            "0:100",
            salt="abc",
        )
        assert helpers == {
            "status": "agcli weights status --netuid 5",
            "status_summary": {
                "current_block": 100,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 2,
                "pending_commits": 1,
                "pending_statuses": ["WAITING (10 blocks until reveal window)"],
                "next_action": "WAIT",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "WAITING (10 blocks until reveal window)",
                        "commit_block": 90,
                        "first_reveal": 110,
                        "last_reveal": 120,
                        "blocks_until_action": 10,
                    }
                ],
            },
            "recommended_action": "WAIT",
            "recommended_command": "agcli weights status --netuid 5",
            "reason": "A pending commit exists but the reveal window is not open yet.",
            "normalized_weights": "0:100",
        }

    def test_next_action_help_rejects_bad_status_shape(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="status block must be an integer"):
            weights.next_action_help(
                1,
                {
                    "block": True,
                    "commit_reveal_enabled": True,
                    "reveal_period_epochs": 3,
                    "commits": [],
                },
            )

    def test_next_action_fetches_live_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        helpers = weights.next_action(7, "0:100", salt="abc")
        assert helpers == {
            "status": "agcli weights status --netuid 7",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 1,
                "pending_statuses": ["EXPIRED"],
                "next_action": "RECOMMIT",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "EXPIRED",
                        "commit_block": 100,
                        "first_reveal": 110,
                        "last_reveal": 130,
                    }
                ],
            },
            "recommended_action": "RECOMMIT",
            "recommended_command": "agcli weights commit --netuid 7 --weights 0:100 --salt abc",
            "reason": "A previous pending commit expired, so fresh weights are required.",
            "normalized_weights": "0:100",
        }

    def test_diagnose_fetches_live_status_summary(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        helpers = weights.diagnose(7, "ExpiredWeightCommit")
        assert helpers == {
            "error": "ExpiredWeightCommit",
            "likely_cause": "The previous commit expired before it was revealed.",
            "next_step": "Commit again, then reveal inside the next valid reveal window.",
            "status": "agcli weights status --netuid 7",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 1,
                "pending_statuses": ["EXPIRED"],
                "next_action": "RECOMMIT",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "EXPIRED",
                        "commit_block": 100,
                        "first_reveal": 110,
                        "last_reveal": 130,
                    }
                ],
            },
            "recommended_action": "RECOMMIT",
            "recommended_command": "agcli weights status --netuid 7",
            "reason": "A previous pending commit expired, so fresh weights are required.",
        }

    def test_diagnose_includes_reveal_recommendation_for_ready_commit(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"commit_block": 100, "first_reveal": 120, '
                '"last_reveal": 130, "status": "READY TO REVEAL (5 blocks remaining)", '
                '"blocks_until_action": 5}]}'
            )
        )
        helpers = weights.diagnose(7, "RevealTooEarly")
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == "agcli weights status --netuid 7"
        assert helpers["reason"] == (
            "A pending commit is ready to reveal now; provide the original weights and salt "
            "to build the reveal command."
        )

    def test_diagnose_includes_wait_guidance_for_pending_commit(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 100, "commit_reveal_enabled": true, "reveal_period_epochs": 2, '
                '"commits": [{"commit_block": 90, "first_reveal": 110, '
                '"last_reveal": 120, "status": "WAITING (10 blocks until reveal window)", '
                '"blocks_until_action": 10}]}'
            )
        )
        helpers = weights.diagnose(5, "RevealTooEarly")
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 5"
        assert helpers["reason"] == "A pending commit exists but the reveal window is not open yet."

    def test_diagnose_includes_direct_set_guidance_when_commit_reveal_is_disabled(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 200, "commit_reveal_enabled": false, "reveal_period_epochs": 0, "commits": []}'
        )
        helpers = weights.diagnose(4, "SettingWeightsTooFast")
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights status --netuid 4"
        assert helpers["reason"] == "No commit is pending and direct weight setting is available."

    def test_diagnose_includes_commit_reveal_guidance_when_enabled(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        helpers = weights.diagnose(3, "NoWeightsCommitFound")
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights status --netuid 3"
        assert helpers["reason"] == "No commit is pending and this subnet uses commit-reveal."

    def test_diagnose_rejects_non_mapping_status_output(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout="[1, 2, 3]")
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            weights.diagnose(3, "NoWeightsCommitFound")

    def test_diagnose_mechanism_fetches_live_status_summary(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"commit_block": 100, "first_reveal": 120, '
                '"last_reveal": 130, "status": "READY TO REVEAL (5 blocks remaining)", '
                '"blocks_until_action": 5}]}'
            )
        )
        helpers = weights.diagnose_mechanism(1, 4, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers == {
            "error": "RevealTooEarly",
            "likely_cause": "The reveal window has not opened yet for the pending commit.",
            "next_step": "Check weights status and retry when the subnet enters the reveal period.",
            "status": "agcli weights status --netuid 1",
            "status_summary": {
                "current_block": 125,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 3,
                "pending_commits": 1,
                "pending_statuses": ["READY TO REVEAL (5 blocks remaining)"],
                "next_action": "REVEAL",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "READY TO REVEAL (5 blocks remaining)",
                        "commit_block": 100,
                        "first_reveal": 120,
                        "last_reveal": 130,
                        "blocks_until_action": 5,
                    }
                ],
            },
            "recommended_action": "REVEAL",
            "recommended_command": (
                "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 7"
            ),
            "reason": "A pending mechanism commit is ready to reveal now.",
            "normalized_weights": "0:100",
            "normalized_hash": "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339",
        }

    def test_diagnose_mechanism_derives_hash_for_recommit_guidance(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        helpers = weights.diagnose_mechanism(1, 4, "NoWeightsCommitFound", "0:100", salt="abc")
        assert helpers["normalized_hash"] == "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339"
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == (
            "agcli weights commit-mechanism --netuid 1 --mechanism-id 4 --hash "
            "0x139067e69007008c569c3e4f625d6a67abcb0b7222d7feea7d32c78ddedb5339"
        )
        assert helpers["reason"] == "No mechanism commit is pending and this subnet uses commit-reveal."
        assert helpers["normalized_weights"] == "0:100"

    def test_diagnose_mechanism_rejects_non_mapping_status_output(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout="[1, 2, 3]")
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            weights.diagnose_mechanism(3, 4, "NoWeightsCommitFound")

    def test_diagnose_timelocked_fetches_live_status_summary(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        helpers = weights.diagnose_timelocked(7, "ExpiredWeightCommit", "0:100", round=42, salt="abc")
        assert helpers == {
            "error": "ExpiredWeightCommit",
            "likely_cause": "The previous commit expired before it was revealed.",
            "next_step": "Commit again, then reveal inside the next valid reveal window.",
            "status": "agcli weights status --netuid 7",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 1,
                "pending_statuses": ["EXPIRED"],
                "next_action": "RECOMMIT",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "EXPIRED",
                        "commit_block": 100,
                        "first_reveal": 110,
                        "last_reveal": 130,
                    }
                ],
            },
            "recommended_action": "RECOMMIT",
            "recommended_command": "agcli weights commit-timelocked --netuid 7 --weights 0:100 --round 42 --salt abc",
            "reason": "A previous pending timelocked commit expired, so a fresh timelocked commit is required.",
            "normalized_weights": "0:100",
            "round": 42,
        }

    def test_diagnose_timelocked_rejects_non_mapping_status_output(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(stdout="[1, 2, 3]")
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            weights.diagnose_timelocked(3, "NoWeightsCommitFound")

    def test_next_mechanism_action_fetches_live_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        helpers = weights.next_mechanism_action(7, 4, "0:100", hash_value="11" * 32)
        assert helpers == {
            "status": "agcli weights status --netuid 7",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 0,
                "pending_statuses": [],
                "next_action": "NO_PENDING_COMMITS",
                "commit_windows": [],
            },
            "recommended_action": "NO_PENDING_COMMITS",
            "recommended_command": ("agcli weights commit-mechanism --netuid 7 --mechanism-id 4 --hash " + "11" * 32),
            "reason": "No mechanism commit is pending and this subnet uses commit-reveal.",
            "normalized_weights": "0:100",
            "normalized_hash": "11" * 32,
        }

    def test_troubleshoot_mechanism_fetches_live_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"commit_block": 100, "first_reveal": 120, '
                '"last_reveal": 130, "status": "READY TO REVEAL (5 blocks remaining)", '
                '"blocks_until_action": 5}]}'
            )
        )
        helpers = weights.troubleshoot_mechanism(1, 4, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal-mechanism --netuid 1 --mechanism-id 4 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending mechanism commit is ready to reveal now."
        assert helpers["status_summary"]["next_action"] == "REVEAL"

    def test_next_timelocked_action_fetches_live_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        helpers = weights.next_timelocked_action(7, "0:100", round=42, salt="abc")
        assert helpers == {
            "status": "agcli weights status --netuid 7",
            "status_summary": {
                "current_block": 140,
                "commit_reveal_enabled": True,
                "reveal_period_epochs": 4,
                "pending_commits": 1,
                "pending_statuses": ["EXPIRED"],
                "next_action": "RECOMMIT",
                "commit_windows": [
                    {
                        "index": 1,
                        "status": "EXPIRED",
                        "commit_block": 100,
                        "first_reveal": 110,
                        "last_reveal": 130,
                    }
                ],
            },
            "recommended_action": "RECOMMIT",
            "recommended_command": "agcli weights commit-timelocked --netuid 7 --weights 0:100 --round 42 --salt abc",
            "reason": "A previous pending timelocked commit expired, so a fresh timelocked commit is required.",
            "normalized_weights": "0:100",
            "round": 42,
        }

    def test_troubleshoot_timelocked_fetches_live_status(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 100, "commit_reveal_enabled": true, "reveal_period_epochs": 2, '
                '"commits": [{"commit_block": 90, "first_reveal": 110, '
                '"last_reveal": 120, "status": "WAITING (10 blocks until reveal window)", '
                '"blocks_until_action": 10}]}'
            )
        )
        helpers = weights.troubleshoot_timelocked(5, "RevealTooEarly", "0:100", round=42, salt="abc")
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 5"
        assert helpers["reason"] == "A pending timelocked commit exists but the reveal window is not open yet."
        assert helpers["status_summary"]["next_action"] == "WAIT"

    def test_troubleshoot_rejects_non_mapping_status_output(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout="[1, 2, 3]")
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            weights.troubleshoot(3, "NoWeightsCommitFound")

    def test_troubleshoot_fetches_live_status_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 125, "commit_reveal_enabled": true, "reveal_period_epochs": 3, '
                '"commits": [{"commit_block": 100, "first_reveal": 120, '
                '"last_reveal": 130, "status": "READY TO REVEAL (5 blocks remaining)", '
                '"blocks_until_action": 5}]}'
            )
        )
        helpers = weights.troubleshoot(1, "RevealTooEarly", "0:100", salt="abc", version_key=7)
        assert helpers["recommended_action"] == "REVEAL"
        assert helpers["recommended_command"] == (
            "agcli weights reveal --netuid 1 --weights 0:100 --salt abc --version-key 7"
        )
        assert helpers["reason"] == "A pending commit is ready to reveal now."
        assert helpers["status_summary"]["next_action"] == "REVEAL"
        assert helpers["normalized_weights"] == "0:100"
        assert helpers["set"] == "agcli weights set --netuid 1 --weights 0:100 --version-key 7"
        assert helpers["commit"] == "agcli weights commit --netuid 1 --weights 0:100 --salt abc"
        assert helpers["commit_reveal"] == "agcli weights commit-reveal --netuid 1 --weights 0:100 --version-key 7"

    def test_troubleshoot_fetches_live_status_without_payload_inputs(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        helpers = weights.troubleshoot(3, "NoWeightsCommitFound")
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights status --netuid 3"
        assert helpers["reason"] == "No commit is pending and this subnet uses commit-reveal."
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"
        assert "normalized_weights" not in helpers
        assert "set" not in helpers
        assert "commit" not in helpers
        assert "commit_reveal" not in helpers
        assert "reveal" not in helpers

    def test_troubleshoot_fetches_live_status_direct_set_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 200, "commit_reveal_enabled": false, "reveal_period_epochs": 0, "commits": []}'
        )
        helpers = weights.troubleshoot(4, "SettingWeightsTooFast", "0:100", version_key=2)
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights set --netuid 4 --weights 0:100 --version-key 2"
        assert helpers["reason"] == "No commit is pending and direct weight setting is available."
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"

    def test_troubleshoot_fetches_live_status_commit_reveal_guidance(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout='{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, "commits": []}'
        )
        helpers = weights.troubleshoot(3, "NoWeightsCommitFound", "0:100", salt="abc", version_key=9)
        assert helpers["recommended_action"] == "NO_PENDING_COMMITS"
        assert helpers["recommended_command"] == "agcli weights commit --netuid 3 --weights 0:100 --salt abc"
        assert helpers["reason"] == "No commit is pending and this subnet uses commit-reveal."
        assert helpers["status_summary"]["next_action"] == "NO_PENDING_COMMITS"

    def test_troubleshoot_fetches_live_status_wait_guidance(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 100, "commit_reveal_enabled": true, "reveal_period_epochs": 2, '
                '"commits": [{"commit_block": 90, "first_reveal": 110, '
                '"last_reveal": 120, "status": "WAITING (10 blocks until reveal window)", '
                '"blocks_until_action": 10}]}'
            )
        )
        helpers = weights.troubleshoot(5, "RevealTooEarly", "0:100", salt="abc")
        assert helpers["recommended_action"] == "WAIT"
        assert helpers["recommended_command"] == "agcli weights status --netuid 5"
        assert helpers["reason"] == "A pending commit exists but the reveal window is not open yet."
        assert helpers["status_summary"]["next_action"] == "WAIT"

    def test_troubleshoot_uses_waiting_commit_reveal_command_when_requested(
        self, weights: Weights, mock_subprocess: Any
    ) -> None:
        mock_subprocess.return_value = make_completed_process(
            stdout=(
                '{"block": 140, "commit_reveal_enabled": true, "reveal_period_epochs": 4, '
                '"commits": [{"commit_block": 100, "first_reveal": 110, '
                '"last_reveal": 130, "status": "EXPIRED"}]}'
            )
        )
        helpers = weights.next_action(7, "0:100", version_key=8, wait=True)
        assert helpers["recommended_action"] == "RECOMMIT"
        assert helpers["recommended_command"] == (
            "agcli weights commit-reveal --netuid 7 --weights 0:100 --version-key 8 --wait"
        )
        assert helpers["reason"] == "A previous pending commit expired, so fresh weights are required."

    def test_next_action_rejects_non_mapping_status_output(self, weights: Weights, mock_subprocess: Any) -> None:
        mock_subprocess.return_value = make_completed_process(stdout="[1, 2, 3]")
        with pytest.raises(ValueError, match="weights status output must be a mapping"):
            weights.next_action(3)

    def test_show_rejects_non_integer_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be an integer"):
            weights.show("1")  # type: ignore[arg-type]

    def test_status_rejects_non_integer_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be an integer"):
            weights.status("1")  # type: ignore[arg-type]

    def test_commit_rejects_boolean_version_key_not_applicable(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit(1, "0:100")
        cmd = mock_subprocess.call_args[0][0]
        assert "commit" in cmd

    def test_set_rejects_json_list_missing_mapping_entry(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match=r"JSON weights must be an object map or array of \{uid, weight\} entries"):
            weights.set(1, '[{"uid": 0, "weight": 1}, []]')

    def test_commit_mechanism_rejects_hash_non_hex_chars(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="hash must be valid hex"):
            weights.commit_mechanism(1, 0, "gg" * 32)

    def test_commit_mechanism_rejects_hash_wrong_size_plain_hex(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="hash must be exactly 32 bytes, got 1 bytes"):
            weights.commit_mechanism(1, 0, "11")

    def test_reveal_help_uses_normalized_weights(self, weights: Weights) -> None:
        command = weights.reveal_help(1, " 0 : 100 ", "abc")
        assert command == "agcli weights reveal --netuid 1 --weights 0:100 --salt abc"

    def test_status_help_rejects_boolean_netuid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="netuid must be an integer"):
            weights.status_help(True)

    def test_set_rejects_empty_weights_string(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights cannot be empty"):
            weights.set(1, "   ")

    def test_set_rejects_malformed_weights_string(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights entries must use uid:value format"):
            weights.set(1, "0:100,,1:200")

    def test_set_rejects_duplicate_uids_in_string(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="duplicate uid in weights: 0"):
            weights.set(1, "0:100, 0:200")

    def test_set_rejects_non_numeric_uid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight uids must be integers"):
            weights.set(1, {"abc": 100})

    def test_set_rejects_non_numeric_value(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight values must be numbers"):
            weights.set(1, {0: "abc"})

    def test_set_rejects_boolean_uid(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight uids must be integers"):
            weights.set(1, {True: 100})

    def test_set_rejects_boolean_value(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight values must be numbers"):
            weights.set(1, {0: True})

    def test_set_rejects_empty_string_value(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weight values must be numbers"):
            weights.set(1, {0: "   "})

    def test_set_rejects_string_missing_value(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights entries must use uid:value format"):
            weights.set(1, "0:")

    def test_set_rejects_empty_weights_mapping(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="weights cannot be empty"):
            weights.set(1, {})

    def test_set_rejects_duplicate_uids(self, weights: Weights) -> None:
        with pytest.raises(ValueError, match="duplicate uid in weights: 0"):
            weights.set(1, [(0, 100), (0, 200)])

    def test_set_rejects_bad_weight_entry(self, weights: Weights) -> None:
        bad_weights: Any = [(0, 100, 200)]
        with pytest.raises(ValueError, match=r"weights entries must be \(uid, value\) pairs"):
            weights.set(1, bad_weights)

    def test_set_with_version_key(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set(1, "0:100", version_key=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version-key" in cmd

    def test_commit(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit(1, "0:100")
        cmd = mock_subprocess.call_args[0][0]
        assert "commit" in cmd

    def test_commit_with_salt(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit(1, "0:100", salt="abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "--salt" in cmd

    def test_reveal(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal(1, "0:100", "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "reveal" in cmd and "--salt" in cmd

    def test_reveal_with_mapping(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal(1, {0: 100}, "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "0:100" in cmd and "--salt" in cmd

    def test_status(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.status(1)
        cmd = mock_subprocess.call_args[0][0]
        assert "status" in cmd

    def test_commit_reveal(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_reveal(1, "0:100")
        cmd = mock_subprocess.call_args[0][0]
        assert "commit-reveal" in cmd

    def test_commit_reveal_wait(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_reveal(1, [(0, 100)], wait=True)
        cmd = mock_subprocess.call_args[0][0]
        assert "--wait" in cmd and "0:100" in cmd

    def test_set_mechanism(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set_mechanism(1, 0, "0:100")
        cmd = mock_subprocess.call_args[0][0]
        assert "set-mechanism" in cmd and "--weights" in cmd and "--mechanism-id" in cmd

    def test_set_mechanism_with_version_key(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.set_mechanism(1, 1, {0: 100}, version_key=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version-key" in cmd and "0:100" in cmd

    def test_commit_mechanism(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_mechanism(1, 0, "0x" + "11" * 32)
        cmd = mock_subprocess.call_args[0][0]
        assert "commit-mechanism" in cmd and "--mechanism-id" in cmd and "--hash" in cmd

    def test_reveal_mechanism(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal_mechanism(1, 0, "0:100", "abc")
        cmd = mock_subprocess.call_args[0][0]
        assert "reveal-mechanism" in cmd and "--mechanism-id" in cmd and "--salt" in cmd

    def test_reveal_mechanism_with_version_key(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.reveal_mechanism(1, 1, [(0, 100)], "abc", version_key=1)
        cmd = mock_subprocess.call_args[0][0]
        assert "--version-key" in cmd and "0:100" in cmd

    def test_commit_timelocked(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_timelocked(1, "0:100", 42)
        cmd = mock_subprocess.call_args[0][0]
        assert "commit-timelocked" in cmd and "--round" in cmd

    def test_commit_timelocked_with_salt(self, weights: Weights, mock_subprocess: Any) -> None:
        weights.commit_timelocked(1, {0: 100}, 42, salt="mysalt")
        cmd = mock_subprocess.call_args[0][0]
        assert "--salt" in cmd and "0:100" in cmd
