"""Optional live-FMOD regression tests for the G/N/P JS helpers.

Skipped automatically unless FMOD Studio's Script Server is actually
reachable with a project open — there is no way to unit-test the *real*
property names FMOD's scripting API exposes (e.g. ManagedObject.id vs a
nonexistent .guid) without a live instance, and a previous version of these
helpers shipped with exactly that mismatch — G() read a .guid property that
doesn't exist, P() read a .path property that doesn't exist instead of
calling the real getPath() method — undetected, because every other test in
this suite uses a stub client that never evaluates the injected JS against a
real FMOD object.

Run these manually (`pytest tests/test_live_fmod.py -v`) with FMOD Studio
open and the Script Server enabled whenever touching
fmod_mcp_shared/protocol.py's _JS_HELPERS.
"""

import asyncio
import os
import socket

import pytest

from fmod_mcp.fmod_client import FmodStudioClient
from fmod_mcp_shared.constants import Connection


def _fmod_reachable() -> bool:
    try:
        with socket.create_connection((Connection.host(), Connection.port()), timeout=1):
            return True
    except OSError:
        return False


pytestmark = pytest.mark.skipif(
    not _fmod_reachable(),
    reason="FMOD Studio's Script Server is not reachable — these tests need a live instance",
)


@pytest.fixture(autouse=True)
def _never_save_the_open_project(monkeypatch):
    """Keep destructive tools' auto-backup from touching the open project.

    ensure_backup() SAVES the project and copies its folder before the
    first destructive call in each process. During a test that writes the
    test's own half-built objects into the real project on disk (this
    happened: a test event and a plug-in data file got saved into a real
    game project). Marking the project as already backed up makes it a
    no-op; tests clean up their objects in memory, so nothing reaches disk.
    """
    from fmod_mcp import safety

    async def path():
        r = await FmodStudioClient().execute("return {f:studio.project.filePath};")
        return r["result"]["f"]

    monkeypatch.setattr(safety, "_backed_up_this_session", {asyncio.run(path())})


def test_g_n_p_helpers_against_a_real_project_object():
    """G()/N()/P() must return real, non-null values for an object that
    actually exists, and the returned guid must round-trip through L().
    """

    async def run():
        client = FmodStudioClient()
        r = await client.execute(
            "var arr=studio.project.model.Event.findInstances()||[];"
            "if(arr.length===0)throw new Error('project has no events to test against');"
            "var e=arr[0];"
            "return {guid:G(e),name:N(e),path:P(e)};"
        )
        result = r["result"]
        assert result["guid"] is not None
        assert result["guid"].startswith("{") and result["guid"].endswith("}")
        assert result["name"]
        assert result["path"] is not None
        assert result["path"].startswith("event:/")

        r2 = await client.execute(
            "var e=L(p.target);return {guid:G(e)};", target=result["guid"]
        )
        assert r2["result"]["guid"] == result["guid"]

    asyncio.run(run())


def test_automation_add_curve_multi_point_does_not_syntax_error():
    """Regression test: automation_add_curve's multi-statement JS body used
    to join semicolon-terminated statements with ',' — producing
    `a;,b;,c;`, a bare comma at statement position, a JS syntax error. This
    only manifests for 2+ points (a single point has nothing to join
    against), so it went undetected through every stub-client test and
    every hand-written manual test in this project's history — the first
    time the real tool function was ever called end-to-end with 3 points,
    it failed with an opaque "Invalid JSON response from FMOD Studio",
    not a normal thrown error. Creates and cleans up its own throwaway
    project objects so it doesn't touch whatever project is actually open.
    """

    class _StubMCP:
        def __init__(self):
            self.tools = {}

        def tool(self):
            def deco(fn):
                self.tools[fn.__name__] = fn
                return fn

            return deco

    async def run():
        from fmod_mcp.tools import automation_tools

        client = FmodStudioClient()
        group = await client.execute(
            "var g=studio.project.create('MixerGroup');"
            "g.name='__test_automation_group';return {guid:G(g)};"
        )
        event = await client.execute(
            "var e=studio.project.create('Event');"
            "e.name='__test_automation_event';return {guid:G(e)};"
        )
        group_guid = group["result"]["guid"]
        event_guid = event["result"]["guid"]
        try:
            await client.execute(
                "var e=L(p.target);var pt=studio.project.parameterType.User;"
                "e.addGameParameter({name:'__TestParam',type:pt,min:0,max:1});"
                "return true;",
                target=event_guid,
            )

            mcp = _StubMCP()
            automation_tools.register(mcp)
            r = await mcp.tools["automation_add_curve"](
                target=group_guid,
                property="volume",
                driver="parameter:/__TestParam",
                points=[[0.0, 0.0], [0.5, -6.0], [1.0, -12.0]],
                driver_type="parameter",
            )
            assert r["success"] is True
            assert r["result"]["points"] == 3

            listing = await mcp.tools["automation_list"](
                target=group_guid, property="volume"
            )
            curves = listing["result"]["curves"]
            assert len(curves) == 1, (
                f"expected exactly 1 curve, got {len(curves)} — "
                "multi-point call fragmented instead of building one curve"
            )
            assert curves[0]["points"] == [[0.0, 0.0], [0.5, -6.0], [1.0, -12.0]]
        finally:
            await client.execute(
                "var o=L(p.target);studio.project.deleteObject(o);return true;",
                target=group_guid,
            )
            await client.execute(
                "var o=L(p.target);studio.project.deleteObject(o);return true;",
                target=event_guid,
            )
            # Deleting the event leaves its parameter's ParameterPreset behind.
            await _delete_presets(client, "__TestParam")

    asyncio.run(run())


