"""`fmod-studio-mcp --doctor`: check a machine's setup without starting the server.

Prints one line per check (or JSON with --json) and exits non-zero when
something required is missing, so a setup script or CI step can gate on it.
Works whether or not FMOD Studio is running.
"""

import json
import os
import re
import subprocess
import sys
from importlib import metadata

from fmod_mcp.tools import studio_tools
from fmod_mcp.tools.analysis_tools import _ffmpeg

DIST_NAME = "xdarkzx-fmod-studio-mcp"

OK, WARN, FAIL = "ok", "warn", "fail"


def package_version() -> str:
    try:
        return metadata.version(DIST_NAME)
    except metadata.PackageNotFoundError:
        return "unknown (not installed as a package)"


def studio_version(cl: str | None) -> str | None:
    """'2.03.15' from `fmodstudiocl -version` (fast; no project loaded)."""
    if not cl:
        return None
    try:
        out = subprocess.run(  # noqa: S603 - path from install lookup, fixed args
            [cl, "-version"], capture_output=True, text=True, timeout=60
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"Version (\d+\.\d+\.\d+)", out)
    return m.group(1) if m else None


def run_checks() -> list[dict]:
    checks = []

    def add(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    add("fmod-studio-mcp", OK, package_version())

    inst = studio_tools.find_install()
    if inst["exe"]:
        add("FMOD Studio", OK, inst["exe"])
    else:
        add("FMOD Studio", FAIL, "not found - install it or set FMOD_STUDIO_EXE")
    version = studio_version(inst["cl"])
    if inst["cl"]:
        add("fmodstudiocl", OK, f"{inst['cl']} (version {version or 'unknown'})")
    else:
        add("fmodstudiocl", WARN, "not found - headless_build/headless_validate unavailable")

    project = studio_tools.default_project()
    if not os.environ.get("FMOD_STUDIO_PROJECT"):
        add("project", WARN, "FMOD_STUDIO_PROJECT not set - studio_launch/headless_* need an explicit path")
    elif not project or not os.path.isfile(project):
        add("project", FAIL, f"FMOD_STUDIO_PROJECT does not resolve to a file: {project}")
    else:
        fmt = studio_tools.project_format(project)
        add("project", OK, f"{project} (format {fmt or 'unknown'})")
        if fmt and version:
            studio_mm = ".".join(f"{int(x):02d}" for x in version.split(".")[:2])
            if studio_mm == fmt:
                add("version match", OK, f"Studio {version} opens format {fmt} without upgrading it")
            elif studio_mm > fmt:
                add("version match", WARN,
                    f"Studio {version} is newer than the project ({fmt}); saving upgrades the "
                    "project for everyone - agree on one Studio version first")
            else:
                add("version match", FAIL, f"Studio {version} is older than the project ({fmt}) and can't open it")

    pref = studio_tools.read_script_server_pref()
    if pref is True:
        add("Script Server preference", OK, "enabled")
    elif pref is False:
        add("Script Server preference", WARN, "off - studio_launch turns it on (Studio must be closed)")
    else:
        add("Script Server preference", WARN, "Studio settings not found - launch Studio once by hand")

    if studio_tools._server_reachable():
        add("Script Server", OK, "reachable - authoring tools available now")
    elif studio_tools.studio_process_running():
        add("Script Server", WARN, "Studio is running but not answering (no project open, or preference off)")
    else:
        add("Script Server", OK, "Studio not running - studio_launch starts it")

    ff, probe = _ffmpeg()
    if ff:
        add("ffmpeg", OK, f"{ff} - audio_analyze handles every format + LUFS")
    else:
        add("ffmpeg", WARN, "not found - audio_analyze limited to PCM WAV, no LUFS (winget install Gyan.FFmpeg)")
    return checks


def main(as_json: bool = False) -> int:
    checks = run_checks()
    failed = any(c["status"] == FAIL for c in checks)
    if as_json:
        print(json.dumps({"ok": not failed, "checks": checks}, indent=1))
    else:
        marks = {OK: "[ ok ]", WARN: "[warn]", FAIL: "[FAIL]"}
        for c in checks:
            print(f"{marks[c['status']]} {c['check']}: {c['detail']}")
        print("result:", "FAILED" if failed else "ready")
    sys.stdout.flush()
    return 1 if failed else 0
