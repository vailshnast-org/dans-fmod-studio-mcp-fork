import os
import struct
import wave

from mcp.server.fastmcp import FastMCP

from fmod_mcp.safety import ensure_backup
from fmod_mcp.tools.asset_tools import JS_ASSET_ROW
from fmod_mcp.tools._common import (
    JS_FOLDER_CHAIN,
    JS_PARAM,
    JS_SET_PROPS,
    JS_SOUNDS,
    MAX_TRACK_LIST_SOUNDS,
    check_property_values,
)
from fmod_mcp_shared.constants import (
    MAX_AUDIO_FILES_PER_EVENT,
    MAX_BATCH_CREATE,
    MAX_NAME_LENGTH,
    MAX_OBJECTS_READ,
)
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode
from fmod_mcp_shared.path_safety import safe_path

# Supported audio import formats + instrument types. Both validated up front
# so a typo fails fast with a typed error instead of an opaque Studio message.
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".aiff", ".aif", ".flac", ".mp3", ".ogg"}
ALLOWED_SOUND_TYPES = {
    "SingleSound",
    "MultiSound",
    "ProgrammerSound",
    "SoundScatterer",
    "EventSound",
}

# What a MultiSound playlist entry can be when created through
# multi_add_entry (Event/Scatterer entries need extra wiring not covered).
MULTI_ENTRY_TYPES = ("SingleSound", "ProgrammerSound", "SilenceSound", "MultiSound")

# __multi(ref): resolve and type-check a MultiSound.
_JS_MULTI = (
    "function __multi(ref){var m=L(ref);"
    "if(!m.isOfType||!m.isOfType('MultiSound'))"
    "throw new Error(ref+' is not a MultiSound (entity '+m.entity+')');return m;}"
)

# How much of a WAV file to scan for silence. A bad DAW bounce is silent
# throughout, not just at the start, so a bounded prefix is enough — reading
# the whole file would be needless time/memory for a multi-minute asset.
_SILENCE_CHECK_SECONDS = 10.0
_SILENCE_PEAK_THRESHOLD = 0.001  # ~ -60 dBFS


def _check_wav_not_silent(path: str) -> None:
    """Best-effort silence detector for an imported WAV before it's wired
    into an instrument. FMOD Studio's import succeeds, and the instrument
    looks correctly set up, even when the source render was blank — the
    only way to have caught that before this was to listen after the fact.

    Uses only the stdlib `wave` module (no new dependency) against raw PCM
    samples, so it only covers 8/16-bit PCM WAV — the common case for a DAW
    bounce. Anything else (compressed WAV, 24/32-bit, non-WAV formats) is
    skipped silently rather than risk a false positive from misreading it;
    this is a safety net for the common failure mode, not a full audio
    validator.
    """
    try:
        with wave.open(path, "rb") as w:
            framerate = w.getframerate() or 44100
            sampwidth = w.getsampwidth()
            max_frames = int(_SILENCE_CHECK_SECONDS * framerate)
            raw = w.readframes(min(w.getnframes(), max_frames))
    except (wave.Error, EOFError, OSError):
        return  # not a WAV we can safely parse this way — skip, not a failure

    if not raw:
        raise FmodMCPError(
            ErrorCode.INVALID_FORMAT, f"audio file has no sample data: {path}"
        )

    if sampwidth == 2:
        count = len(raw) // 2
        if count == 0:
            return
        samples = struct.unpack(f"<{count}h", raw[: count * 2])
        peak = max(abs(s) for s in samples) / 32768.0
    elif sampwidth == 1:
        samples = raw
        peak = max(abs(b - 128) for b in samples) / 128.0
    else:
        return  # 24/32-bit — skip rather than mis-parse

    if peak < _SILENCE_PEAK_THRESHOLD:
        raise FmodMCPError(
            ErrorCode.INVALID_FORMAT,
            f"audio file appears to be silent (peak level {peak:.4f} over the "
            f"first {_SILENCE_CHECK_SECONDS:g}s, threshold {_SILENCE_PEAK_THRESHOLD:g}): "
            f"{path}. This usually means the source render/bounce was blank — "
            f"re-check it before importing rather than wiring up empty audio.",
        )