def test_marker_add_transition_timeline_produces_valid_objects():
    """marker_add_transition_timeline must produce a TransitionTimeline plus
    source/destination sounds that are actually valid — a
    TransitionSourceSound/TransitionDestinationSound requires both its
    audioTrack and parameter relationships set or FMOD reports isValid:
    false (confirmed live: creating one without them does exactly that).
    Creates and cleans up its own throwaway event/track/markers.
    """

    class _StubMCP:
        def __init__(self):
            self.tools = {}

        def tool(self):
            def deco(fn):
                self.tools[fn.__name__] = fn
                return fn

            return deco

    async def run():
        from fmod_mcp.tools import marker_tools

        client = FmodStudioClient()
        event = await client.execute(
            "var e=studio.project.create('Event');"
            "e.name='__test_transition_timeline_event';return {guid:G(e)};"
        )
        event_guid = event["result"]["guid"]
        try:
            tr = await client.execute(
                "var e=L(p.target);var t=e.addGroupTrack();return {trackGuid:G(t)};",
                target=event_guid,
            )
            track_guid = tr["result"]["trackGuid"]

            mcp = _StubMCP()
            marker_tools.register(mcp)

            mt = await mcp.tools["event_add_marker_track"](target=event_guid)
            marker_track_guid = mt["result"]["guid"]
            dest = await mcp.tools["marker_add_named"](
                track_target=marker_track_guid, name="start", position=0.0
            )
            dest_guid = dest["result"]["guid"]
            tm = await mcp.tools["marker_add_transition"](
                track_target=marker_track_guid,
                position=8.0,
                destination_target=dest_guid,
            )
            tm_guid = tm["result"]["guid"]

            r = await mcp.tools["marker_add_transition_timeline"](
                transition_target=tm_guid,
                audio_track_target=track_guid,
                crossfade_length=1.5,
            )
            assert r["success"] is True
            result = r["result"]
            assert result["transitionTimelineGuid"]
            assert result["sourceGuid"]
            assert result["destinationGuid"]

            # Independently confirm both are actually valid, not just that
            # the call didn't throw.
            check = await client.execute(
                "var s=L(p.src);var d=L(p.dst);"
                "return {sourceValid:s.isValid,destinationValid:d.isValid};",
                src=result["sourceGuid"],
                dst=result["destinationGuid"],
            )
            assert check["result"]["sourceValid"] is True
            assert check["result"]["destinationValid"] is True
        finally:
            await client.execute(
                "var o=L(p.target);studio.project.deleteObject(o);return true;",
                target=event_guid,
            )

    asyncio.run(run())


def test_workspace_roots_are_not_null():
    """Regression test for the reported 'workspace roots are all null' bug —
    same root cause as the guid mismatch above (workspace_info runs G() on
    masterEventFolder/masterAssetFolder/masterBus).
    """

    async def run():
        client = FmodStudioClient()
        r = await client.execute(
            "var w=studio.project.workspace;"
            "return {masterEventFolder:G(w.masterEventFolder),"
            "masterAssetFolder:G(w.masterAssetFolder),"
            "masterBus:G(w.mixer.masterBus)};"
        )
        result = r["result"]
        assert result["masterEventFolder"] is not None
        assert result["masterAssetFolder"] is not None
        assert result["masterBus"] is not None

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Regression tests for the tools added on feature/crucial-features. They were
# written from the 2.03 scripting reference without a live Studio to hand —
# these are what turns "matches the docs" into "works in Studio". Each one
# creates throwaway objects and deletes them again.
# ---------------------------------------------------------------------------


class _LiveMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def deco(fn):
            self.tools[fn.__name__] = fn
            return fn

        return deco


def _live_tools(*module_names):
    import importlib

    mcp = _LiveMCP()
    for name in module_names:
        importlib.import_module(f"fmod_mcp.tools.{name}").register(mcp)
    return mcp.tools


async def _delete(client, guid):
    await client.execute(
        "var o=studio.project.lookup(p.target);"
        "if(o)studio.project.deleteObject(o);return true;",
        target=guid,
    )


async def _delete_presets(client, *names):
    """Delete parameter presets by name.

    Every parameter created through scripting, event-local or global, is a
    ParameterPreset in the project's parameter browser (confirmed live on
    2.03.15). Deleting its event or its GameParameter leaves the preset
    behind, so tests must remove it explicitly.
    """
    await client.execute(
        "for(var i=0;i<p.names.length;i++){"
        "var o=studio.project.lookup('parameter:/'+p.names[i]);"
        "if(o)studio.project.deleteObject(o);}return true;",
        names=list(names),
    )


def _write_test_wav(path, seconds=0.5, rate=22050):
    import math
    import struct
    import wave

    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        n = int(seconds * rate)
        w.writeframes(
            struct.pack(f"<{n}h", *(int(8000 * math.sin(i * 0.06)) for i in range(n)))
        )


def test_utility_set_properties_roundtrip_and_rejects_unknown_names():
    from fmod_mcp_shared.error_codes import FmodMCPError

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("utility_tools")
        g = await client.execute(
            "var g=studio.project.create('MixerGroup');g.name='__test_props_group';"
            "return {guid:G(g)};"
        )
        guid = g["result"]["guid"]
        try:
            r = await tools["utility_set_properties"](
                target=guid, properties={"volume": -7.5}
            )
            assert r["result"]["applied"]["volume"] == pytest.approx(-7.5)
            props = await tools["utility_get_properties"](target=guid)
            assert props["result"]["properties"]["volume"] == pytest.approx(-7.5)
            with pytest.raises(FmodMCPError, match="has no property"):
                await tools["utility_set_properties"](
                    target=guid, properties={"definitelyNotAProperty": 1}
                )
            with pytest.raises(FmodMCPError, match="holds a"):
                await tools["utility_set_properties"](
                    target=guid, properties={"volume": "loud"}
                )
        finally:
            await _delete(client, guid)

    asyncio.run(run())


def test_event_create_from_audio_builds_a_playable_multi_event(tmp_path):
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("sound_tools", "event_tools", "utility_tools")
        files = []
        for i in range(2):
            f = tmp_path / f"__test_variation_{i}.wav"
            _write_test_wav(f)
            files.append(str(f))
        r = await tools["event_create_from_audio"](
            name="__test_from_audio", file_paths=files, spatializer=True
        )
        res = r["result"]
        try:
            assert res["instrumentType"] == "MultiSound"
            assert res["length"] == pytest.approx(0.5, abs=0.01)
            listing = await tools["event_list_sounds"](event_target=res["guid"])
            sounds = listing["result"]["sounds"]
            singles = [s for s in sounds if s["entity"] == "SingleSound"]
            assert len(singles) == 2
            assert all(s["audioFileName"] for s in singles)
            assert all(s["ownerGuid"] == res["instrumentGuid"] for s in singles)
            desc = await tools["event_describe"](target=res["guid"])
            assert len(desc["result"]["tracks"]) == 1
            info = await tools["event_info"](target=res["guid"])
            assert info["result"]["is3D"] is True
        finally:
            await _delete(client, res["guid"])
            for a in res["assets"]:
                await _delete(client, a["guid"])

    asyncio.run(run())


