"""End-to-end live test. Optional — not in CI by default."""
import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parent.parent
PYTHON = REPO / ".venv" / "Scripts" / "python.exe"
HELPER = REPO / "bin" / "helper.py"


@pytest.mark.skipif(not PYTHON.exists(), reason="venv not set up")
def test_full_search_returns_at_least_one_marketplace():
    """Live test: query a TV model, expect at least WB or Yandex to return data."""
    r = subprocess.run(
        [str(PYTHON), str(HELPER), "search",
         "--query", "телевизор samsung 55",
         "--marketplaces", "wb,yandex",
         "--max-per", "10",
         "--timeout", "60"],
        capture_output=True, text=True, encoding="utf-8", timeout=180,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    ok_marketplaces = [k for k, v in data["stats"].items() if v["ok"] and v["count"] > 0]
    assert len(ok_marketplaces) >= 1, f"only ok: {ok_marketplaces}; errors: {data['errors']}"
