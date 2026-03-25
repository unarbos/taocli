from __future__ import annotations

from pathlib import Path


def _pyproject_text() -> str:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    return pyproject.read_text(encoding="utf-8")


def test_project_metadata_uses_tao_cli_distribution_name() -> None:
    text = _pyproject_text()

    assert 'name = "tao-cli"' in text
    assert 'version = "0.6.6"' in text


def test_wheel_force_includes_llms_metadata() -> None:
    text = _pyproject_text()

    assert "[tool.hatch.build.targets.wheel.force-include]" in text
    assert '"llms.txt" = "taocli/llms.txt"' in text
