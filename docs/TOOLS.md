# Tools Reference

Every tool in FmodStudioMCP, grouped by module. All tools run in the **live** project — call `project_save` when you want it on disk.

## Conventions

- **References:** paths (`event:/UI/Hover`, `bank:/Master`) or `{guid}`. Echoed results chain straight into the next call.
- **`execute_long`** operations (bank build, audio import) wait up to 600 s.
- **All list tools are capped** (see `constants.py`).

## Studio control & headless builds (`studio_tools.py`)

Run on the MCP host, so they work while Studio is closed. Executables come from `FMOD_STUDIO_EXE` / `FMOD_STUDIO_CL` or the usual install folders, never from arguments; the default project is `FMOD_STUDIO_PROJECT`.

| Tool | Signature | What it does |
|------|-----------|--------------|
| `studio_status` | `()` | Install found, process running, Script Server reachable, open project, unsaved changes, Script Server preference, default project. |
| `studio_launch` | `(project_path?, wait_seconds?, enable_script_server?)` | Start Studio on a project and wait for its Script Server. Turns on the Script Server preference (only while Studio is closed). Refuses if another project is open. |
| `studio_quit` | `(save?)` | Save (default) and close Studio; refuses to quit with unsaved changes when `save=false`. |
| `headless_build` | `(project_path?, banks?, platforms?, export_guids?)` | **long** — build with `fmodstudiocl` (no GUI): success, warning/error lines, every bank/GUIDs file written. Refuses if Studio has the project open. |
| `headless_validate` | `(project_path?)` | **long** — FMOD's own project diagnostic (dangling objects, cyclical references). |

## Analysis (`analysis_tools.py`) — measuring instead of listening

Needs nothing for PCM WAV; with `ffmpeg` on PATH (or `FFMPEG_PATH`) handles every format and adds EBU R128 loudness.

| Tool | Signature | What it does |
|------|-----------|--------------|
| `audio_analyze` | `(file_paths)` | Duration, rate, channels, peak/RMS dBFS, clipped samples, DC offset, leading/trailing silence, integrated LUFS, loudness range, true peak; `flags` per file and a loudness-spread warning across files. |
| `event_audio_report` | `(event_target)` | The same for every file an event plays (playlist entries included), plus instruments without audio. |

## Project (`project_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `project_get_info` | `()` | Open project's `.fspro` file path + display name. |
| `project_save` | `()` | Save the project. |
| `project_save_all` | `()` | Save project + every edited file (assets, banks, plugins). |
| `project_build` | `(banks?, platforms?)` | **long** — build inside Studio, optionally scoped; returns a report: `built`, every bank/GUIDs file written (size) and warning/error lines Studio logged during the build. |
| `project_get_modified` | `()` | Whether the project has unsaved changes. |
| `project_undo` | `(steps?)` | Studio's Edit > Undo (1–20 steps), via `studio.window.triggerAction`. |
| `project_redo` | `(steps?)` | Studio's Edit > Redo (1–20 steps). |
| `project_trigger_action` | `(window_action)` | Run a non-destructive Studio menu action: `RefreshModifiedAssets`, `ValidateProject`, `ExportGuids`, `ZoomToFit`, `ToggleTransitionTimelineVisibility`, `ShowLogicTracks`. |
| `project_export_guids` | `()` | Export GUIDs.txt for game code. |
| `project_list_plugins` | `()` | Plug-in effects/instruments available to this Studio install. |
| `project_get_version` | `()` | Running Studio version + OS. |

