from mcp.server.fastmcp import FastMCP

from fmod_mcp.tools._common import (
    JS_PROPS,
    JS_SET_PROPS,
    check_identifier,
    check_property_values,
)
from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError

# AutomatableObject.addModulator(modulatorType, propertyName) — the four
# types the 2.03 scripting reference lists as accepted by addModulator.
# (model.LFOModulator exists as an entity but isn't documented as creatable
# through addModulator, so it's left out rather than guessed at.)
ALLOWED_MODULATOR_TYPES = (
    "RandomizerModulator",
    "ADSRModulator",
    "SidechainModulator",
    "AutopitchModulator",
)

# Cap per listing — an event-wide search can turn up one modulator per
# instrument property.
_MAX_MODULATORS_LISTED = 200


def _check_modulator_type(modulator_type: str) -> None:
    if modulator_type not in ALLOWED_MODULATOR_TYPES:
        raise FmodMCPError(
            ErrorCode.INVALID_TYPE,
            f"invalid modulator_type {modulator_type!r}; use one of "
            f"{', '.join(ALLOWED_MODULATOR_TYPES)}",
        )


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def modulator_add(
        target: str,
        modulator_type: str,
        property: str,
        settings: dict | None = None,
    ) -> dict:
        """Add a modulator to one property of an instrument, effect, event
        or bus — e.g. RandomizerModulator on a footstep's `pitch`/`volume`
        so repeats don't sound identical, ADSRModulator for fades on
        start/stop, AutopitchModulator for engine RPM.

        Optional `settings` are applied right after creation through the same
        validated setter as utility_set_properties (names must exist on the
        modulator — read them with the returned `properties`).

        Args:
            target: Instrument/effect/event/mixer group path or {guid}.
            modulator_type: RandomizerModulator | ADSRModulator |
                            SidechainModulator | AutopitchModulator.
            property: Property to modulate, e.g. "volume", "pitch".
            settings: Optional {"name": value} for the new modulator.
        """
        _check_modulator_type(modulator_type)
        check_identifier(property, "property")
        props = check_property_values(settings) if settings else None
        return await client.execute(
            JS_PROPS
            + JS_SET_PROPS
            + "var o=L(p.target);"
            "if(typeof o.addModulator!=='function')throw new Error("
            "'target (entity '+o.entity+') cannot be modulated - it has no addModulator()');"
            "var m=o.addModulator(p.modulator_type,p.property);"
            "if(!m)throw new Error('addModulator returned nothing for '+p.modulator_type+"
            "' on property '+p.property);"
            "var applied=null;if(p.settings){applied=__setProps(m,p.settings);}"
            "return {guid:G(m),entity:m.entity,targetGuid:G(o),property:p.property,"
            "applied:applied,properties:__props(m)};",
            target=target,
            modulator_type=modulator_type,
            property=property,
            settings=props,
        )

    @mcp.tool()
    async def modulator_list(target: str) -> dict:
        """List the modulators under an object (an instrument, or a whole
        event), each with its type and current settings.

        Args:
            target: Instrument/effect/event path or {guid}.
        """
        return await client.execute(
            JS_PROPS
            + "var o=L(p.target);"
            "var arr=studio.project.model.Modulator.findInstances("
            "{searchContext:o,includeDerivedTypes:true})||[];"
            "var out=[];"
            f"for(var i=0;i<arr.length&&i<{_MAX_MODULATORS_LISTED};i++){{"
            "out.push({guid:G(arr[i]),entity:arr[i].entity,properties:__props(arr[i])});}"
            "return {total:arr.length,modulators:out};",
            target=target,
        )