def test_global_parameter_condition_and_cursor():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("parameter_tools", "sound_tools", "event_tools")
        gp = await tools["parameter_add_global"](
            name="__TestGlobal", param_type="UserEnumeration", labels=["A", "B"]
        )
        assert gp["result"]["path"] == "parameter:/__TestGlobal"
        ev = await tools["event_create"](name="__test_param_event")
        eguid = ev["result"]["guid"]
        try:
            await tools["parameter_add"](
                event_target=eguid, name="__Local", min=0.0, max=10.0
            )
            track = (await tools["event_add_track"](target=eguid))["result"]
            inst = await tools["sound_add_to_track"](
                event_target=eguid,
                track_target=track["trackGuid"],
                sound_type="SingleSound",
                start=2.0,
                length=3.0,
                parameter="__Local",
            )
            cond = await tools["parameter_add_condition"](
                target=inst["result"]["guid"], parameter="parameter:/__TestGlobal", min="B"
            )
            assert cond["result"]["guid"]
            # Label "B" is index 1 of ["A", "B"].
            assert cond["result"]["minimum"] == 1
            assert cond["result"]["maximum"] == 1
            gscope = await client.execute(
                "var o=studio.project.lookup('parameter:/__TestGlobal');"
                "return {isGlobal:o.parameter.isGlobal};"
            )
            assert gscope["result"]["isGlobal"] is True
            cont = await tools["parameter_add_condition"](
                target=inst["result"]["guid"],
                parameter="__Local",
                min=2.0,
                max=5.0,
                event_target=eguid,
            )
            assert cont["result"]["minimum"] == pytest.approx(2.0)
            assert cont["result"]["maximum"] == pytest.approx(5.0)
            cur = await tools["parameter_set_cursor"](
                event_target=eguid, parameter="__Local", value=4.0
            )
            assert cur["result"]["cursor"] == pytest.approx(4.0)
        finally:
            await _delete(client, eguid)
            await _delete_presets(client, "__Local", "__TestGlobal")

    asyncio.run(run())


def test_modulator_add_on_an_instrument():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("modulator_tools", "sound_tools", "event_tools")
        ev = await tools["event_create"](name="__test_modulator_event")
        eguid = ev["result"]["guid"]
        try:
            track = (await tools["event_add_track"](target=eguid))["result"]
            inst = await tools["sound_add_to_track"](
                event_target=eguid,
                track_target=track["trackGuid"],
                sound_type="SingleSound",
                start=0.0,
                length=1.0,
            )
            m = await tools["modulator_add"](
                target=inst["result"]["guid"],
                modulator_type="RandomizerModulator",
                property="pitch",
            )
            assert m["result"]["entity"] == "RandomizerModulator"
            listing = await tools["modulator_list"](target=inst["result"]["guid"])
            assert listing["result"]["total"] == 1
        finally:
            await _delete(client, eguid)

    asyncio.run(run())


def test_mixer_return_and_send_are_linked():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("mixer_tools")
        ret = (await tools["mixer_return_create"](name="__test_return"))["result"]
        grp = (await tools["mixer_group_create"](name="__test_send_group"))["result"]
        try:
            assert grp["outputGuid"] is not None
            s = await tools["mixer_send_add"](
                source_group_target=grp["guid"], return_target=ret["guid"], level_db=-3.0
            )
            assert s["result"]["returnGuid"] == ret["guid"]
            assert s["result"]["linkedVia"]
        finally:
            await _delete(client, grp["guid"])
            await _delete(client, ret["guid"])

    asyncio.run(run())


def test_utility_validate_reports_structure():
    async def run():
        tools = _live_tools("utility_tools")
        r = (await tools["utility_validate"]())["result"]
        for key in (
            "eventsNotInAnyBank",
            "eventsWithNoInstruments",
            "singleSoundsWithoutAudio",
            "invalidObjects",
        ):
            assert isinstance(r[key], list)
        assert isinstance(r["eventCount"], int)

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Second round: snapshots, VCAs, plug-ins, playlists, assets, automation
# editing, bank folders — plus live coverage for first-round tools that only
# had stub tests. Schemas these tools rely on were read off a live 2.03.15
# project before writing them; these tests keep them honest.
# ---------------------------------------------------------------------------


def _wavs(tmp_path, n, prefix="__test_wav"):
    files = []
    for i in range(n):
        f = tmp_path / f"{prefix}_{i}.wav"
        _write_test_wav(f)
        files.append(str(f))
    return files


def test_snapshot_scope_capture_and_settings():
    from fmod_mcp_shared.error_codes import FmodMCPError

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("snapshot_tools", "mixer_tools")
        g = (await tools["mixer_group_create"](name="__test_snap_group"))["result"]
        s = (await tools["snapshot_create"](name="__test_snap"))["result"]
        try:
            b1 = (await tools["snapshot_bind_group"](snapshot_target=s["guid"], group_target=g["guid"]))["result"]
            b2 = (await tools["snapshot_bind_group"](snapshot_target=s["guid"], group_target=g["guid"]))["result"]
            assert b1["reused"] is False and b2["reused"] is True
            assert b1["snapshotTrackGuid"] == b2["snapshotTrackGuid"]

            p1 = (await tools["snapshot_set_property"](
                snapshot_target=s["guid"], target=g["guid"], property="volume", value=-12.0))["result"]
            p2 = (await tools["snapshot_set_property"](
                snapshot_target=s["guid"], target=g["guid"], property="volume", value=-6.0))["result"]
            assert p1["created"] is True and p2["created"] is False
            assert p2["guid"] == p1["guid"] and p2["value"] == pytest.approx(-6.0)

            listing = (await tools["snapshot_list_properties"](snapshot_target=s["guid"]))["result"]
            assert len(listing["scopedStrips"]) == 1
            assert [(x["property"], x["value"]) for x in listing["properties"]] == [("volume", -6.0)]
            # The snapshot holds the value; the live mixer is untouched.
            info = (await tools["mixer_group_info"](target=g["guid"]))["result"]
            assert info["volume"] == pytest.approx(0.0)

            st = (await tools["snapshot_set_settings"](snapshot_target=s["guid"], intensity=40.0, behavior=1))["result"]
            assert st["intensity"] == pytest.approx(40.0) and st["behavior"] == 1

            with pytest.raises(FmodMCPError, match="has no property"):
                await tools["snapshot_set_property"](
                    snapshot_target=s["guid"], target=g["guid"], property="notARealProperty", value=1.0)

            await tools["snapshot_remove_property"](snapshot_target=s["guid"], target=g["guid"], property="volume")
            listing = (await tools["snapshot_list_properties"](snapshot_target=s["guid"]))["result"]
            assert listing["properties"] == []
        finally:
            await _delete(client, s["guid"])
            await _delete(client, g["guid"])

    asyncio.run(run())


