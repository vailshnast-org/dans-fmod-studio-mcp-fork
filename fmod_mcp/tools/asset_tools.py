import posixpath

from mcp.server.fastmcp import FastMCP

from fmod_mcp_shared.constants import MAX_OBJECTS_READ
from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError

# Audio assets on 2.03.15 (confirmed live): an AudioFile has no name and no
# folder object — its identity is `assetPath`, relative to the project's
# Assets directory ("light/L.neonLight.flac"), and `asset:/<assetPath>` is a
# lookup path. Asset "folders" are just subdirectories of that path, so
# organizing assets means Asset.setAssetPath(), which MOVES THE FILE ON DISK.

# Per-asset fields reported by every listing.
JS_ASSET_ROW = (
    "function __asset(a){var used=0;"
    "try{used=a.relationships.sounds.destinations.length+"
    "a.relationships.programmerSounds.destinations.length;}catch(__e){}"
    "return {guid:G(a),path:P(a),assetPath:a.assetPath,length:a.length,"
    "channels:a.channelCount,sampleRateKHz:a.frequencyInKHz,"
    "streaming:a.isStreaming,usedBy:used};}"
)


def _check_asset_path(path: str) -> str:
    """Normalize a destination asset path and keep it inside the Assets dir."""
    if not isinstance(path, str) or not path.strip():
        raise FmodMCPError(ErrorCode.INVALID_PATH, "new_path must not be empty")
    norm = path.strip().replace("\\", "/")
    if norm.startswith("asset:/"):
        norm = norm[len("asset:/") :]
    if norm.startswith("/") or (len(norm) > 1 and norm[1] == ":"):
        raise FmodMCPError(
            ErrorCode.INVALID_PATH,
            "new_path must be relative to the project's Assets folder, e.g. 'sfx/hit.wav'",
        )
    if any(seg in ("", ".", "..") for seg in norm.split("/")):
        raise FmodMCPError(
            ErrorCode.INVALID_PATH, f"new_path has an empty, '.' or '..' segment: {path!r}"
        )
    return posixpath.normpath(norm)


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def audio_asset_info(target: str) -> dict:
        """Details of one audio asset: asset path, absolute file path,
        length (s), channels, sample rate, streaming, and the instruments
        using it.

        Args:
            target: Asset {guid} or asset:/ path.
        """
        return await client.execute(
            JS_ASSET_ROW
            + "var a=L(p.target);"
            "if(!a.isOfType('AudioFile'))throw new Error(p.target+' is not an audio asset');"
            "var r=__asset(a);r.absolutePath=a.getAbsoluteAssetPath();"
            "var users=[];var sd=a.relationships.sounds.destinations||[];"
            f"for(var i=0;i<sd.length&&i<{MAX_OBJECTS_READ};i++){{"
            "var ev=null;try{ev=sd[i].audioTrack?sd[i].audioTrack.event:null;}catch(__e){}"
            "users.push({guid:G(sd[i]),entity:sd[i].entity,event:ev?P(ev):null});}"
            "r.instruments=users;return r;",
            target=target,
        )

    @mcp.tool()
    async def audio_asset_move(target: str, new_path: str) -> dict:
        """Move/rename an audio asset within the project's Assets folder —
        how assets are organized into folders. MOVES THE FILE ON DISK
        (Asset.setAssetPath); instruments keep pointing at it. Refuses to
        change the file extension or overwrite an existing asset.

        Args:
            target: Asset {guid} or asset:/ path.
            new_path: New path relative to Assets, e.g. "sfx/player/step_01.wav".
        """
        dest = _check_asset_path(new_path)
        return await client.execute(
            "var a=L(p.target);"
            "if(!a.isOfType('AudioFile'))throw new Error(p.target+' is not an audio asset');"
            "var old=a.assetPath;"
            "function ext(x){var i=x.lastIndexOf('.');return i<0?'':x.substring(i).toLowerCase();}"
            "if(ext(old)!==ext(p.dest))throw new Error('new_path must keep the extension '+ext(old));"
            "if(old===p.dest)return {guid:G(a),assetPath:old,moved:false};"
            "if(studio.project.lookup('asset:/'+p.dest))throw new Error('an asset already exists at '+p.dest);"
            # setAssetPath() returns undefined on 2.03.15 even when the move
            # succeeds (the docs say true/false) — judge by the read-back.
            "a.setAssetPath(p.dest);"
            "if(a.assetPath!==p.dest)throw new Error('setAssetPath failed (file locked or path invalid?)');"
            "return {guid:G(a),from:old,assetPath:a.assetPath,"
            "absolutePath:a.getAbsoluteAssetPath(),moved:true};",
            target=target,
            dest=dest,
        )
