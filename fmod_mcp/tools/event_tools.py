from mcp.server.fastmcp import FastMCP

from fmod_mcp.safety import ensure_backup
from fmod_mcp.tools._common import JS_SOUNDS, MAX_TRACK_LIST_SOUNDS, js_info, js_list
from fmod_mcp_shared.constants import MAX_NAME_LENGTH, MAX_OBJECTS_READ
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode


def _check_name(name: str) -> None:
    if not name or not name.strip():
        raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "name must not be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE, f"name too long ({MAX_NAME_LENGTH} max)"
        )


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
