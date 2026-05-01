import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HELPER = REPO / "bin" / "helper.py"
PYTHON = REPO / ".venv" / "Scripts" / "python.exe"


def test_helper_search_help():
    r = subprocess.run([str(PYTHON), str(HELPER), "search", "--help"],
                       capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    assert "--query" in r.stdout
    assert "--marketplaces" in r.stdout


def test_helper_search_returns_valid_json():
    """CLI produces valid JSON regardless of adapter outcomes (success/error)."""
    r = subprocess.run(
        [str(PYTHON), str(HELPER), "search",
         "--query", "test",
         "--marketplaces", "mvideo,citilink",
         "--max-per", "5",
         "--timeout", "10"],
        capture_output=True, encoding="utf-8", errors="replace", timeout=30,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert "products" in data
    assert "errors" in data
    assert "stats" in data
    assert set(data["stats"].keys()) == {"mvideo", "citilink"}