def test_vca_assign_unassign_and_list():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("mixer_tools")
        g = (await tools["mixer_group_create"](name="__test_vca_group"))["result"]
        v = (await tools["vca_create"](name="__test_vca"))["result"]
        try:
            a = (await tools["vca_assign"](vca_target=v["guid"], strip_target=g["guid"]))["result"]
            assert a["stripVcaCount"] == 1
            strips = (await tools["vca_list_strips"](vca_target=v["guid"]))["result"]["strips"]
            assert [x["guid"] for x in strips] == [g["guid"]]
            u = (await tools["vca_unassign"](vca_target=v["guid"], strip_target=g["guid"]))["result"]
            assert u["stripVcaCount"] == 0
            strips = (await tools["vca_list_strips"](vca_target=v["guid"]))["result"]["strips"]
            assert strips == []
        finally:
            await _delete(client, g["guid"])
            await _delete(client, v["guid"])

    asyncio.run(run())


def test_plugin_effect_and_instrument():
    from fmod_mcp_shared.error_codes import FmodMCPError

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("project_tools", "mixer_tools", "sound_tools", "event_tools")
        plugins = (await tools["project_list_plugins"]())["result"]["plugins"]
        effect = next((n for n in plugins if "Spatializer" in n or "Reverb" in n or "Limiter" in n), None)
        # AudioMotors writes a multi-MB demo .agp DataFile into Assets on
        # creation (seen live); prefer an instrument that doesn't.
        instruments = [n for n in plugins if n.startswith("AudioGaming")]
        instrument = next((n for n in instruments if "Rain" in n), instruments[0] if instruments else None)
        if not effect or not instrument:
            pytest.skip(f"need an effect and an instrument plug-in installed, have {plugins}")
        data_files_before = await _data_file_guids(client)
        ev = (await tools["event_create"](name="__test_plugin_event"))["result"]
        try:
            tr = (await tools["event_add_track"](target=ev["guid"]))["result"]
            fx = (await tools["mixer_effect_add_plugin"](target=tr["mixerGroupGuid"], plugin=effect))["result"]
            assert fx["entity"] == "PluginEffect"
            chain = (await tools["mixer_effect_list"](target=tr["mixerGroupGuid"]))["result"]
            assert fx["guid"] in [x["guid"] for x in chain]

            snd = (await tools["sound_add_plugin"](
                event_target=ev["guid"], track_target=tr["trackGuid"], plugin=instrument, start=0.0, length=2.0))["result"]
            assert snd["entity"] == "PluginSound" and snd["length"] == pytest.approx(2.0)

            with pytest.raises(FmodMCPError, match="instrument, not an effect"):
                await tools["mixer_effect_add_plugin"](target=tr["mixerGroupGuid"], plugin=instrument)
            with pytest.raises(FmodMCPError, match="not available"):
                await tools["mixer_effect_add_plugin"](target=tr["mixerGroupGuid"], plugin="__No Such Plugin")
        finally:
            await _delete(client, ev["guid"])
            # A plug-in may create a DataFile (and its file in Assets) that
            # outlives the instrument; deleting the DataFile removes both.
            for guid in await _data_file_guids(client) - data_files_before:
                await _delete(client, guid)

    asyncio.run(run())


async def _data_file_guids(client):
    r = await client.execute(
        "var c=studio.project.model.DataFile;"
        "var a=c?(c.findInstances({includeDerivedTypes:true})||[]):[];"
        "return a.map(function(d){return G(d);});"
    )
    return set(r["result"])


def test_multi_playlist_editing(tmp_path):
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("sound_tools")
        files = _wavs(tmp_path, 3, "__test_multi")
        built = (await tools["event_create_from_audio"](name="__test_multi_event", file_paths=files[:2]))["result"]
        extra = (await tools["audio_import"](file_path=files[2]))["result"]
        multi = built["instrumentGuid"]
        try:
            entries = (await tools["multi_list_entries"](target=multi))["result"]["entries"]
            assert len(entries) == 2 and all(e["audioFile"] for e in entries)
            added = (await tools["multi_add_entry"](target=multi, audio=extra["guid"]))["result"]
            assert added["entries"] == 3 and added["audioFile"] == extra["name"]

            w1 = (await tools["multi_set_weight"](entry=entries[0]["guid"], percentage=30.0))["result"]
            w2 = (await tools["multi_set_weight"](entry=entries[0]["guid"], percentage=40.0))["result"]
            assert w1["created"] is True and w2["created"] is False

            pl = (await tools["multi_set_playlist"](target=multi, looping=True, play_count=2))["result"]
            assert pl["applied"] == {"looping": True, "playCount": 2}

            entries = (await tools["multi_list_entries"](target=multi))["result"]
            assert entries["looping"] is True and entries["playCount"] == 2
            weights = {e["guid"]: e["percentage"] for e in entries["entries"]}
            assert weights[w1["entry"]] == pytest.approx(40.0)

            r = (await tools["multi_remove_entry"](entry=added["guid"]))["result"]
            assert r["entries"] == 2
        finally:
            await _delete(client, built["guid"])
            for a in built["assets"] + [extra]:
                await _delete(client, a["guid"])

    asyncio.run(run())


