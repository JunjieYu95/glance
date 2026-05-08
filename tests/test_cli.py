"""Smoke tests for glance CLI."""

import json
import sys


def test_glance_version():
    from glance import __version__

    assert __version__ is not None


def test_glance_help():
    from glance.cli import main

    rc = main(["help"])
    assert rc == 0


def test_glance_list_no_components(tmp_path, monkeypatch):
    """list should return empty when no components exist."""
    monkeypatch.setenv("GLANCE_HOME", str(tmp_path))

    import io

    from glance.cli import cmd_list

    saved = sys.stdout
    sys.stdout = io.StringIO()
    try:
        rc = cmd_list([])
        output = sys.stdout.getvalue()
        result = json.loads(output)
        assert isinstance(result, list)
        assert rc == 0
    finally:
        sys.stdout = saved
