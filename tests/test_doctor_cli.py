"""Tests for team-setup plumbing: relative FMOD_STUDIO_PROJECT resolution,
project format detection, `--doctor` verdicts and the CLI flags."""

import json
import os
import subprocess
import sys

import pytest

from fmod_mcp import doctor
from fmod_mcp.tools import studio_tools

_FSPRO = '<?xml version="1.0" encoding="UTF-8"?>\n<objects serializationModel="Studio.{v}" />\n'


def _project(root, rel="FMODProject/game.fspro", version="02.03.00"):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_FSPRO.format(v=version), encoding="utf-8")
    return path


def test_relative_project_prefers_claude_project_dir(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    proj = _project(repo)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", "FMODProject/game.fspro")
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(repo))
    assert studio_tools.default_project() == str(proj)


def test_relative_project_found_from_cwd_and_its_parents(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    proj = _project(repo)
    deep = repo / "Assets" / "Game"
    deep.mkdir(parents=True)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", "FMODProject/game.fspro")
    monkeypatch.chdir(repo)
    assert studio_tools.default_project() == str(proj)
    monkeypatch.chdir(deep)  # e.g. a client that starts servers in a subfolder
    assert studio_tools.default_project() == str(proj)


def test_unresolvable_relative_project_names_a_concrete_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", "FMODProject/missing.fspro")
    resolved = studio_tools.default_project()
    assert resolved == os.path.normpath(os.path.join(str(tmp_path), "FMODProject/missing.fspro"))
    with pytest.raises(Exception, match="project not found"):
        studio_tools.check_project_path(None)


def test_absolute_project_and_unset(tmp_path, monkeypatch):
    proj = _project(tmp_path)
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", str(proj))
    assert studio_tools.default_project() == str(proj)
    monkeypatch.delenv("FMOD_STUDIO_PROJECT")
    assert studio_tools.default_project() is None


def test_project_format(tmp_path):
    assert studio_tools.project_format(str(_project(tmp_path, "a.fspro", "02.03.00"))) == "02.03"
    assert studio_tools.project_format(str(_project(tmp_path, "b.fspro", "02.02.00"))) == "02.02"
    junk = tmp_path / "c.fspro"
    junk.write_text("not xml")
    assert studio_tools.project_format(str(junk)) is None
    assert studio_tools.project_format(str(tmp_path / "missing.fspro")) is None


@pytest.fixture()
def machine(tmp_path, monkeypatch):
    """A fake machine: Studio 2.03.15 installed, nothing running, no ffmpeg."""
    monkeypatch.setattr(studio_tools, "find_install", lambda: {"exe": "C:/S/FMOD Studio.exe", "cl": "C:/S/cl.exe"})
    monkeypatch.setattr(doctor, "studio_version", lambda cl: "2.03.15")
    monkeypatch.setattr(studio_tools, "read_script_server_pref", lambda: True)
    monkeypatch.setattr(studio_tools, "_server_reachable", lambda timeout=1.0: False)
    monkeypatch.setattr(studio_tools, "studio_process_running", lambda: False)
    monkeypatch.setattr(doctor, "_ffmpeg", lambda: (None, None))
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    return tmp_path


def _status(checks, name):
    return next(c["status"] for c in checks if c["check"] == name)


def test_doctor_ready_machine(machine, monkeypatch):
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", str(_project(machine)))
    checks = doctor.run_checks()
    assert _status(checks, "project") == "ok"
    assert _status(checks, "version match") == "ok"
    assert _status(checks, "ffmpeg") == "warn"  # optional
    assert doctor.main() == 0


def test_doctor_warns_before_a_newer_studio_upgrades_the_project(machine, monkeypatch):
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", str(_project(machine, version="02.02.00")))
    assert _status(doctor.run_checks(), "version match") == "warn"


def test_doctor_fails_when_studio_is_too_old(machine, monkeypatch):
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", str(_project(machine, version="02.04.00")))
    assert _status(doctor.run_checks(), "version match") == "fail"
    assert doctor.main() == 1


def test_doctor_fails_without_studio_or_project(machine, monkeypatch):
    monkeypatch.setattr(studio_tools, "find_install", lambda: {"exe": None, "cl": None})
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", "nowhere/x.fspro")
    checks = doctor.run_checks()
    assert _status(checks, "FMOD Studio") == "fail"
    assert _status(checks, "project") == "fail"
    assert _status(checks, "fmodstudiocl") == "warn"


def test_doctor_json_output(machine, monkeypatch, capsys):
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", str(_project(machine)))
    assert doctor.main(as_json=True) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True and {c["check"] for c in data["checks"]} >= {"project", "ffmpeg"}


def test_cli_version_does_not_start_the_server():
    out = subprocess.run(  # noqa: S603 - test runs this package's own CLI
        [sys.executable, "-m", "fmod_mcp.cli", "--version"],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0
    assert out.stdout.strip() == doctor.package_version()
    assert "Registered tools" not in out.stderr  # server modules never imported
