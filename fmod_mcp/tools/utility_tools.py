from mcp.server.fastmcp import FastMCP

from fmod_mcp.safety import ensure_backup
from fmod_mcp.tools._common import (
    JS_PROPS,
    JS_SET_PROPS,
    check_identifier,
    check_property_values,
)
from fmod_mcp_shared.constants import MAX_OBJECTS_READ
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode

# Common model classes, named in utility_list's docstring as a hint. Any
# entity name `studio.project.model` actually knows is accepted (read-only,
# capped), so this is documentation, not a whitelist.
COMMON_LIST_TYPES = (
    "Event",
    "Bank",
    "MixerGroup",
    "MixerBus",
    "MixerReturn",
    "MixerVCA",
    "Snapshot",
    "Folder",
    "EventFolder",
    "AudioFile",
    "ParameterPreset",
    "SingleSound",
    "MultiSound",
    "Sound",
    "MixerEffect",
    "Modulator",
)

RELATIONSHIP_ACTIONS = ("add", "remove")

# Destinations reported per relationship by utility_dump — enough to follow
# a link without turning a big folder's dump into a context flood.
_DUMP_DESTINATIONS = 10

# Per-category cap for utility_validate's findings.
_VALIDATE_CAP = 100


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def utility_lookup(target: str) -> dict:
        """Resolve any object (event, bank, group, asset, ...) to its identity.

        Args:
            target: Path (event:/..., bank:/...) or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);return {guid:G(o),name:N(o),path:P(o),entity:o.entity};",
            target=target,
        )

    @mcp.tool()
    async def utility_list(
        obj_type: str, include_derived: bool = False, within: str | None = None
    ) -> dict:
        """List every object of a model entity type (capped), optionally
        including derived types and/or confined to one object's children.

        Args:
            obj_type: Any model entity name, e.g. Event, Bank, MixerGroup,
                      MixerBus, MixerReturn, MixerVCA, Snapshot, Folder,
                      AudioFile, ParameterPreset, SingleSound, Sound,
                      MixerEffect, Modulator.
            include_derived: Also return derived types (Sound -> every
                             instrument type, MixerBus -> groups/returns).
            within: Optional path/{guid} to search inside (e.g. one event).
        """
        check_identifier(obj_type, "obj_type")
        return await client.execute(
            "var cls=studio.project.model[p.obj_type];"
            "if(!cls||!(cls.findInstances))throw new Error('No model class '+p.obj_type);"
            "var opts={includeDerivedTypes:!!p.include_derived};"
            "if(p.within)opts.searchContext=L(p.within);"
            "var arr=cls.findInstances(opts)||[];"
            "var out=[];"
            f"for(var i=0;i<arr.length&&i<{MAX_OBJECTS_READ};i++){{"
            "out.push({guid:G(arr[i]),name:N(arr[i]),path:P(arr[i]),entity:arr[i].entity});}"
            "return {total:arr.length,items:out};",
            obj_type=obj_type,
            include_derived=include_derived,
            within=within,
        )

    @mcp.tool()
    async def utility_is_valid(target: str) -> dict:
        """Check whether an object is valid (survived recent edits).

        Args:
            target: Object path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);return {valid:!!(o.isValid)};",
            target=target,
        )

    @mcp.tool()
    async def utility_delete(target: str) -> dict:
        """Delete any object from the project.

        Warning: destructive and not undoable from the terminal.

        Args:
            target: Object path or {guid}.
        """
        await ensure_backup(client)
        return await client.execute(
            "var o=L(p.target);studio.project.deleteObject(o);return true;",
            target=target,
        )

    @mcp.tool()
    async def utility_dump(target: str) -> dict:
        """Real introspection: every plain property (with value) + every
        relationship (cardinality, count, first destinations) on a live
        object. Use this BEFORE concluding a capability "doesn't exist" —
        FMOD's docs only list methods, not plain properties (e.g.
        `looping`), and FMOD's own `dump()` only logs to Studio's console
        and returns nothing here.

        Args:
            target: Object path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);"
            "var props=[];"
            "for(var k in o){"
            "if(k.charAt(0)==='_')continue;"
            "var v;try{v=o[k];}catch(__e){continue;}"
            "var t=typeof v;if(t==='function'||t==='object')continue;"
            "props.push({name:k,type:t,value:v});}"
            "var rels=[];"
            "for(var k in o.relationships){"
            "var r;try{r=o.relationships[k];}catch(__e){continue;}"
            "if(!r||typeof r!=='object')continue;"
            "var ds=(r.destinations)?r.destinations:[];"
            f"var dl=[];for(var j=0;j<ds.length&&j<{_DUMP_DESTINATIONS};j++){{"
            "dl.push({guid:G(ds[j]),name:N(ds[j]),entity:ds[j].entity});}"
            "rels.push({name:k,cardinality:r.cardinality||null,"
            "count:r.destinations?ds.length:null,destinations:dl});}"
            "return {guid:G(o),entity:o.entity,properties:props,relationships:rels};",
            target=target,
        )

    @mcp.tool()
    async def utility_describe_entity(entity: str) -> dict:
        """Describe a model entity TYPE (not an object) via FMOD's own
        entity.document(): its properties + relationships. Use it to learn
        what a type supports before creating/editing one.

        Args:
            entity: Entity name, e.g. SingleSound, MixerSend, LoopRegion.
        """
        check_identifier(entity, "entity")
        return await client.execute(
            "var cls=studio.project.model[p.entity];"
            "if(!cls)throw new Error('No model entity named '+p.entity);"
            "var doc=null;try{doc=String(cls.document());}catch(__e){}"
            "var sup=null;try{sup=cls.superEntities||cls.superentities||null;}catch(__e){}"
            "return {entity:p.entity,isAbstract:!!cls.isAbstract,"
            "isSingleton:!!cls.isSingleton,superEntities:sup,document:doc};",
            entity=entity,
        )

    @mcp.tool()
    async def utility_get_properties(target: str) -> dict:
        """Read every plain property (name -> current value) of an object —
        a lighter utility_dump for when you only need values to edit.

        Args:
            target: Object path or {guid}.
        """
        return await client.execute(
            JS_PROPS
            + "var o=L(p.target);"
            "return {guid:G(o),entity:o.entity,properties:__props(o)};",
            target=target,
        )

    @mcp.tool()
    async def utility_set_properties(target: str, properties: dict) -> dict:
        """Set plain properties on any object — instrument volume/pitch/
        looping, effect parameters (reverb decay, compressor threshold),
        modulator depth, bus/event settings, ...

        Validated: each name must exist on the object (else it errors — run
        utility_dump for real names), the value type must match, and every
        value is read back. `clamped` lists properties Studio adjusted.

        Args:
            target: Object path or {guid}.
            properties: {"name": value, ...} — numbers, bools or strings.
        """
        props = check_property_values(properties)
        return await client.execute(
            JS_SET_PROPS
            + "var o=L(p.target);var r=__setProps(o,p.props);"
            "return {guid:G(o),entity:o.entity,applied:r.applied,clamped:r.clamped};",
            target=target,
            props=props,
        )

    @mcp.tool()
    async def utility_set_relationship(
        target: str, relationship: str, destination: str, action: str = "add"
    ) -> dict:
        """Add/remove a link between two objects (e.g. a strip to a VCA, an
        instrument's owner, an asset's folder). For a ToOne relationship
        `add` replaces the current destination. Verified by reading the
        relationship back.

        Args:
            target: Object path or {guid} owning the relationship.
            relationship: Name from utility_dump's relationships list.
            destination: Object path or {guid} to link/unlink.
            action: add | remove.
        """
        check_identifier(relationship, "relationship")
        if action not in RELATIONSHIP_ACTIONS:
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER,
                f"action must be one of {RELATIONSHIP_ACTIONS}",
            )
        return await client.execute(
            "var o=L(p.target);var d=L(p.destination);"
            "var r=o.relationships?o.relationships[p.relationship]:null;"
            "if(!r)throw new Error('object (entity '+o.entity+') has no relationship '+"
            "p.relationship+' - call utility_dump to list them');"
            "var ok=(p.action==='remove')?r.remove(d):r.add(d);"
            "var ds=r.destinations||[];var present=false;"
            "for(var i=0;i<ds.length;i++){if(G(ds[i])===G(d)){present=true;break;}}"
            "if(p.action==='add'&&!present)throw new Error("
            "'relationship add did not take effect (Studio rejected '+d.entity+"
            "' as a destination of '+p.relationship+')');"
            "if(p.action==='remove'&&present)throw new Error("
            "'relationship remove did not take effect');"
            "return {guid:G(o),relationship:p.relationship,cardinality:r.cardinality,"
            "action:p.action,ok:!!ok,count:ds.length};",
            target=target,
            relationship=relationship,
            destination=destination,
            action=action,
        )

    @mcp.tool()
    async def utility_validate() -> dict:
        """Audit the project for problems that build fine but play wrong:
        events in no bank (never ship), events with no instruments, single
        instruments with no audio (play silence), invalid objects (missing
        required relationships), and events still named "New Event" /
        "Nested Event" (usually leftovers; reported, not counted against
        ok). Capped per category. For one event in depth use event_lint.
        """
        # The previous version called studio.project.validate(), which is not
        # part of FMOD's scripting API (absent from the 2.03 reference) — it
        # threw, and the catch turned that into a meaningless string result.
        return await client.execute(
            f"var cap={_VALIDATE_CAP};"
            "var events=studio.project.model.Event.findInstances()||[];"
            "var noBank=[],empty=[],invalid=[],silent=[],defaultNamed=[];"
            "var dn=/^(New Event|Nested Event)( \\d+)?$/;"
            "for(var i=0;i<events.length;i++){var e=events[i];"
            "var br=e.relationships.banks;"
            "var nb=(br&&br.destinations)?br.destinations.length:0;"
            "if(nb===0&&noBank.length<cap)noBank.push({guid:G(e),path:P(e)});"
            "if(dn.test(N(e)||'')&&defaultNamed.length<cap)defaultNamed.push({guid:G(e),path:P(e)});"
            "var n=0;try{n=(studio.project.model.Sound.findInstances("
            "{searchContext:e,includeDerivedTypes:true})||[]).length;}catch(__e){n=-1;}"
            "if(n===0&&empty.length<cap)empty.push({guid:G(e),path:P(e)});}"
            "var singles=studio.project.model.SingleSound.findInstances()||[];"
            "for(var j=0;j<singles.length&&silent.length<cap;j++){"
            "var af=null;try{af=singles[j].audioFile;}catch(__e){}"
            "if(!af)silent.push({guid:G(singles[j]),name:N(singles[j])});}"
            "var types=['Event','SingleSound','MultiSound','MixerGroup','MixerReturn',"
            "'Snapshot','TransitionSourceSound','TransitionDestinationSound'];"
            "for(var t=0;t<types.length;t++){var cls=studio.project.model[types[t]];"
            "if(!cls)continue;var arr=[];try{arr=cls.findInstances()||[];}catch(__e){}"
            "for(var k=0;k<arr.length&&invalid.length<cap;k++){"
            "if(arr[k].isValid===false)invalid.push("
            "{guid:G(arr[k]),name:N(arr[k]),entity:types[t]});}}"
            "return {eventCount:events.length,"
            "eventsNotInAnyBank:noBank,eventsWithNoInstruments:empty,"
            "singleSoundsWithoutAudio:silent,invalidObjects:invalid,"
            "eventsWithDefaultNames:defaultNamed,"
            "ok:noBank.length+empty.length+silent.length+invalid.length===0};"
        )
