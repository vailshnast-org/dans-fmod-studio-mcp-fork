from mcp.server.fastmcp import FastMCP

from fmod_mcp.safety import ensure_backup
from fmod_mcp.tools._common import (
    JS_SET_PROPS,
    JS_SOUNDS,
    MAX_TRACK_LIST_SOUNDS,
    js_info,
    js_list,
)
from fmod_mcp_shared.constants import MAX_NAME_LENGTH, MAX_OBJECTS_READ
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode


def _check_name(name: str) -> None:
    if not name or not name.strip():
        raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "name must not be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE, f"name too long ({MAX_NAME_LENGTH} max)"
        )


# Event > Macros "Stealing" options in the order the 2.03 manual lists them
# (Range: Oldest, Furthest, Quietest, Virtualize, None). Studio exposes no
# enum labels to scripts; the stored default 0 matches the documented
# default (Oldest). The raw value is always returned alongside.
VOICE_STEALING = {"oldest": 0, "furthest": 1, "quietest": 2, "virtualize": 3, "none": 4}

MAX_TAG_NAME = 100


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def event_create(
        name: str, folder: str | None = None, spatializer: bool | None = None
    ) -> dict:
        """Create an event in the master event folder (or an event:// folder).

        Args:
            name: Event name (e.g. "Hit").
            folder: Optional event:// path or {guid} of the owning folder.
            spatializer: True = 3D event (FMOD spatializer on the master
                         track), False = explicitly 2D. Omit for Studio's
                         plain create.
        """
        _check_name(name)
        if spatializer is None:
            body = "var e=studio.project.create('Event');e.name=p.name;"
        else:
            # workspace.addEvent(name, withSpatializer) — the documented way to
            # choose 2D/3D at creation time.
            body = "var e=studio.project.workspace.addEvent(p.name,!!p.spatializer);"
        if folder:
            body += "e.folder=L(p.folder);"
        body += "return {guid:G(e),name:N(e),path:P(e)};"
        return await client.execute(
            body, name=name, folder=folder, spatializer=spatializer
        )

    @mcp.tool()
    async def event_delete(target: str) -> dict:
        """Delete an event.

        Args:
            target: event:// path or {guid}.
        """
        await ensure_backup(client)
        return await client.execute(
            "var o=L(p.target);studio.project.deleteObject(o);return true;",
            target=target,
        )

    @mcp.tool()
    async def event_info(target: str) -> dict:
        """Get an event's guid, name, path, maxVoices, whether it is 3D /
        one-shot (Event.is3D / isOneShot), and the banks it is assigned to.

        Args:
            target: event:// path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);var mx=null;"
            "try{mx=o.automatableProperties?o.automatableProperties.maxVoices:null;}catch(__e){}"
            "var is3d=null,oneShot=null;"
            "try{is3d=!!o.is3D();}catch(__e){}"
            "try{oneShot=!!o.isOneShot();}catch(__e){}"
            "var br=o.relationships.banks;var bs=(br&&br.destinations)?br.destinations:[];"
            "var banks=[];for(var i=0;i<bs.length;i++){banks.push({guid:G(bs[i]),path:P(bs[i])});}"
            "return {guid:G(o),name:N(o),path:P(o),maxVoices:mx,is3D:is3d,"
            "isOneShot:oneShot,banks:banks};",
            target=target,
        )

    @mcp.tool()
    async def event_describe(target: str) -> dict:
        """One-call overview of an event's structure: tracks (with their
        instruments), parameters, marker tracks + markers, and banks. Use it
        to audit before editing and to verify after building — far fewer
        round-trips than event_list_tracks + event_list_sounds + marker_list.

        Args:
            target: event:// path or {guid}.
        """
        markers_js = ",".join(
            f"'{t}'"
            for t in (
                "NamedMarker",
                "LoopRegion",
                "SustainPoint",
                "TransitionMarker",
                "TransitionRegion",
                "TempoMarker",
            )
        )
        return await client.execute(
            JS_SOUNDS
            + "var e=L(p.target);"
            "var gt=e.relationships.groupTracks;"
            "var tracks=(gt&&gt.destinations)?gt.destinations:[];"
            "var tOut=[];"
            "for(var i=0;i<tracks.length;i++){var mg=tracks[i].mixerGroup;"
            "var snd=[];try{snd=__sounds(tracks[i]," + str(MAX_TRACK_LIST_SOUNDS) + ");}catch(__e){}"
            "tOut.push({trackGuid:G(tracks[i]),mixerGroupGuid:mg?G(mg):null,"
            "name:mg?N(mg):null,sounds:snd});}"
            "var mt=e.masterTrack;"
            "var ps=(e.getParameterPresets?e.getParameterPresets():[])||[];var pOut=[];"
            "for(var j=0;j<ps.length;j++){var rel=ps[j].relationships&&ps[j].relationships.presetOwner;"
            "var d=rel?rel.destinations:null;"
            "pOut.push({guid:G(ps[j]),name:(d&&d[0])?N(d[0]):null});}"
            "var mr=e.relationships.markerTracks;"
            "var mts=(mr&&mr.destinations)?mr.destinations:[];var mOut=[];"
            "var types=[" + markers_js + "];"
            "for(var k=0;k<mts.length;k++){var items=[];"
            "for(var q=0;q<types.length;q++){try{var cls=studio.project.model[types[q]];"
            "if(!cls)continue;var arr=cls.findInstances({searchContext:mts[k]})||[];"
            "for(var r=0;r<arr.length&&items.length<200;r++){"
            "items.push({guid:G(arr[r]),name:N(arr[r]),markerType:types[q],"
            "position:arr[r].position,length:arr[r].length});}}catch(__e){}}"
            "mOut.push({guid:G(mts[k]),markers:items});}"
            "var br=e.relationships.banks;var bs=(br&&br.destinations)?br.destinations:[];"
            "var bOut=[];for(var b=0;b<bs.length;b++){bOut.push({guid:G(bs[b]),path:P(bs[b])});}"
            "return {guid:G(e),path:P(e),"
            "masterTrack:{trackGuid:G(mt),mixerGroupGuid:mt&&mt.mixerGroup?G(mt.mixerGroup):null},"
            "tracks:tOut,parameters:pOut,markerTracks:mOut,banks:bOut};",
            target=target,
        )

    @mcp.tool()
    async def event_list() -> dict:
        """List every event in the project (capped)."""
        return await client.execute(
            js_list("studio.project.model.Event.findInstances()", MAX_OBJECTS_READ)
        )

    @mcp.tool()
    async def event_lookup(target: str) -> dict:
        """Resolve an event reference to its canonical event:/ path and guid.

        Args:
            target: A path (event:/...) or {guid}.
        """
        return await client.execute(js_info("L(p.target)"), target=target)

    @mcp.tool()
    async def event_set_name(target: str, name: str) -> dict:
        """Rename an event.

        Args:
            target: event:// path or {guid}.
            name: New name.
        """
        _check_name(name)
        return await client.execute(
            "var o=L(p.target);o.name=p.name;return {guid:G(o),name:N(o),path:P(o)};",
            target=target,
            name=name,
        )

    @mcp.tool()
    async def event_set_folder(target: str, folder: str) -> dict:
        """Move an event into a folder (or the master folder root).

        Args:
            target: event:// path or {guid}.
            folder: event:// folder path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);o.folder=L(p.folder);return {guid:G(o),path:P(o)};",
            target=target,
            folder=folder,
        )

    @mcp.tool()
    async def event_add_track(target: str, name: str | None = None) -> dict:
        """Add a group (audio) track to an event's timeline.

        Returns two distinct GUIDs — a track and its mixer group are
        different objects. Use `trackGuid` for `sound_add_to_track`
        (placing instruments on the timeline). Use `mixerGroupGuid` for
        `automation_add_curve`, `mixer_group_volume`, `mixer_effect_add`,
        and anything else that operates on the mixer strip — a track
        itself has no `addAutomator()`.

        Args:
            target: event:// path or {guid}.
            name: Optional mixer-group name for the track ("Audio 1" by default).
        """
        _check_name(name) if name else None
        body = "var e=L(p.target);var t=e.addGroupTrack();"
        if name:
            body += "t.mixerGroup.name=p.name;"
        body += (
            "return {trackGuid:G(t),mixerGroupGuid:G(t.mixerGroup),"
            "name:N(t.mixerGroup)};"
        )
        return await client.execute(body, target=target, name=name)

    @mcp.tool()
    async def event_list_tracks(target: str, include_master: bool = True) -> dict:
        """List an event's group tracks (mixer-group name + both guids each).

        Args:
            target: event:// path or {guid}.
            include_master: Whether to include the event's master track (True).
        """
        return await client.execute(
            "var e=L(p.target);var out=[];"
            "var rel=e.relationships.groupTracks;"
            "var arr=(rel&&rel.destinations)?rel.destinations:[];"
            "for(var i=0;i<arr.length;i++){"
            "var mg=arr[i].mixerGroup;"
            "out.push({trackGuid:G(arr[i]),mixerGroupGuid:mg?G(mg):null,"
            "name:mg?N(mg):null});}"
            "if(p.include_master!==false){"
            "var mt=e.masterTrack;var mmg=mt.mixerGroup;"
            "out.push({trackGuid:G(mt),mixerGroupGuid:mmg?G(mmg):null,name:'Master'});}"
            "return out;",
            target=target,
            include_master=include_master,
        )

    @mcp.tool()
    async def event_set_max_voices(target: str, max_voices: int) -> dict:
        """Cap simultaneous instances of an event (maxVoices).

        Args:
            target: event:// path or {guid}.
            max_voices: 1-1000.
        """
        if not 1 <= max_voices <= 1000:
            raise FmodMCPError(
                ErrorCode.VALUE_OUT_OF_RANGE, "max_voices must be 1-1000"
            )
        return await client.execute(
            "var o=L(p.target);"
            "if(o.automatableProperties){o.automatableProperties.maxVoices=p.max_voices;}"
            "return {guid:G(o),maxVoices:p.max_voices};",
            target=target,
            max_voices=max_voices,
        )

    @mcp.tool()
    async def event_timeline_cursor(target: str, position: float) -> dict:
        """Scrub an event's timeline cursor to a position (in seconds).

        Args:
            target: event:// path or {guid}.
            position: Cursor position in seconds (>= 0).
        """
        if position < 0:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "position must be >= 0")
        return await client.execute(
            "var o=L(p.target);o.timeline.setCursorPosition(p.position);return {position:p.position};",
            target=target,
            position=position,
        )

    @mcp.tool()
    async def event_set_settings(
        target: str,
        max_instances: int | None = None,
        voice_stealing: str | int | None = None,
        priority: int | None = None,
        cooldown_s: float | None = None,
        persistent: bool | None = None,
        min_distance: float | None = None,
        max_distance: float | None = None,
        doppler: bool | None = None,
        doppler_scale: float | None = None,
    ) -> dict:
        """Event macro settings in one call (Studio's Event Macros panel):
        max instances, voice stealing, priority, trigger cooldown,
        persistent, 3D min/max distance, doppler. Values are read back.

        Args:
            target: event:/ path or {guid}.
            max_instances: 1-1000 simultaneous instances (the "Max
                           Instances" macro).
            voice_stealing: oldest | furthest | quietest | virtualize | none
                            (or the raw 0-4 value).
            priority: Studio's priority index 0-4 (default 2 = Medium). The
                      manual lists Lowest..Highest but scripts can't see which
                      end 0 is — confirm one event in Studio before relying
                      on the direction.
            cooldown_s: Minimum seconds between starts (0-60).
            persistent: Keep the instance alive after its timeline ends.
            min_distance: 3D attenuation start distance.
            max_distance: 3D attenuation end distance (> min).
            doppler: Enable doppler.
            doppler_scale: Doppler scale in % (0-500).
        """
        props = {}
        if max_instances is not None:
            if not 1 <= max_instances <= 1000:
                raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "max_instances must be 1-1000")
            props["maxVoices"] = max_instances
        if voice_stealing is not None:
            if isinstance(voice_stealing, str):
                key = voice_stealing.strip().lower()
                if key not in VOICE_STEALING:
                    raise FmodMCPError(
                        ErrorCode.INVALID_TYPE,
                        f"voice_stealing must be one of {', '.join(VOICE_STEALING)}",
                    )
                props["voiceStealing"] = VOICE_STEALING[key]
            elif voice_stealing in VOICE_STEALING.values():
                props["voiceStealing"] = voice_stealing
            else:
                raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "voice_stealing must be 0-4")
        if priority is not None:
            if not 0 <= priority <= 4:
                raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "priority must be 0-4")
            props["priority"] = priority
        if cooldown_s is not None:
            if not 0 <= cooldown_s <= 60:
                raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "cooldown_s must be 0-60")
            props["triggerCooldown"] = float(cooldown_s)
        if persistent is not None:
            props["isPersistent"] = persistent
        if min_distance is not None:
            props["minimumDistance"] = float(min_distance)
        if max_distance is not None:
            props["maximumDistance"] = float(max_distance)
        if (min_distance is not None and max_distance is not None
                and not 0 <= min_distance < max_distance):
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "need 0 <= min_distance < max_distance")
        if doppler is not None:
            props["dopplerEnabled"] = doppler
        if doppler_scale is not None:
            if not 0 <= doppler_scale <= 500:
                raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "doppler_scale must be 0-500")
            props["dopplerScale"] = float(doppler_scale)
        if not props:
            raise FmodMCPError(ErrorCode.MISSING_PARAMETER, "pass at least one setting")
        return await client.execute(
            JS_SET_PROPS
            + "var e=L(p.target);"
            "if(!e.isOfType('Event'))throw new Error(p.target+' is not an event');"
            "var r=__setProps(e.automatableProperties,p.props);"
            "return {guid:G(e),path:P(e),applied:r.applied,clamped:r.clamped};",
            target=target,
            props=props,
        )

    @mcp.tool()
    async def event_get_settings(target: str) -> dict:
        """Read an event's macro settings (max instances, stealing, priority,
        cooldown, persistent, distances, doppler, snapshot intensity).

        Args:
            target: event:/ path or {guid}.
        """
        return await client.execute(
            "var e=L(p.target);var a=e.automatableProperties;"
            "return {guid:G(e),path:P(e),maxInstances:a.maxVoices,voiceStealing:a.voiceStealing,"
            "priority:a.priority,cooldownS:a.triggerCooldown,persistent:a.isPersistent,"
            "minDistance:a.minimumDistance,maxDistance:a.maximumDistance,"
            "doppler:a.dopplerEnabled,dopplerScale:a.dopplerScale};",
            target=target,
        )

    @mcp.tool()
    async def tag_add(target: str, tag: str) -> dict:
        """Tag an event (or other taggable object); the tag is created if it
        doesn't exist. Tags help find/batch-process events (utility_list
        can't filter by tag; use tag_list).

        Args:
            target: event:/ path or {guid}.
            tag: Tag name.
        """
        _check_tag(tag)
        return await client.execute(
            "var o=L(p.target);var t=studio.project.workspace.addTag(p.tag);"
            "if(!t)throw new Error('could not create tag '+p.tag);"
            "var rel=t.relationships.taggables;rel.add(o);var ok=false;"
            "var ds=rel.destinations||[];for(var i=0;i<ds.length;i++){if(G(ds[i])===G(o)){ok=true;break;}}"
            "if(!ok)throw new Error('object (entity '+o.entity+') cannot be tagged');"
            "return {tag:N(t),tagGuid:G(t),target:G(o),taggedCount:ds.length};",
            target=target,
            tag=tag,
        )

    @mcp.tool()
    async def tag_remove(target: str, tag: str) -> dict:
        """Remove a tag from an object.

        Args:
            target: event:/ path or {guid}.
            tag: Tag name.
        """
        _check_tag(tag)
        return await client.execute(
            "var o=L(p.target);var all=studio.project.model.Tag.findInstances()||[];var t=null;"
            "for(var i=0;i<all.length;i++){if(all[i].name===p.tag){t=all[i];break;}}"
            "if(!t)throw new Error('no tag named '+p.tag);"
            "t.relationships.taggables.remove(o);"
            "return {tag:p.tag,target:G(o),taggedCount:t.relationships.taggables.destinations.length};",
            target=target,
            tag=tag,
        )

    @mcp.tool()
    async def tag_list(tag: str | None = None) -> dict:
        """List tags with how many objects carry each — or, with `tag`, every
        object carrying that tag.

        Args:
            tag: Optional tag name to list the objects of.
        """
        if tag is not None:
            _check_tag(tag)
        return await client.execute(
            "var all=studio.project.model.Tag.findInstances()||[];"
            "if(p.tag===null){return {tags:all.map(function(t){return {name:N(t),guid:G(t),"
            "count:t.relationships.taggables.destinations.length};})};}"
            "for(var i=0;i<all.length;i++){if(all[i].name!==p.tag)continue;"
            "var ds=all[i].relationships.taggables.destinations||[];"
            f"return {{tag:p.tag,objects:ds.slice(0,{MAX_OBJECTS_READ}).map(function(o){{"
            "return {guid:G(o),path:P(o),entity:o.entity};})};}"
            "throw new Error('no tag named '+p.tag);",
            tag=tag,
        )


    @mcp.tool()
    async def event_lint(target: str) -> dict:
        """Static check that an event will actually make sound — run it after
        building or editing an event, before building banks. Errors: no
        instruments, SingleSound without audio, zero-length instrument, empty
        playlist, broken nested-event reference. Warnings: -80 dB
        instrument/track/master, 0% trigger probability, an instrument held
        at a sustain point without looping+async (goes silent while held),
        event in no bank, default event name. It can't hear — pair it with
        event_audio_report for the audio itself.

        Args:
            target: event:/ path or {guid}.
        """
        r = await client.execute(
            _JS_LINT
            + "var e=L(p.target);if(!e.isOfType('Event'))throw new Error(p.target+' is not an event');"
            "var res=__lint(e);res.event=P(e);res.ok=res.errors.length===0;return res;",
            target=target,
        )
        return r