## Events (`event_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `event_create` | `(name, folder?, spatializer?)` | Create an event (optionally under an `event:/…` folder); `spatializer=True/False` picks 3D/2D via `workspace.addEvent`. |
| `event_delete` | `(target)` | Delete an event. |
| `event_info` | `(target)` | guid/name/path, maxVoices, is3D, isOneShot, assigned banks. |
| `event_set_settings` | `(target, max_instances?, voice_stealing?, priority?, cooldown_s?, persistent?, min_distance?, max_distance?, doppler?, doppler_scale?)` | Event macros in one call (stealing: oldest/furthest/quietest/virtualize/none). |
| `event_get_settings` | `(target)` | Read the event macros. |
| `event_lint` | `(target)` | Static "will it make sound?" check: errors (no instruments, no audio, zero length, empty playlist, broken nested event) and warnings (-80 dB, 0 % trigger, sustain point without loop+async, no bank, default name). |
| `tag_add` / `tag_remove` | `(target, tag)` | Tag/untag an event (tag created on first use). |
| `tag_list` | `(tag?)` | Tags with counts, or every object with one tag. |
| `event_describe` | `(target)` | One-call overview: tracks (with instruments), parameters, marker tracks + markers, banks. |
| `event_list` | `()` | List every event (capped). |
| `event_lookup` | `(target)` | Resolve to canonical path + guid. |
| `event_set_name` | `(target, name)` | Rename. |
| `event_set_folder` | `(target, folder)` | Move into a folder / to the root. |
| `event_add_track` | `(target, name?)` | Add a group (audio) track. Returns `trackGuid` (for `sound_add_to_track`) and `mixerGroupGuid` (for `automation_add_curve`/`mixer_group_volume`/`mixer_effect_add`) — different objects, don't mix them up. |
| `event_list_tracks` | `(target, include_master?)` | List group tracks (+ master), each with `trackGuid` and `mixerGroupGuid`. |
| `event_set_max_voices` | `(target, max_voices)` | Cap simultaneous instances (1–1000). |
| `event_timeline_cursor` | `(target, position)` | Scrub the timeline cursor (seconds). |

## Audition (`audition_tools.py`) — hear the result, don't just read the event tree

| Tool | Signature | What it does |
|------|-----------|--------------|
| `event_play` | `(target)` | Play an event instance. |
| `event_stop` | `(target, immediate?)` | Stop a playing instance (immediate, or let release/tails finish). |
| `event_toggle_pause` | `(target)` | Toggle pause on a playing instance. |
| `event_key_off` | `(target)` | Send keyoff (releases a pending sustain point). |
| `event_return_to_start` | `(target)` | Return playback to the cursor/timeline start. |
| `event_playback_status` | `(target)` | isPlaying/isPaused/isStopping + playhead position. |
| `event_set_3d_attributes` | `(target, radial_distance, azimuth?, height?, rotation?)` | Position the auditioned event relative to the listener (hear attenuation/panning). |

## Markers (`marker_tools.py`) — timeline logic markers for interactive music

| Tool | Signature | What it does |
|------|-----------|--------------|
| `event_add_marker_track` | `(target)` | Add a marker (logic) track — required once before placing markers. |
| `marker_add_named` | `(track_target, name, position)` | Add a named destination marker. |
| `marker_add_region` | `(track_target, name, position, length, loop_mode?)` | Add a destination (loop) region. |
| `marker_add_sustain_point` | `(track_target, position)` | Add a sustain point (holds until `event_key_off`). |
| `marker_add_transition` | `(track_target, position, destination_target)` | Add a transition marker (jumps to a NamedMarker/LoopRegion). |
| `marker_add_transition_region` | `(track_target, position, length, destination_target)` | Add a transition region. |
| `marker_list` | `(track_target)` | List a track's markers/regions/transitions, tagged by type (capped). |
| `marker_rename` | `(target, name)` | Rename a marker/region. |
| `marker_set_position` | `(target, position)` | Move a point-type marker. |
| `marker_set_region` | `(target, position, length)` | Move/resize a region-type marker. |
| `marker_delete` | `(target)` | Delete a marker/region (**destructive**, backed up). |
| `marker_add_tempo` | `(track_target, position, bpm, beats_per_bar?, beat_unit?)` | Tempo marker — the bars/beats quantized transitions and instruments snap to. |
| `marker_add_transition_timeline` | `(transition_target, audio_track_target, crossfade_length?)` | Add a crossfaded transition timeline (source+destination sound pair) to a transition marker/region/loop/magnet region — FMOD's "Add Transition Timeline" feature, the professional seamless-loop technique instead of a hard cut. Structurally verified; audition the actual blend in Studio. |

