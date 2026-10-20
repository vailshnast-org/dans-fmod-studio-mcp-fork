from mcp.server.fastmcp import FastMCP

from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def event_play(target: str) -> dict:
        """Play an event instance — the equivalent of pressing play in
        FMOD Studio's transport controls. This is how you actually hear a
        result instead of guessing from the event tree.

        Args:
            target: event:// path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);o.play();return {guid:G(o)};", target=target
        )

    @mcp.tool()
    async def event_stop(target: str, immediate: bool = True) -> dict:
        """Stop a playing event instance.

        Args:
            target: event:// path or {guid}.
            immediate: True (default) stops instantly, skipping the
                       stopping state. False lets release/fade-outs and
                       one-shot tails play out before stopping.
        """
        body = (
            "var o=L(p.target);"
            "if(p.immediate){o.stopImmediate();}else{o.stopNonImmediate();}"
            "return {guid:G(o)};"
        )
        return await client.execute(body, target=target, immediate=immediate)

    @mcp.tool()
    async def event_toggle_pause(target: str) -> dict:
        """Toggle the pause state of a playing event instance.

        Args:
            target: event:// path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);o.togglePause();return {guid:G(o)};", target=target
        )

    @mcp.tool()
    async def event_key_off(target: str) -> dict:
        """Send the keyoff command to a playing event instance — triggers
        the release behavior for any sustain point ahead of the playhead.

        Args:
            target: event:// path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);o.keyOff();return {guid:G(o)};", target=target
        )

    @mcp.tool()
    async def event_return_to_start(target: str) -> dict:
        """Return a playing/paused/stopping event instance's timeline
        playback position to the cursor (or to the timeline start, if the
        instance is stopped).

        Args:
            target: event:// path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);o.returnToStart();return {guid:G(o)};", target=target
        )

    @mcp.tool()
    async def event_set_3d_attributes(
        target: str,
        radial_distance: float,
        azimuth: float = 0.0,
        height: float = 0.0,
        rotation: float = 0.0,
    ) -> dict:
        """Position an auditioned event relative to the listener (the 3D
        preview in Studio's transport) to hear distance attenuation and
        panning — e.g. play, then step radial_distance 1 -> 50.

        Args:
            target: event:// path or {guid} (a 3D event).
            radial_distance: Distance from the listener (>= 0).
            azimuth: Angle around the listener, degrees.
            height: Vertical position.
            rotation: Horizontal rotation of the event, degrees.
        """
        if radial_distance < 0:
            raise FmodMCPError(
                ErrorCode.VALUE_OUT_OF_RANGE, "radial_distance must be >= 0"
            )
        return await client.execute(
            "var o=L(p.target);"
            "o.set3DAttributes({radialDistance:p.radial_distance,azimuth:p.azimuth,"
            "height:p.height,rotation:p.rotation});"
            "var now=null;try{now=o.get3DAttributes();}catch(__e){}"
            "return {guid:G(o),attributes:now};",
            target=target,
            radial_distance=radial_distance,
            azimuth=azimuth,
            height=height,
            rotation=rotation,
        )

    @mcp.tool()
    async def event_playback_status(target: str) -> dict:
        """Check whether an event instance is playing/paused/stopping, and
        its current timeline playhead position — use this to validate a
        play/stop/pause call actually took effect.

        Args:
            target: event:// path or {guid}.
        """
        return await client.execute(
            "var o=L(p.target);var pos=null;"
            "try{pos=o.getPlayheadPosition(o.timeline);}catch(__e){}"
            "return {guid:G(o),isPlaying:!!o.isPlaying(),isPaused:!!o.isPaused(),"
            "isStopping:!!o.isStopping(),playheadPosition:pos};",
            target=target,
        )
