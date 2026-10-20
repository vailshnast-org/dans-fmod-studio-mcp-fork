import asyncio
import importlib
import inspect
import json
import os
import pkgutil
import shutil
import subprocess
import tempfile

import pytest

import fmod_mcp.main as main_mod  # noqa: F401  (import side effect: client exists)
import fmod_mcp.tools as tools_pkg
from fmod_mcp_shared.protocol import format_command


class StubMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def deco(fn):
            self.tools[fn.__name__] = fn
            return fn

        return deco


class StubClient:
    def __init__(self):
        self.calls = []

    async def execute(self, command, **params):
        self.calls.append((command, params))
        return {"success": True, "result": {"$status": "ok"}}

    async def execute_long(self, command, **params):
        self.calls.append((command, params))
        return {"success": True, "result": {"$status": "ok"}}


_A_GUID = "{00000000-0000-0000-0000-000000000001}"
_B_GUID = "{00000000-0000-0000-0000-000000000002}"
_C_GUID = "{00000000-0000-0000-0000-000000000003}"

# Sensible per-name samples so every tool can be invoked with valid-ish args.
_SAMPLES = {
    "name": "TestObject",
    "parameter_name": "Intensity",
    "path": "UI/HUD",
    "file_path": None,  # filled below with a real temp file
    "target": "event:/Test/TestObject",
    "event_target": "event:/Test/TestObject",
    "track_target": _A_GUID,
    "bank_target": "bank:/Test",
    "audio": _C_GUID,
    "owner": _B_GUID,
    "folder": "event:/UI",
    "output_target": "bus:/Master",
    "sound_type": "SingleSound",
    "param_type": "User",
    "effect": "CompressorEffect",
    "obj_type": "Event",
    "kind": "EventFolder",
    "labels": ["Off", "Quiet", "Loud"],
    "property": "volume",
    "driver": "parameter:/Intensity",
    "driver_type": "parameter",
    "position": 0.25,
    "value": -12.0,
    "points": [[0.0, -80.0], [0.5, -6.0], [1.0, 0.0]],
    "snapshot_target": "snapshot:/TestSnapshot",
    "group_target": "mixer:/Test/TestGroup",
    "destination_target": _B_GUID,
    "vca_target": "vca:/TestVCA",
    "strip_target": "mixer:/Test/TestGroup",
    "source_group_target": "mixer:/Test/TestGroup",
    "return_name": "TestReturn",
    "return_target": _C_GUID,
    "file_paths": None,  # filled below with real temp files
    "properties": {"volume": -6.0, "looping": True},
    "relationship": "output",
    "destination": _B_GUID,
    "entity": "SingleSound",
    "modulator_type": "RandomizerModulator",
    "parameter": "Intensity",
    "min": 0.0,
    "radial_distance": 10.0,
    "window_action": "RefreshModifiedAssets",
    "new_path": "sfx/player/step_01.wav",
    "plugin": "Steam Audio Spatializer",
    "percentage": 25.0,
    "entry": _A_GUID,
    "point": _A_GUID,
    "curve": _B_GUID,
}


# Tools whose arguments are all optional but that (correctly) refuse a call
# setting nothing — give them one field so the harness exercises their JS.
_EXTRA_ARGS = {
    "sound_set_properties": {"volume": -6.0},
    "sound_set_fade": {"fade_in": 0.5},
    "automation_set_point": {"value": -6.0},
    "multi_set_playlist": {"looping": True},
    "snapshot_set_settings": {"intensity": 50.0},
}


def _sample_args(fn):
    args = dict(_EXTRA_ARGS.get(fn.__name__, {}))
    sig = inspect.signature(fn)
    for pname, p in sig.parameters.items():
        if p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        if p.default is not inspect.Parameter.empty:
            continue  # exercise only required params
        if pname == "file_path" and _SAMPLES["file_path"] is not None:
            args[pname] = _SAMPLES["file_path"]
        elif pname == "file_paths" and _SAMPLES["file_path"] is not None:
            args[pname] = [_SAMPLES["file_path"]]
        elif pname in _SAMPLES:
            args[pname] = _SAMPLES[pname]
        elif p.annotation is str:
            args[pname] = f"sample-{pname}"
        elif p.annotation is int:
            args[pname] = 2
        elif p.annotation is float:
            args[pname] = 0.5
        elif p.annotation is bool:
            args[pname] = True
        elif getattr(p.annotation, "__origin__", None) is list:
            args[pname] = ["a", "b"]
        else:
            args[pname] = f"sample-{pname}"
    return args


