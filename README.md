<!-- mcp-name: io.github.xDarkzx/fmod-studio-mcp-dk -->
<h1 align="center">FmodStudioMCP</h1>

<p align="center">
  <strong>AI-powered game-audio authoring in FMOD Studio through the Model Context Protocol</strong>
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg" alt="License" /></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-compatible-purple.svg" alt="MCP Compatible" /></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-0.4.0-orange.svg" alt="v0.4.0" /></a>
  <a href="https://github.com/xDarkzx/Dans_Fmod_Studio_MCP/actions/workflows/ci.yml"><img src="https://github.com/xDarkzx/Dans_Fmod_Studio_MCP/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <a href="https://www.fmod.com/"><img src="https://img.shields.io/badge/FMOD%20Studio-2.02%2B-red.svg" alt="FMOD Studio 2.02+" /></a>
  <a href="https://github.com/sponsors/xDarkzx"><img src="https://img.shields.io/badge/Sponsor-30363D?logo=githubsponsors&logoColor=EA4AAA" alt="Sponsor" /></a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#features">Features</a> &bull;
  <a href="docs/TOOLS.md">Tools Reference</a> &bull;
  <a href="docs/ARCHITECTURE.md">Architecture</a> &bull;
  <a href="CHANGELOG.md">Changelog</a> &bull;
  <a href="CONTRIBUTING.md">Contributing</a> &bull;
  <a href="#troubleshooting">Troubleshooting</a>
</p>

---

