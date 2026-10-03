"""Verify agent.yaml and SOUL.md satisfy the OpenGAP v0.1.0 required fields."""

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
AGENT_YAML = ROOT / "agent.yaml"
SOUL_MD = ROOT / "SOUL.md"


@pytest.fixture(scope="module")
def manifest():
    return yaml.safe_load(AGENT_YAML.read_text())


def test_agent_yaml_exists():
    assert AGENT_YAML.is_file()


def test_required_fields_present(manifest):
    for field in ("name", "version", "description"):
        assert field in manifest, f"required field missing: {field}"


def test_name_is_kebab_case(manifest):
    assert re.match(r"^[a-z][a-z0-9-]*$", manifest["name"])


def test_version_is_semver(manifest):
    assert re.match(r"^\d+\.\d+\.\d+", manifest["version"])


def test_spec_version(manifest):
    assert manifest.get("spec_version") == "0.1.0"


def test_tools_is_non_empty_list(manifest):
    assert isinstance(manifest.get("tools"), list)
    assert len(manifest["tools"]) > 0


def test_soul_md_exists_and_non_empty():
    assert SOUL_MD.is_file()
    text = SOUL_MD.read_text().strip()
    paragraphs = [p for p in text.split("\n\n") if p.strip() and not p.strip().startswith("#")]
    assert len(paragraphs) >= 1, "SOUL.md must contain at least one non-heading paragraph"
