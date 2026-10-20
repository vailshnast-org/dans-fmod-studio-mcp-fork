# FMOD Studio 2.03 Scripting API — local copy

A snapshot of the official FMOD Studio User Manual pages this server is built against (manual version 2.03.15, downloaded 2026-10-19 from fmod.com's docs CDN). Use it to check what an API really is before writing or changing a tool. The manual lists methods but rarely plain data properties, so check those against a live object with `utility_dump`.

- `html/` — the pages exactly as downloaded.
- `md/` — the same pages converted to plain Markdown for grepping (navigation sidebar stripped).

| Page | Covers |
|------|--------|
| `scripting-api-reference-project.md` | `studio.project`: build, create, deleteObject, lookup paths, importAudioFile, exportGUIDs, enums (`parameterType`, `regionLoopMode`, ...) |
| `scripting-api-reference-project-managedobject.md` | ManagedObject / properties / relationships (add/insert/remove, cardinality) |
| `scripting-api-reference-project-entity.md` | `findInstances({searchContext, includeDerivedTypes})`, `document()` |
| `scripting-api-reference-project-workspace.md` | `addEvent`, `addGameParameter`, `addTag`, `createPlugin` |
| `scripting-api-reference-project-model-event.md` | Event: tracks, parameters, playback, cursor, 3D attributes |
| `scripting-api-reference-project-model-track.md` | GroupTrack.addSound, MarkerTrack markers/regions, addAutomationTrack |
| `scripting-api-reference-project-model-sound.md` | Instrument types, setFadeIn/OutCurve |
| `scripting-api-reference-project-model-parameter.md` | GameParameter / ParameterPreset / Timeline cursors |
| `scripting-api-reference-project-model-automatableobject.md` | addAutomator, addModulator |
| `scripting-api-reference-project-model-automator.md`, `-automationcurve.md` | Automation curves and points |
| `scripting-api-reference-project-model-modulator.md` | Modulator types |
| `scripting-api-reference-project-model-triggerable.md` | addParameterCondition |
| `scripting-api-reference-project-model-mixerstrip.md`, `-mixereffect.md` | Buses, returns, VCAs, effect chain, effect types |
| `scripting-api-reference-window.md` | navigateTo, selections, `triggerAction` + the full `window.actions` list (Undo/Redo, ...) |
| `scripting-api-reference-system.md`, `-ui.md`, `-menu.md`, `-globals.md` | Host/UI APIs (not exposed as tools) |
| `effect-reference.md`, `instrument-reference.md`, `modulator-reference.md`, `parameters-reference.md`, `plugin-reference.md`, `event-macro-controls-reference.md` | User-facing descriptions of every effect/instrument/modulator control |

© Firelight Technologies Pty Ltd. Included for offline development reference.

## Where the manual and Studio 2.03.15 disagree

These were confirmed against a running Studio while building this server. When the manual and the running Studio disagree, trust Studio:

| Manual says | Studio actually does |
|---|---|
| `AudioFile.container` relationship places an asset in a folder | No such relationship and no asset-folder entity; folders are subdirectories of `assetPath`, changed with `setAssetPath()` |
| `Asset.setAssetPath()` returns true/false | Returns `undefined`, even on success |
| `Triggerable.addParameterCondition(param, min)` — `max` optional, labels as strings | The 2-argument form throws; label strings are stored as index 0. Pass 3 arguments and label indices |
| `GroupTrack.addSound(parameter, ...)` takes "the parameter sheet" | It must be the event's `ParameterProxy` (`event.relationships.parameters`), not the `GameParameter` |
| `workspace.addGameParameter()` adds a project parameter | Creates a preset with `isGlobal: false`; set `GameParameter.isGlobal = true` for a global one |
| `MixerBusEffectChain.addEffect` accepts the listed effect strings | Correct, and `'SendEffect'` isn't one of them — create a `MixerSend` and link `mixerReturn` |
| (undocumented) | `AudioFile` has no `name`/`getPath()`; use `assetPath` and `asset:/<assetPath>` |
| (undocumented) | `model.Asset.findInstances()` returns nothing; query `AudioFile` or pass `includeDerivedTypes` |
| (undocumented) | Deleting an event leaves its parameters' `ParameterPreset`s behind |
| (undocumented) | Some errors (wrong destination entity type, `add(undefined)`) abort the whole script, so no JS `catch` runs; only an `error():` console line comes back |
