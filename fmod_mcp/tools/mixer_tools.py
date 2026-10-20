from mcp.server.fastmcp import FastMCP

from fmod_mcp.safety import ensure_backup
from fmod_mcp.tools._common import JS_SET_PROPS, check_property_values, js_list
from fmod_mcp_shared.constants import MAX_NAME_LENGTH, MAX_OBJECTS_READ
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode

# Volume is in dB in FMOD Studio's mixer (-80 .. +10).
VOLUME_MIN, VOLUME_MAX = -80.0, 10.0

# Documented effects the effect chain accepts.
ALLOWED_EFFECTS = {
    "ThreeEQEffect",
    "GainEffect",
    "ChannelMixEffect",
    "ChorusEffect",
    "CompressorEffect",
    "ConvolutionReverbEffect",
    "DistortionEffect",
    "DelayEffect",
    "FlangerEffect",
    "LimiterEffect",
    "MultibandEqEffect",
    "PitchShifterEffect",
    "SFXReverbEffect",
    "TransceiverEffect",
    "TremoloEffect",
    "HighpassEffect",
    "HighpassSimpleEffect",
    "LowpassEffect",
    "LowpassSimpleEffect",
    "ParamEqEffect",
    "SpatialiserEffect",
    "ObjectSpatialiserEffect",
    "LoudnessMeter",
    "SendEffect",
}

# __send(group, ret, levelDb): add a MixerSend to `group`'s chain and point it
# at `ret`, verified by read-back. The 2.03 reference does not list
# 'SendEffect' among addEffect()'s accepted strings (the entity is
# model.MixerSend), so it falls back to creating a MixerSend and appending
# it to the chain's `effects` relationship. The send->return link's
# relationship name isn't documented either: each candidate is tried and
# the first whose destinations then contain `ret` wins — otherwise it raises
# (and removes the half-made send) instead of reporting a send to nowhere.
JS_SEND = (
    "function __send(g,ret,levelDb){"
    "if(!g.effectChain)throw new Error('source (entity '+g.entity+') has no effect chain');"
    "var fx=null;try{fx=g.effectChain.addEffect('SendEffect');}catch(__e){}"
    "if(!fx){fx=studio.project.create('MixerSend');"
    "if(!fx)throw new Error('could not create a MixerSend');"
    "g.effectChain.relationships.effects.add(fx);}"
    "var names=['mixerReturn','target','destination','returnBus'];var via=null;"
    "for(var i=0;i<names.length&&!via;i++){var rel=fx.relationships?fx.relationships[names[i]]:null;"
    "if(!rel)continue;try{rel.add(ret);}catch(__e){continue;}"
    "var ds=rel.destinations||[];"
    "for(var j=0;j<ds.length;j++){if(G(ds[j])===G(ret)){via=names[i];break;}}}"
    "if(!via){try{g.effectChain.relationships.effects.remove(fx);"
    "studio.project.deleteObject(fx);}catch(__e){}"
    "throw new Error('could not link the send to the return - run utility_dump on a "
    "MixerSend to find its return relationship, then utility_set_relationship');}"
    "var lvl=null;try{if(fx.properties&&fx.properties.level){fx.level=levelDb;lvl=fx.level;}}catch(__e){}"
    "return {sendGuid:G(fx),sendEntity:fx.entity,returnGuid:G(ret),linkedVia:via,level:lvl};}"
)



def _check_name(name: str) -> None:
    if not name or not name.strip():
        raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "name must not be empty")
    if len(name) > MAX_NAME_LENGTH:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE, f"name too long ({MAX_NAME_LENGTH} max)"
        )


