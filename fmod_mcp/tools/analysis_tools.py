"""Offline audio analysis — the closest an agent gets to "listening".

FMOD Studio's scripting API exposes no meter readings (a LoudnessMeter
effect only has settings; confirmed live on 2.03.15) and no offline render,
so loudness/clipping/silence problems can only be caught by measuring the
source files. These tools do that on the MCP host:

- With ffmpeg on PATH (or FFMPEG_PATH): any format, plus integrated
  loudness (LUFS), loudness range and true peak from ffmpeg's EBU R128
  filter.
- Without it: PCM WAV only (8/16/24/32-bit) through the stdlib `wave`
  module; LUFS/true peak come back null rather than approximated.

numpy is used for speed when importable, never required.
"""

import array
import asyncio
import json
import math
import os
import re
import shutil
import subprocess
import wave

from mcp.server.fastmcp import FastMCP

from fmod_mcp_shared.error_codes import ErrorCode, FmodMCPError
from fmod_mcp_shared.path_safety import safe_path

try:  # optional accelerator
    import numpy as _np
except ImportError:  # pragma: no cover - environment dependent
    _np = None

ANALYZABLE_EXTENSIONS = {".wav", ".aiff", ".aif", ".flac", ".mp3", ".ogg"}
MAX_FILES_PER_CALL = 50
MAX_ANALYSIS_SECONDS = 600  # analyze at most the first 10 minutes of a file
_FFMPEG_TIMEOUT = 300

# Thresholds behind each flag — reported with the result so an agent (or a
# person reading its log) can see why something was flagged.
THRESHOLDS = {
    "clip_sample_level": 0.9999,  # |x| at or above this counts as clipped
    "true_peak_max_dbtp": -1.0,  # above this: no headroom left for encoding
    "silent_peak_dbfs": -60.0,  # peak below this: effectively silence
    "quiet_lufs": -40.0,  # integrated loudness below this: very quiet
    "quiet_rms_dbfs": -45.0,  # fallback when LUFS isn't available
    "dc_offset": 0.01,  # |mean| above this per channel
    "silence_level": 0.001,  # ~-60 dBFS, for leading/trailing silence
    "leading_silence_s": 0.05,  # one-shots should start immediately
    "trailing_silence_s": 1.0,
    "variation_spread_lu": 6.0,  # loudness spread across an event's files
}

_EBUR128_RE = {
    "integratedLufs": re.compile(r"I:\s+(-?[\d.]+|-inf)\s+LUFS"),
    "loudnessRangeLu": re.compile(r"LRA:\s+(-?[\d.]+)\s+LU"),
    "truePeakDbtp": re.compile(r"Peak:\s+(-?[\d.]+|-inf)\s+dBFS"),
}


def _db(x: float) -> float | None:
    return round(20 * math.log10(x), 2) if x > 0 else None


def _ffmpeg() -> tuple[str | None, str | None]:
    ff = os.environ.get("FFMPEG_PATH") or shutil.which("ffmpeg")
    probe = None
    if ff:
        cand = os.path.join(os.path.dirname(ff), "ffprobe" + (".exe" if os.name == "nt" else ""))
        probe = cand if os.path.isfile(cand) else shutil.which("ffprobe")
    return ff, probe


def check_analysis_path(path: str) -> str:
    resolved = safe_path(path)
    if not os.path.isfile(resolved):
        raise FmodMCPError(ErrorCode.INVALID_PATH, f"audio file not found: {resolved}")
    ext = os.path.splitext(resolved)[1].lower()
    if ext not in ANALYZABLE_EXTENSIONS:
        raise FmodMCPError(
            ErrorCode.INVALID_FORMAT,
            f"unsupported audio format {ext!r}; supported: {sorted(ANALYZABLE_EXTENSIONS)}",
        )
    return resolved


