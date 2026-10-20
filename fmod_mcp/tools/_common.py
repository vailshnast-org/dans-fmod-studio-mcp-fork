"""Shared JS-building helpers for tool modules (no tools registered here).

Kept out of the tools' individual files so every *list-style* command emits
the same capped, mapped result shape:
    [{guid, name, path}, ...]
instead of leaking raw ManagedObjects into JSON.stringify.
"""

import re

from fmod_mcp_shared.constants import (
    MAX_OBJECTS_READ,
    MAX_PROPERTIES_PER_CALL,
    MAX_SOUNDS_READ,
)
from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError


def js_list(expr: str, cap: int = MAX_OBJECTS_READ) -> str:
    """Build a command body that maps an object-array expression to info dicts.

    `expr` must evaluate to an array of ManagedObjects (or undefined). Safe
    against a null from a broken call: the `|| []` guards it into an empty
    list, and the cap keeps a giant project from flooding the model's context.
    """
    cap = int(cap)
    return (
        f"var __a=({expr})||[];var __o=[];"
        f"for(var __i=0;__i<__a.length&&__i<{cap};__i++){{"
        f"__o.push({{guid:G(__a[__i]),name:N(__a[__i]),path:P(__a[__i])}});}}"
        f"return __o;"
    )


def js_info(expr: str) -> str:
    """Build a command body that returns the canonical info dict for one object."""
    return f"var __o=({expr});return {{guid:G(__o),name:N(__o),path:P(__o)}};"


# Max instruments reported per track/event listing — stricter than the generic
# object cap because a busy event can carry many sounds, and instrument
# payloads are heavier than bare object rows.
MAX_TRACK_LIST_SOUNDS = MAX_SOUNDS_READ

# Property/relationship names travel inside `p` like every other param, but
# are also used as a computed key (`o[k]`) — restrict them to plain
# identifiers so a key can never be `__proto__`-style or path-shaped.
IDENTIFIER_RE = r"^[A-Za-z][A-Za-z0-9_]*$"

# Python-side mirror of the JS identifier check, applied before a command is
# ever sent — a typo fails fast with a typed error.
_IDENT_JS = "/^[A-Za-z][A-Za-z0-9_]*$/"

# __props(o): every plain (non-object, non-function) member of a live object
# with its current value. Same enumeration utility_dump has always used —
# FMOD's own dump() only logs to Studio's console and returns nothing.
JS_PROPS = (
    "function __props(o){var out={};"
    "for(var k in o){if(k.charAt(0)==='_')continue;"
    "var v;try{v=o[k];}catch(__e){continue;}"
    "var t=typeof v;if(t==='function'||t==='object'||t==='undefined')continue;"
    "out[k]=v;}return out;}"
)

# __setProps(o, props): validated, read-back property assignment.
#
# - The name must exist in the object's ManagedPropertyMap
#   (`o.properties[name]`, documented in Project.ManagedObject) — a wrong
#   name raises instead of silently creating a JS expando field that FMOD
#   ignores, which is the exact "success but nothing happened" failure
#   family this codebase has been bitten by repeatedly.
# - The value's JS type must match the current value's type (number vs
#   bool vs string), so `looping: "true"` can't land as a string.
# - Every value is read back after assignment; Studio clamps out-of-range
#   numbers, so the caller gets the value that actually stuck plus a
#   `clamped` list naming any property whose read-back differs.
JS_SET_PROPS = (
    "function __setProps(o,props){var applied={};var clamped=[];"
    "for(var k in props){"
    "if(!" + _IDENT_JS + ".test(k))throw new Error('invalid property name: '+k);"
    "var mp=null;try{mp=o.properties?o.properties[k]:null;}catch(__e){}"
    "if(!mp)throw new Error('object (entity '+o.entity+') has no property \\''+k+"
    "'\\' - call utility_dump on it to list the real property names');"
    "var cur=o[k];var v=props[k];"
    "if(cur!==null&&cur!==undefined&&typeof cur!==typeof v)throw new Error("
    "'property \\''+k+'\\' holds a '+typeof cur+', got a '+typeof v);"
    "o[k]=v;var got=o[k];applied[k]=got;"
    "if(got!==v)clamped.push(k);}"
    "return {applied:applied,clamped:clamped};}"
)