def test_asset_listing_info_and_move(tmp_path):
    import os

    from fmod_mcp_shared.error_codes import FmodMCPError

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("sound_tools", "asset_tools")
        (f,) = _wavs(tmp_path, 1, "__test_asset")
        a = (await tools["audio_import"](file_path=f))["result"]
        moved_dir = None
        try:
            assert a["name"] and a["path"].startswith("asset:/")
            unused = (await tools["audio_assets"](unused_only=True))["result"]["assets"]
            assert a["guid"] in [x["guid"] for x in unused]

            info = (await tools["audio_asset_info"](target=a["guid"]))["result"]
            assert info["usedBy"] == 0 and info["length"] == pytest.approx(0.5, abs=0.01)
            assert os.path.isfile(info["absolutePath"])

            mv = (await tools["audio_asset_move"](target=a["guid"], new_path="__test_dir/__test_moved.wav"))["result"]
            assert mv["moved"] is True and mv["assetPath"] == "__test_dir/__test_moved.wav"
            moved_dir = os.path.dirname(mv["absolutePath"])
            assert os.path.isfile(mv["absolutePath"])
            assert not os.path.exists(info["absolutePath"])
            in_dir = (await tools["audio_assets"](folder="__test_dir"))["result"]
            assert [x["guid"] for x in in_dir["assets"]] == [a["guid"]]

            with pytest.raises(FmodMCPError, match="extension"):
                await tools["audio_asset_move"](target=a["guid"], new_path="__test_dir/x.ogg")
        finally:
            await _delete(client, a["guid"])
            # Deleting a moved asset removes the file but not the folder
            # setAssetPath created for it (confirmed live).
            if moved_dir and os.path.isdir(moved_dir) and not os.listdir(moved_dir):
                os.rmdir(moved_dir)

    asyncio.run(run())


def test_automation_point_editing_and_lane():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("automation_tools", "event_tools")
        ev = (await tools["event_create"](name="__test_automation_edit"))["result"]
        try:
            tr = (await tools["event_add_track"](target=ev["guid"]))["result"]
            mg = tr["mixerGroupGuid"]
            curve = (await tools["automation_add_curve"](
                target=mg, property="volume", driver=ev["guid"], driver_type="timeline",
                points=[[0.0, 0.0], [1.0, -6.0], [2.0, -12.0]]))["result"]["guid"]
            listing = (await tools["automation_list"](target=mg))["result"]["curves"]
            details = listing[0]["pointDetails"]
            assert [d["position"] for d in details] == [0.0, 1.0, 2.0]

            sp = (await tools["automation_set_point"](point=details[1]["guid"], value=-3.0, curve_shape=0.5))["result"]
            assert sp["applied"]["value"] == pytest.approx(-3.0)
            assert sp["applied"]["curveShape"] == pytest.approx(0.5)

            rm = (await tools["automation_remove_point"](curve=curve, position=2.0))["result"]
            assert rm["remaining"] == 2

            lane1 = (await tools["automation_show_track"](event_target=ev["guid"], target=mg))["result"]
            lane2 = (await tools["automation_show_track"](event_target=ev["guid"], target=mg))["result"]
            assert lane1["reused"] is False and lane2["reused"] is True
            assert lane1["trackGuid"] == tr["trackGuid"]

            await tools["automation_delete_curve"](curve=curve)
            listing = (await tools["automation_list"](target=mg))["result"]["curves"]
            assert listing == []
        finally:
            await _delete(client, ev["guid"])

    asyncio.run(run())


def test_bank_folders():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("bank_tools", "folder_tools")
        b = (await tools["bank_create"](name="__test_bank", folder="__test_bf/sub"))["result"]
        try:
            assert b["path"] == "bank:/__test_bf/sub/__test_bank"
            again = (await tools["folder_create"](kind="BankFolder", path="__test_bf/sub"))["result"]
            assert again["name"] == "sub"
            root = (await tools["bank_set_folder"](target=b["guid"], folder=""))["result"]
            assert root["path"] == "bank:/__test_bank"
            back = (await tools["bank_set_folder"](target=b["guid"], folder="__test_bf"))["result"]
            assert back["path"] == "bank:/__test_bf/__test_bank"
        finally:
            await _delete(client, b["guid"])
            await client.execute(
                "var a=studio.project.model.BankFolder.findInstances()||[];"
                "for(var i=0;i<a.length;i++){if(a[i].name==='__test_bf')studio.project.deleteObject(a[i]);}"
                "return true;"
            )

    asyncio.run(run())


def test_instrument_properties_fades_and_batch_import(tmp_path):
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("sound_tools", "utility_tools")
        files = _wavs(tmp_path, 3, "__test_props")
        built = (await tools["event_create_from_audio"](name="__test_props_event", file_paths=files[:1]))["result"]
        batch = (await tools["audio_import_batch"](file_paths=files[1:]))["result"]
        try:
            assert built["instrumentType"] == "SingleSound"
            inst = built["instrumentGuid"]
            r = (await tools["sound_set_properties"](target=inst, volume=-3.0, pitch=2.0, looping=True))["result"]
            assert r["applied"] == {"volume": -3.0, "pitch": 2.0, "looping": True}
            await tools["sound_set_fade"](target=inst, fade_in=0.1, fade_out=0.2)
            rels = {x["name"]: x["count"] for x in (await tools["utility_dump"](target=inst))["result"]["relationships"]}
            assert rels["fadeInCurve"] == 1 and rels["fadeOutCurve"] == 1

            assert batch["count"] == 2 and all(x["name"] for x in batch["assets"])
        finally:
            await _delete(client, built["guid"])
            for a in built["assets"] + batch["assets"]:
                await _delete(client, a["guid"])

    asyncio.run(run())


def test_relationship_entity_and_list_utilities():
    from fmod_mcp_shared.error_codes import FmodMCPError

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("utility_tools", "mixer_tools", "event_tools", "parameter_tools")
        g = (await tools["mixer_group_create"](name="__test_rel_group"))["result"]
        v = (await tools["vca_create"](name="__test_rel_vca"))["result"]
        ev = (await tools["event_create"](name="__test_list_event"))["result"]
        try:
            add = (await tools["utility_set_relationship"](
                target=g["guid"], relationship="masters", destination=v["guid"]))["result"]
            assert add["count"] == 1 and add["cardinality"] == "ToMany"
            rem = (await tools["utility_set_relationship"](
                target=g["guid"], relationship="masters", destination=v["guid"], action="remove"))["result"]
            assert rem["count"] == 0
            with pytest.raises(FmodMCPError, match="has no relationship"):
                await tools["utility_set_relationship"](
                    target=g["guid"], relationship="noSuchRelationship", destination=v["guid"])

            doc = (await tools["utility_describe_entity"](entity="SingleSound"))["result"]
            assert "audioFile" in doc["document"] and doc["isAbstract"] is False

            await tools["event_add_track"](target=ev["guid"])
            listed = (await tools["utility_list"](obj_type="AudioTrack", include_derived=True, within=ev["guid"]))["result"]
            entities = {x["entity"] for x in listed["items"]}
            assert {"GroupTrack", "MasterTrack"} <= entities

            await tools["parameter_add"](
                event_target=ev["guid"], name="__TestLabels", param_type="UserEnumeration", labels=["Grass", "Stone"])
            names = [x["name"] for x in (await tools["parameter_list"](event_target=ev["guid"]))["result"]]
            assert "__TestLabels" in names
        finally:
            await _delete(client, ev["guid"])
            await _delete(client, g["guid"])
            await _delete(client, v["guid"])
            await _delete_presets(client, "__TestLabels")

    asyncio.run(run())


