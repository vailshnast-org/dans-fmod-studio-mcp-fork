"""Unit tests for the host-side tools (Studio process control, headless
builds, audio analysis) and the new validators. Nothing here starts a
process or touches the real Studio preferences: every file is a temp copy.
"""

import asyncio
import math
import os
import shutil
import struct
import time
import wave

import pytest

import fmod_mcp.main as main_mod  # noqa: F401  (import side effect: client exists)
from fmod_mcp.tools import analysis_tools, asset_tools, event_tools, studio_tools
from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError

_PREFS = """<?xml version="1.0" encoding="UTF-8"?>
<objects serializationModel="Studio.02.03.00">
	<object class="EditorSettings" id="{50706988-cfb2-4a81-840d-be59d37eff0d}">
		<property name="recentVersionOpened">
			<value>20315</value>
		</property>
		{SCRIPT}
	</object>
</objects>
"""


def _prefs(tmp_path, script_value):
    block = (
        ""
        if script_value is None
        else f'<property name="scriptServerEnabled"><value>{script_value}</value></property>'
    )
    path = tmp_path / "Studio.02.03.00.config"
    path.write_text(_PREFS.replace("{SCRIPT}", block), encoding="utf-8")
    return str(path)


@pytest.mark.parametrize(
    "value, before, outcome",
    [("true", True, "already"), ("false", False, "enabled"), (None, False, "created")],
)
def test_script_server_preference_read_and_enable(tmp_path, monkeypatch, value, before, outcome):
    path = _prefs(tmp_path, value)
    monkeypatch.setattr(studio_tools, "_settings_file", lambda: path)
    assert studio_tools.read_script_server_pref() is before
    assert studio_tools.enable_script_server_pref() == outcome
    assert studio_tools.read_script_server_pref() is True
    # Everything else in the file survives the edit.
    assert "recentVersionOpened" in open(path, encoding="utf-8").read()


def test_missing_preferences_file_is_a_clear_error(monkeypatch):
    monkeypatch.setattr(studio_tools, "_settings_file", lambda: None)
    assert studio_tools.read_script_server_pref() is None
    with pytest.raises(FmodMCPError) as ei:
        studio_tools.enable_script_server_pref()
    assert ei.value.code == ErrorCode.INVALID_PATH


def test_find_install_honours_environment(tmp_path, monkeypatch):
    exe = tmp_path / "FMOD Studio.exe"
    exe.write_bytes(b"")
    cl = tmp_path / ("fmodstudiocl.exe" if os.name == "nt" else "fmodstudiocl")
    cl.write_bytes(b"")
    monkeypatch.setenv("FMOD_STUDIO_EXE", str(exe))
    monkeypatch.delenv("FMOD_STUDIO_CL", raising=False)
    found = studio_tools.find_install()
    assert found["exe"] == str(exe)
    assert found["cl"] == str(cl)  # discovered next to the GUI exe


def test_check_project_path(tmp_path, monkeypatch):
    proj = tmp_path / "Game.fspro"
    proj.write_text("x")
    other = tmp_path / "notes.txt"
    other.write_text("x")
    assert studio_tools.check_project_path(str(proj)) == os.path.realpath(proj)
    monkeypatch.setenv("FMOD_STUDIO_PROJECT", str(proj))
    assert studio_tools.check_project_path(None) == os.path.realpath(proj)
    monkeypatch.delenv("FMOD_STUDIO_PROJECT")
    for bad, code in (
        (None, ErrorCode.MISSING_PARAMETER),
        (str(other), ErrorCode.INVALID_PATH),
        (str(tmp_path / "missing.fspro"), ErrorCode.INVALID_PATH),
        ("relative.fspro", ErrorCode.INVALID_PATH),
    ):
        with pytest.raises(FmodMCPError) as ei:
            studio_tools.check_project_path(bad)
        assert ei.value.code == code, bad


