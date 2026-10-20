# FmodStudioMCP — Core Authoring Guide

You are driving **FMOD Studio** through its JS scripting terminal — creating,
editing, and building game audio content (events, sounds, parameters, mixer,
banks). Studio applies and persists your changes to the live project.

## How content is organized

- **Events** (`event:/...`) are the playable units the game triggers. Each has
  a **timeline** with **tracks** carrying **instruments** (sounds).
- **Parameter automation** on a timeline (x = time/parameter value, y =
  property value) turns a parameter into a curve.
- **Mixer groups** aggregate channels; **buses** are output destinations;
  **VCAs** group volume controls; **snapshots** drive parameter/bus automation.
- **Banks** (`bank:/...`) are build units — the game loads banks, not events.
  An event not assigned to a bank never ships.

## Object references

Every `target` accepts either form: **path** (`event:/UI/HUD/element`,
`bank:/Master`) or **GUID** (`{aabe5118-...}`). Echo results back — tool
outputs return the same forms, chain a creation result into the next call.

## Authoring workflow

1. **Audit first** — list what exists before creating; duplication is the
   most common mistake. `event_describe` shows an event's tracks,
   instruments, parameters, markers and banks in one call.
2. **Folders before mass creation** — `folder_create("EventFolder", "UI/HUD")`,
   then `event_set_folder`.
3. **Import audio first** — `audio_import` returns an asset GUID; attach it
   with `sound_set_audio_file`.
4. **Build the event** — `event_add_track` (returns `trackGuid` AND
   `mixerGroupGuid`, different objects — use `trackGuid` for
   `sound_add_to_track`, `mixerGroupGuid` for automation/volume/effects) →
   `sound_add_to_track` (SingleSound=one file, MultiSound=weighted playlist,
   ProgrammerSound=runtime-resolved, SoundScatterer=3D randomized,
   EventSound=nested event) → `sound_set_audio_file`.
5. **Assign to a bank** — `bank_add_event`.
6. **Play it** — `event_play`/`event_stop`/`event_playback_status`. You can't
   hear the result by reading the event tree. Move parameters while it plays
   with `parameter_set_cursor`; position 3D events with
   `event_set_3d_attributes`.

**Shortcut for the common case:** `event_create_from_audio(name, files,
folder?, bank?, spatializer?, looping?)` does steps 3–5 in one call (one file
= SingleSound, several = MultiSound random playlist) and rolls back the event
if a step fails.

## Editing settings (volume, pitch, looping, effect parameters, ...)

Most of what you see in Studio's deck is a plain property. Read real names
with `utility_get_properties`/`utility_dump`, then write them with
`utility_set_properties(target, {...})` (or `sound_set_properties` /
`mixer_effect_add(..., settings=...)`). Names are checked against the live
object and every value is read back — an unknown name errors instead of
silently doing nothing. Fades: `sound_set_fade`. Variation: `modulator_add`
(e.g. RandomizerModulator on `pitch`). Links between objects:
`utility_set_relationship`. Type schemas: `utility_describe_entity`.

## Interactive / evolving music

**Vertical (parameter-driven crossfade):** each layer gets its own track +
looping instrument. Add a parameter (`parameter_add`), then
`automation_add_curve(mixerGroupGuid, "volume", "parameter:/Intensity", "parameter", [[0,-100],[0.5,-6],[1,0]])`
per layer. For a bed that changes *through* the event instead, use
`driver_type="timeline"` with an `event:/…` driver. Any automatable property
works (e.g. an effect's cutoff), not just volume.

**Parameter sheets & conditions:** `sound_add_to_track(..., parameter="Surface")`
places an instrument on a parameter sheet instead of the timeline;
`parameter_add_condition` makes an instrument/loop region/transition fire
only inside a parameter range or label. Game-wide values (TimeOfDay,
GameState) are global parameters: `parameter_add_global`, referenced as
`parameter:/Name`.

**Horizontal (section transitions):** `event_add_marker_track`, then
`marker_add_named`/`marker_add_region` for destinations,
`marker_add_transition`/`marker_add_transition_region` for jump points. A
`LoopRegion` already loops on its own (paired transition+destination marker
built in) — do NOT also add an explicit `marker_add_transition` at its end
point; that creates a conflicting logic point at the same position instead of
letting the region's own behavior work. For a *seamless* loop/transition
(crossfaded, not a hard cut) use `marker_add_transition_timeline` on the
transition marker/region/loop region — this is FMOD's real "Add Transition
Timeline" mechanism; do not try to build one by manually creating
`TransitionSourceSound`/`TransitionDestinationSound` objects without it, they
require both `audioTrack` and `parameter` relationships set to be valid.

**Snapshots** swap whole mixer states: `snapshot_create`, then
`snapshot_set_property(snapshot, strip_or_effect, "volume", -12)` per value
it should change (`snapshot_list_properties` to check, `snapshot_set_settings`
for intensity). Triggered by game code like a sound, not "built" — they ship
in banks.

**Variations:** a MultiSound's playlist is editable — `multi_list_entries`,
`multi_add_entry(audio=...)`, `multi_set_weight`, `multi_set_playlist`.

## Mixer rules

- A group's output routes to a bus/group (default Master) via
  `mixer_group_route`. Routing to a *different event's* mixer crashes Studio —
  stay within the same event/bank surface.
- Volume is dB (-80..+10); -80 effectively silences.
- `mixer_effect_add` adds built-in effects; `mixer_effect_add_plugin` adds
  plug-ins (names from `project_list_plugins`). `vca_assign` groups strips
  under a VCA.
- Organize: `bank_create(folder=...)`/`bank_set_folder` for bank folders;
  `audio_asset_move` for asset folders (moves the file on disk).

## Before concluding something isn't possible

Call `utility_dump(target)` on a real live object before saying a capability
"doesn't exist." It lists every plain property (with value) and relationship
(cardinality + count) — most of this project's tools were built this way,
since FMOD's docs only list methods, not plain data properties (e.g.
`looping`). Do NOT use FMOD's own `dump()` for this — it only logs to
Studio's own console and returns nothing to a script; an empty dump means
that limitation, not that the object has nothing on it.

## Async / save / verification discipline

- Edits apply live. `project_undo`/`project_redo` drive Studio's own
  Edit > Undo/Redo (a single tool call may be several undo steps — check the
  result before undoing more). Still validate before destructive calls
  (`utility_delete`, `event_delete`, `bank_delete`, etc.).
- `utility_validate` before building: lists events in no bank (never ship),
  events with no instruments, SingleSounds with no audio, invalid objects.
- `project_save` persists to disk explicitly — a Studio crash before save
  loses bridge edits.
- `project_build` is long-running on a big project; scope it with
  `banks=`/`platforms=` args when you only need one bank.
- **A tool returning `success: true` is not proof the result is correct** —
  some setters only confirm the JS didn't throw, not that content actually
  attached. After `sound_set_audio_file`, check `sound_info`'s
  `hasAudioFile`/`audioFileName` rather than trusting the set call alone.

## Dangers to avoid

- Empty names are invalid — set `name` immediately after creation.
- Don't guess sound types — see the list under step 4 above.
- Rerouting a child event's master track output crashes Studio.
- Keep batches modest — hundreds of objects in one call locks the editor.
