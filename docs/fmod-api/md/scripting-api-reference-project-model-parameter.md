# 26. Scripting API Reference | Project.Model.Parameter

Types:

- model.ActionSheet A sheet for an `model.Event` that plays through a playlist of instruments.

- model.GameParameter A built-in parameter or user parameter of a `model.Event`, whose input value is specified by the game.

- model.Parameter The base class for a parameter sheet upon which instruments can be placed, within an `model.Event`.

- model.ParameterPreset An object representing a parameter in your project.

- model.ParameterProxy An object containing a reference to a `model.ParameterPreset`.

- model.Timeline A parameter sheet of a `model.Event` that automatically increases its value over time.

Extension Methods:

- GameParameter.getCursorPosition Retrieves the parameter's cursor position.

- GameParameter.setCursorPosition Sets the cursor position of the global, user, or built-in parameter to a number.

- Parameter.getPlayheadPosition Retrieves the playback position of a parameter, within the context of the associated `model.Event`.

- ParameterPreset.getPath Retrieves the project's unique path identifier for the parameter.

- ParameterProxy.getCursorPosition Retrieves the parameter's cursor position.

- ParameterProxy.setCursorPosition Sets the cursor position of the parameter to a number.

- Timeline.getCursorPosition Retrieves the timeline's cursor position.

- Timeline.setCursorPosition Sets the cursor position of the timeline to a number.

## model.ActionSheet

A sheet for an model.Event that plays through a playlist of instruments.

See Also: Action Sheet

## model.GameParameter

A built-in parameter or user parameter of a model.Event, whose input value is specified by the game.

See Also: Built-in parameters, User parameters

## model.Parameter

The base class for a parameter sheet upon which instruments can be placed, within an model.Event.

See Also: Parameters Reference

## model.ParameterPreset

An object representing a parameter in your project.

See Also: Parameter

## model.ParameterProxy

An object containing a reference to a model.ParameterPreset.

## model.Timeline

A parameter sheet of a model.Event that automatically increases its value over time.

See Also: Timeline

## GameParameter.getCursorPosition

Retrieves the parameter's cursor position.

```
GameParameter.getCursorPosition()

```

Returns the cursor position of the global user parameter as a `number`. Returns `undefined` if the scope of the game parameter is not global.

Example:

```
var globalParameterPreset = studio.project.lookup("parameter:/game_state/time_of_day"); // return a ParameterPreset object
var timeOfDay = globalParameterPreset.parameter.getCursorPosition();

```

## GameParameter.setCursorPosition

Sets the cursor position of the global, user, or built-in parameter to a number.

```
GameParameter.setCursorPosition(
    position
)

```

  position The numerical position to set the parameter's cursor to.
Example:

```
var globalParameterPreset = studio.project.lookup("parameter:/game_state/time_of_day"); // return a ParameterPreset object
globalParameterPreset.parameter.setCursorPosition(1300);

```

See Also: Game Parameter

## Parameter.getPlayheadPosition

Retrieves the playback position of a parameter, within the context of the associated model.Event.

See Also: Parameter

## ParameterPreset.getPath

Retrieves the project's unique path identifier for the parameter.

```
ParameterPreset.getPath()

```

Returns the parameter's path in your project as a `string`.

See Also: Parameter

## ParameterProxy.getCursorPosition

Retrieves the parameter's cursor position.

```
ParameterProxy.getCursorPosition()

```

Returns the cursor position as a `number`, within the context of the associated event.

This is only meaningful when dealing with global parameters, since local parameters do not have meaningful cursor positions outside of specific event instances.

The equivalent of calling `parameterProxy.event.getCursorPosition(parameterProxy.preset)`.

## ParameterProxy.setCursorPosition

Sets the cursor position of the parameter to a number.

```
ParameterProxy.setCursorPosition(
    position
)

```

  position The numerical position to set the parameter proxy's cursor to.
Sets the parameter's cursor position to a `number`, within the context of the associated event.

The equivalent of calling `parameterProxy.event.setCursorPosition(parameterProxy.preset, position)`.

## Timeline.getCursorPosition()

Retrieves the timeline's cursor position.

```
Timeline.getCursorPosition()

```

Returns the cursor position as a `number`, within the context of the associated event.

The equivalent of calling `timeline.event.getCursorPosition(timeline)`.

## Timeline.setCursorPosition

Sets the cursor position of the timeline to a number.

```
Timeline.setCursorPosition(
    position
)

```

  position The numerical position to set the timeline to.
Sets the cursor position to a `number`, within the context of the associated event.

The equivalent of calling `timeline.event.setCursorPosition(timeline, position)`.

See Also: Timeline

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
