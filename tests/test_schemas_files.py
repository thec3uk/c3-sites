import json
from pathlib import Path

import pytest

SCHEMAS = Path(__file__).resolve().parent.parent / "schemas"
CUSTOM_TYPES = sorted((SCHEMAS / "customtypes").glob("*.json"))
SLICES = sorted((SCHEMAS / "slices").glob("*.json"))


def test_expected_counts():
    assert len(CUSTOM_TYPES) == 14
    assert len(SLICES) == 8


@pytest.mark.parametrize("path", CUSTOM_TYPES + SLICES, ids=lambda p: f"{p.parent.name}/{p.stem}")
def test_file_parses_and_id_matches_filename(path):
    assert json.loads(path.read_text())["id"] == path.stem
