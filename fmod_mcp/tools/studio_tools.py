"""FMOD Studio process control and headless (command-line) builds.

Unlike every other module these tools run on the MCP host, not through the
Script Server, so they work while Studio is closed — which is the point:
an unattended agent has to be able to start Studio, wait for its Script
Server, build without a GUI, and shut Studio down again.

Paths to executables come only from the environment / well-known install
locations, never from tool arguments, so no tool can be used to launch an
arbitrary program. `fmodstudiocl -script` (run arbitrary JS) is deliberately
not exposed, in keeping with the no-escape-hatch policy.
"""

import asyncio
import glob
import os
import re
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from mcp.server.fastmcp import FastMCP

from fmod_mcp_shared.constants import Connection
from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError
from fmod_mcp_shared.path_safety import safe_path

# Where FMOD Studio is usually installed, newest version first after sorting.
_INSTALL_GLOBS_WIN = (
    r"C:\Program Files\FMOD SoundSystem\FMOD Studio *",
    r"C:\Program Files (x86)\FMOD SoundSystem\FMOD Studio *",
    r"C:\Apps\FMOD Studio*",
    r"C:\FMOD Studio*",
)
_INSTALL_GLOBS_MAC = ("/Applications/FMOD Studio*.app",)

# Headless build/validate can take a while on a big project.
HEADLESS_TIMEOUT = 1800.0
LAUNCH_WAIT_DEFAULT = 120.0
QUIT_WAIT = 60.0

# fmodstudiocl prints one progress line per step; only these matter.
_CL_PROBLEM_RE = re.compile(r"\b(error|warning|failed|could not)\b", re.IGNORECASE)
_CL_NOISE_PREFIXES = ("Validation Status:", "Build Status:")


def _version_key(path: str):
    nums = re.findall(r"\d+", os.path.basename(path.rstrip("\\/")))
    return [int(n) for n in nums]


def find_install() -> dict:
    """Locate FMOD Studio's GUI and command-line executables.

    FMOD_STUDIO_EXE (GUI) / FMOD_STUDIO_CL (command line) override the
    search. The command-line tool ships next to the GUI executable.
    """
    exe = os.environ.get("FMOD_STUDIO_EXE")
    cl = os.environ.get("FMOD_STUDIO_CL")
    if not exe:
        if sys.platform == "win32":
            roots = []
            for pattern in _INSTALL_GLOBS_WIN:
                roots.extend(glob.glob(pattern))
            for root in sorted(set(roots), key=_version_key, reverse=True):
                cand = os.path.join(root, "FMOD Studio.exe")
                if os.path.isfile(cand):
                    exe = cand
                    break
        elif sys.platform == "darwin":
            for app in sorted(glob.glob(_INSTALL_GLOBS_MAC[0]), key=_version_key, reverse=True):
                cand = os.path.join(app, "Contents", "MacOS", "FMOD Studio")
                if os.path.isfile(cand):
                    exe = cand
                    break
    if exe and not cl:
        name = "fmodstudiocl.exe" if sys.platform == "win32" else "fmodstudiocl"
        cand = os.path.join(os.path.dirname(exe), name)
        if os.path.isfile(cand):
            cl = cand
    return {"exe": exe if exe and os.path.isfile(exe) else None,
            "cl": cl if cl and os.path.isfile(cl) else None}


def _settings_file() -> str | None:
    """Studio's per-user preferences file (holds scriptServerEnabled)."""
    if sys.platform == "win32":
        base = os.path.join(os.environ.get("LOCALAPPDATA", ""), "FMOD Studio", "Settings")
    else:
        base = os.path.expanduser("~/Library/Application Support/FMOD Studio/Settings")
    files = sorted(glob.glob(os.path.join(base, "Studio.*.config")), key=_version_key, reverse=True)
    return files[0] if files else None


def _logs_dir() -> str | None:
    if sys.platform == "win32":
        d = os.path.join(os.environ.get("LOCALAPPDATA", ""), "FMOD Studio", "Logs")
    else:
        d = os.path.expanduser("~/Library/Application Support/FMOD Studio/Logs")
    return d if os.path.isdir(d) else None


