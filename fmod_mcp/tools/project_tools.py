import os
import time

from mcp.server.fastmcp import FastMCP

from fmod_mcp.tools.studio_tools import build_outputs, studio_log_problems

from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError

# studio.window.actions members project_trigger_action may run. Deliberately
# excludes anything destructive or session-ending (Delete, RevertToSaved,
# CloseProject, ExitApplication, NewProject, OpenProject, Paste, source
# control, ...). Undo/Redo have their own tools with a step count.
SAFE_WINDOW_ACTIONS = frozenset(
    {
        "RefreshModifiedAssets",
        "ValidateProject",
        "ExportGuids",
        "ZoomToFit",
        "ToggleTransitionTimelineVisibility",
        "ShowLogicTracks",
    }
)

MAX_UNDO_STEPS = 20


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def project_get_info() -> dict:
        """Get the open project's file path and display name."""
        return await client.execute(
            "return {filePath: studio.project.filePath, name: N(studio.project)};"
        )

    @mcp.tool()
    async def project_save() -> dict:
        """Save the open FMOD Studio project (the active .fspro)."""
        return await client.execute("studio.project.save(); return true;")

    @mcp.tool()
    async def project_save_all() -> dict:
        """Save the project and every edited file (assets, banks, plugins)."""
        return await client.execute("studio.project.saveAll(); return true;")

    @mcp.tool()
    async def project_build(
        banks: list[str] | str | None = None,
        platforms: list[str] | str | None = None,
    ) -> dict:
        """Build banks inside the open Studio, or scope to specific
        banks/platforms (scoping a big project to one bank is much faster).
        Returns a build report: success, each bank/GUIDs file written (path,
        size) and any warning/error lines Studio logged during the build —
        check `problems` before assuming the banks are shippable.

        Args:
            banks: Bank name or list (default: every bank).
            platforms: Platform name or list (default: every platform).
        """
        started = time.time()
        if banks is None and platforms is None:
            r = await client.execute_long(
                "var ok=studio.project.build();"
                "return {built:!!ok,project:studio.project.filePath};"
            )
        else:
            r = await client.execute_long(
                "var opts={};"
                "if(p.banks!==null)opts.banks=p.banks;"
                "if(p.platforms!==null)opts.platforms=p.platforms;"
                "var ok=studio.project.build(opts);"
                "return {built:!!ok,project:studio.project.filePath};",
                banks=banks,
                platforms=platforms,
            )
        res = r.get("result") or {}
        project = res.get("project")
        res["outputs"] = build_outputs(os.path.dirname(project), started) if project else []
        res["problems"] = studio_log_problems(started)
        # Kept for callers of the pre-report version of this tool.
        res["success"] = res.get("built")
        return {"success": True, "result": res}

    @mcp.tool()
    async def project_get_modified() -> dict:
        """Check whether the project has unsaved changes."""
        return await client.execute(
            "var m = false;"
            "try { m = !!studio.project.isModified; } catch (__e) {}"
            "return {modified: m};"
        )

    @mcp.tool()
    async def project_undo(steps: int = 1) -> dict:
        """Undo the last edit(s) in Studio — the same as Edit > Undo, via
        studio.window.triggerAction(actions.Undo). One scripted tool call
        may be one or several undo steps; check the result with a read tool
        (event_describe, utility_dump) before undoing further.

        Args:
            steps: How many undo steps (1-20).
        """
        return await _trigger_repeated(client, "Undo", steps)

    @mcp.tool()
    async def project_redo(steps: int = 1) -> dict:
        """Redo edit(s) undone with project_undo (Edit > Redo).

        Args:
            steps: How many redo steps (1-20).
        """
        return await _trigger_repeated(client, "Redo", steps)

    @mcp.tool()
    async def project_trigger_action(window_action: str) -> dict:
        """Run one of Studio's own menu actions that has no scripting
        method. Limited to non-destructive actions: RefreshModifiedAssets
        (re-read changed audio files from disk), ValidateProject (Studio's
        own validation window), ExportGuids, ZoomToFit,
        ToggleTransitionTimelineVisibility, ShowLogicTracks.

        Args:
            window_action: One of the actions listed above.
        """
        if window_action not in SAFE_WINDOW_ACTIONS:
            raise FmodMCPError(
                ErrorCode.INVALID_TYPE,
                f"action {window_action!r} is not allowed; use one of "
                f"{', '.join(sorted(SAFE_WINDOW_ACTIONS))}",
            )
        return await client.execute(
            "var a=studio.window.actions[p.action];"
            "if(a===undefined)throw new Error('Studio has no window action '+p.action);"
            "var r=studio.window.triggerAction(a);"
            "return {action:p.action,result:(r===undefined?null:r)};",
            action=window_action,
        )

    @mcp.tool()
    async def project_export_guids() -> dict:
        """Export the project's GUIDs.txt (event/bus/VCA/snapshot GUIDs the
        game code can reference) next to the build output."""
        return await client.execute(
            "var ok=studio.project.exportGUIDs();return {success:!!ok};"
        )

    @mcp.tool()
    async def project_list_plugins() -> dict:
        """List the plug-in effects/instruments this Studio install can use
        (studio.project.findAvailablePlugins) — e.g. Steam Audio, Resonance."""
        return await client.execute(
            "var arr=studio.project.findAvailablePlugins()||[];var out=[];"
            "for(var i=0;i<arr.length;i++){out.push(String(arr[i]));}"
            "return {count:out.length,plugins:out};"
        )

    @mcp.tool()
    async def project_get_version() -> dict:
        """Get the running FMOD Studio version and OS — useful when an API
        behaves differently between Studio versions."""
        return await client.execute(
            "var v=studio.version;"
            "return {version:v?String(v):null,"
            "major:v?v.majorVersion:null,minor:v?v.minorVersion:null,"
            "product:v?v.productVersion:null,platform:studio.os?studio.os.platform:null};"
        )


async def _trigger_repeated(client, action: str, steps: int) -> dict:
    if not 1 <= steps <= MAX_UNDO_STEPS:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE, f"steps must be 1-{MAX_UNDO_STEPS}"
        )
    return await client.execute(
        "var a=studio.window.actions[p.action];"
        "if(a===undefined)throw new Error('Studio has no window action '+p.action);"
        "for(var i=0;i<p.steps;i++){studio.window.triggerAction(a);}"
        "var m=null;try{m=!!studio.project.isModified;}catch(__e){}"
        "return {action:p.action,steps:p.steps,modified:m};",
        action=action,
        steps=steps,
    )