def _balance(js):
    pairs = {"}": "{", ")": "(", "]": "["}
    stack = []
    # Track which quote opened the current string: command bodies use
    # single-quoted JS strings, the injected params are double-quoted JSON,
    # and either may legitimately contain brackets (e.g. charAt(0)==='{').
    in_str = None
    esc = False
    for ch in js:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == in_str:
                in_str = None
            continue
        if ch in "\"'":
            in_str = ch
        elif ch in "{([":
            stack.append(ch)
        elif ch in "})]":
            assert stack and stack[-1] == pairs[ch], f"mismatch {ch} in {js}"
            stack.pop()
    assert not stack, f"unbalanced: {stack}"


@pytest.fixture()
def stub_client(monkeypatch):
    client = StubClient()
    monkeypatch.setattr(main_mod, "client", client)
    return client


def _tool_modules():
    return [m.name for m in pkgutil.iter_modules(tools_pkg.__path__)]


def _run_every_tool():
    """Invoke every registered tool once with sample args (stub client)."""
    if _SAMPLES["file_path"] is None:
        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        _SAMPLES["file_path"] = path

    checked = 0
    tool_names = set()
    for name in _tool_modules():
        module = importlib.import_module(f"fmod_mcp.tools.{name}")
        if not hasattr(module, "register"):
            continue
        mcp = StubMCP()
        module.register(mcp)
        assert mcp.tools, f"{name} registered no tools"
        tool_names.update(mcp.tools)
        for tool_name, fn in mcp.tools.items():
            args = _sample_args(fn)
            result = asyncio.run(fn(**args))
            assert result["success"] is True, f"{tool_name} failed: {result}"
            checked += 1
    return checked, tool_names


def test_every_tool_registers_and_produces_valid_js(stub_client):
    checked, tool_names = _run_every_tool()

    assert stub_client.calls, "stub client never saw a command"
    # Every captured (command body, params) must form a balanced, parseable
    # JS wrapper — this is what actually gets sent to FMOD Studio.
    for body, params in stub_client.calls:
        js = format_command(body, **params)
        assert js.startswith("(function(){const p=")
        assert js.endswith("})()")
        _balance(js)

    # Sanity: core surface exists with sane reach.
    assert "event_create" in tool_names
    assert "project_build" in tool_names
    assert "bank_list_events" in tool_names
    assert checked >= 30, f"expected a rich tool surface, saw {checked}"


def test_no_arbitrary_eval_tool(stub_client):
    """Parity with Reaper-MCP's philosophy: no raw-script escape hatch."""
    mcp = StubMCP()
    for name in _tool_modules():
        module = importlib.import_module(f"fmod_mcp.tools.{name}")
        if hasattr(module, "register"):
            module.register(mcp)
    names = set(mcp.tools)
    assert not any("eval" in n or "exec" in n or "script" in n for n in names)


def test_params_never_break_out_of_wrapper(stub_client):
    """A hostile name must be able to escape neither its string nor the body."""
    hostile = '"); globalThis.pwned = 1; ("'
    js = format_command("return p.name;", name=hostile)
    assert "return p.name;" in js
    assert js.startswith("(function(){const p=")
    _balance(js)


# Parses (never runs) each payload with Node: new Function(src) throws a
# SyntaxError for malformed code without executing it. The bracket check
# above can't see statement-level errors — e.g. automation_add_curve once
# joined statements with "," ("a;,b;"), which balanced fine and failed only
# inside FMOD Studio as an opaque "Invalid JSON response".
_NODE_PARSE = r"""
const fs = require("fs");
const items = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const bad = [];
for (const it of items) {
  try { new Function("return " + it.js); }
  catch (e) { bad.push({ tool: it.tool, error: String(e) }); }
}
process.stdout.write(JSON.stringify(bad));
"""

# FMOD Studio's script engine is an older Qt JS engine; command bodies stick
# to ES5 plus the wrapper's own const. Arrow functions, template literals and
# let are the constructs most likely to slip in from modern-JS habits.
_ES6_ONLY = ("=>", "`", "let ")


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_every_command_is_syntactically_valid_js(stub_client, tmp_path):
    _run_every_tool()
    items = [
        {"tool": body[:60], "js": format_command(body, **params)}
        for body, params in stub_client.calls
    ]
    for body, _params in stub_client.calls:
        for token in _ES6_ONLY:
            assert token not in body, f"ES6-only {token!r} in command body: {body[:120]}"
    src = tmp_path / "items.json"
    src.write_text(json.dumps(items), encoding="utf-8")
    script = tmp_path / "parse.js"
    script.write_text(_NODE_PARSE, encoding="utf-8")
    out = subprocess.run(  # noqa: S603 - fixed argv, test-only
        [shutil.which("node"), str(script), str(src)],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    bad = json.loads(out.stdout)
    assert not bad, f"syntax errors in generated JS: {bad}"
