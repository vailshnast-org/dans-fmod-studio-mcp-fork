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


# EncodingSetting.encodingFormat values, identified on 2.03.15 by building a
# bank with each value and reading the codec id from the bank's FSB5 sample
# header (0 -> PCM16, 1 -> FADPCM, 2 -> XMA, 3 -> Vorbis, 5 -> Opus; 4 asked
# for Sony's libatrac9.dll, i.e. ATRAC9). Values 6+ are silently reset to 0.
ENCODING_FORMATS = {"pcm": 0, "fadpcm": 1, "xma": 2, "vorbis": 3, "at9": 4, "opus": 5}
_FORMAT_NAMES = {v: k for k, v in ENCODING_FORMATS.items()}

# EncodingSetting.sampleRateMode, identified the same way (per-sample
# frequency codes in the FSB5 headers): 0 resamples every asset to
# `sampleRate`, 1 lets Studio pick per asset, 2 keeps each source's rate.
SAMPLE_RATE_MODES = {"fixed": 0, "optimize": 1, "preserve": 2}
_RATE_MODE_NAMES = {v: k for k, v in SAMPLE_RATE_MODES.items()}
FIXED_SAMPLE_RATES = (8000, 11025, 16000, 22050, 24000, 32000, 44100, 48000, 96000)
MAX_ENCODING_TARGETS = 500

_JS_PLATFORM = (
    "function __platform(name){var ps=studio.project.model.Platform.findInstances()||[];"
    "if(!name){if(ps.length===1)return ps[0];"
    "throw new Error('project has several platforms ('+ps.map(function(x){return x.name;}).join(', ')+"
    "') - pass platform');}"
    "for(var i=0;i<ps.length;i++){if(ps[i].name===name)return ps[i];}"
    "throw new Error('no platform named '+name+' (have: '+ps.map(function(x){return x.name;}).join(', ')+')');}"
    "function __override(a,pl){var es=a.relationships.encodingSettings.destinations||[];"
    "for(var i=0;i<es.length;i++){if(es[i].platform&&G(es[i].platform)===G(pl))return es[i];}return null;}"
    "function __enc(es){return es?{format:es.encodingFormat,quality:es.quality,"
    "sampleRateMode:es.sampleRateMode,sampleRate:es.sampleRate}:null;}"
    "function __assets(p){var out=[];"
    "if(p.targets){for(var i=0;i<p.targets.length;i++){var a=L(p.targets[i]);"
    "if(!a.isOfType('AudioFile'))throw new Error(p.targets[i]+' is not an audio asset');out.push(a);}}"
    "if(p.folder){var all=studio.project.model.AudioFile.findInstances()||[];"
    "for(var j=0;j<all.length;j++){if(String(all[j].assetPath).indexOf(p.folder)===0)out.push(all[j]);}}"
    "return out;}"
)


def _label(table: dict, value):
    return table.get(value, value)


def _folder_prefix(folder: str | None) -> str | None:
    if folder is None:
        return None
    norm = _check_asset_path(folder.rstrip("/\\") + "/x").rsplit("/", 1)[0]
    return norm + "/"


def _encoding_values(fmt, quality, rate_mode, rate) -> dict:
    vals = {}
    if fmt is not None:
        key = str(fmt).strip().lower()
        if key not in ENCODING_FORMATS:
            raise FmodMCPError(
                ErrorCode.INVALID_TYPE, f"format must be one of {', '.join(ENCODING_FORMATS)}"
            )
        vals["encodingFormat"] = ENCODING_FORMATS[key]
    if quality is not None:
        if not 1 <= quality <= 100:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "quality must be 1-100")
        vals["quality"] = int(quality)
    if rate_mode is not None:
        key = str(rate_mode).strip().lower()
        if key not in SAMPLE_RATE_MODES:
            raise FmodMCPError(
                ErrorCode.INVALID_TYPE,
                f"sample_rate_mode must be one of {', '.join(SAMPLE_RATE_MODES)}",
            )
        vals["sampleRateMode"] = SAMPLE_RATE_MODES[key]
    if rate is not None:
        if rate not in FIXED_SAMPLE_RATES:
            raise FmodMCPError(
                ErrorCode.VALUE_OUT_OF_RANGE, f"sample_rate must be one of {FIXED_SAMPLE_RATES}"
            )
        vals["sampleRate"] = int(rate)
    return vals


def _decorate(enc: dict | None) -> dict | None:
    if not enc:
        return enc
    enc["formatName"] = _label(_FORMAT_NAMES, enc.get("format"))
    enc["sampleRateModeName"] = _label(_RATE_MODE_NAMES, enc.get("sampleRateMode"))
    return enc


