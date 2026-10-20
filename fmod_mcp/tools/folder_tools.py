from mcp.server.fastmcp import FastMCP

from fmod_mcp.tools._common import JS_FOLDER_CHAIN
from fmod_mcp_shared.constants import MAX_OBJECTS_READ
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode

ALLOWED_FOLDER_KINDS = {"EventFolder", "BankFolder", "AssetFolder"}


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def folder_create(kind: str, path: str) -> dict:
        """Find-or-create a folder chain (e.g. "UI/HUD" resolves/creates UI
        then HUD) — safe to call repeatedly, reuses existing folders.

        Args:
            kind: EventFolder | BankFolder | AssetFolder. AssetFolder isn't
                  creatable (2.03 has no such entity; asset folders are just
                  asset-path subdirectories — use audio_asset_move).
            path: Slash-separated, e.g. "UI/HUD".
        """
        if kind not in ALLOWED_FOLDER_KINDS:
            raise FmodMCPError(ErrorCode.INVALID_TYPE, f"invalid folder kind {kind!r}")
        return await client.execute(
            JS_FOLDER_CHAIN
            + "var cur=__folderChain(p.kind,p.path);"
            "return {guid:G(cur),name:N(cur),path:P(cur)};",
            kind=kind,
            path=path,
        )

    @mcp.tool()
    async def folder_list(kind: str | None = None) -> dict:
        """List folders in the project browser (capped).

        Args:
            kind: Optional filter — EventFolder | BankFolder. Omit for all.
        """
        # js_list can't filter — inline the cap+filter so the model never
        # floods the reply with folders from both browsers.
        body = (
            "var all=studio.project.model.Folder.findInstances()||[];"
            "var out=[];"
            "for(var i=0;i<all.length&&out.length<{cap};i++){{"
            "var o=all[i];"
            "if(p.kind&&!(o.isOfExactType&&o.isOfExactType(p.kind)))continue;"
            "out.push({{guid:G(o),name:N(o),path:P(o)}});}}"
            "return out;".format(cap=MAX_OBJECTS_READ)
        )
        return await client.execute(body, kind=kind)