def _decode_wave(path: str):
    """PCM WAV -> (interleaved float samples, rate, channels) via stdlib."""
    with wave.open(path, "rb") as w:
        rate, ch, width = w.getframerate(), w.getnchannels(), w.getsampwidth()
        frames = min(w.getnframes(), int(MAX_ANALYSIS_SECONDS * rate))
        raw = w.readframes(frames)
    if width == 1:
        data = [(b - 128) / 128.0 for b in raw]
    elif width == 2:
        a = array.array("h")
        a.frombytes(raw[: len(raw) // 2 * 2])
        data = [v / 32768.0 for v in a]
    elif width == 3:
        data = []
        for i in range(0, len(raw) - 2, 3):
            v = int.from_bytes(raw[i : i + 3], "little", signed=True)
            data.append(v / 8388608.0)
    elif width == 4:
        a = array.array("i")
        a.frombytes(raw[: len(raw) // 4 * 4])
        data = [v / 2147483648.0 for v in a]
    else:
        raise FmodMCPError(ErrorCode.INVALID_FORMAT, f"unsupported WAV sample width {width}")
    return data, rate, ch


def _decode_ffmpeg(path: str, ff: str, probe: str | None):
    rate = ch = None
    if probe:
        out = subprocess.run(  # noqa: S603 - argv list, no shell
            [probe, "-v", "error", "-select_streams", "a:0", "-show_entries",
             "stream=sample_rate,channels", "-of", "json", path],
            capture_output=True, text=True, timeout=_FFMPEG_TIMEOUT,
        )
        try:
            st = json.loads(out.stdout)["streams"][0]
            rate, ch = int(st["sample_rate"]), int(st["channels"])
        except (ValueError, KeyError, IndexError):
            pass
    if not rate or not ch:
        raise FmodMCPError(ErrorCode.INVALID_FORMAT, f"ffprobe could not read {path}")
    out = subprocess.run(  # noqa: S603 - argv list, no shell
        [ff, "-v", "error", "-t", str(MAX_ANALYSIS_SECONDS), "-i", path,
         "-f", "f32le", "-acodec", "pcm_f32le", "-"],
        capture_output=True, timeout=_FFMPEG_TIMEOUT,
    )
    if out.returncode != 0:
        raise FmodMCPError(
            ErrorCode.INVALID_FORMAT,
            f"ffmpeg could not decode {path}: {out.stderr.decode('utf-8', 'replace')[:300]}",
        )
    a = array.array("f")
    a.frombytes(out.stdout[: len(out.stdout) // 4 * 4])
    return a, rate, ch


def _ebur128(path: str, ff: str) -> dict:
    out = subprocess.run(  # noqa: S603 - argv list, no shell
        [ff, "-hide_banner", "-nostats", "-t", str(MAX_ANALYSIS_SECONDS), "-i", path,
         "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True, text=True, timeout=_FFMPEG_TIMEOUT,
    )
    # The summary block is at the end of stderr.
    tail = out.stderr[out.stderr.rfind("Summary:"):] if "Summary:" in out.stderr else ""
    res = {}
    for key, rx in _EBUR128_RE.items():
        m = rx.search(tail)
        if m:
            val = m.group(1)
            res[key] = None if val == "-inf" else float(val)
    return res


def _stats(samples, rate: int, ch: int) -> dict:
    n = len(samples) // ch if ch else 0
    if n == 0:
        return {"frames": 0}
    level = THRESHOLDS["silence_level"]
    clip = THRESHOLDS["clip_sample_level"]
    if _np is not None:
        x = _np.asarray(samples, dtype=_np.float64)[: n * ch].reshape(n, ch)
        ax = _np.abs(x)
        peak = float(ax.max())
        rms = float(_np.sqrt(_np.mean(x * x)))
        clipped = int((ax >= clip).sum())
        dc = [float(v) for v in x.mean(axis=0)]
        loud = _np.nonzero(ax.max(axis=1) > level)[0]
        first, last = (int(loud[0]), int(loud[-1])) if loud.size else (None, None)
    else:
        peak = 0.0
        sq = 0.0
        clipped = 0
        sums = [0.0] * ch
        first = last = None
        for i in range(n):
            frame_peak = 0.0
            for c in range(ch):
                v = samples[i * ch + c]
                av = -v if v < 0 else v
                if av > frame_peak:
                    frame_peak = av
                if av >= clip:
                    clipped += 1
                sq += v * v
                sums[c] += v
            if frame_peak > peak:
                peak = frame_peak
            if frame_peak > level:
                if first is None:
                    first = i
                last = i
        rms = math.sqrt(sq / (n * ch))
        dc = [s / n for s in sums]
    return {
        "frames": n,
        "peakDbfs": _db(peak),
        "rmsDbfs": _db(rms),
        "clippedSamples": clipped,
        "dcOffset": [round(v, 5) for v in dc],
        "leadingSilenceS": round(first / rate, 4) if first is not None else round(n / rate, 4),
        "trailingSilenceS": round((n - 1 - last) / rate, 4) if last is not None else round(n / rate, 4),
    }


def _flags(m: dict) -> list[str]:
    t = THRESHOLDS
    flags = []
    peak = m.get("peakDbfs")
    if peak is None or peak < t["silent_peak_dbfs"]:
        flags.append("silent")
    if m.get("clippedSamples", 0) > 0:
        flags.append("clipping")
    tp = m.get("truePeakDbtp")
    if tp is not None and tp > t["true_peak_max_dbtp"] and "clipping" not in flags:
        flags.append("no_headroom")
    lufs = m.get("integratedLufs")
    if "silent" not in flags:
        if lufs is not None and lufs < t["quiet_lufs"]:
            flags.append("very_quiet")
        elif lufs is None and m.get("rmsDbfs") is not None and m["rmsDbfs"] < t["quiet_rms_dbfs"]:
            flags.append("very_quiet")
    if any(abs(v) > t["dc_offset"] for v in m.get("dcOffset", [])):
        flags.append("dc_offset")
    if "silent" not in flags:
        if m.get("leadingSilenceS", 0) > t["leading_silence_s"]:
            flags.append("leading_silence")
        if m.get("trailingSilenceS", 0) > t["trailing_silence_s"]:
            flags.append("trailing_silence")
    if m.get("sampleRate") not in (44100, 48000):
        flags.append("unusual_sample_rate")
    if (m.get("channels") or 0) > 2:
        flags.append("more_than_stereo")
    return flags


def analyze_file(path: str) -> dict:
    """Measure one (already validated) file. Never raises for a bad file —
    the problem is reported in `error` so one bad file doesn't sink a batch."""
    ff, probe = _ffmpeg()
    result = {"path": path, "decoder": None, "error": None}
    try:
        ext = os.path.splitext(path)[1].lower()
        if ff:
            samples, rate, ch = _decode_ffmpeg(path, ff, probe)
            result["decoder"] = "ffmpeg"
        elif ext == ".wav":
            samples, rate, ch = _decode_wave(path)
            result["decoder"] = "wave"
        else:
            result["error"] = f"{ext} needs ffmpeg (set FFMPEG_PATH or put ffmpeg on PATH)"
            return result
        result.update({"sampleRate": rate, "channels": ch})
        st = _stats(samples, rate, ch)
        result["durationS"] = round(st.pop("frames") / rate, 4) if rate else None
        result.update(st)
        loud = _ebur128(path, ff) if ff else {}
        lufs = loud.get("integratedLufs")
        # Integrated loudness gates on 400 ms blocks: a shorter one-shot (or
        # one quieter than the -70 LUFS absolute gate) measures as -70,
        # which is the gate, not a loudness. Fall back to RMS for those.
        if lufs is not None and (lufs <= -70.0 or (result["durationS"] or 0) < 0.4):
            result["lufsNote"] = "too short or too quiet for integrated loudness; use rmsDbfs"
            lufs = None
        result["integratedLufs"] = lufs
        result["loudnessRangeLu"] = loud.get("loudnessRangeLu")
        result["truePeakDbtp"] = loud.get("truePeakDbtp")
        result["flags"] = _flags(result)
    except (wave.Error, EOFError, OSError, subprocess.SubprocessError) as e:
        result["error"] = f"could not analyze: {e}"
    except FmodMCPError as e:
        result["error"] = e.message
    return result


async def analyze_files(paths: list[str]) -> dict:
    files = [await asyncio.to_thread(analyze_file, p) for p in paths]
    lufs = [f["integratedLufs"] for f in files if f.get("integratedLufs") is not None]
    summary = {
        "files": len(files),
        "flagged": sum(1 for f in files if f.get("flags") or f.get("error")),
        "loudnessSpreadLu": round(max(lufs) - min(lufs), 2) if len(lufs) > 1 else None,
    }
    if summary["loudnessSpreadLu"] is not None and summary["loudnessSpreadLu"] > THRESHOLDS["variation_spread_lu"]:
        summary["warning"] = (
            f"loudness differs by {summary['loudnessSpreadLu']} LU across these files — "
            "variations of one sound should usually sit within "
            f"{THRESHOLDS['variation_spread_lu']:g} LU"
        )
    return {"summary": summary, "thresholds": THRESHOLDS, "files": files}


def register(mcp: FastMCP):
    from fmod_mcp.main import client

    @mcp.tool()
    async def audio_analyze(file_paths: list[str]) -> dict:
        """Measure audio files before (or after) importing them: duration,
        sample rate, channels, peak/RMS dBFS, clipped samples, DC offset,
        leading/trailing silence, and — with ffmpeg — integrated loudness
        (LUFS), loudness range and true peak. Each file gets `flags`
        (silent, clipping, no_headroom, very_quiet, dc_offset,
        leading_silence, trailing_silence, unusual_sample_rate,
        more_than_stereo); the summary warns when variations of one sound
        differ too much in loudness. This is how to catch bad sources
        without a person listening — it cannot judge whether a sound fits.

        Args:
            file_paths: Absolute paths (1-50) to .wav/.aiff/.flac/.mp3/.ogg.
        """
        if not file_paths:
            raise FmodMCPError(ErrorCode.MISSING_PARAMETER, "file_paths is empty")
        if len(file_paths) > MAX_FILES_PER_CALL:
            raise FmodMCPError(
                ErrorCode.VALUE_OUT_OF_RANGE, f"at most {MAX_FILES_PER_CALL} files per call"
            )
        paths = [check_analysis_path(p) for p in file_paths]
        return {"success": True, "result": await analyze_files(paths)}

    @mcp.tool()
    async def event_audio_report(event_target: str) -> dict:
        """Analyze every audio file an event's instruments play (including
        playlist entries) — same measurements and flags as audio_analyze,
        plus the loudness spread across the event's variations. Use it after
        building an event to check what it will actually play.

        Args:
            event_target: event:/ path or {guid}.
        """
        r = await client.execute(
            "var e=L(p.event_target);"
            "var ss=studio.project.model.SingleSound.findInstances({searchContext:e})||[];"
            "var seen={};var out=[];"
            "for(var i=0;i<ss.length;i++){var af=null;try{af=ss[i].audioFile;}catch(__e){}"
            "if(!af||seen[af.id])continue;seen[af.id]=1;"
            "out.push({guid:G(af),assetPath:af.assetPath,abs:af.getAbsoluteAssetPath()});}"
            "return {event:P(e),assets:out,instrumentsWithoutAudio:"
            "ss.filter(function(s){var a=null;try{a=s.audioFile;}catch(__e){}return !a;}).length};",
            event_target=event_target,
        )
        res = r["result"]
        if len(res["assets"]) > MAX_FILES_PER_CALL:
            res["assets"] = res["assets"][:MAX_FILES_PER_CALL]
            res["truncated"] = True
        report = await analyze_files([a["abs"] for a in res["assets"]]) if res["assets"] else {
            "summary": {"files": 0, "flagged": 0, "loudnessSpreadLu": None},
            "thresholds": THRESHOLDS, "files": []}
        for f, a in zip(report["files"], res["assets"]):
            f["assetPath"] = a["assetPath"]
            f["assetGuid"] = a["guid"]
        report["event"] = res["event"]
        report["instrumentsWithoutAudio"] = res["instrumentsWithoutAudio"]
        return {"success": True, "result": report}