def register_encoding(mcp: FastMCP, client) -> None:
    @mcp.tool()
    async def encoding_get(
        targets: list[str] | None = None,
        folder: str | None = None,
        platform: str | None = None,
    ) -> dict:
        """Read compression settings: the platform default, and for given
        assets (or every asset under an Assets folder) their override if any
        and the effective setting. Formats: pcm, fadpcm, xma, vorbis, at9,
        opus; sample-rate modes: fixed, optimize, preserve.

        Args:
            targets: Asset {guid}s / asset:/ paths.
            folder: Assets subfolder, e.g. "music".
            platform: Platform name (default: the only platform).
        """
        prefix = _folder_prefix(folder)
        r = await client.execute(
            _JS_PLATFORM
            + "var pl=__platform(p.platform);var def=__enc(pl.encodingSettings);"
            "var as=__assets(p);var out=[];"
            f"for(var i=0;i<as.length&&i<{MAX_ENCODING_TARGETS};i++){{var o=__override(as[i],pl);"
            "out.push({guid:G(as[i]),assetPath:as[i].assetPath,streaming:as[i].isStreaming,"
            "override:__enc(o),effective:o?__enc(o):def});}"
            "return {platform:pl.name,platformDefault:def,assets:out,total:as.length};",
            platform=platform,
            targets=targets,
            folder=prefix,
        )
        res = r.get("result") or {}
        _decorate(res.get("platformDefault"))
        for a in res.get("assets", []):
            _decorate(a["override"])
            _decorate(a["effective"])
        return r

    @mcp.tool()
    async def encoding_set(
        format: str | None = None,
        quality: int | None = None,
        sample_rate_mode: str | None = None,
        sample_rate: int | None = None,
        streaming: bool | None = None,
        targets: list[str] | None = None,
        folder: str | None = None,
        platform: str | None = None,
    ) -> dict:
        """Set compression — what decides shipped bank size. With no
        targets/folder it changes the platform default (every asset without
        an override); with targets/folder it creates or updates per-asset
        overrides. `streaming` (assets only) streams long files from disk
        instead of loading them into memory — use it for music/ambience.

        Args:
            format: pcm | fadpcm | xma | vorbis | at9 | opus.
            quality: 1-100 (lossy formats).
            sample_rate_mode: fixed | optimize | preserve.
            sample_rate: Rate for "fixed" mode (e.g. 48000).
            streaming: Stream these assets (needs targets/folder).
            targets: Asset {guid}s / asset:/ paths.
            folder: Assets subfolder — applies to every asset under it.
            platform: Platform name (default: the only platform).
        """
        vals = _encoding_values(format, quality, sample_rate_mode, sample_rate)
        prefix = _folder_prefix(folder)
        if not vals and streaming is None:
            raise FmodMCPError(ErrorCode.MISSING_PARAMETER, "nothing to set")
        if streaming is not None and not (targets or prefix):
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER, "streaming applies to assets — pass targets or folder"
            )
        if targets and len(targets) > MAX_ENCODING_TARGETS:
            raise FmodMCPError(
                ErrorCode.VALUE_OUT_OF_RANGE, f"at most {MAX_ENCODING_TARGETS} targets"
            )
        r = await client.execute(
            _JS_PLATFORM
            + "var pl=__platform(p.platform);"
            "function apply(es){for(var k in p.vals){es[k]=p.vals[k];}"
            "for(var k2 in p.vals){if(es[k2]!==p.vals[k2])throw new Error("
            "'Studio rejected '+k2+'='+p.vals[k2]+' (now '+es[k2]+')');}}"
            "if(!p.targets&&!p.folder){apply(pl.encodingSettings);"
            "return {platform:pl.name,scope:'platformDefault',setting:__enc(pl.encodingSettings)};}"
            "var as=__assets(p);"
            f"if(as.length>{MAX_ENCODING_TARGETS})throw new Error('too many assets ('+as.length+')');"
            "var created=0,updated=0;"
            "for(var i=0;i<as.length;i++){"
            "if(Object.keys(p.vals).length){var o=__override(as[i],pl);"
            "if(!o){o=studio.project.create('EncodingSetting');o.platform=pl;o.encodable=as[i];"
            "o.encodingFormat=pl.encodingSettings.encodingFormat;o.quality=pl.encodingSettings.quality;"
            "o.sampleRateMode=pl.encodingSettings.sampleRateMode;o.sampleRate=pl.encodingSettings.sampleRate;"
            "created++;}else{updated++;}apply(o);}"
            "if(p.streaming!==null)as[i].isStreaming=p.streaming;}"
            "return {platform:pl.name,scope:'assets',assets:as.length,overridesCreated:created,"
            "overridesUpdated:updated,streaming:p.streaming};",
            platform=platform,
            targets=targets,
            folder=prefix,
            vals=vals,
            streaming=streaming,
        )
        _decorate((r.get("result") or {}).get("setting"))
        return r

    @mcp.tool()
    async def encoding_clear(
        targets: list[str] | None = None,
        folder: str | None = None,
        platform: str | None = None,
    ) -> dict:
        """Remove per-asset compression overrides so the assets follow the
        platform default again.

        Args:
            targets: Asset {guid}s / asset:/ paths.
            folder: Assets subfolder.
            platform: Platform name (default: the only platform).
        """
        prefix = _folder_prefix(folder)
        if not targets and not prefix:
            raise FmodMCPError(ErrorCode.MISSING_PARAMETER, "pass targets or folder")
        return await client.execute(
            _JS_PLATFORM
            + "var pl=__platform(p.platform);var as=__assets(p);var removed=0;"
            "for(var i=0;i<as.length;i++){var o=__override(as[i],pl);"
            "if(o){studio.project.deleteObject(o);removed++;}}"
            "return {platform:pl.name,assets:as.length,overridesRemoved:removed};",
            platform=platform,
            targets=targets,
            folder=prefix,
        )


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

    register_encoding(mcp, client)
