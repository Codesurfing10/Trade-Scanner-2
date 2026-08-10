import json


def test_smoke():
    # very small smoke test to ensure test runner works
    assert json.loads('{"ok": true}')["ok"] is True
