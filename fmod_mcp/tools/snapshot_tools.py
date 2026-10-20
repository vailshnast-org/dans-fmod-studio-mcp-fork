from mcp.server.fastmcp import FastMCP

from fmod_mcp.safety import ensure_backup
from fmod_mcp.tools._common import check_identifier, js_list
from fmod_mcp_shared.constants import MAX_NAME_LENGTH, MAX_OBJECTS_READ
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode


def _check_name(name: str) -> None:
    if not name or not name.strip():
        raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "name must not be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE, f"name too long ({MAX_NAME_LENGTH} max)"
        )


# Snapshot model, confirmed live on 2.03.15:
#   snapshot.snapshotTracks     -> SnapshotTrack { mixerStrip, snapshot }
#       (a strip "scoped into" the snapshot)
#   snapshot.snapshotProperties -> SnapshotProperty { propertyName, value,
#       automatableObject, snapshot } (one captured value)
# Both are created with project.create() and linked by setting their ToOne
# relationships; each comes out isValid.
_JS_SCOPE = (
    "function __scope(s,strip){"
    "var tr=s.relationships.snapshotTracks.destinations||[];"
    "for(var i=0;i<tr.length;i++){var ms=tr[i].mixerStrip;"
    "if(ms&&G(ms)===G(strip))return {track:tr[i],reused:true};}"
    "var t=studio.project.create('SnapshotTrack');"
    "if(!t)throw new Error('could not create a SnapshotTrack');"
    "t.mixerStrip=strip;t.snapshot=s;"
    "if(!t.isValid)throw new Error('snapshot track did not become valid for '+strip.entity);"
    "return {track:t,reused:false};}"
    "function __findSnapProp(s,o,name){"
    "var sp=s.relationships.snapshotProperties.destinations||[];"
    "for(var i=0;i<sp.length;i++){var ao=sp[i].automatableObject;"
    "if(ao&&G(ao)===G(o)&&sp[i].propertyName===name)return sp[i];}return null;}"
)