def _check_volume(db: float) -> None:
    if not VOLUME_MIN <= db <= VOLUME_MAX:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE,
            f"volume must be {VOLUME_MIN:g}..{VOLUME_MAX:g} dB",
        )


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def mixer_group_create(name: str, output_target: str | None = None) -> dict:
        """Create a mixer group (routed to Master by default).

        Args:
            name: Group name.
            output_target: Optional output bus/group path or {guid}.
        """
        _check_name(name)
        body = "var g=studio.project.create('MixerGroup');g.name=p.name;"
        # The docstring always promised "routed to Master by default", but
        # nothing set the output — make the default explicit.
        if output_target:
            body += "g.output=L(p.output_target);"
        else:
            body += (
                "if(!g.output){try{g.output=studio.project.workspace.mixer.masterBus;}"
                "catch(__e){}}"
            )
        body += "return {guid:G(g),name:N(g),path:P(g),outputGuid:g.output?G(g.output):null};"
        return await client.execute(body, name=name, output_target=output_target)

    @mcp.tool()
    async def mixer_group_list() -> dict:
        """List every mixer group in the project (capped)."""
        return await client.execute(
            js_list("studio.project.model.MixerGroup.findInstances()", MAX_OBJECTS_READ)
        )

    @mcp.tool()
    async def mixer_group_info(target: str) -> dict:
        """Get a mixer group's guid, name, path and current volume (dB).

        Args:
            target: Group path or {guid}.
        """
        return await client.execute(
            "var g=L(p.target);var v=null;"
            "try{v=g.volume;}catch(__e){}"
            "return {guid:G(g),name:N(g),path:P(g),volume:v};",
            target=target,
        )

    @mcp.tool()
    async def mixer_group_rename(target: str, name: str) -> dict:
        """Rename a mixer group.

        Args:
            target: Group path or {guid}.
            name: New name.
        """
        _check_name(name)
        return await client.execute(
            "var g=L(p.target);g.name=p.name;return {guid:G(g),name:N(g)};",
            target=target,
            name=name,
        )

    @mcp.tool()
    async def mixer_group_delete(target: str) -> dict:
        """Delete a mixer group.

        Warning: objects routed through it will need re-routing afterwards.

        Args:
            target: Group path or {guid}.
        """
        await ensure_backup(client)
        return await client.execute(
            "var g=L(p.target);studio.project.deleteObject(g);return true;",
            target=target,
        )

    @mcp.tool()
    async def mixer_group_route(target: str, output_target: str) -> dict:
        """Route a group's output to a bus or group. Keep routing inside the
        same event/mixer surface — routing an event's master track into a
        different event's mixer has been known to crash Studio.

        Args:
            target: Group path or {guid}.
            output_target: Destination bus/group path or {guid}.
        """
        return await client.execute(
            "var g=L(p.target);g.output=L(p.output_target);return true;",
            target=target,
            output_target=output_target,
        )

    @mcp.tool()
    async def mixer_group_volume(target: str, db: float) -> dict:
        """Set a mixer group's volume, in dB (-80 .. +10).

        Args:
            target: Group path or {guid}.
            db: Volume in decibels.
        """
        _check_volume(db)
        return await client.execute(
            "var g=L(p.target);g.volume=p.db;return {guid:G(g),volume:p.db};",
            target=target,
            db=db,
        )

    @mcp.tool()
    async def mixer_effect_add(
        target: str, effect: str, settings: dict | None = None
    ) -> dict:
        """Add an effect to a group's effect chain, optionally configuring
        it in the same call (validated like utility_set_properties).

        Args:
            target: Group path or {guid} (event track mixer groups work too).
            effect: Effect type, e.g. CompressorEffect, LimiterEffect,
                    ParamEqEffect, LowpassEffect, DelayEffect,
                    ConvolutionReverbEffect, DistortionEffect, ...
            settings: Optional {"property": value} for the new effect —
                      read real names with utility_get_properties(effect).
        """
        if effect not in ALLOWED_EFFECTS:
            raise FmodMCPError(ErrorCode.INVALID_TYPE, f"invalid effect {effect!r}")
        props = check_property_values(settings) if settings else None
        return await client.execute(
            JS_SET_PROPS
            + "var g=L(p.target);var fx=g.effectChain.addEffect(p.effect);"
            "if(!fx)throw new Error('addEffect returned nothing for '+p.effect);"
            "var applied=null;if(p.settings){applied=__setProps(fx,p.settings);}"
            "return {guid:G(fx),entity:fx.entity,applied:applied};",
            target=target,
            effect=effect,
            settings=props,
        )

    @mcp.tool()
    async def mixer_effect_remove(target: str, effect: str) -> dict:
        """Remove an effect from a group's chain and delete it. Refuses the
        built-in fader/panner, which every chain must keep.

        Args:
            target: Group path or {guid} owning the chain.
            effect: Effect {guid} from mixer_effect_list.
        """
        await ensure_backup(client)
        return await client.execute(
            "var g=L(p.target);var fx=L(p.effect);"
            "if(fx.entity==='MixerBusFader'||fx.entity==='MixerBusPanner')"
            "throw new Error('refusing to remove the built-in '+fx.entity+' of the chain');"
            "var rel=g.effectChain.relationships.effects;"
            "var ds=(rel&&rel.destinations)?rel.destinations:[];var found=false;"
            "for(var i=0;i<ds.length;i++){if(G(ds[i])===G(fx)){found=true;break;}}"
            "if(!found)throw new Error('effect '+p.effect+' is not on this chain');"
            "rel.remove(fx);studio.project.deleteObject(fx);"
            "return {removed:p.effect};",
            target=target,
            effect=effect,
        )

    @mcp.tool()
    async def mixer_effect_list(target: str) -> dict:
        """List the effects on a group's chain.

        Args:
            target: Group path or {guid}.
        """
        return await client.execute(
            "var g=L(p.target);"
            "var rel=g.effectChain.relationships.effects;"
            "var arr=(rel&&rel.destinations)?rel.destinations:[];"
            "var out=[];"
            "for(var i=0;i<arr.length&&i<50;i++){"
            "out.push({guid:G(arr[i]),name:N(arr[i]),entity:arr[i].entity});}"
            "return out;",
            target=target,
        )

    @mcp.tool()
    async def mixer_master_info() -> dict:
        """Get the master bus guid, name and volume."""
        return await client.execute(
            "var mb=studio.project.workspace.mixer.masterBus;"
            "return {guid:G(mb),name:N(mb),volume:mb.volume};"
        )

    @mcp.tool()
    async def mixer_master_volume(db: float) -> dict:
        """Set the master bus volume, in dB (-80 .. +10).

        Args:
            db: Volume in decibels.
        """
        _check_volume(db)
        return await client.execute(
            "var mb=studio.project.workspace.mixer.masterBus;mb.volume=p.db;return {volume:p.db};",
            db=db,
        )

    @mcp.tool()
    async def vca_create(name: str) -> dict:
        """Create a VCA (Voltage-Controlled Amplifier) — a volume control
        that scales every mixer strip assigned to it, for grouping several
        buses under one fader (e.g. "Music", "SFX", "Voice").

        Args:
            name: VCA name.
        """
        _check_name(name)
        return await client.execute(
            "var v=studio.project.create('MixerVCA');v.name=p.name;"
            "return {guid:G(v),name:N(v)};",
            name=name,
        )

    @mcp.tool()
    async def vca_list() -> dict:
        """List every VCA in the project (capped)."""
        return await client.execute(
            js_list("studio.project.model.MixerVCA.findInstances()", MAX_OBJECTS_READ)
        )

    @mcp.tool()
    async def vca_info(target: str) -> dict:
        """Get a VCA's guid, name and current volume (dB).

        Args:
            target: vca:/ path or {guid}.
        """
        return await client.execute(
            "var v=L(p.target);var vol=null;try{vol=v.volume;}catch(__e){}"
            "return {guid:G(v),name:N(v),volume:vol};",
            target=target,
        )

    @mcp.tool()
    async def vca_volume(target: str, db: float) -> dict:
        """Set a VCA's volume, in dB (-80 .. +10).

        Args:
            target: vca:/ path or {guid}.
            db: Volume in decibels.
        """
        _check_volume(db)
        return await client.execute(
            "var v=L(p.target);v.volume=p.db;return {guid:G(v),volume:p.db};",
            target=target,
            db=db,
        )

    @mcp.tool()
    async def vca_assign(vca_target: str, strip_target: str) -> dict:
        """Assign a mixer strip (group/bus/return) to a VCA so the VCA's
        fader scales it alongside every other strip assigned to it.
        Verified by reading the assignment back.

        Args:
            vca_target: vca:/ path or {guid}.
            strip_target: Mixer group/bus path or {guid} to assign.
        """
        # A strip's VCAs are its `masters` relationship (VCA side: `slaves`),
        # confirmed live on 2.03.15. The previous version tried `vcas` /
        # `assignedVCAs`, which don't exist, so it failed on every call.
        return await client.execute(
            "var v=L(p.vca_target);var s=L(p.strip_target);"
            "if(!v.isOfType('MixerVCA'))throw new Error(p.vca_target+' is not a VCA');"
            "var rel=s.relationships?s.relationships.masters:null;"
            "if(!rel)throw new Error('target (entity '+s.entity+') cannot be assigned to a VCA');"
            "rel.add(v);var ds=rel.destinations||[];var ok=false;"
            "for(var i=0;i<ds.length;i++){if(G(ds[i])===G(v)){ok=true;break;}}"
            "if(!ok)throw new Error('VCA assignment did not take effect');"
            "return {vca:G(v),strip:G(s),stripVcaCount:ds.length};",
            vca_target=vca_target,
            strip_target=strip_target,
        )

    @mcp.tool()
    async def vca_unassign(vca_target: str, strip_target: str) -> dict:
        """Remove a mixer strip from a VCA.

        Args:
            vca_target: vca:/ path or {guid}.
            strip_target: Mixer group/bus path or {guid}.
        """
        return await client.execute(
            "var v=L(p.vca_target);var s=L(p.strip_target);"
            "var rel=s.relationships?s.relationships.masters:null;"
            "if(!rel)throw new Error('target (entity '+s.entity+') has no VCA assignments');"
            "rel.remove(v);var ds=rel.destinations||[];"
            "for(var i=0;i<ds.length;i++){if(G(ds[i])===G(v))"
            "throw new Error('VCA unassignment did not take effect');}"
            "return {vca:G(v),strip:G(s),stripVcaCount:ds.length};",
            vca_target=vca_target,
            strip_target=strip_target,
        )

    @mcp.tool()
    async def vca_list_strips(vca_target: str) -> dict:
        """List the mixer strips assigned to a VCA.

        Args:
            vca_target: vca:/ path or {guid}.
        """
        return await client.execute(
            "var v=L(p.vca_target);"
            "var ds=v.relationships.slaves.destinations||[];var out=[];"
            "for(var i=0;i<ds.length;i++){out.push({guid:G(ds[i]),path:P(ds[i]),entity:ds[i].entity});}"
            "return {vca:P(v),strips:out};",
            vca_target=vca_target,
        )

    @mcp.tool()
    async def mixer_effect_add_plugin(
        target: str, plugin: str, settings: dict | None = None
    ) -> dict:
        """Add a plug-in effect (e.g. "Steam Audio Spatializer", "Resonance
        Audio Source") to a group's/track's effect chain. Names come from
        project_list_plugins.

        Args:
            target: Group path or {guid} (event track mixer groups work too).
            plugin: Exact plug-in name from project_list_plugins.
            settings: Optional {"property": value} for the new effect.
        """
        props = check_property_values(settings) if settings else None
        return await client.execute(
            JS_SET_PROPS
            + "var g=L(p.target);"
            "if(!g.effectChain)throw new Error('target (entity '+g.entity+') has no effect chain');"
            "var avail=studio.project.findAvailablePlugins()||[];var known=false;"
            "for(var i=0;i<avail.length;i++){if(String(avail[i])===p.plugin){known=true;break;}}"
            "if(!known)throw new Error('plug-in not available: '+p.plugin+' (see project_list_plugins)');"
            "var fx=studio.project.workspace.createPlugin(p.plugin);"
            "if(!fx)throw new Error('createPlugin returned nothing for '+p.plugin);"
            "if(!fx.isOfType('MixerEffect')){studio.project.deleteObject(fx);"
            "throw new Error(p.plugin+' is a plug-in instrument, not an effect - use sound_add_plugin');}"
            "g.effectChain.relationships.effects.add(fx);"
            "if(!fx.owner||G(fx.owner)!==G(g.effectChain))throw new Error('plug-in did not attach to the chain');"
            "var applied=null;if(p.settings){applied=__setProps(fx,p.settings);}"
            "return {guid:G(fx),entity:fx.entity,plugin:p.plugin,applied:applied};",
            target=target,
            plugin=plugin,
            settings=props,
        )

    @mcp.tool()
    async def mixer_return_create(name: str, output_target: str | None = None) -> dict:
        """Create a project-level return bus (e.g. a shared "Reverb" bus
        every event can send to), routed to Master by default. Then use
        mixer_send_add from any group/track to feed it, and
        mixer_effect_add to put the reverb on it.

        Args:
            name: Return bus name.
            output_target: Optional output bus/group path or {guid}.
        """
        _check_name(name)
        return await client.execute(
            "var r=studio.project.create('MixerReturn');"
            "if(!r)throw new Error('studio.project.create failed for MixerReturn');"
            "r.name=p.name;"
            "if(p.output_target){r.output=L(p.output_target);}"
            "else if(!r.output){try{r.output=studio.project.workspace.mixer.masterBus;}catch(__e){}}"
            "return {guid:G(r),name:N(r),path:P(r),outputGuid:r.output?G(r.output):null};",
            name=name,
            output_target=output_target,
        )

    @mcp.tool()
    async def mixer_send_add(
        source_group_target: str, return_target: str, level_db: float = 0.0
    ) -> dict:
        """Add a send from a mixer group / event track to a return bus
        (project-level from mixer_return_create, or an event return track).
        The send is verified to actually point at the return.

        Args:
            source_group_target: Source group path or mixerGroupGuid.
            return_target: Return bus path or {guid}.
            level_db: Send level in dB (-80..+10, default 0).
        """
        _check_volume(level_db)
        return await client.execute(
            JS_SEND + "var g=L(p.source_group_target);var ret=L(p.return_target);"
            "return __send(g,ret,p.level_db);",
            source_group_target=source_group_target,
            return_target=return_target,
            level_db=level_db,
        )

    @mcp.tool()
    async def mixer_send_create(
        event_target: str,
        source_group_target: str,
        return_name: str,
        level_db: float = 0.0,
    ) -> dict:
        """Create a return track inside one event's mixer plus a send to it
        from one of that event's groups. For a bus shared by many events,
        use mixer_return_create + mixer_send_add instead.

        Args:
            event_target: event:// path or {guid}, owns both the source
                          group and the new return.
            source_group_target: Source mixerGroupGuid to send from.
            return_name: Name for the new return track.
            level_db: Send level in dB (-80..+10, default 0).
        """
        _check_name(return_name)
        _check_volume(level_db)
        return await client.execute(
            JS_SEND + "var e=L(p.event_target);var g=L(p.source_group_target);"
            "var rt=e.addReturnTrack(p.return_name);"
            "if(!rt)throw new Error('addReturnTrack returned nothing');"
            # A ReturnTrack's bus is its `mixerReturn` (an EventMixerReturn);
            # unlike a GroupTrack it has no `mixerGroup` (confirmed live).
            "var ret=rt.mixerReturn;"
            "if(!ret)throw new Error('return track has no mixerReturn bus');"
            "var r=__send(g,ret,p.level_db);"
            "r.returnTrackGuid=G(rt);r.returnName=N(ret)||p.return_name;"
            "return r;",
            event_target=event_target,
            source_group_target=source_group_target,
            return_name=return_name,
            level_db=level_db,
        )
