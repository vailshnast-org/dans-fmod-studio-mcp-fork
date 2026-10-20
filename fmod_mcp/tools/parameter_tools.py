from mcp.server.fastmcp import FastMCP

from fmod_mcp.tools._common import JS_PARAM
from fmod_mcp_shared.constants import MAX_NAME_LENGTH
from fmod_mcp_shared.error_codes import FmodMCPError, ErrorCode

# The FMOD scripting API distinguishes game parameters (set by the game at
# runtime) from the automation curves on a timeline. These are the documented
# `studio.project.parameterType` members (2.03 reference; `Invalid` omitted).
ALLOWED_PARAM_TYPES = {
    "User",
    "UserDiscrete",
    "UserEnumeration",
    "Distance",
    "DistanceNormalized",
    "Direction",
    "Elevation",
    "EventConeAngle",
    "EventOrientation",
    "Speed",
    "SpeedAbsolute",
}

MAX_ENUM_LABELS = 128

# Builds the documented parameterDefinition object ({name, type, min, max,
# enumerationLabels}) shared by Event.addGameParameter and
# workspace.addGameParameter. A labeled parameter's range is its label
# indices, so min/max are derived from the labels instead.
_JS_PARAM_DEFINITION = (
    "var pt=studio.project.parameterType[p.param_type];"
    "if(pt===undefined)throw new Error('Unknown parameter type: '+p.param_type);"
    "var def={name:p.name,type:pt,min:p.min,max:p.max};"
    "if(p.labels){def.enumerationLabels=p.labels;def.min=0;def.max=p.labels.length-1;}"
)