# Lines captured from fmodstudiocl 2.03.15.
_CL_BUILD_OK = """Loading project "C:\\p\\game.fspro"...
Successfully opened project.
Building project "C:\\p\\game.fspro"...
Build Status: Gathering file stats...
Build Status: Building "Master" for Desktop...
Build completed successfully.
GUIDs exported successfully.
"""
_CL_BUILD_FAIL = """Loading project "C:\\p\\game.fspro"...
Successfully opened project.
Build Error: Failed to encode bank "Master" due to the following error: External encoder dynamic library not found.
Build Banks Error: Could not locate bank "NoSuchBank".
"""


def test_cl_output_parsing():
    ok = studio_tools._parse_cl_output(_CL_BUILD_OK)
    assert ok["problems"] == []
    assert "Build completed successfully." in ok["messages"]
    assert not any(m.startswith("Build Status:") for m in ok["messages"])
    bad = studio_tools._parse_cl_output(_CL_BUILD_FAIL)
    assert len(bad["problems"]) == 2
    assert all("Error" in p for p in bad["problems"])


def test_bank_and_platform_name_lists():
    assert studio_tools._split_names(None) is None
    assert studio_tools._split_names("Master") == "Master"
    assert studio_tools._split_names(["Master", " Music "]) == "Master,Music"
    for bad in ("", ["a,b"], [""], [3]):
        with pytest.raises(FmodMCPError):
            studio_tools._split_names(bad)


def test_build_outputs_lists_only_fresh_banks(tmp_path):
    (tmp_path / "Build" / "Desktop").mkdir(parents=True)
    (tmp_path / "Assets").mkdir()
    old = tmp_path / "Build" / "Desktop" / "Old.bank"
    old.write_bytes(b"x")
    os.utime(old, (time.time() - 3600, time.time() - 3600))
    since = time.time()
    (tmp_path / "Build" / "Desktop" / "Master.bank").write_bytes(b"1234")
    (tmp_path / "Build" / "GUIDs.txt").write_text("{x} event:/a")
    (tmp_path / "Assets" / "decoy.bank").write_bytes(b"x")  # never a build output
    out = studio_tools.build_outputs(str(tmp_path), since)
    assert [o["relative"] for o in out] == ["Build/Desktop/Master.bank", "Build/GUIDs.txt"]
    assert out[0]["bytes"] == 4


# ---------------------------------------------------------------- analysis


def _wav(path, seconds=1.0, rate=48000, amp=0.5, lead=0.0, dc=0.0, clip=False, ch=1):
    n = int(seconds * rate)
    lead_n = int(lead * rate)
    frames = []
    for i in range(n):
        v = 0.0 if i < lead_n else amp * math.sin(2 * math.pi * 1000 * i / rate) + dc
        if clip and i == n // 2:
            v = 1.0
        v = max(-1.0, min(1.0, v))
        frames.extend([int(v * 32767)] * ch)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack(f"<{len(frames)}h", *frames))
    return str(path)


@pytest.fixture(params=["wave", "numpy-off"])
def no_ffmpeg(request, monkeypatch):
    """Exercise the stdlib path, with and without the numpy accelerator."""
    monkeypatch.setattr(analysis_tools, "_ffmpeg", lambda: (None, None))
    if request.param == "numpy-off":
        monkeypatch.setattr(analysis_tools, "_np", None)


def test_clean_file_has_no_flags(tmp_path, no_ffmpeg):
    r = analysis_tools.analyze_file(_wav(tmp_path / "clean.wav", amp=0.5))
    assert r["error"] is None and r["decoder"] == "wave"
    assert r["flags"] == []
    assert r["peakDbfs"] == pytest.approx(-6.02, abs=0.1)
    assert r["durationS"] == pytest.approx(1.0)
    assert r["integratedLufs"] is None  # needs ffmpeg