def _wav_duration(path: str) -> float | None:
    """Length in seconds of a PCM WAV, or None for anything `wave` can't read.

    Used to size a new instrument's trigger region to its audio — Studio
    does this itself on drag-and-drop, but GroupTrack.addSound() takes an
    explicit length. Non-WAV formats fall back to the asset's own length in
    Studio (see event_create_from_audio).
    """
    try:
        with wave.open(path, "rb") as w:
            rate = w.getframerate()
            return w.getnframes() / rate if rate else None
    except (wave.Error, EOFError, OSError):
        return None


def _check_import(path: str) -> str:
    """Validate an audio import path and return its resolved, safe form.

    Blocks traversal/system-directory access via safe_path() (the same guard
    Reaper-MCP applies to every path-taking tool) before checking existence
    and extension — a project has no business importing from outside its own
    asset tree. WAV files also get a best-effort silence check — see
    _check_wav_not_silent.
    """
    resolved = safe_path(path)
    if not os.path.exists(resolved):
        raise FmodMCPError(ErrorCode.INVALID_PATH, f"audio file not found: {resolved}")
    ext = os.path.splitext(resolved)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise FmodMCPError(
            ErrorCode.INVALID_FORMAT,
            f"unsupported audio format {ext!r}; supported: "
            f"{sorted(ALLOWED_AUDIO_EXTENSIONS)}",
        )
    if ext == ".wav":
        _check_wav_not_silent(resolved)
    return resolved


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def audio_import(file_path: str) -> dict:
        """Import an audio file into the project as a reusable asset.

        Returns the asset's {guid} so it can be assigned to an instrument.
        Long operation — asset files are copied into the project.

        Args:
            file_path: Absolute path to a .wav/.aiff/.flac/.mp3/.ogg file.
        """
        resolved_path = _check_import(file_path)
        return await client.execute_long(
            "var a=studio.project.importAudioFile(p.file_path);"
            "if(!a)throw new Error('Failed to import audio file: '+p.file_path);"
            "return {guid:G(a),name:N(a),path:P(a)};",
            file_path=resolved_path,
        )

    @mcp.tool()
    async def audio_assets(folder: str | None = None, unused_only: bool = False) -> dict:
        """List imported audio assets (capped): asset path, length,
        channels, sample rate, streaming, and how many instruments use each.

        Args:
            folder: Only assets under this Assets subfolder, e.g. "sfx/player".
            unused_only: Only assets no instrument uses (cleanup candidates).
        """
        # model.Asset is abstract: findInstances() without includeDerivedTypes
        # returned nothing on 2.03.15 (0 vs 97 AudioFiles in a real project),
        # so this listing was always empty. AudioFile is the concrete type.
        prefix = folder.strip().strip("/").replace("\\", "/") + "/" if folder else None
        return await client.execute(
            JS_ASSET_ROW
            + "var arr=studio.project.model.AudioFile.findInstances()||[];var out=[];var total=0;"
            "for(var i=0;i<arr.length;i++){var a=arr[i];"
            "if(p.prefix&&String(a.assetPath).indexOf(p.prefix)!==0)continue;"
            "var r=__asset(a);if(p.unused_only&&r.usedBy>0)continue;"
            f"total++;if(out.length<{MAX_OBJECTS_READ})out.push(r);}}"
            "return {total:total,assets:out};",
            prefix=prefix,
            unused_only=unused_only,
        )

    @mcp.tool()
    async def sound_add_to_track(
        event_target: str,
        track_target: str,
        sound_type: str,
        start: float = 0.0,
        length: float | None = None,
        name: str | None = None,
        parameter: str | None = None,
        audio: str | None = None,
    ) -> dict:
        """Place an instrument on an event's track — on the timeline, or on a
        parameter sheet (`parameter`) so it plays across a parameter range
        instead of over time (e.g. a "Surface" or "RPM" sheet). Returned
        {guid} is for follow-up calls (sound_set_audio_file, sound_set_owner).

        Args:
            event_target: event:/ path or {guid}.
            track_target: trackGuid (not mixerGroupGuid) from event_list_tracks.
            sound_type: SingleSound | MultiSound | ProgrammerSound |
                        SoundScatterer | EventSound.
            start: Start position — seconds on the timeline, or a parameter
                   value on a parameter sheet.
            length: Length in seconds / parameter units (> 0). Omit it when
                    passing `audio` to size the region to the file.
            name: Optional instrument name.
            parameter: Optional parameter name (or "parameter:/Name") whose
                       sheet to place it on, instead of the timeline.
            audio: Optional asset {guid}/asset:/ path to assign right away
                   (SingleSound only).
        """
        if sound_type not in ALLOWED_SOUND_TYPES:
            raise FmodMCPError(
                ErrorCode.INVALID_TYPE, f"invalid sound_type {sound_type!r}"
            )
        # length 0 used to be allowed ("untrimmed") but produced a silent,
        # zero-length trigger region — a known bug in the game's pipeline doc.
        if length is not None and length <= 0:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "length must be > 0")
        if length is None and not audio:
            raise FmodMCPError(
                ErrorCode.MISSING_PARAMETER,
                "pass length (> 0), or audio to size the instrument to the file",
            )
        if audio and sound_type != "SingleSound":
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER, "audio only applies to sound_type='SingleSound'"
            )
        body = (
            JS_PARAM
            + "var e=L(p.event_target);var t=L(p.track_target);"
            "var sheet=p.parameter?__sheet(e,p.parameter):e.timeline;"
            "var a=p.audio?L(p.audio):null;var len=p.length;"
            "if(len===null){len=a&&a.length>0?a.length:0;"
            "if(!len)throw new Error('could not read the audio file length - pass length');}"
            "var inst=t.addSound(sheet,p.sound_type,p.start,len);"
            "if(!inst)throw new Error('addSound returned nothing - '+p.sound_type+"
            "' may not be placeable this way, or start/length is outside the sheet range');"
        )
        if name:
            _check_instrument_name(name)
            body += "inst.name=p.name;"
        body += (
            "if(a){inst.audioFile=a;if(!inst.audioFile)throw new Error("
            "'audioFile assignment did not take effect');}"
            "return {guid:G(inst),name:N(inst),start:inst.start,length:inst.length,"
            "audioFile:a?N(a):null};"
        )
        return await client.execute(
            body,
            event_target=event_target,
            track_target=track_target,
            sound_type=sound_type,
            start=start,
            length=length,
            name=name,
            parameter=parameter,
            audio=audio,
        )

    @mcp.tool()
    async def sound_add_nested_event(
        event_target: str,
        track_target: str,
        referenced_event: str,
        start: float = 0.0,
        length: float = 1.0,
        parameter: str | None = None,
    ) -> dict:
        """Place an event instrument that plays another event (or a snapshot)
        — nested/referenced events, e.g. a shared "Splash" event reused by
        several bigger events.

        Args:
            event_target: event:/ path or {guid} to add the instrument to.
            track_target: trackGuid from event_list_tracks.
            referenced_event: event:/ or snapshot:/ path or {guid} to play.
            start: Start position (seconds, or parameter value on a sheet).
            length: Length (> 0).
            parameter: Optional parameter sheet instead of the timeline.
        """
        if length <= 0:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "length must be > 0")
        return await client.execute(
            JS_PARAM
            + "var e=L(p.event_target);var t=L(p.track_target);var r=L(p.referenced_event);"
            "if(!r.isOfType('Event'))throw new Error(p.referenced_event+' is not an event or snapshot');"
            "if(G(r)===G(e))throw new Error('an event cannot reference itself');"
            "var sheet=p.parameter?__sheet(e,p.parameter):e.timeline;"
            "var s=t.addSound(sheet,'EventSound',p.start,p.length);"
            "if(!s)throw new Error('addSound returned nothing for EventSound');"
            "s.event=r;"
            "if(!s.event||G(s.event)!==G(r)){studio.project.deleteObject(s);"
            "throw new Error('event reference did not take effect');}"
            "return {guid:G(s),references:P(r),start:s.start,length:s.length};",
            event_target=event_target,
            track_target=track_target,
            referenced_event=referenced_event,
            start=start,
            length=length,
            parameter=parameter,
        )

    @mcp.tool()
    async def sound_create(sound_type: str, name: str | None = None) -> dict:
        """Create a standalone instrument (usually a SingleSound for a Multi's playlist).

        Args:
            sound_type: SingleSound | MultiSound | ProgrammerSound |
                        SoundScatterer | EventSound.
            name: Optional instrument name.
        """
        if sound_type not in ALLOWED_SOUND_TYPES:
            raise FmodMCPError(
                ErrorCode.INVALID_TYPE, f"invalid sound_type {sound_type!r}"
            )
        body = "var s=studio.project.create(p.sound_type);"
        if name:
            _check_instrument_name(name)
            body += "s.name=p.name;"
        body += "return {guid:G(s),name:N(s)};"
        return await client.execute(body, sound_type=sound_type, name=name)

    @mcp.tool()
    async def sound_set_audio_file(target: str, audio: str) -> dict:
        """Assign an imported audio asset to an instrument.

        Reads the assignment back before returning — a `guid` alone isn't
        proof the audio actually attached, only that the JS call didn't
        throw. If `audioFileGuid` comes back null, the assignment silently
        didn't take (this raises instead of reporting a false success).

        Args:
            target: Instrument {guid} or path.
            audio: Asset {guid} from audio_import.
        """
        return await client.execute(
            "var s=L(p.target);var a=L(p.audio);s.audioFile=a;"
            "var af=s.audioFile;"
            "if(!af)throw new Error("
            "'audioFile assignment did not take effect on '+p.target+"
            "' — this instrument type may not support an audioFile relationship.');"
            "return {guid:G(s),audioFileGuid:G(af),audioFileName:N(af)};",
            target=target,
            audio=audio,
        )

    @mcp.tool()
    async def sound_set_owner(target: str, owner: str) -> dict:
        """Set a sound's owning instrument (e.g. a SingleSound into a MultiSound
        or a Scatterer's playlist).

        Reads the assignment back before returning — see sound_set_audio_file.

        Args:
            target: SingleSound {guid}.
            owner: Owner MultiSound/Scatterer {guid}.
        """
        # A SoundScatterer keeps its playlist in an inner MultiSound
        # (`scatterer.sound`); setting owner=scatterer is silently ignored
        # (confirmed live), which is why this used to fail for Scatterers.
        return await client.execute(
            "var s=L(p.target);var o=L(p.owner);"
            "if(o.isOfType&&o.isOfType('SoundScatterer')){"
            "if(!o.sound)throw new Error('scatterer has no playlist MultiSound');o=o.sound;}"
            "s.owner=o;"
            "var actual=s.owner;"
            "if(!actual||G(actual)!==G(o))throw new Error("
            "'owner assignment did not take effect on '+p.target+'.');"
            "return {guid:G(s),ownerGuid:G(actual)};",
            target=target,
            owner=owner,
        )

    @mcp.tool()
    async def sound_set_name(target: str, name: str) -> dict:
        """Rename an instrument.

        Args:
            target: Instrument {guid} or path.
            name: New name.
        """
        _check_instrument_name(name)
        return await client.execute(
            "var s=L(p.target);s.name=p.name;return {guid:G(s),name:N(s)};",
            target=target,
            name=name,
        )

    @mcp.tool()
    async def sound_info(target: str) -> dict:
        """Get an instrument's guid, name, path, and whether it actually has
        an audio asset attached (hasAudioFile / audioFileName) — a SingleSound
        with no audio assigned shows an empty box with no waveform in Studio
        and plays silence; check this after sound_set_audio_file rather than
        assuming the assignment stuck.

        Args:
            target: Instrument {guid} or path.
        """
        return await client.execute(
            "var s=L(p.target);var af=s.audioFile;"
            "return {guid:G(s),name:N(s),path:P(s),"
            "hasAudioFile:!!af,"
            "audioFileGuid:af?G(af):null,"
            "audioFileName:af?N(af):null};",
            target=target,
        )

    @mcp.tool()
    async def sound_set_properties(
        target: str,
        volume: float | None = None,
        pitch: float | None = None,
        looping: bool | None = None,
        is_async: bool | None = None,
        start: float | None = None,
        length: float | None = None,
        extra: dict | None = None,
    ) -> dict:
        """Set an instrument's common playback properties — volume (dB),
        pitch (semitones), looping — plus any other real property via
        `extra` (names checked against the object; see utility_dump).
        Every value is read back; `clamped` names any Studio adjusted.

        Args:
            target: Instrument {guid}.
            volume: Volume in dB.
            pitch: Pitch in semitones.
            looping: Loop the instrument.
            is_async: Asynchronous (keeps playing once triggered, e.g. an
                      instrument held at a sustain point needs looping AND
                      is_async).
            start: Move the trigger region (seconds / sheet units).
            length: Resize the trigger region (> 0).
            extra: Other {"property": value} pairs.
        """
        if length is not None and length <= 0:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "length must be > 0")
        props = dict(extra or {})
        for key, val in (
            ("volume", volume),
            ("pitch", pitch),
            ("looping", looping),
            ("isAsync", is_async),
            ("start", start),
            ("length", length),
        ):
            if val is not None:
                props[key] = val
        props = check_property_values(props)
        return await client.execute(
            JS_SET_PROPS
            + "var s=L(p.target);var r=__setProps(s,p.props);"
            "return {guid:G(s),entity:s.entity,applied:r.applied,clamped:r.clamped};",
            target=target,
            props=props,
        )

    @mcp.tool()
    async def sound_set_fade(
        target: str,
        fade_in: float | None = None,
        fade_out: float | None = None,
        curve: float | None = None,
    ) -> dict:
        """Set an instrument's fade-in and/or fade-out (Sound.setFadeInCurve/
        setFadeOutCurve). A length of 0 removes that fade.

        Args:
            target: Instrument {guid}.
            fade_in: Fade-in length (seconds / sheet units), >= 0.
            fade_out: Fade-out length, >= 0.
            curve: Shape — 0 linear, > 0 accelerating, < 0 decelerating
                   (default: Studio's default shape).
        """
        if fade_in is None and fade_out is None:
            raise FmodMCPError(
                ErrorCode.MISSING_PARAMETER, "pass fade_in and/or fade_out"
            )
        for val in (fade_in, fade_out):
            if val is not None and val < 0:
                raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "fade lengths must be >= 0")
        return await client.execute(
            "var s=L(p.target);"
            "if(typeof s.setFadeInCurve!=='function')throw new Error("
            "'target (entity '+s.entity+') is not an instrument - no setFadeInCurve()');"
            "function fade(fn,len){if(p.curve===null)s[fn](len);else s[fn](len,p.curve);}"
            "if(p.fade_in!==null)fade('setFadeInCurve',p.fade_in);"
            "if(p.fade_out!==null)fade('setFadeOutCurve',p.fade_out);"
            "return {guid:G(s),fadeIn:p.fade_in,fadeOut:p.fade_out,curve:p.curve};",
            target=target,
            fade_in=fade_in,
            fade_out=fade_out,
            curve=curve,
        )

    @mcp.tool()
    async def event_list_sounds(event_target: str) -> dict:
        """List every instrument inside an event (all types, nested playlist
        entries included): guid, name, type, start/length, attached audio
        file, and owner (a Multi/Scatterer for playlist entries). Audit this
        before adding instruments — duplication is the most common mistake.

        Args:
            event_target: event:/ path or {guid}.
        """
        return await client.execute(
            JS_SOUNDS
            + "var e=L(p.event_target);"
            f"var out=__sounds(e,{MAX_TRACK_LIST_SOUNDS});"
            "return {count:out.length,sounds:out};",
            event_target=event_target,
        )

    @mcp.tool()
    async def audio_import_batch(file_paths: list[str]) -> dict:
        """Import several audio files in one call (long). Every path is
        validated up front (exists, supported format, not silent) so a bad
        file fails before anything is imported.

        Args:
            file_paths: Absolute paths to .wav/.aiff/.flac/.mp3/.ogg files.
        """
        if not file_paths:
            raise FmodMCPError(ErrorCode.MISSING_PARAMETER, "file_paths is empty")
        if len(file_paths) > MAX_BATCH_CREATE:
            raise FmodMCPError(
                ErrorCode.VALUE_OUT_OF_RANGE,
                f"too many files in one call (max {MAX_BATCH_CREATE})",
            )
        resolved = [_check_import(fp) for fp in file_paths]
        return await client.execute_long(
            "var out=[];"
            "for(var i=0;i<p.files.length;i++){"
            "var a=studio.project.importAudioFile(p.files[i]);"
            "if(!a)throw new Error('Failed to import audio file: '+p.files[i]+"
            "' ('+out.length+' imported before it)');"
            "out.push({guid:G(a),name:N(a),path:P(a)});}"
            "return {count:out.length,assets:out};",
            files=resolved,
        )

    @mcp.tool()
    async def event_create_from_audio(
        name: str,
        file_paths: list[str],
        folder: str | None = None,
        bank: str | None = None,
        spatializer: bool = False,
        looping: bool = False,
    ) -> dict:
        """One call for the most common job: import audio and build a
        playable event around it. One file -> a SingleSound; several -> a
        MultiSound playlist (random variations, e.g. footsteps). Optionally
        files it into an event folder, assigns a bank and adds a 3D
        spatializer. If any step after the event exists fails, the event is
        deleted again (imported assets stay) so no half-built event is left.

        Args:
            name: Event name.
            file_paths: Absolute audio file paths (1-50).
            folder: Optional event folder path, e.g. "SFX/Player"
                    (created if missing).
            bank: Optional bank:/ path or {guid} to assign.
            spatializer: Add an FMOD spatializer (3D event).
            looping: Loop the instrument.
        """
        _check_instrument_name(name)
        if not file_paths:
            raise FmodMCPError(ErrorCode.MISSING_PARAMETER, "file_paths is empty")
        if len(file_paths) > MAX_AUDIO_FILES_PER_EVENT:
            raise FmodMCPError(
                ErrorCode.VALUE_OUT_OF_RANGE,
                f"too many files for one event (max {MAX_AUDIO_FILES_PER_EVENT})",
            )
        resolved = [_check_import(fp) for fp in file_paths]
        durations = [d for d in (_wav_duration(fp) for fp in resolved) if d]
        return await client.execute_long(
            JS_FOLDER_CHAIN
            + JS_SET_PROPS
            + "var assets=[];"
            "for(var i=0;i<p.files.length;i++){"
            "var a=studio.project.importAudioFile(p.files[i]);"
            "if(!a)throw new Error('Failed to import audio file: '+p.files[i]);"
            "assets.push(a);}"
            "var len=p.length;"
            "if(!len){for(var j=0;j<assets.length;j++){"
            "var al=assets[j].length;if(typeof al==='number'&&al>len)len=al;}}"
            "var warnings=[];"
            "if(!len){len=1;warnings.push('could not read audio length - trigger region set to 1s, resize it in Studio');}"
            "var e=studio.project.workspace.addEvent(p.name,!!p.spatializer);"
            "if(!e)throw new Error('workspace.addEvent returned nothing');"
            "try{"
            "if(p.folder){e.folder=__folderChain('EventFolder',p.folder);}"
            "var t=e.addGroupTrack('Audio 1');"
            "var inst;var kind=assets.length===1?'SingleSound':'MultiSound';"
            "inst=t.addSound(e.timeline,kind,0,len);"
            "if(!inst)throw new Error('addSound failed for '+kind);"
            "if(assets.length===1){inst.audioFile=assets[0];"
            "if(!inst.audioFile)throw new Error('audioFile assignment did not take effect');}"
            "else{for(var k=0;k<assets.length;k++){"
            "var s=studio.project.create('SingleSound');s.audioFile=assets[k];s.owner=inst;"
            "if(!s.owner||G(s.owner)!==G(inst))throw new Error('playlist entry '+k+' did not attach to the MultiSound');}}"
            "if(p.looping){try{__setProps(inst,{looping:true});}catch(__le){"
            "warnings.push('looping not set: '+String(__le.message||__le));}}"
            "if(p.bank){var b=L(p.bank);e.relationships.banks.add(b);}"
            "}catch(__err){try{studio.project.deleteObject(e);}catch(__d){}throw __err;}"
            "return {guid:G(e),path:P(e),trackGuid:G(t),mixerGroupGuid:G(t.mixerGroup),"
            "instrumentGuid:G(inst),instrumentType:kind,length:len,"
            "assets:assets.map(function(x){return {guid:G(x),name:N(x)};}),"
            "bank:p.bank,warnings:warnings};",
            name=name,
            files=resolved,
            folder=folder,
            bank=bank,
            spatializer=spatializer,
            looping=looping,
            length=max(durations) if durations else 0,
        )


    @mcp.tool()
    async def sound_add_plugin(
        event_target: str,
        track_target: str,
        plugin: str,
        start: float = 0.0,
        length: float = 1.0,
        parameter: str | None = None,
    ) -> dict:
        """Place a plug-in instrument (e.g. "AudioGaming AudioRain",
        "AudioGaming AudioMotors") on a track — names from
        project_list_plugins.

        Args:
            event_target: event:/ path or {guid}.
            track_target: trackGuid from event_list_tracks.
            plugin: Exact plug-in instrument name.
            start: Start position (seconds, or parameter value on a sheet).
            length: Length (> 0).
            parameter: Optional parameter sheet instead of the timeline.
        """
        if length <= 0:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "length must be > 0")
        return await client.execute(
            JS_PARAM
            + "var e=L(p.event_target);var t=L(p.track_target);"
            "var avail=studio.project.findAvailablePlugins()||[];var known=false;"
            "for(var i=0;i<avail.length;i++){if(String(avail[i])===p.plugin){known=true;break;}}"
            "if(!known)throw new Error('plug-in not available: '+p.plugin+' (see project_list_plugins)');"
            "var sheet=p.parameter?__sheet(e,p.parameter):e.timeline;"
            "var ps=studio.project.workspace.createPlugin(p.plugin);"
            "if(!ps)throw new Error('createPlugin returned nothing for '+p.plugin);"
            "if(!ps.isOfType('PluginSound')){studio.project.deleteObject(ps);"
            "throw new Error(p.plugin+' is a plug-in effect, not an instrument - use mixer_effect_add_plugin');}"
            # Confirmed live: a PluginSound is placed by setting the same
            # audioTrack/parameter/start/length a timeline instrument has.
            "ps.audioTrack=t;ps.parameter=sheet;ps.start=p.start;ps.length=p.length;"
            "if(!ps.isValid){studio.project.deleteObject(ps);"
            "throw new Error('plug-in instrument did not become valid on that track');}"
            "return {guid:G(ps),entity:ps.entity,plugin:p.plugin,start:ps.start,length:ps.length};",
            event_target=event_target,
            track_target=track_target,
            plugin=plugin,
            start=start,
            length=length,
            parameter=parameter,
        )

    @mcp.tool()
    async def multi_list_entries(target: str) -> dict:
        """List a MultiSound's playlist: each entry's type, name/audio and
        play percentage (weight, null = Studio's automatic share), plus the
        playlist settings (playlistMode, playbackMode, looping, playCount).

        Args:
            target: MultiSound {guid}.
        """
        return await client.execute(
            _JS_MULTI
            + "var m=__multi(p.target);"
            "var ds=m.relationships.sounds.destinations||[];var out=[];"
            "for(var i=0;i<ds.length;i++){var sd=ds[i];var af=null;try{af=sd.audioFile;}catch(__e){}"
            "var pp=null;try{pp=sd.playPercentage;}catch(__e){}"
            "out.push({guid:G(sd),entity:sd.entity,name:N(sd),audioFile:af?N(af):null,"
            "percentage:pp?pp.percentage:null});}"
            "return {guid:G(m),playlistMode:m.playlistMode,playbackMode:m.playbackMode,"
            "looping:m.looping,playCount:m.playCount,entries:out};",
            target=target,
        )

    @mcp.tool()
    async def multi_add_entry(
        target: str, audio: str | None = None, sound_type: str = "SingleSound"
    ) -> dict:
        """Add an entry to a MultiSound's playlist — usually a SingleSound
        playing an imported asset (pass `audio`).

        Args:
            target: MultiSound {guid}.
            audio: Asset {guid} or asset:/ path (SingleSound only).
            sound_type: SingleSound | ProgrammerSound | SilenceSound | MultiSound.
        """
        if sound_type not in MULTI_ENTRY_TYPES:
            raise FmodMCPError(
                ErrorCode.INVALID_TYPE,
                f"sound_type must be one of {', '.join(MULTI_ENTRY_TYPES)}",
            )
        if audio and sound_type != "SingleSound":
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER, "audio only applies to a SingleSound entry"
            )
        return await client.execute(
            _JS_MULTI
            + "var m=__multi(p.target);"
            "var sd=studio.project.create(p.sound_type);"
            "if(!sd)throw new Error('could not create '+p.sound_type);"
            "sd.owner=m;"
            "if(!sd.owner||G(sd.owner)!==G(m)){studio.project.deleteObject(sd);"
            "throw new Error('entry did not attach to the MultiSound');}"
            "if(p.audio){sd.audioFile=L(p.audio);if(!sd.audioFile){studio.project.deleteObject(sd);"
            "throw new Error('audioFile assignment did not take effect');}}"
            "return {guid:G(sd),entity:sd.entity,audioFile:sd.audioFile?N(sd.audioFile):null,"
            "entries:m.relationships.sounds.destinations.length};",
            target=target,
            audio=audio,
            sound_type=sound_type,
        )

    @mcp.tool()
    async def multi_remove_entry(entry: str) -> dict:
        """Remove (delete) one entry from its MultiSound's playlist.

        Args:
            entry: Entry {guid} from multi_list_entries.
        """
        await ensure_backup(client)
        return await client.execute(
            "var sd=L(p.entry);var m=sd.owner;"
            "if(!m||!m.isOfType('MultiSound'))throw new Error(p.entry+' is not a playlist entry');"
            "studio.project.deleteObject(sd);"
            "return {removed:p.entry,multi:G(m),entries:m.relationships.sounds.destinations.length};",
            entry=entry,
        )

    @mcp.tool()
    async def multi_set_weight(entry: str, percentage: float) -> dict:
        """Set a playlist entry's play percentage (its chance of being
        picked), like typing a % into the entry in Studio.

        Args:
            entry: Entry {guid} from multi_list_entries.
            percentage: 0-100.
        """
        if not 0 <= percentage <= 100:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "percentage must be 0-100")
        return await client.execute(
            "var sd=L(p.entry);var m=sd.owner;"
            "if(!m||!m.isOfType('MultiSound'))throw new Error(p.entry+' is not a playlist entry');"
            # Weights are separate PlayPercentage objects {sound, owner,
            # percentage} — none exists until one is set (confirmed live).
            "var pp=sd.playPercentage;var created=false;"
            "if(!pp){pp=studio.project.create('PlayPercentage');"
            "if(!pp)throw new Error('could not create a PlayPercentage');"
            "pp.sound=sd;pp.owner=m;created=true;}"
            "pp.percentage=p.percentage;"
            "if(!pp.isValid)throw new Error('play percentage did not become valid');"
            "return {entry:G(sd),percentage:pp.percentage,created:created};",
            entry=entry,
            percentage=percentage,
        )

    @mcp.tool()
    async def multi_set_playlist(
        target: str,
        playlist_mode: int | None = None,
        playback_mode: int | None = None,
        looping: bool | None = None,
        play_count: int | None = None,
    ) -> dict:
        """Set a MultiSound's playlist behavior. Modes are Studio's numeric
        enums (0 = Studio's default; read current values with
        multi_list_entries and match them against the Multi's deck in
        Studio before changing them).

        Args:
            target: MultiSound {guid}.
            playlist_mode: playlistMode enum value.
            playback_mode: playbackMode enum value.
            looping: Loop the playlist.
            play_count: Times to play when looping (0 = infinite).
        """
        props = {}
        for key, val in (
            ("playlistMode", playlist_mode),
            ("playbackMode", playback_mode),
            ("looping", looping),
            ("playCount", play_count),
        ):
            if val is not None:
                props[key] = val
        props = check_property_values(props)
        return await client.execute(
            _JS_MULTI
            + JS_SET_PROPS
            + "var m=__multi(p.target);var r=__setProps(m,p.props);"
            "return {guid:G(m),applied:r.applied,clamped:r.clamped};",
            target=target,
            props=props,
        )


def _check_instrument_name(name: str) -> None:
    if not name or not name.strip():
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE, "instrument name must not be empty"
        )
    if len(name) > MAX_NAME_LENGTH:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE, f"name too long ({MAX_NAME_LENGTH} max)"
        )