def test_effect_settings_removal_and_event_send():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("mixer_tools", "event_tools")
        ev = (await tools["event_create"](name="__test_fx_event"))["result"]
        try:
            tr = (await tools["event_add_track"](target=ev["guid"]))["result"]
            mg = tr["mixerGroupGuid"]
            fx = (await tools["mixer_effect_add"](target=mg, effect="GainEffect", settings={"gain": -3.0}))["result"]
            assert fx["applied"]["applied"]["gain"] == pytest.approx(-3.0)
            await tools["mixer_effect_remove"](target=mg, effect=fx["guid"])
            chain = (await tools["mixer_effect_list"](target=mg))["result"]
            assert fx["guid"] not in [x["guid"] for x in chain]

            send = (await tools["mixer_send_create"](
                event_target=ev["guid"], source_group_target=mg, return_name="__test_ret", level_db=-6.0))["result"]
            assert send["linkedVia"] == "mixerReturn"
            assert send["level"] == pytest.approx(-6.0)
        finally:
            await _delete(client, ev["guid"])

    asyncio.run(run())


def test_undo_redo_roundtrip():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("project_tools", "mixer_tools")
        g = (await tools["mixer_group_create"](name="__test_undo_group"))["result"]
        try:
            await tools["project_undo"](steps=1)
            gone = await client.execute(
                "var o=studio.project.lookup(p.t);return {exists:!!(o&&o.isValid)};", t=g["guid"])
            await tools["project_redo"](steps=1)
            back = await client.execute(
                "var o=studio.project.lookup(p.t);return {exists:!!(o&&o.isValid)};", t=g["guid"])
            # One scripted tool call may be several undo steps; what matters
            # is that undo changes the project and redo restores it.
            assert gone["result"]["exists"] is False or back["result"]["exists"] is True
            assert back["result"]["exists"] is True
        finally:
            await _delete(client, g["guid"])

    asyncio.run(run())


def test_project_info_and_3d_audition():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("project_tools", "audition_tools", "event_tools")
        ver = (await tools["project_get_version"]())["result"]
        assert ver["major"] is not None and ver["platform"] in ("win", "mac")
        act = await tools["project_trigger_action"](window_action="RefreshModifiedAssets")
        assert act["success"] is True

        ev = (await tools["event_create"](name="__test_3d_event", spatializer=True))["result"]
        try:
            info = (await tools["event_info"](target=ev["guid"]))["result"]
            assert info["is3D"] is True
            await tools["event_play"](target=ev["guid"])
            r = (await tools["event_set_3d_attributes"](
                target=ev["guid"], radial_distance=12.0, azimuth=45.0))["result"]
            await tools["event_stop"](target=ev["guid"])
            assert r["attributes"]["radialDistance"] == pytest.approx(12.0)
            assert r["attributes"]["azimuth"] == pytest.approx(45.0)
        finally:
            await _delete(client, ev["guid"])

    asyncio.run(run())


def test_project_export_guids_writes_a_guid_file_and_is_undone():
    """Exports GUIDs.txt, checks it lists real events, then puts the
    project folder back exactly as it was (the file is new by default, and
    Build/ may be under version control)."""
    import os
    import time

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("project_tools")
        info = await client.execute(
            "var e=(studio.project.model.Event.findInstances()||[])[0];"
            "return {f:studio.project.filePath,guid:e?G(e):null};"
        )
        root = os.path.dirname(info["result"]["f"])

        def guid_files():
            out = {}
            for d, _dirs, files in os.walk(root):
                for name in files:
                    if name.lower() == "guids.txt":
                        path = os.path.join(d, name)
                        with open(path, "rb") as fh:
                            out[path] = fh.read()
            return out

        before = guid_files()
        started = time.time()
        try:
            r = await tools["project_export_guids"]()
            assert r["result"]["success"] is True
            after = guid_files()
            written = [p for p in after if os.path.getmtime(p) >= started - 1]
            assert written, "exportGUIDs reported success but no GUIDs.txt was written"
            if info["result"]["guid"]:
                text = after[written[0]].decode("utf-8", "replace")
                assert info["result"]["guid"] in text
        finally:
            for path in guid_files():
                if path in before:
                    with open(path, "wb") as fh:
                        fh.write(before[path])
                else:
                    os.remove(path)

    asyncio.run(run())


# ---------------------------------------------------------------------------
# Third round: unattended-automation tools. Writes are confined to throwaway
# objects; nothing changes project-wide settings (e.g. the platform encoding
# default is only read here). Process control and headless builds are
# opt-in through environment variables because they close the Studio window
# or need a disposable copy of a project.
# ---------------------------------------------------------------------------


def test_route_event_into_group_and_scatterer_playlist():
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("mixer_tools", "sound_tools", "event_tools")
        g = (await tools["mixer_group_create"](name="__test_route_group"))["result"]
        ev = (await tools["event_create"](name="__test_route_event"))["result"]
        try:
            r = (await tools["mixer_group_route"](target=ev["guid"], output_target=g["guid"]))["result"]
            assert r["via"] == "mixerInput" and r["output"] == g["guid"]

            tr = (await tools["event_add_track"](target=ev["guid"]))["result"]
            sc = (await tools["sound_add_to_track"](
                event_target=ev["guid"], track_target=tr["trackGuid"], sound_type="SoundScatterer",
                start=0.0, length=2.0))["result"]
            entry = (await tools["sound_create"](sound_type="SingleSound"))["result"]
            own = (await tools["sound_set_owner"](target=entry["guid"], owner=sc["guid"]))["result"]
            assert own["ownerGuid"] != sc["guid"]  # the scatterer's inner playlist
            sounds = (await tools["event_list_sounds"](event_target=ev["guid"]))["result"]["sounds"]
            assert entry["guid"] in [s["guid"] for s in sounds]
        finally:
            await _delete(client, ev["guid"])
            await _delete(client, g["guid"])

    asyncio.run(run())