def read_script_server_pref() -> bool | None:
    path = _settings_file()
    if not path:
        return None
    try:
        root = ET.parse(path).getroot()  # noqa: S314 - Studio's own prefs file in the user profile
    except (ET.ParseError, OSError):
        return None
    for prop in root.iter("property"):
        if prop.get("name") == "scriptServerEnabled":
            val = prop.find("value")
            return val is not None and (val.text or "").strip().lower() == "true"
    return False


def enable_script_server_pref() -> str:
    """Set scriptServerEnabled=true in Studio's preferences file.

    Only safe while Studio is closed — Studio rewrites the file on exit.
    Returns what happened ("already", "enabled", "created").
    """
    path = _settings_file()
    if not path:
        raise FmodMCPError(
            ErrorCode.INVALID_PATH,
            "FMOD Studio preferences file not found — launch Studio once by hand "
            "so it creates its settings, then retry.",
        )
    tree = ET.parse(path)  # noqa: S314 - Studio's own prefs file in the user profile
    root = tree.getroot()
    editor = None
    for obj in root.iter("object"):
        if obj.get("class") == "EditorSettings":
            editor = obj
            break
    if editor is None:
        raise FmodMCPError(
            ErrorCode.INVALID_FORMAT,
            f"no EditorSettings in {path}; enable the Script Server in Studio's "
            "Preferences > Interface by hand.",
        )
    for prop in editor.findall("property"):
        if prop.get("name") == "scriptServerEnabled":
            val = prop.find("value")
            if val is not None and (val.text or "").strip().lower() == "true":
                return "already"
            if val is None:
                val = ET.SubElement(prop, "value")
            val.text = "true"
            tree.write(path, encoding="UTF-8", xml_declaration=True)
            return "enabled"
    prop = ET.SubElement(editor, "property", {"name": "scriptServerEnabled"})
    ET.SubElement(prop, "value").text = "true"
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    return "created"


def _server_reachable(timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((Connection.host(), Connection.port()), timeout=timeout):
            return True
    except OSError:
        return False


def studio_process_running() -> bool:
    """Whether an FMOD Studio GUI process exists (any project)."""
    try:
        if sys.platform == "win32":
            tasklist = os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "System32", "tasklist.exe")
            out = subprocess.run(  # noqa: S603 - fixed argv
                [tasklist, "/FI", "IMAGENAME eq FMOD Studio.exe", "/NH"],
                capture_output=True, text=True, timeout=15,
            ).stdout
            return "FMOD Studio.exe" in out
        out = subprocess.run(  # noqa: S603 - fixed argv
            ["/usr/bin/pgrep", "-f", "FMOD Studio.app/Contents/MacOS/FMOD Studio"],
            capture_output=True, text=True, timeout=15,
        ).stdout
        return bool(out.strip())
    except (OSError, subprocess.SubprocessError):
        return False


def default_project() -> str | None:
    """FMOD_STUDIO_PROJECT, with a relative value resolved for a shared config.

    A committed team config can't hold one person's absolute path, so a
    relative value ("FMODProject/game.fspro") is looked up against, in order:
    CLAUDE_PROJECT_DIR (Claude Code sets it to the project root for servers it
    spawns), the working directory, and the working directory's parents (other
    clients' working directory isn't specified). The first existing match
    wins; if none exists the first candidate is returned so the error names a
    concrete path.
    """
    raw = os.environ.get("FMOD_STUDIO_PROJECT")
    if not raw:
        return None
    raw = os.path.expanduser(raw)
    if os.path.isabs(raw):
        return raw
    bases = []
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    if root:
        bases.append(root)
    cwd = os.getcwd()
    bases.append(cwd)
    parent = os.path.dirname(cwd)
    for _ in range(5):
        if not parent or parent == bases[-1]:
            break
        bases.append(parent)
        parent = os.path.dirname(parent)
    candidates = [os.path.normpath(os.path.join(b, raw)) for b in bases]
    for cand in candidates:
        if os.path.isfile(cand):
            return cand
    return candidates[0]


