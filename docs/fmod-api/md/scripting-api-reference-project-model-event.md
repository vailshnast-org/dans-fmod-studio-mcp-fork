# 26. Scripting API Reference | Project.Model.Event

Types:

- model.Event An arrangement of instruments that can be played by the game.

- model.Snapshot An instanceable unit of changes to the project mix.

Extension Methods:

- Event.addGameParameter Adds a game parameter to the event.

- Event.addGroupTrack Adds an audio track with the given name to the event.

- Event.addMarkerTrack Adds a marker track to the event.

- Event.addReturnTrack Adds a return track with the given name to the event.

- Event.get3DAttributes Retrieves the 3D attributes of an event.

- Event.getCursorPosition Retrieves the cursor position.

- Event.getParameterPresets Retrieves an array of all the parameters in your project that are referenced by the event.

- Event.getPath Retrieves the event's unique path identifier.

- Event.getPlayheadPosition Retrieves the playback position of a given parameter.

- Event.is3D Reports whether an event is 3D.

- Event.isOneShot Reports whether an event is a one-shot.

- Event.isPaused Reports whether an event instance is paused.

- Event.isPlaying Reports whether an event instance is playing.

- Event.isRecording Reports whether an event instance is being recorded in a profiler session.

- Event.isStopping Reports whether an event instance is stopping.

- Event.keyOff Sends the keyoff command to a currently playing event instance.

- Event.returnToStart Moves the playback position to the cursor position if called while the event instance is playing, stopping, or paused, or to the start of the timeline while the event instance is stopped.

- Event.set3DAttributes Sets the 3D attributes of an event instance being auditioned based on a 3D attributes object.

- Event.setCursorPosition Sets the cursor position to a number.

- Event.stopImmediate Stops an event instance immediately, skipping the stopping event state.

- Event.stopNonImmediate Commands a playing event instance to enter the stopping event state.

- Event.togglePause Toggles the pause state of an event instance.

- Event.toggleRecording Toggles the recording state for a profiler session.

## model.Event

An arrangement of instruments that can be played by the game.

See Also: Event

## model.Snapshot

An instanceable unit of changes to the project mix.

See Also: Snapshots and the Tracks VIew

## Event.addGameParameter

Adds a game parameter to the event.

```
Event.addGameParameter(
    parameterDefinition
)

```

  parameterDefinition Either a model.ParameterPreset, a model.GameParameter, or a parameterDefinition object.
Returns the game parameter ManagedObject.

## Event.addGroupTrack

Adds an audio track with the given name to the event.

```
Event.addGroupTrack(
    name
)

```

  name The `string` value to assign the audio track when it is created.
Returns the newly created model.GroupTrack.

## Event.addMarkerTrack()

Adds a marker track to the event.

```
Event.addMarkerTrack()

```

Returns the newly created model.MarkerTrack.

See Also: Event

## Event.addReturnTrack

Adds a return track with the given name to the event.

```
Event.addReturnTrack(
    name
)

```

  name The `string` value to assign the return track when it is created.
Returns the newly created return track ManagedObject.

## Event.get3DAttributes

Retrieves the 3D attributes of an event.

```
Event.get3DAttributes()

```

Returns an object representing the currently auditioned 3D attributes of the event instance:

- `radialDistance`: Distance from the listener (`number`)

- `azimuth`: Angle of event in relation to listener (`number`)

- `height`: Vertical position of the event (`number`)

- `rotation`: The horizontal rotation of the event (`number`)

## Event.getCursorPosition

Retrieves the cursor position.

```
Event.getCursorPosition(
    parameter
)

```

  parameter The parameter to get to cursor postion of. Must be the event's model.Timeline or one of the event's model.GameParameters.
Returns the cursor position as a `number`.

## Event.getParameterPresets

Retrieves an array of all the parameters in your project that are referenced by the event.

```
Event.getParameterPresets()

```