# __param(e, ref): resolve a parameter reference to the GameParameter that
# addSound / setCursorPosition / addParameterCondition / addAutomationCurve
# expect.
#   - 'parameter:/Name' or a {guid}: project lookup. A ParameterPreset
#     (what a parameter:/ path resolves to) exposes its GameParameter via
#     `.parameter` — documented in Project.Model.Parameter.
#   - A bare name: searched among the event's own parameters. A
#     GameParameter has no `.name`; its name lives on the ParameterPreset
#     behind `relationships.presetOwner` (see parameter_tools).
JS_PARAM = (
    "function __param(e,ref){"
    "if(!ref)throw new Error('parameter reference is required');"
    "if(ref.indexOf('parameter:/')===0||ref.charAt(0)==='{'){"
    "var o=studio.project.lookup(ref);"
    "if(!o)throw new Error('parameter lookup failed: '+ref);"
    "return o.parameter?o.parameter:o;}"
    "if(!e)throw new Error('a bare parameter name needs an event to search: '+ref);"
    "var ps=(e.getParameterPresets?e.getParameterPresets():[])||[];"
    "for(var i=0;i<ps.length;i++){"
    "var rel=ps[i].relationships&&ps[i].relationships.presetOwner;"
    "var d=rel?rel.destinations:null;"
    "if(d&&d[0]&&N(d[0])===ref)return ps[i];}"
    "throw new Error('parameter not found on event: '+ref+"
    "' (use parameter_list, or pass a parameter:/ path for a global parameter)');}"
    # __sheet(e, ref): the event's ParameterProxy for a parameter — the
    # parameter *sheet* GroupTrack.addSound() places instruments on. Passing
    # the GameParameter instead makes Studio abort the whole script with
    # "Relationship 'parameter' expects a destination of entity type
    # 'Parameter'" (confirmed live, 2.03.15): a GameParameter is not a
    # Parameter, its per-event ParameterProxy is. A global parameter the
    # event doesn't use yet gets a proxy via Event.addGameParameter(preset).
    "function __sheet(e,ref){var gp=__param(e,ref);"
    "var pr=e.relationships.parameters;var px=(pr&&pr.destinations)?pr.destinations:[];"
    "for(var i=0;i<px.length;i++){var pre=px[i].preset;if(pre&&G(pre)===G(gp))return px[i];}"
    "var po=gp.presetOwner?gp.presetOwner:gp;"
    "var np=e.addGameParameter(po);"
    "if(!np||!np.isOfType||!np.isOfType('Parameter'))"
    "throw new Error('could not get a parameter sheet for '+ref+' on this event');"
    "return np;}"
)

# __sounds(ctx): every instrument under a search context (event or track),
# using the documented includeDerivedTypes option so Single/Multi/
# Programmer/Scatterer/Event/... sounds all come back from one query.
JS_SOUNDS = (
    "function __sounds(ctx,cap){"
    "var arr=studio.project.model.Sound.findInstances("
    "{searchContext:ctx,includeDerivedTypes:true})||[];"
    "var out=[];for(var i=0;i<arr.length&&out.length<cap;i++){var s=arr[i];"
    "var af=null;try{af=s.audioFile;}catch(__e){}"
    "var ow=null;try{ow=s.owner;}catch(__e){}"
    "out.push({guid:G(s),name:N(s),entity:s.entity,start:s.start,length:s.length,"
    "audioFileName:af?N(af):null,ownerGuid:ow?G(ow):null});}"
    "return out;}"
)


# __folderChain(kind, path): find-or-create a slash-separated folder chain
# under the master event/bank/asset folder and return the deepest folder. Walks
# `relationships.items.destinations` — `folder.children` doesn't exist (see
# CHANGELOG 0.3.0), so an older walk always "missed" and duplicated folders.
JS_FOLDER_CHAIN = (
    "function __folderChain(kind,path){"
    "var w=studio.project.workspace;"
    "var root=kind==='AssetFolder'?w.masterAssetFolder:"
    "(kind==='BankFolder'?w.masterBankFolder:w.masterEventFolder);"
    "var segs=(path||'').split('/');"
    "var cur=root;"
    "function findChild(f,n){"
    "var rel=f.relationships&&f.relationships.items;"
    "var kids=(rel&&rel.destinations)?rel.destinations:[];"
    "for(var i=0;i<kids.length;i++){"
    "if(kids[i].name===n)return kids[i];}return null;}"
    "for(var i=0;i<segs.length;i++){"
    "var s=segs[i];if(!s)continue;"
    "var child=findChild(cur,s);"
    "if(!child){"
    "child=studio.project.create(kind);"
    "if(!child)throw new Error("
    "'studio.project.create failed for kind: '+kind+"
    "' - this folder kind may not be creatable via scripting in this FMOD version.');"
    "child.name=s;"
    "try{child.folder=cur;}catch(__e){"
    "try{child.parent=cur;}catch(__e2){}}}"
    "cur=child;}"
    "return cur;}"
)

def check_identifier(value: str, what: str) -> None:
    """Reject a property/relationship/entity name that isn't a plain identifier."""
    if not isinstance(value, str) or not re.match(IDENTIFIER_RE, value):
        raise FmodMCPError(
            ErrorCode.INVALID_PARAMETER,
            f"{what} must be a plain identifier (letters/digits/_), got {value!r}",
        )


def check_property_values(props) -> dict:
    """Validate a {name: value} map for __setProps before it's sent."""
    if not isinstance(props, dict) or not props:
        raise FmodMCPError(
            ErrorCode.INVALID_PARAMETER, "properties must be a non-empty object"
        )
    if len(props) > MAX_PROPERTIES_PER_CALL:
        raise FmodMCPError(
            ErrorCode.VALUE_OUT_OF_RANGE,
            f"too many properties in one call (max {MAX_PROPERTIES_PER_CALL})",
        )
    for k, v in props.items():
        check_identifier(k, "property name")
        # bool is an int subclass in Python — both are fine, JSON keeps them apart.
        if not isinstance(v, (bool, int, float, str)):
            raise FmodMCPError(
                ErrorCode.INVALID_PARAMETER,
                f"property {k!r} must be a number, bool or string, got {type(v).__name__}",
            )
    return props