def project_format(path: str) -> str | None:
    """The .fspro's serialization version, e.g. "02.03" (None if unreadable)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            head = fh.read(400)
    except OSError:
        return None
    m = re.search(r'serializationModel="Studio\.(\d+)\.(\d+)', head)
    return f"{m.group(1)}.{m.group(2)}" if m else None


def check_project_path(path: str | None) -> str:
    """Resolve the target .fspro: explicit (absolute) arg, else FMOD_STUDIO_PROJECT."""
    path = path or default_project()
    if not path:
        raise FmodMCPError(
            ErrorCode.MISSING_PARAMETER,
            "no project given — pass project_path or set FMOD_STUDIO_PROJECT "
            "to the .fspro in the MCP server's environment",
        )
    resolved = safe_path(path)
    if not resolved.lower().endswith(".fspro"):
        raise FmodMCPError(ErrorCode.INVALID_PATH, f"not an .fspro project file: {resolved}")
    if not os.path.isfile(resolved):
        raise FmodMCPError(ErrorCode.INVALID_PATH, f"project not found: {resolved}")
    return resolved


def _same_path(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def build_outputs(project_dir: str, since: float) -> list[dict]:
    """Bank / GUID files under the project written at or after `since`."""
    out = []
    for dirpath, _dirs, files in os.walk(project_dir):
        rel = os.path.relpath(dirpath, project_dir)
        top = rel.split(os.sep)[0]
        if top in ("Assets", "Metadata", ".unsaved", ".user", ".cache", "Plugins"):
            continue
        for name in files:
            if not (name.endswith(".bank") or name.lower() == "guids.txt"):
                continue
            full = os.path.join(dirpath, name)
            st = os.stat(full)
            if st.st_mtime >= since - 1:
                out.append({
                    "path": full,
                    "relative": os.path.relpath(full, project_dir).replace("\\", "/"),
                    "bytes": st.st_size,
                })
    return sorted(out, key=lambda x: x["relative"])


def studio_log_problems(since: float, limit: int = 100) -> list[str]:
    """Warning/error lines from Studio's newest log written after `since`."""
    d = _logs_dir()
    if not d:
        return []
    logs = sorted(glob.glob(os.path.join(d, "*_log.txt")), key=os.path.getmtime, reverse=True)
    if not logs:
        return []
    lines = []
    stamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(since - 1))
    try:
        with open(logs[0], encoding="utf-8", errors="replace") as fh:
            for line in fh:
                ts = line[2:21] if len(line) > 21 else ""
                if ts and ts < stamp:
                    continue
                if line.startswith(("*", "!")) or _CL_PROBLEM_RE.search(line):
                    if "ScriptServer" in line or "Script Server" in line:
                        continue
                    lines.append(line.rstrip())
                    if len(lines) >= limit:
                        break
    except OSError:
        return []
    return lines


def _parse_cl_output(text: str) -> dict:
    problems, summary = [], []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(_CL_NOISE_PREFIXES):
            continue
        if _CL_PROBLEM_RE.search(line):
            problems.append(line)
        else:
            summary.append(line)
    return {"problems": problems[:200], "messages": summary[-30:]}


async def _run_cl(args: list[str], timeout: float = HEADLESS_TIMEOUT) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise FmodMCPError(
            ErrorCode.COMMAND_TIMEOUT, f"fmodstudiocl did not finish within {timeout:g}s"
        )
    return proc.returncode, out.decode("utf-8", errors="replace")