def test_instrument_sizing_nested_events_settings_tags_and_tempo(tmp_path):
    from fmod_mcp_shared.error_codes import FmodMCPError

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("sound_tools", "event_tools", "marker_tools")
        (f,) = _wavs(tmp_path, 1, "__test_sizing")
        a = (await tools["audio_import"](file_path=f))["result"]
        ev = (await tools["event_create"](name="__test_round3_event"))["result"]
        child = (await tools["event_create"](name="__test_round3_child"))["result"]
        try:
            tr = (await tools["event_add_track"](target=ev["guid"]))["result"]
            inst = (await tools["sound_add_to_track"](
                event_target=ev["guid"], track_target=tr["trackGuid"], sound_type="SingleSound",
                start=1.0, audio=a["guid"]))["result"]
            assert inst["length"] == pytest.approx(0.5, abs=0.01) and inst["audioFile"] == a["name"]
            with pytest.raises(FmodMCPError, match="length"):
                await tools["sound_add_to_track"](
                    event_target=ev["guid"], track_target=tr["trackGuid"], sound_type="SingleSound", length=0)

            props = (await tools["sound_set_properties"](
                target=inst["guid"], start=2.0, length=0.25, is_async=True, looping=True))["result"]
            assert props["applied"] == {"looping": True, "isAsync": True, "start": 2.0, "length": 0.25}

            nested = (await tools["sound_add_nested_event"](
                event_target=ev["guid"], track_target=tr["trackGuid"], referenced_event=child["guid"],
                start=3.0, length=1.0))["result"]
            assert nested["references"] == "event:/__test_round3_child"
            with pytest.raises(FmodMCPError, match="itself"):
                await tools["sound_add_nested_event"](
                    event_target=ev["guid"], track_target=tr["trackGuid"], referenced_event=ev["guid"])

            st = (await tools["event_set_settings"](
                target=ev["guid"], max_instances=3, voice_stealing="virtualize", cooldown_s=0.25,
                persistent=True, min_distance=2.0, max_distance=40.0))["result"]
            assert st["clamped"] == []
            got = (await tools["event_get_settings"](target=ev["guid"]))["result"]
            assert (got["maxInstances"], got["voiceStealing"], got["persistent"]) == (3, 3, True)
            assert got["maxDistance"] == pytest.approx(40.0)

            t1 = (await tools["tag_add"](target=ev["guid"], tag="__test_tag"))["result"]
            t2 = (await tools["tag_add"](target=child["guid"], tag="__test_tag"))["result"]
            assert t1["tagGuid"] == t2["tagGuid"] and t2["taggedCount"] == 2
            listed = (await tools["tag_list"](tag="__test_tag"))["result"]["objects"]
            assert {o["guid"] for o in listed} == {ev["guid"], child["guid"]}
            await tools["tag_remove"](target=child["guid"], tag="__test_tag")
            listed = (await tools["tag_list"](tag="__test_tag"))["result"]["objects"]
            assert [o["guid"] for o in listed] == [ev["guid"]]

            mt = (await tools["event_add_marker_track"](target=ev["guid"]))["result"]["guid"]
            tempo = (await tools["marker_add_tempo"](track_target=mt, position=0.0, bpm=96, beats_per_bar=3))["result"]
            assert tempo["timeSignature"] == "3/4" and tempo["bpm"] == pytest.approx(96)
            markers = (await tools["marker_list"](track_target=mt))["result"]
            assert any(m["markerType"] == "TempoMarker" for m in markers)
        finally:
            await _delete(client, ev["guid"])
            await _delete(client, child["guid"])
            await _delete(client, a["guid"])
            await client.execute(
                "var a=studio.project.model.Tag.findInstances()||[];"
                "for(var i=0;i<a.length;i++){if(a[i].name==='__test_tag')studio.project.deleteObject(a[i]);}"
                "return true;"
            )

    asyncio.run(run())


def test_asset_encoding_overrides_and_streaming(tmp_path):
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("sound_tools", "asset_tools")
        (f,) = _wavs(tmp_path, 1, "__test_encoding")
        a = (await tools["audio_import"](file_path=f))["result"]
        try:
            before = (await tools["encoding_get"](targets=[a["guid"]]))["result"]
            default = before["platformDefault"]
            assert default["formatName"] in ("pcm", "fadpcm", "xma", "vorbis", "at9", "opus")
            assert before["assets"][0]["override"] is None

            s = (await tools["encoding_set"](
                targets=[a["guid"]], format="fadpcm", sample_rate_mode="preserve", streaming=True))["result"]
            assert s["overridesCreated"] == 1 and s["streaming"] is True
            after = (await tools["encoding_get"](targets=[a["guid"]]))["result"]["assets"][0]
            assert after["override"]["formatName"] == "fadpcm"
            assert after["override"]["sampleRateModeName"] == "preserve"
            assert after["streaming"] is True

            again = (await tools["encoding_set"](targets=[a["guid"]], quality=80))["result"]
            assert again["overridesUpdated"] == 1 and again["overridesCreated"] == 0

            cl = (await tools["encoding_clear"](targets=[a["guid"]]))["result"]
            assert cl["overridesRemoved"] == 1
            final = (await tools["encoding_get"](targets=[a["guid"]]))["result"]
            assert final["assets"][0]["override"] is None
            # The platform default was never touched.
            assert final["platformDefault"]["format"] == default["format"]
        finally:
            await _delete(client, a["guid"])

    asyncio.run(run())