@pytest.mark.parametrize(
    "kwargs, flag",
    [
        ({"amp": 0.0}, "silent"),
        ({"amp": 0.5, "clip": True}, "clipping"),
        ({"amp": 0.3, "dc": 0.05}, "dc_offset"),
        ({"amp": 0.5, "lead": 0.3}, "leading_silence"),
        ({"amp": 0.002}, "very_quiet"),
        ({"amp": 0.5, "rate": 22050}, "unusual_sample_rate"),
    ],
)
def test_problem_files_are_flagged(tmp_path, no_ffmpeg, kwargs, flag):
    r = analysis_tools.analyze_file(_wav(tmp_path / f"{flag}.wav", **kwargs))
    assert flag in r["flags"], r


def test_non_wav_without_ffmpeg_reports_instead_of_raising(tmp_path, no_ffmpeg):
    f = tmp_path / "x.ogg"
    f.write_bytes(b"OggS")
    r = analysis_tools.analyze_file(str(f))
    assert "needs ffmpeg" in r["error"]


def test_variation_loudness_spread_warning(tmp_path, monkeypatch):
    monkeypatch.setattr(analysis_tools, "_ffmpeg", lambda: (None, None))
    files = [_wav(tmp_path / "a.wav", amp=0.5), _wav(tmp_path / "b.wav", amp=0.5)]
    r = asyncio.run(analysis_tools.analyze_files(files))
    assert r["summary"]["files"] == 2
    assert r["summary"]["loudnessSpreadLu"] is None  # no LUFS without ffmpeg


@pytest.mark.skipif(analysis_tools._ffmpeg()[0] is None, reason="ffmpeg not installed")
def test_ffmpeg_lufs_matches_a_known_sine(tmp_path):
    # A 1 kHz sine at peak amplitude A reads 20*log10(A) - 3.01 LUFS
    # (K-weighting is ~0 dB at 1 kHz).
    r = analysis_tools.analyze_file(_wav(tmp_path / "sine.wav", seconds=3.0, amp=0.1))
    assert r["decoder"] == "ffmpeg"
    assert r["integratedLufs"] == pytest.approx(-23.0, abs=0.5)
    assert r["truePeakDbtp"] == pytest.approx(-20.0, abs=0.5)
    quiet = analysis_tools.analyze_file(_wav(tmp_path / "q.wav", seconds=3.0, amp=0.1))
    loud = analysis_tools.analyze_file(_wav(tmp_path / "l.wav", seconds=3.0, amp=0.9))
    spread = asyncio.run(analysis_tools.analyze_files([quiet["path"], loud["path"]]))
    assert spread["summary"]["loudnessSpreadLu"] == pytest.approx(19.1, abs=0.5)
    assert "warning" in spread["summary"]


@pytest.mark.skipif(analysis_tools._ffmpeg()[0] is None, reason="ffmpeg not installed")
def test_short_one_shot_does_not_report_gate_as_loudness(tmp_path):
    r = analysis_tools.analyze_file(_wav(tmp_path / "click.wav", seconds=0.2, amp=0.5))
    assert r["integratedLufs"] is None and "lufsNote" in r
    assert "very_quiet" not in r["flags"]


def test_analysis_path_validation(tmp_path):
    bad = tmp_path / "notes.txt"
    bad.write_text("x")
    with pytest.raises(FmodMCPError) as ei:
        analysis_tools.check_analysis_path(str(bad))
    assert ei.value.code == ErrorCode.INVALID_FORMAT
    with pytest.raises(FmodMCPError) as ei:
        analysis_tools.check_analysis_path(str(tmp_path / "missing.wav"))
    assert ei.value.code == ErrorCode.INVALID_PATH


# ---------------------------------------------------------------- encoding