def _check_tag(tag: str) -> None:
    if not isinstance(tag, str) or not tag.strip():
        raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "tag must not be empty")
    if len(tag) > MAX_TAG_NAME:
        raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, f"tag too long ({MAX_TAG_NAME} max)")


# Names Studio gives new events; an event still called this is almost always
# a leftover ("New Event", "Nested Event 3", ...).
DEFAULT_EVENT_NAME_JS = "/^(New Event|Nested Event)( \\d+)?$/"

# event_lint's checks. Errors mean the event will not play as intended;
# warnings are likely mistakes worth a look.
_JS_LINT = (
    "function __lint(e){var errs=[],warns=[];"
    "function add(list,o,msg){list.push({guid:o?G(o):null,name:o?(N(o)||o.entity):null,message:msg});}"
    "var snd=studio.project.model.Sound.findInstances({searchContext:e,includeDerivedTypes:true})||[];"
    "if(snd.length===0)add(errs,e,'event has no instruments - it plays nothing');"
    "var sus=studio.project.model.SustainPoint.findInstances({searchContext:e})||[];"
    "for(var i=0;i<snd.length;i++){var s=snd[i];var ent=s.entity;"
    "var nested=!!(s.owner||(s.isOfType('MultiSound')&&s.scattererOwner));"
    "if(ent==='SingleSound'){var af=null;try{af=s.audioFile;}catch(__e){}"
    "if(!af)add(errs,s,'SingleSound has no audio file - it plays silence');}"
    "if(!nested&&s.audioTrack&&!(s.length>0))add(errs,s,'instrument has zero length - it never plays');"
    "if(ent==='MultiSound'&&!s.scattererOwner&&(s.relationships.sounds.destinations||[]).length===0)"
    "add(errs,s,'MultiSound playlist is empty');"
    "if(ent==='SoundScatterer'&&(!s.sound||(s.sound.relationships.sounds.destinations||[]).length===0))"
    "add(errs,s,'Scatterer playlist is empty');"
    "if(ent==='EventSound'){var r=s.event;if(!r||!r.isValid)add(errs,s,'event instrument references no (valid) event');"
    "else if(G(r)===G(e))add(errs,s,'event instrument references its own event');}"
    "if(typeof s.volume==='number'&&s.volume<=-80)add(warns,s,'instrument volume is -80 dB (inaudible)');"
    "if(s.triggerProbabilityEnabled&&s.triggerProbability<=0)add(warns,s,'trigger probability is 0% - never triggers');"
    "if(!nested&&s.parameter&&s.parameter.isOfType&&s.parameter.isOfType('Timeline')){"
    "for(var j=0;j<sus.length;j++){var sp=sus[j].position;"
    "if(sp>=s.start&&sp<s.start+s.length&&!(s.looping&&s.isAsync))"
    "add(warns,s,'instrument spans the sustain point at '+sp+'s but is not looping+async - it goes silent while held');}}}"
    "var tr=(e.relationships.groupTracks.destinations||[]);"
    "for(var k=0;k<tr.length;k++){var mg=tr[k].mixerGroup;if(mg&&mg.volume<=-80)add(warns,mg,'track volume is -80 dB (inaudible)');}"
    "var mm=e.masterTrack?e.masterTrack.mixerGroup:null;if(mm&&mm.volume<=-80)add(warns,mm,'event master volume is -80 dB');"
    "if((e.relationships.banks.destinations||[]).length===0)add(warns,e,'event is in no bank - it will not ship');"
    "if(" + DEFAULT_EVENT_NAME_JS + ".test(N(e)||''))add(warns,e,'event still has a default name');"
    "return {errors:errs,warnings:warns};}"
)