Returns an array of all model.GameParameter objects that the event has a corresponding model.ParameterProxy for. This includes both parameters that have a parameter sheet in the event and those that do not. The order of the array matches the order displayed in the transport bar.

## Event.getPath

Retrieves the event's unique path identifier.

```
Event.getPath()

```

Returns the event's path as a `string`.

## Event.getPlayheadPosition

Retrieves the playback position of a given parameter.

```
Event.getPlayheadPosition(
    parameter
)

```

  parameter The model.Timeline or model.GameParameter to retrieve the playback position of.
Returns the playback position of a model.Parameter as a `number`.

## Event.is3D

Reports whether an event is 3D.

```
Event.is3D()

```

Returns `true` if an event is 3D. An event is considered 3D if any of these conditions are met:

 - The event has a Spatializer, 3D Object Spatializer, or a 3rd party spatializer.

 - The event contains a built-in parameter.

 - The event contains or references any other events which are 3D.

This function performs calculations that require the event be fully loaded into memory. This can be slow if triggered on a large number of events.

See Also: Spatializer Effect

## Event.isOneShot

Reports whether an event is a one-shot.

```
Event.isOneShot()

```

Returns `true` if an event is one-shot. An event is considered one-shot if it is guaranteed to terminate without intervention in bounded time after being started.

This function performs calculations that require the event be fully loaded into memory. This can be slow if triggered on a large number of events.

## Event.isPaused

Reports whether an event instance is paused.

```
Event.isPaused()

```

Returns `true` if an event instance is paused.

See Also: Event State

## Event.isPlaying

Reports whether an event instance is playing.

```
Event.isPlaying()

```

Returns `true` if an event instance is playing.

See Also: Event State

## Event.isRecording

Reports whether an event instance is being recorded in a profiler session.

```
Event.isRecording()

```

Returns `true` for profiler sessions with recording enabled.

Profiler sessions are event instances that record realtime data from the FMOD Studio system, buses, and event instances for profiling purposes.

## Event.isStopping

Reports whether an event instance is stopping.

```
Event.isStopping()

```

Returns `true` if an event instance is stopping.

This call ignores the paused event state.

## Event.keyOff

Sends the keyoff command to a currently playing event instance.

```
Event.keyOff()

```

If a sustain point exists ahead of the playback position this triggers the event instance's keyoff behavior.

## Event.returnToStart

Moves the playback position to the cursor position if called while the event instance is playing, stopping, or paused, or to the start of the timeline while the event instance is stopped.

```
Event.returnToStart()

```

Only the timeline playback position is affected by this particular function; the playback positions of other parameters are unaffected.

See Also: Event State, Cursor

## Event.set3DAttributes

Sets the 3D attributes of an event instance being auditioned based on a 3D attributes object.

```
Event.set3DAttributes(
    attributes
)

```

  attributes Object describing the 3D attributes to give to the event.
See Event.get3DAttributes for more information on the properties required for the `attributes` object.

## Event.setCursorPosition

Sets the cursor position to a number.

```
Event.setCursorPosition(
    parameter,
    position
)

```

  parameter The parameter to set the cursor postion of. Either a model.Timeline or a model.GameParameter. position The numerical value to set the cursor postion to.

## Event.stopImmediate

Stops an event instance immediately, skipping the stopping event state.

```
Event.stopImmediate()

```

See Also: Event State

## Event.stopNonImmediate()

Commands a playing event instance to enter the stopping event state.

```
Event.stopNonImmediate()

```

See Also: Event State

## Event.togglePause

Toggles the pause state of an event instance.

```
Event.togglePause()

```

The equivalent of pressing the pause button in the transport controls.

See Also: Event State

## Event.toggleRecording

Toggles the recording state for a profiler session.

```
Event.toggleRecording()

```

## Event.play

Plays the event instance.

```
Event.play()

```

The equivalent of pressing the play button in the transport controls.

See Also: Event State

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