_SNAPSHOT_FIND = "studio.project.model.Snapshot.findInstances()"


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def snapshot_create(name: str) -> dict:
        """Create a mixer snapshot.

        A snapshot captures a set of mixer state changes (group/bus/VCA
        volumes, effect settings) that the game activates as a blendable
        state — e.g. a 'dungeon' or 'night' reverb/level shift layered over
        the base mix. Mixer settings are captured by Studio when you move a
        control while the snapshot is armed; pass the returned path to
        snapshot_bind_group to pin a group's current settings.

        Args:
            name: Snapshot name.
        """
        _check_name(name)
        return await client.execute(
            "var s=studio.project.create('Snapshot');s.name=p.name;"
            "return {guid:G(s),name:N(s),path:P(s)};",
            name=name,
        )

    @mcp.tool()
    async def snapshot_list() -> dict:
        """List every mixer snapshot in the project (capped)."""
        return await client.execute(js_list(_SNAPSHOT_FIND, MAX_OBJECTS_READ))

    @mcp.tool()
    async def snapshot_info(target: str) -> dict:
        """Get a snapshot's guid, name and path.

        Args:
            target: snapshot:/ path or {guid}.
        """
        return await client.execute(
            "var s=L(p.target);return {guid:G(s),name:N(s),path:P(s)};",
            target=target,
        )

    @mcp.tool()
    async def snapshot_rename(target: str, name: str) -> dict:
        """Rename a mixer snapshot.

        Args:
            target: snapshot:/ path or {guid}.
            name: New name.
        """
        _check_name(name)
        return await client.execute(
            "var s=L(p.target);s.name=p.name;return {guid:G(s),name:N(s)};",
            target=target,
            name=name,
        )

    @mcp.tool()
    async def snapshot_delete(target: str) -> dict:
        """Delete a mixer snapshot.

        Args:
            target: snapshot:/ path or {guid}.
        """
        await ensure_backup(client)
        return await client.execute(
            "var s=L(p.target);studio.project.deleteObject(s);return true;",
            target=target,
        )

    @mcp.tool()
    async def snapshot_bind_group(snapshot_target: str, group_target: str) -> dict:
        """Scope a mixer strip (group/bus/return/VCA) into a snapshot — the
        snapshot gets a track for it, like dragging the strip into the
        snapshot in Studio. Reuses an existing scope track (`reused`).
        Then capture values with snapshot_set_property.

        Args:
            snapshot_target: snapshot:/ path or {guid}.
            group_target: Mixer strip path or {guid}.
        """
        # Previously this added to `snapshot.relationships.groups`, which does
        # not exist on 2.03.15 (the real scope is `snapshotTracks`, each a
        # SnapshotTrack pointing at a `mixerStrip`) — it returned bound:false
        # on every call.
        return await client.execute(
            _JS_SCOPE
            + "var s=L(p.snapshot_target);var g=L(p.group_target);"
            "var r=__scope(s,g);"
            "return {snapshot:P(s),strip:P(g),snapshotTrackGuid:G(r.track),"
            "reused:r.reused,bound:true};",
            snapshot_target=snapshot_target,
            group_target=group_target,
        )

    @mcp.tool()
    async def snapshot_set_property(
        snapshot_target: str,
        target: str,
        property: str,
        value: float | bool,
    ) -> dict:
        """Capture one value in a snapshot — e.g. a group's `volume` at -12 dB
        or a lowpass effect's cutoff — applied while the snapshot is active.
        Updates the existing captured value if there is one. A mixer strip
        target is also scoped into the snapshot automatically.

        Args:
            snapshot_target: snapshot:/ path or {guid}.
            target: Mixer strip or effect path/{guid} whose property to capture.
            property: Property name on the target (e.g. "volume").
            value: Value to hold while the snapshot is active.
        """
        check_identifier(property, "property")
        return await client.execute(
            _JS_SCOPE
            + "var s=L(p.snapshot_target);var t=L(p.target);"
            "if(!s.isOfType('Snapshot'))throw new Error(p.snapshot_target+' is not a snapshot');"
            "var mp=null;try{mp=t.properties?t.properties[p.property]:null;}catch(__e){}"
            "if(!mp)throw new Error('target (entity '+t.entity+') has no property '+p.property);"
            "var scoped=null;if(t.isOfType('MixerStrip')){scoped=__scope(s,t);}"
            "var sp=__findSnapProp(s,t,p.property);var created=false;"
            "if(!sp){sp=studio.project.create('SnapshotProperty');"
            "if(!sp)throw new Error('could not create a SnapshotProperty');"
            "sp.propertyName=p.property;sp.snapshot=s;sp.automatableObject=t;created=true;}"
            "sp.value=p.value;"
            "if(!sp.isValid)throw new Error('snapshot property did not become valid');"
            "return {guid:G(sp),snapshot:P(s),target:G(t),property:p.property,"
            "value:sp.value,created:created,"
            "snapshotTrackGuid:scoped?G(scoped.track):null};",
            snapshot_target=snapshot_target,
            target=target,
            property=property,
            value=value,
        )

    @mcp.tool()
    async def snapshot_list_properties(snapshot_target: str) -> dict:
        """List what a snapshot changes: its scoped strips and every
        captured property value, plus its intensity and behavior.

        Args:
            snapshot_target: snapshot:/ path or {guid}.
        """
        return await client.execute(
            "var s=L(p.snapshot_target);"
            "var tr=s.relationships.snapshotTracks.destinations||[];var tOut=[];"
            "for(var i=0;i<tr.length;i++){var ms=tr[i].mixerStrip;"
            "tOut.push({guid:G(tr[i]),stripGuid:ms?G(ms):null,strip:ms?P(ms):null});}"
            "var sp=s.relationships.snapshotProperties.destinations||[];var pOut=[];"
            "for(var j=0;j<sp.length;j++){var o=sp[j].automatableObject;"
            "pOut.push({guid:G(sp[j]),targetGuid:o?G(o):null,target:o?(P(o)||o.entity):null,"
            "targetEntity:o?o.entity:null,property:sp[j].propertyName,value:sp[j].value});}"
            "return {snapshot:P(s),intensity:s.automatableProperties.snapshotIntensity,"
            "behavior:s.behavior,scopedStrips:tOut,properties:pOut};",
            snapshot_target=snapshot_target,
        )

    @mcp.tool()
    async def snapshot_remove_property(
        snapshot_target: str, target: str, property: str
    ) -> dict:
        """Stop a snapshot changing one property (deletes the captured value).

        Args:
            snapshot_target: snapshot:/ path or {guid}.
            target: Mixer strip or effect path/{guid}.
            property: Property name, e.g. "volume".
        """
        check_identifier(property, "property")
        return await client.execute(
            _JS_SCOPE
            + "var s=L(p.snapshot_target);var t=L(p.target);"
            "var sp=__findSnapProp(s,t,p.property);"
            "if(!sp)throw new Error('snapshot does not capture '+p.property+' on that target');"
            "studio.project.deleteObject(sp);"
            "return {removed:true,property:p.property};",
            snapshot_target=snapshot_target,
            target=target,
            property=property,
        )

    @mcp.tool()
    async def snapshot_set_settings(
        snapshot_target: str,
        intensity: float | None = None,
        behavior: int | None = None,
    ) -> dict:
        """Set a snapshot's intensity (0-100 %, how strongly it applies) and/or
        behavior (Studio's numeric enum: 0 = the default, Overriding; 1 =
        Blending).

        Args:
            snapshot_target: snapshot:/ path or {guid}.
            intensity: 0-100.
            behavior: 0 or 1.
        """
        if intensity is None and behavior is None:
            raise FmodMCPError(
                ErrorCode.MISSING_PARAMETER, "pass intensity and/or behavior"
            )
        if intensity is not None and not 0 <= intensity <= 100:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "intensity must be 0-100")
        if behavior is not None and behavior not in (0, 1):
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "behavior must be 0 or 1")
        return await client.execute(
            "var s=L(p.snapshot_target);"
            "if(!s.isOfType('Snapshot'))throw new Error(p.snapshot_target+' is not a snapshot');"
            "if(p.intensity!==null)s.automatableProperties.snapshotIntensity=p.intensity;"
            "if(p.behavior!==null)s.behavior=p.behavior;"
            "return {snapshot:P(s),intensity:s.automatableProperties.snapshotIntensity,"
            "behavior:s.behavior};",
            snapshot_target=snapshot_target,
            intensity=intensity,
            behavior=behavior,
        )