def _split_names(value) -> str | None:
    if value is None:
        return None
    items = [value] if isinstance(value, str) else list(value)
    for item in items:
        if not isinstance(item, str) or not item.strip() or "," in item:
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER, f"invalid bank/platform name: {item!r}"
            )
    return ",".join(i.strip() for i in items)


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    async def _open_project_path() -> str | None:
        if not _server_reachable():
            return None
        try:
            r = await client.execute("return {f:studio.project.filePath};")
            return (r.get("result") or {}).get("f")
        except FmodMCPError:
            return None

    async def _refuse_if_open_in_gui(project: str) -> None:
        open_path = await _open_project_path()
        if _same_path(open_path, project):
            raise FmodMCPError(
                ErrorCode.COMMAND_REJECTED,
                "this project is open in FMOD Studio — use project_build / "
                "utility_validate (they run inside Studio), or studio_quit first. "
                "Building it headless at the same time would race Studio's own "
                "writes to the project.",
            )

    @mcp.tool()
    async def studio_status() -> dict:
        """Where FMOD Studio stands right now, without needing it to run:
        install found (GUI + command-line tool), whether the Studio process
        is running, whether its Script Server answers, which project is open
        (and unsaved?), whether the Script Server preference is on, and the
        default project (FMOD_STUDIO_PROJECT). Call this first in an
        unattended session.
        """
        inst = find_install()
        running = studio_process_running()
        reachable = _server_reachable()
        project = modified = version = None
        if reachable:
            try:
                r = await client.execute(
                    "var m=null;try{m=!!studio.project.isModified;}catch(__e){}"
                    "return {f:studio.project.filePath,m:m,v:String(studio.version)};"
                )
                res = r.get("result") or {}
                project, modified, version = res.get("f"), res.get("m"), res.get("v")
            except FmodMCPError:
                pass
        default = default_project()
        return {
            "success": True,
            "result": {
                "studioExe": inst["exe"],
                "commandLineTool": inst["cl"],
                "processRunning": running,
                "scriptServerReachable": reachable,
                "scriptServerPreference": read_script_server_pref(),
                "openProject": project,
                "unsavedChanges": modified,
                "studioVersion": version,
                "defaultProject": default,
                "defaultProjectIsOpen": _same_path(project, default) if default else None,
            },
        }

    @mcp.tool()
    async def studio_launch(
        project_path: str | None = None,
        wait_seconds: float = LAUNCH_WAIT_DEFAULT,
        enable_script_server: bool = True,
    ) -> dict:
        """Start FMOD Studio on a project and wait until its Script Server
        answers with that project open — after this every authoring tool
        works. No-op if it is already open.

        If Studio is running on a different project (or without a Script
        Server) it refuses rather than touching someone's open session. With
        enable_script_server (default), turns on Studio's "Enable Script
        Server" preference first — only possible while Studio is closed.

        Args:
            project_path: .fspro to open (default: FMOD_STUDIO_PROJECT).
            wait_seconds: How long to wait for the Script Server (10-600).
            enable_script_server: Turn the preference on if it is off.
        """
        project = check_project_path(project_path)
        if not 10 <= wait_seconds <= 600:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "wait_seconds must be 10-600")
        open_path = await _open_project_path()
        if open_path is not None:
            if _same_path(open_path, project):
                return {"success": True, "result": {"project": open_path, "launched": False,
                                                    "alreadyOpen": True}}
            raise FmodMCPError(
                ErrorCode.COMMAND_REJECTED,
                f"FMOD Studio already has another project open ({open_path}); save and "
                "close it (studio_quit) before launching a different one.",
            )
        if studio_process_running():
            raise FmodMCPError(
                ErrorCode.COMMAND_REJECTED,
                "FMOD Studio is running but its Script Server is not answering (no project "
                "open, or the Script Server preference is off). Close Studio, then call "
                "studio_launch again.",
            )
        inst = find_install()
        if not inst["exe"]:
            raise FmodMCPError(
                ErrorCode.INVALID_PATH,
                "FMOD Studio not found — install it or set FMOD_STUDIO_EXE to 'FMOD Studio.exe'.",
            )
        pref = None
        if enable_script_server and read_script_server_pref() is not True:
            pref = enable_script_server_pref()
        elif read_script_server_pref() is False:
            raise FmodMCPError(
                ErrorCode.COMMAND_REJECTED,
                "the Script Server preference is off; pass enable_script_server=true",
            )
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
                  "stdin": subprocess.DEVNULL, "close_fds": True}
        if sys.platform == "win32":
            kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS|NEW_PROCESS_GROUP
        else:
            kwargs["start_new_session"] = True
        subprocess.Popen([inst["exe"], project], **kwargs)  # noqa: S603 - exe from install lookup only
        deadline = time.monotonic() + wait_seconds
        while time.monotonic() < deadline:
            await asyncio.sleep(2.0)
            open_path = await _open_project_path()
            if _same_path(open_path, project):
                return {"success": True, "result": {"project": open_path, "launched": True,
                                                    "scriptServerPreference": pref or "already"}}
        raise FmodMCPError(
            ErrorCode.CONNECTION_TIMEOUT,
            f"Studio was started but its Script Server did not answer with {project} open "
            f"within {wait_seconds:g}s. A dialog (crash recovery, version upgrade, login) may "
            "be waiting in the Studio window.",
        )

    @mcp.tool()
    async def studio_quit(save: bool = True) -> dict:
        """Close FMOD Studio cleanly. Saves first by default; with save=false
        it refuses if there are unsaved changes (Studio would block on a
        "save changes?" dialog, which an unattended session can't answer).

        Args:
            save: Save the project before quitting (default true).
        """
        if not _server_reachable():
            return {"success": True, "result": {"quit": False, "reason": "Script Server not reachable"
                                                + (" (Studio is running)" if studio_process_running() else "")}}
        r = await client.execute(
            "var m=false;try{m=!!studio.project.isModified;}catch(__e){}"
            "if(p.save){studio.project.save();m=false;}"
            "if(m)throw new Error('the project has unsaved changes - call with save=true');"
            "var f=studio.project.filePath;"
            "studio.window.triggerAction(studio.window.actions.ExitApplication);"
            "return {project:f};",
            save=save,
        )
        deadline = time.monotonic() + QUIT_WAIT
        while time.monotonic() < deadline:
            await asyncio.sleep(1.0)
            if not _server_reachable() and not studio_process_running():
                return {"success": True, "result": {"quit": True, "saved": save,
                                                    "project": r["result"]["project"]}}
        raise FmodMCPError(
            ErrorCode.COMMAND_TIMEOUT,
            "asked Studio to exit but it is still running — a dialog may be open in its window",
        )

    @mcp.tool()
    async def headless_build(
        project_path: str | None = None,
        banks: list[str] | str | None = None,
        platforms: list[str] | str | None = None,
        export_guids: bool = True,
    ) -> dict:
        """Build banks with FMOD's command-line tool — no Studio window needed
        (CI, or after studio_quit). Returns success, every warning/error line,
        and each bank/GUIDs file written with its size. Refuses if the same
        project is open in Studio (use project_build there instead).

        Args:
            project_path: .fspro to build (default: FMOD_STUDIO_PROJECT).
            banks: Bank name(s) to build (default: all).
            platforms: Platform name(s) (default: all).
            export_guids: Also write GUIDs.txt (default true).
        """
        project = check_project_path(project_path)
        cl = find_install()["cl"]
        if not cl:
            raise FmodMCPError(ErrorCode.INVALID_PATH,
                               "fmodstudiocl not found — set FMOD_STUDIO_CL")
        await _refuse_if_open_in_gui(project)
        args = [cl, "-build"]
        bank_arg, plat_arg = _split_names(banks), _split_names(platforms)
        if bank_arg:
            args += ["-banks", bank_arg]
        if plat_arg:
            args += ["-platforms", plat_arg]
        if export_guids:
            args.append("-export-guids")
        args.append(project)
        started = time.time()
        code, text = await _run_cl(args)
        parsed = _parse_cl_output(text)
        ok = code == 0 and "Build completed successfully" in text
        return {"success": True, "result": {
            "built": ok, "exitCode": code, "project": project,
            "problems": parsed["problems"], "messages": parsed["messages"],
            "outputs": build_outputs(os.path.dirname(project), started),
        }}

    @mcp.tool()
    async def headless_validate(project_path: str | None = None) -> dict:
        """Run FMOD's own project diagnostic (corruption, dangling objects,
        cyclical references) with the command-line tool — no Studio window
        needed. Complements utility_validate's content audit. Refuses if the
        project is open in Studio.

        Args:
            project_path: .fspro to check (default: FMOD_STUDIO_PROJECT).
        """
        project = check_project_path(project_path)
        cl = find_install()["cl"]
        if not cl:
            raise FmodMCPError(ErrorCode.INVALID_PATH,
                               "fmodstudiocl not found — set FMOD_STUDIO_CL")
        await _refuse_if_open_in_gui(project)
        code, text = await _run_cl([cl, "-diagnostic", project])
        parsed = _parse_cl_output(text)
        ok = code == 0 and "validation completed successfully" in text.lower()
        return {"success": True, "result": {
            "valid": ok, "exitCode": code, "project": project,
            "problems": parsed["problems"], "messages": parsed["messages"],
        }}