def _check_definition(param_type: str, min: float, max: float, labels) -> None:
    if param_type not in ALLOWED_PARAM_TYPES:
        raise FmodMCPError(ErrorCode.INVALID_TYPE, f"invalid param_type {param_type!r}")
    if labels is not None:
        if param_type != "UserEnumeration":
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER,
                "labels only apply to param_type='UserEnumeration'",
            )
        if (
            not labels
            or len(labels) > MAX_ENUM_LABELS
            or not all(isinstance(x, str) and x for x in labels)
        ):
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER,
                f"labels must be 1-{MAX_ENUM_LABELS} non-empty strings",
            )
    elif not min < max:
        raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "min must be < max")


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
    async def parameter_add(
        event_target: str,
        name: str,
        param_type: str = "User",
        min: float = 0.0,
        max: float = 1.0,
        labels: list[str] | None = None,
    ) -> dict:
        """Add a game parameter to an event. Errors if a parameter with this
        name already exists on the event, rather than creating a duplicate —
        use parameter_set_initial/parameter_list on the existing one instead.

        The parameter is then settable by the game at runtime, or provides an
        automation line target on the event's timeline.

        Args:
            event_target: event:/ path or {guid}.
            name: Parameter name.
            param_type: User | UserDiscrete | UserEnumeration | Distance |
                        DistanceNormalized | Direction | Elevation |
                        EventConeAngle | EventOrientation | Speed |
                        SpeedAbsolute.
            min: Minimum value (default 0).
            max: Maximum value (default 1).
            labels: UserEnumeration only — labels in order (the range comes
                    from the labels; min/max are ignored).
        """
        _check_name(name)
        _check_definition(param_type, min, max, labels)
        return await client.execute(
            "var e=L(p.event_target);"
            "var existing=(e.getParameterPresets?e.getParameterPresets():[])||[];"
            "function pname(item){var rel=item.relationships&&item.relationships.presetOwner;"
            "var dest=rel?rel.destinations:null;return (dest&&dest[0])?N(dest[0]):null;}"
            "for(var i=0;i<existing.length;i++){"
            "if(pname(existing[i])===p.name){throw new Error("
            "'parameter \\''+p.name+'\\' already exists on this event (guid '+"
            "G(existing[i])+'); use parameter_set_initial to change it or "
            "parameter_list to inspect it instead of creating a duplicate.');}}"
            + _JS_PARAM_DEFINITION
            + "var prm=e.addGameParameter(def);"
            "if(!prm)throw new Error('addGameParameter returned nothing');"
            "return {guid:G(prm),name:p.name,type:p.param_type};",
            event_target=event_target,
            name=name,
            param_type=param_type,
            min=min,
            max=max,
            labels=labels,
        )

    @mcp.tool()
    async def parameter_add_global(
        name: str,
        param_type: str = "User",
        min: float = 0.0,
        max: float = 1.0,
        labels: list[str] | None = None,
    ) -> dict:
        """Add a GLOBAL (project-level) parameter, e.g. TimeOfDay or
        GameState — one value the game sets once for every event using it.
        Reference it afterwards as "parameter:/<name>" (automation driver,
        sound sheet, trigger condition, parameter_set_cursor). Errors if a
        global parameter with that name already exists.

        Args:
            name: Parameter name.
            param_type: Same types as parameter_add.
            min: Minimum value (default 0).
            max: Maximum value (default 1).
            labels: UserEnumeration only — labels in order.
        """
        _check_name(name)
        _check_definition(param_type, min, max, labels)
        return await client.execute(
            "var ex=studio.project.lookup('parameter:/'+p.name);"
            "if(ex)throw new Error('global parameter parameter:/'+p.name+"
            "' already exists (guid '+G(ex)+')');"
            + _JS_PARAM_DEFINITION
            + "var prm=studio.project.workspace.addGameParameter(def);"
            "if(!prm)throw new Error('workspace.addGameParameter returned nothing');"
            # workspace.addGameParameter() alone yields a *local*-scoped preset
            # (GameParameter.isGlobal === false) — confirmed live on 2.03.15.
            # The scope flag is a plain property on the GameParameter.
            "var gp=prm.parameter?prm.parameter:prm;gp.isGlobal=true;"
            "if(gp.isGlobal!==true)throw new Error('could not make the parameter global');"
            "return {guid:G(prm),name:p.name,path:'parameter:/'+p.name,type:p.param_type};",
            name=name,
            param_type=param_type,
            min=min,
            max=max,
            labels=labels,
        )

    @mcp.tool()
    async def parameter_set_cursor(
        event_target: str, parameter: str, value: float
    ) -> dict:
        """Move a parameter's value while auditioning — like dragging its
        knob in Studio's transport bar. Use with event_play to actually hear
        layering/transitions react (e.g. sweep Intensity 0 -> 1).

        Args:
            event_target: event:/ path or {guid} being auditioned.
            parameter: Parameter name on that event, or "parameter:/Name".
            value: New value (within the parameter's range).
        """
        return await client.execute(
            JS_PARAM
            + "var e=L(p.event_target);var prm=__param(e,p.parameter);"
            "e.setCursorPosition(prm,p.value);"
            "var now=null;try{now=e.getCursorPosition(prm);}catch(__e){}"
            "return {parameter:p.parameter,requested:p.value,cursor:now};",
            event_target=event_target,
            parameter=parameter,
            value=value,
        )

    @mcp.tool()
    async def parameter_add_condition(
        target: str,
        parameter: str,
        min: float | str,
        max: float | None = None,
        event_target: str | None = None,
    ) -> dict:
        """Add a parameter trigger condition to an instrument, loop region,
        transition marker or transition region — it only triggers/applies
        while the parameter is inside [min, max]. E.g. footstep instruments
        per "Surface" label, or a transition that fires only at high
        Intensity.

        Args:
            target: Instrument / LoopRegion / TransitionMarker /
                    TransitionRegion {guid}.
            parameter: Parameter name (needs event_target) or "parameter:/Name".
            min: Range start, or the label string for a labeled parameter.
            max: Range end (omit for a single value / labeled parameter).
            event_target: Event owning a bare-named parameter.
        """
        if isinstance(min, (int, float)) and max is not None and max < min:
            raise FmodMCPError(ErrorCode.VALUE_OUT_OF_RANGE, "max must be >= min")
        return await client.execute(
            JS_PARAM
            + "var t=L(p.target);"
            "if(typeof t.addParameterCondition!=='function')throw new Error("
            "'target (entity '+t.entity+') is not triggerable - it has no "
            "addParameterCondition()');"
            "var e=p.event_target?L(p.event_target):null;"
            "var prm=__param(e,p.parameter);"
            # Always pass three arguments: the documented two-argument form
            # (max omitted) throws "addParameterCondition() expects arguments:
            # project, triggerable" on 2.03.15 — confirmed live, for labels
            # and numbers alike. A single value / label is the range [min, min].
            # A label string is accepted by Studio but stored as index 0
            # whatever the label (confirmed live), so labels are resolved to
            # their index via the parameter's enumerationLabels first.
            "var lo=p.min,hi=(p.max===null)?p.min:p.max;"
            "if(typeof lo==='string'){"
            "var labs=null;try{labs=prm.enumerationLabels;}catch(__e){}"
            "var idx=-1;if(labs){for(var li=0;li<labs.length;li++){if(String(labs[li])===lo){idx=li;break;}}}"
            "if(idx<0)throw new Error('label '+lo+' not found on parameter '+p.parameter+"
            "' (labels: '+(labs?Array.prototype.join.call(labs,', '):'none')+')');"
            "lo=idx;hi=idx;}"
            "var c=t.addParameterCondition(prm,lo,hi);"
            "if(!c)throw new Error('addParameterCondition returned nothing');"
            "return {guid:G(c),target:G(t),parameter:p.parameter,"
            "minimum:c.minimum,maximum:c.maximum,isInverted:c.isInverted};",
            target=target,
            parameter=parameter,
            min=min,
            max=max,
            event_target=event_target,
        )

    @mcp.tool()
    async def parameter_list(event_target: str) -> dict:
        """List an event's game parameters (name + guid). A parameter's name
        lives behind its presetOwner relationship, not a direct property —
        don't read `.name` on the result of getParameterPresets() directly.

        Args:
            event_target: event:/ path or {guid}.
        """
        return await client.execute(
            "var e=L(p.event_target);"
            "var ps=(e.getParameterPresets?e.getParameterPresets():[])||[];"
            "var out=[];"
            "for(var i=0;i<ps.length;i++){"
            "var rel=ps[i].relationships&&ps[i].relationships.presetOwner;"
            "var dest=rel?rel.destinations:null;"
            "out.push({guid:G(ps[i]),name:(dest&&dest[0])?N(dest[0]):null});}"
            "return out;",
            event_target=event_target,
        )

    @mcp.tool()
    async def parameter_set_initial(
        event_target: str, parameter_name: str, value: float
    ) -> dict:
        """Set a game parameter's initial value on an event.

        Args:
            event_target: event:/ path or {guid}.
            parameter_name: Name of the parameter (from parameter_list).
            value: Initial value.
        """
        return await client.execute(
            "var e=L(p.event_target);"
            "var ps=(e.getParameterPresets?e.getParameterPresets():[])||[];"
            "function pname(item){var rel=item.relationships&&item.relationships.presetOwner;"
            "var dest=rel?rel.destinations:null;return (dest&&dest[0])?N(dest[0]):null;}"
            "var found=null;"
            "for(var i=0;i<ps.length;i++){if(pname(ps[i])===p.parameter_name){found=ps[i];break;}}"
            "if(!found)throw new Error('Parameter not found on event: '+p.parameter_name);"
            "found.initialValue=p.value;"
            "return {parameter:p.parameter_name,initialValue:p.value};",
            event_target=event_target,
            parameter_name=parameter_name,
            value=value,
        )

    @mcp.tool()
    async def parameter_set_labels(
        event_target: str, parameter_name: str, labels: list[str]
    ) -> dict:
        """Set enumeration labels on a UserEnumeration parameter.

        Args:
            event_target: event:/ path or {guid}.
            parameter_name: The parameter's name.
            labels: Human-readable labels, in order (e.g. ["Off","Quiet","Loud"]).
        """
        if not labels or not all(isinstance(x, str) and x for x in labels):
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER,
                "labels must be a non-empty list of strings",
            )
        return await client.execute(
            "var e=L(p.event_target);"
            "var ps=(e.getParameterPresets?e.getParameterPresets():[])||[];"
            "function pname(item){var rel=item.relationships&&item.relationships.presetOwner;"
            "var dest=rel?rel.destinations:null;return (dest&&dest[0])?N(dest[0]):null;}"
            "var found=null;"
            "for(var i=0;i<ps.length;i++){if(pname(ps[i])===p.parameter_name){found=ps[i];break;}}"
            "if(!found)throw new Error('Parameter not found on event: '+p.parameter_name);"
            "found.enumerationLabels=p.labels;"
            "return {parameter:p.parameter_name,labels:p.labels};",
            event_target=event_target,
            parameter_name=parameter_name,
            labels=labels,
        )