## Sounds (`sound_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `audio_import` | `(file_path)` | **long** — import a .wav/.aiff/.flac/.mp3/.ogg as an asset; returns `{guid}`. |
| `audio_assets` | `(folder?, unused_only?)` | List audio assets (capped): asset path, length, channels, sample rate, streaming, instrument count. Filter by Assets subfolder or to unused assets. |
| `sound_add_to_track` | `(event_target, track_target, sound_type, start, length?, name?, parameter?, audio?)` | Place an instrument on a track — on the timeline, or on a parameter sheet with `parameter`. Needs `length` > 0, or `audio` to assign a file and size the region to it. |
| `sound_add_nested_event` | `(event_target, track_target, referenced_event, start?, length?, parameter?)` | Event instrument that plays another event/snapshot. |
| `sound_create` | `(sound_type, name?)` | Stand-alone instrument (e.g. for a Multi's playlist). |
| `sound_set_audio_file` | `(target, audio)` | Assign an imported asset to an instrument. |
| `sound_set_owner` | `(target, owner)` | Nest instruments (SingleSound into a Multi or a Scatterer's playlist). |
| `sound_set_name` | `(target, name)` | Rename an instrument. |
| `sound_info` | `(target)` | Instrument guid/name/path + hasAudioFile/audioFileName. |
| `sound_set_properties` | `(target, volume?, pitch?, looping?, is_async?, start?, length?, extra?)` | Instrument playback properties and trigger-region position/size (validated + read back). |
| `sound_set_fade` | `(target, fade_in?, fade_out?, curve?)` | Instrument fade-in/out (`setFadeInCurve`/`setFadeOutCurve`). |
| `event_list_sounds` | `(event_target)` | Every instrument in an event: type, start/length, audio file, owner. |
| `audio_import_batch` | `(file_paths)` | **long** — import up to 100 files; all validated before any import. |
| `sound_add_plugin` | `(event_target, track_target, plugin, start?, length?, parameter?)` | Place a plug-in instrument (e.g. AudioGaming AudioRain). |
| `multi_list_entries` | `(target)` | A MultiSound's playlist entries (audio, play %) + playlist settings. |
| `multi_add_entry` | `(target, audio?, sound_type?)` | Add a playlist entry (SingleSound with an asset, Programmer, Silence, nested Multi). |
| `multi_remove_entry` | `(entry)` | Delete one playlist entry. |
| `multi_set_weight` | `(entry, percentage)` | Set an entry's play percentage (0–100). |
| `multi_set_playlist` | `(target, playlist_mode?, playback_mode?, looping?, play_count?)` | Playlist behavior (modes are Studio's numeric enums; 0 = default). |
| `event_create_from_audio` | `(name, file_paths, folder?, bank?, spatializer?, looping?)` | **long** — import audio and build a playable event in one call (1 file = SingleSound, more = MultiSound playlist); rolls the event back on failure. |

## Assets (`asset_tools.py`)

Asset "folders" are subdirectories of each asset's `assetPath` (2.03 has no asset-folder object). Assets are referenced by `{guid}` or `asset:/<assetPath>`.

| Tool | Signature | What it does |
|------|-----------|--------------|
| `audio_asset_info` | `(target)` | Asset path, absolute file path, length, channels, sample rate, streaming, instruments using it. |
| `audio_asset_move` | `(target, new_path)` | Move/rename an asset inside Assets — **moves the file on disk**; refuses to change the extension or overwrite. |
| `encoding_get` | `(targets?, folder?, platform?)` | Platform default compression and, per asset, override + effective setting. |
| `encoding_set` | `(format?, quality?, sample_rate_mode?, sample_rate?, streaming?, targets?, folder?, platform?)` | Set the platform default, or per-asset overrides for given assets / an Assets folder. Formats: pcm, fadpcm, xma, vorbis, at9, opus; rate modes: fixed, optimize, preserve. |
| `encoding_clear` | `(targets?, folder?, platform?)` | Remove per-asset overrides. |

## Parameters (`parameter_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `parameter_add` | `(event_target, name, param_type?, min?, max?, labels?)` | Add a game parameter (all 11 `parameterType`s: User, UserDiscrete, UserEnumeration, Distance, DistanceNormalized, Direction, Elevation, EventConeAngle, EventOrientation, Speed, SpeedAbsolute). |
| `parameter_add_global` | `(name, param_type?, min?, max?, labels?)` | Add a project-level parameter, referenced as `parameter:/Name`. |
| `parameter_set_cursor` | `(event_target, parameter, value)` | Move a parameter while auditioning (hear layers/transitions react). |
| `parameter_add_condition` | `(target, parameter, min, max?, event_target?)` | Trigger condition on an instrument/LoopRegion/TransitionMarker/TransitionRegion (range or label). |
| `parameter_list` | `(event_target)` | List an event's parameters. |
| `parameter_set_initial` | `(event_target, parameter_name, value)` | Set the initial value. |
| `parameter_set_labels` | `(event_target, parameter_name, labels)` | Set enumeration labels on a UserEnumeration. |

## Banks (`bank_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `bank_create` | `(name, folder?)` | Create a bank, optionally inside a bank folder (created if missing). |
| `bank_set_folder` | `(target, folder)` | Move a bank into a bank folder (`""` = root); its `bank:/` path changes accordingly. |
| `bank_list` | `()` | List every bank (capped). |
| `bank_info` | `(target)` | guid/name/path. |
| `bank_rename` | `(target, name)` | Rename. |
| `bank_delete` | `(target)` | Delete a bank + contents. |
| `bank_add_event` | `(bank_target, event_target)` | Assign an event to a bank. |
| `bank_remove_event` | `(bank_target, event_target)` | Remove an event from a bank. |
| `bank_list_events` | `(bank_target)` | Events assigned to the bank (capped). |

## Mixer (`mixer_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `mixer_group_create` | `(name, output_target?)` | Create a group (now explicitly routed to Master when no output is given). |
| `mixer_group_list` | `()` | List mixer groups (capped). |
| `mixer_group_info` | `(target)` | guid/name/path/volume. |
| `mixer_group_rename` | `(target, name)` | Rename. |
| `mixer_group_delete` | `(target)` | Delete a group. |
| `mixer_group_route` | `(target, output_target)` | Set a group's output bus/group; with an event as the target, routes the whole event (its MixerInput). Verified. |
| `mixer_group_volume` | `(target, db)` | Volume in dB (-80…+10). |
| `mixer_effect_add` | `(target, effect, settings?)` | Add an effect (e.g. `CompressorEffect`, `LimiterEffect`), optionally configuring it in the same call. |
| `mixer_effect_add_plugin` | `(target, plugin, settings?)` | Add a plug-in effect (Steam Audio, Resonance, …) from `project_list_plugins`. |
| `mixer_effect_remove` | `(target, effect)` | Remove + delete an effect from a chain (refuses the built-in fader/panner). |
| `mixer_effect_list` | `(target)` | List effects on a group's chain (tagged with `entity` type — includes built-in `MixerBusFader`/`MixerBusPanner` alongside any effects added). |
| `mixer_master_info` | `()` | Master bus guid/name/volume. |
| `mixer_master_volume` | `(db)` | Set master volume in dB. |
| `vca_create` | `(name)` | Create a VCA (scales every strip assigned to it). |
| `vca_list` | `()` | List every VCA (capped). |
| `vca_info` | `(target)` | guid/name/volume. |
| `vca_volume` | `(target, db)` | Set a VCA's volume in dB. |
| `vca_assign` | `(vca_target, strip_target)` | Assign a mixer strip to a VCA (strip `masters` relationship, verified). |
| `vca_unassign` | `(vca_target, strip_target)` | Remove a strip from a VCA. |
| `vca_list_strips` | `(vca_target)` | Strips assigned to a VCA. |
| `mixer_send_create` | `(event_target, source_group_target, return_name, level_db?)` | Create a return track + send within one event's mixer. Send link verified by read-back. |
| `mixer_return_create` | `(name, output_target?)` | Create a project-level return bus (shared reverb etc.). |
| `mixer_send_add` | `(source_group_target, return_target, level_db?)` | Send from any group/track to a return bus, verified by read-back. |

## Automation (`automation_tools.py`) — the heart of evolving/interactive music

| Tool | Signature | What it does |
|------|-----------|--------------|
| `automation_add_curve` | `(target, property, driver, driver_type, points)` | Bind a property to a curve; as the driver moves, the property follows. |
| `automation_add` | `(target, property, driver, driver_type, position, value)` | Add one point to an existing curve. |
| `automation_list` | `(target, property?)` | Every curve on a target's automator: guid, driver, sorted points, and `pointDetails` (point guid, curveShape, isSCurve). |
| `automation_set_point` | `(point, position?, value?, curve_shape?, s_curve?)` | Move/edit one point or shape the segment after it. |
| `automation_remove_point` | `(curve, position, tolerance?)` | Remove the point at a position. |
| `automation_delete_curve` | `(curve)` | Delete a whole curve. |
| `automation_show_track` | `(event_target, target, property?)` | Show the automation as a lane under its track in the event editor. |

- `property` = `volume` | `pitch` | `gain`, or any other automatable property
  of the target (e.g. an effect's cutoff — checked to exist on the live
  object first). `target` is the automated object (mixer group, bus, VCA,
  event, effect).
- `driver_type="parameter"` → `driver` is `parameter:/Intensity`; points are
  `[parameterValue, mappedValue]`.
- `driver_type="timeline"` → `driver` is `event:/…`; points are `[seconds, value]`.

**Vertical layering example** — three music layers crossfading with an
"Intensity" game parameter:

```
parameter_add "event:/Music/CombatDrums" params...
automation_add_curve "group:/Music/Drums" "volume" "parameter:/Intensity" "parameter" [[0,-100],[0.4,-6],[1,0]]
automation_add_curve "group:/Music/Pads"   "volume" "parameter:/Intensity" "parameter" [[0,0],[0.6,-6],[1,-80]]
```

## Modulators (`modulator_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `modulator_add` | `(target, modulator_type, property, settings?)` | `RandomizerModulator` / `ADSRModulator` / `SidechainModulator` / `AutopitchModulator` on one property (e.g. random `pitch` on footsteps). |
| `modulator_list` | `(target)` | Modulators under an instrument/event with their settings. |

## Snapshots (`snapshot_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `snapshot_create` | `(name)` | Create a mixer snapshot. |
| `snapshot_list` | `()` | List every snapshot (capped). |
| `snapshot_info` | `(target)` | guid/name/path. |
| `snapshot_rename` | `(target, name)` | Rename. |
| `snapshot_delete` | `(target)` | Delete a snapshot. |
| `snapshot_bind_group` | `(snapshot_target, group_target)` | Scope a mixer strip into a snapshot (creates/reuses its snapshot track). |
| `snapshot_set_property` | `(snapshot_target, target, property, value)` | Capture a value in the snapshot (e.g. a group's volume at -12 dB); strips are scoped automatically. |
| `snapshot_list_properties` | `(snapshot_target)` | Scoped strips + every captured value, intensity, behavior. |
| `snapshot_remove_property` | `(snapshot_target, target, property)` | Stop the snapshot changing a property. |
| `snapshot_set_settings` | `(snapshot_target, intensity?, behavior?)` | Intensity 0–100, behavior 0 (Overriding, default) / 1 (Blending). |

Snapshots are activated by the game like a sound (they ship in banks); the
authoring side here creates and organises them.

## Folders (`folder_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `folder_create` | `(kind, path)` | Find-or-create a folder chain (`"UI/HUD"`); kind = `EventFolder`/`BankFolder`. `AssetFolder` doesn't exist in 2.03 (asset folders are asset-path subdirectories — use `audio_asset_move`). |
| `folder_list` | `(kind?)` | List folders (optionally filtered by kind). |

## Workspace (`workspace_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `workspace_info` | `()` | Roots: event/asset/bank folders + master bus. |
| `workspace_browser_current` | `()` | Object selected in the project browser. |
| `workspace_navigate` | `(target)` | Open the object in its editor. |
| `workspace_editor_selection` | `()` | Object selected in the open editor. |

## Utility (`utility_tools.py`)

| Tool | Signature | What it does |
|------|-----------|--------------|
| `utility_lookup` | `(target)` | Resolve any object to guid/name/path. |
| `utility_list` | `(obj_type, include_derived?, within?)` | List any model entity type (capped), optionally with derived types / inside one object. |
| `utility_is_valid` | `(target)` | Whether the object is valid. |
| `utility_delete` | `(target)` | Delete any object (**destructive**). |
| `utility_dump` | `(target)` | Real introspection: every plain settable property (with value) + every relationship (cardinality + count). **Use this before concluding a capability doesn't exist** — FMOD's own `dump()` only logs to Studio's own console, invisible to this bridge, and is not what this tool calls. |
| `utility_validate` | `()` | Audit: events in no bank, events with no instruments, SingleSounds without audio, invalid objects. |
| `utility_get_properties` | `(target)` | Every plain property → value. |
| `utility_set_properties` | `(target, properties)` | Set any plain properties; names checked against the live object, types matched, values read back (`clamped` lists adjusted ones). |
| `utility_set_relationship` | `(target, relationship, destination, action?)` | Add/remove a relationship destination, verified by read-back. |
| `utility_describe_entity` | `(entity)` | A model type's schema via `entity.document()`. |