def test_encoding_value_mapping():
    v = asset_tools._encoding_values("Vorbis", 60, "preserve", None)
    assert v == {"encodingFormat": 3, "quality": 60, "sampleRateMode": 2}
    assert asset_tools._encoding_values("fadpcm", None, "fixed", 48000) == {
        "encodingFormat": 1, "sampleRateMode": 0, "sampleRate": 48000}
    assert asset_tools.ENCODING_FORMATS == {
        "pcm": 0, "fadpcm": 1, "xma": 2, "vorbis": 3, "at9": 4, "opus": 5}
    for args in (("mp3", None, None, None), (None, 0, None, None), (None, 101, None, None),
                 (None, None, "auto", None), (None, None, None, 12345)):
        with pytest.raises(FmodMCPError):
            asset_tools._encoding_values(*args)


def test_folder_prefix():
    assert asset_tools._folder_prefix(None) is None
    assert asset_tools._folder_prefix("music") == "music/"
    assert asset_tools._folder_prefix("sfx/player/") == "sfx/player/"
    with pytest.raises(FmodMCPError):
        asset_tools._folder_prefix("../outside")


# ---------------------------------------------------------- event settings


class _StubMCP:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def deco(fn):
            self.tools[fn.__name__] = fn
            return fn

        return deco


class _Recorder:
    def __init__(self):
        self.calls = []

    async def execute(self, command, **params):
        self.calls.append(params)
        return {"success": True, "result": {}}


@pytest.fixture()
def event_tool(monkeypatch):
    rec = _Recorder()
    monkeypatch.setattr(main_mod, "client", rec)
    mcp = _StubMCP()
    event_tools.register(mcp)
    return mcp.tools["event_set_settings"], rec


def test_event_settings_mapping(event_tool):
    fn, rec = event_tool
    asyncio.run(fn(target="event:/a", max_instances=3, voice_stealing="Virtualize",
                   cooldown_s=0.5, min_distance=1, max_distance=30))
    assert rec.calls[-1]["props"] == {
        "maxVoices": 3, "voiceStealing": 3, "triggerCooldown": 0.5,
        "minimumDistance": 1.0, "maximumDistance": 30.0}


@pytest.mark.parametrize(
    "kwargs",
    [{}, {"max_instances": 0}, {"voice_stealing": "loudest"}, {"voice_stealing": 9},
     {"priority": 5}, {"cooldown_s": 61}, {"min_distance": 10, "max_distance": 5},
     {"doppler_scale": 600}],
)
def test_event_settings_rejects_bad_values(event_tool, kwargs):
    fn, rec = event_tool
    with pytest.raises(FmodMCPError):
        asyncio.run(fn(target="event:/a", **kwargs))
    assert rec.calls == []


def test_ffmpeg_lookup_respects_env(tmp_path, monkeypatch):
    fake = tmp_path / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    fake.write_bytes(b"")
    monkeypatch.setenv("FFMPEG_PATH", str(fake))
    assert analysis_tools._ffmpeg()[0] == str(fake)
    monkeypatch.delenv("FFMPEG_PATH")
    assert analysis_tools._ffmpeg()[0] == shutil.which("ffmpeg")


def test_studio_log_problems_only_reports_new_warnings(tmp_path, monkeypatch):
    since = time.mktime(time.strptime("2026-10-20 11:12:20", "%Y-%m-%d %H:%M:%S"))
    log = tmp_path / "2026-10-20-11-12-15_log.txt"
    log.write_text(
        "  2026-10-20 11:12:15 FMOD Studio Version 2.03.15\n"
        "* 2026-10-20 11:12:16 old warning before the build\n"
        "  2026-10-20 11:12:25 Building bank Master\n"
        "* 2026-10-20 11:12:26 [Build] Event 'x' references a missing asset\n"
        "- 2026-10-20 11:12:27 [Scripting]ScriptServer started on 127.0.0.1 (3663)\n"
        "  2026-10-20 11:12:28 Build error: could not write bank\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(studio_tools, "_logs_dir", lambda: str(tmp_path))
    problems = studio_tools.studio_log_problems(since)
    assert problems == [
        "* 2026-10-20 11:12:26 [Build] Event 'x' references a missing asset",
        "  2026-10-20 11:12:28 Build error: could not write bank",
    ]