FmodStudioMCP connects any MCP-compatible AI assistant to [FMOD Studio](https://www.fmod.com/), the game-audio middleware, and gives it full control over the authoring tool. Talk to your AI and it creates events, imports audio, builds parameter cultures, routes mixer buses, assigns banks, and builds your project — while you watch the editor apply every change live.

It runs over FMOD Studio's **built-in JavaScript scripting terminal** (TCP, port 3663), so — like its sibling ReaperMCP — there is **no plugin, no cloud, nothing to install inside the tool**: FMOD Studio ships the bridge. The MCP server is the only new piece, and it talks to a stock FMOD Studio install.

**If this is useful to you, a star helps other people find it.**

### Works With

- Claude Desktop, Claude Code, Cursor, or any [MCP-compatible client](https://modelcontextprotocol.io/clients)

---

## Quick Start

### 1. Get FmodStudioMCP

Install directly:

```powershell
pip install xdarkzx-fmod-studio-mcp
```

or clone and `pip install -e .` for development (see [CONTRIBUTING.md](CONTRIBUTING.md)).

### 2. Enable FMOD Studio's Script Server (one time)

The scripting terminal is **disabled by default**, and opening the console with **Ctrl+0 is not enough** — that only shows output.

1. Launch **FMOD Studio** and open your project (`.fspro`).
2. `Edit → Preferences…` (Windows) or `FMOD Studio → Preferences…` (macOS).
3. On the **Interface** tab, tick **Enable Script Server (requires restart)**.
4. **Quit and relaunch FMOD Studio**, then reopen the project. The port is `3663` by default.

> Confirmed it's listening? Check the newest log under `%LOCALAPPDATA%\FMOD Studio\Logs\` for `[Scripting] ScriptServer started on 127.0.0.1 (3663)`.

### 3. Register the server with your MCP client

```json
{
  "mcpServers": {
    "fmod-studio": {
      "command": "fmod-studio-mcp"
    }
  }
}
```

`fmod-studio-mcp` reads `FMOD_STUDIO_HOST` / `FMOD_STUDIO_PORT` (defaults `127.0.0.1:3663`) if your setup differs.

### 4. Start authoring

```
"List every event in the project"
"Create an event called 'Player/Footsteps' with a SingleSound loop of footsteps.wav"
"Add a 'Fear' User parameter to it, range 0-1, initial 0"
"Assign it to the Master bank and build the project"
```

> **FMOD Studio must be running with a project open.** The bridge cannot launch Studio for you, and the Script Server only binds once a project is open.

---

## Features

### Curated tool surface (not generated)

Unlike auto-generated "one tool per API member" servers, every tool here is hand-shaped around the real authoring workflow. 135+ tools in 15 modules —

| Module | Tools | Highlights |
|--------|------:|------------|
| **Project** | 11 | Info, save, build (scoped), modified-check, **undo/redo**, safe menu actions, GUID export, plug-in list, version |
| **Events** | 12 | Create (2D/3D)/delete/list/lookup, rename, folders, group tracks, maxVoices, timeline scrub, one-call `event_describe` |
| **Audition** | 7 | Play/stop/pause/keyoff, return-to-start, playback status, 3D listener position — hear the result, don't just read the tree |
| **Markers** | 12 | Marker tracks, named markers, loop regions, sustain points, transition markers/regions/timelines, list/rename/reposition/delete |
| **Sounds** | 19 | Import (single/batch), place instruments (incl. plug-in instruments) on the timeline or a parameter sheet, playback properties, fades, **MultiSound playlist editing + weights**, asset listing, **build an event from audio files in one call** |
| **Assets** | 2 | Asset details, move/rename assets into folders |
| **Parameters** | 7 | All 11 parameter types, labels, **global parameters**, initial values, **live parameter values while auditioning**, **trigger conditions** |
| **Banks** | 9 | Create (into bank folders)/rename/delete/move, assign/remove events, list membership |
| **Automation** | 7 | Parameter/timeline-driven curves on any automatable property, point editing/shapes, automation lanes — the heart of evolving/interactive music |
| **Modulators** | 2 | Random/AHDSR/sidechain/autopitch modulators on any property |
| **Snapshots** | 10 | Mixer state presets: scope strips, **capture property values**, intensity/behavior |
| **Mixer** | 23 | Groups + routing, dB volume, effect chains (built-in + **plug-in effects**, settings, remove), master bus, VCAs (assign/unassign/list), **project-level return buses + sends** |
| **Folders** | 2 | Create hierarchies, list browser tree |
| **Workspace** | 4 | Browser/editor selection, navigate-to, roots |
| **Utility** | 10 | Lookup/list (any entity type)/delete/isValid, dump, **validated property + relationship editing**, entity schemas, project audit |

### Typed, safe by default

- Every command is a named, schema-validated operation — **no arbitrary-script escape hatch** (same policy as ReaperMCP).
- Values are validated before they reach Studio (names, dB ranges, type whitelists, audio file paths/extensions).
- Params travel as inert JSON literals into a self-trapping JS wrapper — a hostile string can't break out of its quotes or reach the command body.
- Results are capped (`MAX_OBJECTS_READ`, etc.) so a busy project can't flood your model's context window.

### Profile-trimmable tool surface

Smaller/cheaper models truncate tool lists. Set `FMOD_STUDIO_MCP_PROFILE` in your client's server config to pick a workflow-specific subset:

| Profile | For |
|---------|-----|
| `full` *(default)* | All 15 modules |
| `events` | Building/editing events, sounds, parameters, modulators, audition, markers |
| `mixer` | Mixer structure, routing, effects, modulators, audition, markers |
| `banks` | Bank management + build plumbing |
| `minimal` | Read the project, verify the bridge |

### Production-grade plumbing, same as ReaperMCP

- TCP bridge with **read-until-idle** framing + typed connection/timeout errors (never a silent hang).
- Cross-process **file mutex** so multiple MCP clients can share one Studio without their evals interleaving.
- **Command history** archive (30-day retention) for after-the-fact debugging.
- Startup **UTF-8 stdio fix** and a self-retiring **parent watchdog** — battle-tested client behaviour inherited from ReaperMCP.

---

## Architecture

```
┌──────────────┐    stdio    ┌──────────────┐    TCP 3663    ┌──────────────┐
│  MCP Client  │◄──────────►│ FmodStudioMCP│◄──────────────►│ FMOD Studio  │
│(AI assistant)│  (JSON-RPC) │   FastMCP    │  (JS eval)     │ (JS terminal)│
└──────────────┘             └──────────────┘                └──────────────┘
```

The Python server wraps every tool's command body in a self-evaluating, error-trapping JavaScript IIFE, sends it to the Script Server, and parses the string reply back into a structured result. **No cloud. Nothing leaves your machine** — Studio and the AI talk over localhost.

> Full details — framing, wrapping, safety limits, lifecycle — in **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "Cannot reach FMOD Studio's scripting terminal" | Script Server isn't enabled. Preferences → Interface → tick **Enable Script Server** → **restart** FMOD Studio, then open a project. |
| Enabled but nothing on 3663 | A project must be **open** before the server binds. Check `%LOCALAPPDATA%\FMOD Studio\Logs\` (newest file) for `ScriptServer started` vs `is disabled`. |
| Port conflict | Set the same value in FMOD Studio's Preferences and `FMOD_STUDIO_PORT`. |
| Claude Desktop doesn't see it | Restart Claude Desktop after editing its config file. |
| "command not found: fmod-studio-mcp" | Reinstall with `pip install xdarkzx-fmod-studio-mcp`, or `pip install -e .` from the repo. |

---

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -x -q
ruff check .
```

### Adding a tool

1. Add a module in `fmod_mcp/tools/` (or extend an existing one).
2. Export `register(mcp: FastMCP)`.
3. Define tools with `@mcp.tool()`, using the `client.execute("js body", **params)` helper.
4. Add the module name to `_EXPECTED_MODULES` in `tool_registry.py`.
5. Every new tool is automatically exercised by the test harness in `tests/test_tools_registration.py`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

Built by **Daniel Hodgetts** ([@xDarkzx](https://github.com/xDarkzx)).

---

Need a custom tool, plugin, or integration built like this? Open an issue.