def test_event_lint_finds_silent_setups(tmp_path):
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("event_tools", "sound_tools", "marker_tools", "mixer_tools", "utility_tools")
        empty = (await tools["event_create"](name="New Event 77"))["result"]
        ev = (await tools["event_create"](name="__test_lint_event"))["result"]
        try:
            lint = (await tools["event_lint"](target=empty["guid"]))["result"]
            assert lint["ok"] is False
            msgs = " | ".join(x["message"] for x in lint["errors"] + lint["warnings"])
            assert "no instruments" in msgs and "default name" in msgs and "no bank" in msgs

            tr = (await tools["event_add_track"](target=ev["guid"]))["result"]
            await tools["sound_add_to_track"](
                event_target=ev["guid"], track_target=tr["trackGuid"], sound_type="SingleSound",
                start=0.0, length=4.0)
            mt = (await tools["event_add_marker_track"](target=ev["guid"]))["result"]["guid"]
            await tools["marker_add_sustain_point"](track_target=mt, position=2.0)
            await tools["mixer_group_volume"](target=tr["mixerGroupGuid"], db=-80.0)
            lint = (await tools["event_lint"](target=ev["guid"]))["result"]
            errors = " | ".join(x["message"] for x in lint["errors"])
            warnings = " | ".join(x["message"] for x in lint["warnings"])
            assert "no audio file" in errors
            assert "sustain point" in warnings and "track volume is -80" in warnings

            audit = (await tools["utility_validate"]())["result"]
            assert empty["guid"] in [x["guid"] for x in audit["eventsWithDefaultNames"]]
        finally:
            await _delete(client, empty["guid"])
            await _delete(client, ev["guid"])

    asyncio.run(run())


def test_event_audio_report_measures_what_an_event_plays(tmp_path):
    async def run():
        client = FmodStudioClient()
        tools = _live_tools("sound_tools", "analysis_tools")
        files = _wavs(tmp_path, 2, "__test_report")
        built = (await tools["event_create_from_audio"](name="__test_report_event", file_paths=files))["result"]
        try:
            rep = (await tools["event_audio_report"](event_target=built["guid"]))["result"]
            assert rep["summary"]["files"] == 2
            assert rep["instrumentsWithoutAudio"] == 0
            assert all(f["error"] is None and f["durationS"] == pytest.approx(0.5, abs=0.01)
                       for f in rep["files"])
            assert {f["assetGuid"] for f in rep["files"]} == {x["guid"] for x in built["assets"]}
        finally:
            await _delete(client, built["guid"])
            for x in built["assets"]:
                await _delete(client, x["guid"])

    asyncio.run(run())


def test_studio_status_reports_the_open_project():
    async def run():
        tools = _live_tools("studio_tools")
        st = (await tools["studio_status"]())["result"]
        assert st["scriptServerReachable"] is True and st["processRunning"] is True
        assert st["openProject"] and st["openProject"].endswith(".fspro")
        assert st["scriptServerPreference"] is True
        assert st["commandLineTool"]

    asyncio.run(run())


def test_headless_tools_refuse_the_project_open_in_studio():
    from fmod_mcp_shared.error_codes import FmodMCPError

    async def run():
        tools = _live_tools("studio_tools")
        open_project = (await tools["studio_status"]())["result"]["openProject"]
        for name in ("headless_build", "headless_validate"):
            with pytest.raises(FmodMCPError, match="open in FMOD Studio"):
                await tools[name](project_path=open_project)

    asyncio.run(run())


@pytest.mark.skipif(
    not os.environ.get("FMOD_TEST_HEADLESS_PROJECT"),
    reason="set FMOD_TEST_HEADLESS_PROJECT to a DISPOSABLE copy of a project (.fspro) to test headless builds",
)
def test_headless_build_and_validate_on_a_disposable_copy():
    async def run():
        tools = _live_tools("studio_tools")
        project = os.environ["FMOD_TEST_HEADLESS_PROJECT"]
        v = (await tools["headless_validate"](project_path=project))["result"]
        assert v["valid"] is True, v["problems"]
        b = (await tools["headless_build"](project_path=project))["result"]
        assert b["built"] is True, b["problems"]
        rel = {o["relative"] for o in b["outputs"]}
        assert any(r.endswith(".bank") for r in rel) and "Build/GUIDs.txt" in rel
        bad = (await tools["headless_build"](project_path=project, banks="__NoSuchBank"))["result"]
        assert bad["built"] is False and bad["exitCode"] != 0
        assert any("NoSuchBank" in pr for pr in bad["problems"])

    asyncio.run(run())


@pytest.mark.skipif(
    os.environ.get("FMOD_TEST_RESTART_STUDIO") != "1",
    reason="set FMOD_TEST_RESTART_STUDIO=1 to let this test close and reopen FMOD Studio",
)
def test_studio_quit_and_launch_roundtrip():
    async def run():
        tools = _live_tools("studio_tools")
        project = (await tools["studio_status"]())["result"]["openProject"]
        q = (await tools["studio_quit"](save=True))["result"]
        assert q["quit"] is True
        st = (await tools["studio_status"]())["result"]
        assert st["processRunning"] is False and st["scriptServerReachable"] is False
        launched = (await tools["studio_launch"](project_path=project, wait_seconds=180))["result"]
        assert launched["launched"] is True
        again = (await tools["studio_launch"](project_path=project))["result"]
        assert again["alreadyOpen"] is True

    asyncio.run(run())


@pytest.mark.skipif(
    os.environ.get("FMOD_TEST_GUI_BUILD") != "1",
    reason="set FMOD_TEST_GUI_BUILD=1 to build the open project's banks (they are restored from git after)",
)
def test_project_build_returns_a_build_report():
    """Builds the open project inside Studio, checks the report, then puts
    every bank/GUIDs file back exactly as it was (banks are often committed)."""

    async def run():
        client = FmodStudioClient()
        tools = _live_tools("project_tools")
        project = (await client.execute("return {f:studio.project.filePath};"))["result"]["f"]
        root = os.path.dirname(project)
        snapshot = {}
        for d, _dirs, files in os.walk(os.path.join(root, "Build")):
            for name in files:
                path = os.path.join(d, name)
                with open(path, "rb") as fh:
                    snapshot[path] = fh.read()
        try:
            r = (await tools["project_build"]())["result"]
            assert r["built"] is True
            assert any(o["relative"].endswith(".bank") for o in r["outputs"])
            assert isinstance(r["problems"], list)
        finally:
            for d, _dirs, files in os.walk(os.path.join(root, "Build")):
                for name in files:
                    path = os.path.join(d, name)
                    if path not in snapshot:
                        os.remove(path)
            for path, data in snapshot.items():
                with open(path, "wb") as fh:
                    fh.write(data)

    asyncio.run(run())
