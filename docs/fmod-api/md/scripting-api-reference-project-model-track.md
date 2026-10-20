# 26. Scripting API Reference | Project.Model.Track

Types:

- model.AudioTrack The base class for tracks that can contain instruments.

- model.GroupTrack A track within an event that is associated with a mixer group.

- model.MarkerTrack A logic track containing logic markers.

Extension Methods:

- AudioTrack.addAutomationTrack Creates an automation track for a given property of an automatable object.

- GroupTrack.addSound Adds an instrument to the track on the `model.Parameter` specified.

- GroupBus.getItem Retrieves the mixer bus at the relative path specified.

- MarkerTrack.addNamedMarker Adds a destination marker to the marker track at the given position.

- MarkerTrack.addRegion Adds a destination region to the marker track at the given position with the given length.

- MarkerTrack.addSustainPoint Adds a sustain point to the track at the given position.

- MarkerTrack.addTransitionMarker Adds a transition marker to the track at the given position.

- MarkerTrack.addTransitionRegion Adds a transition region to the track at the given position with the given length.

## model.AudioTrack

The base class for tracks that can contain instruments.

See Also: model.Sound

## model.GroupTrack

A track within an event that is associated with a mixer group.

See Also: model.Event, model.MixerGroup

## model.MarkerTrack

A logic track containing logic markers.

## AudioTrack.addAutomationTrack

Creates an automation track for a given property of an automatable object.

```
AudioTrack.addAutomationTrack(
    automatableObject,
    propertyName
)

```

  automatableObject Any model.AutomatableObject of the track such as a model.Sound, a model.MixerEffect, or the model.MixerBus of the track itself. propertyName Any valid automatable property of the specified model.AutomatableObject.
Returns the automation track ManagedObject.

Automation can be present even if the automation track is hidden.

Example:

```
// adds an automation track for a master track's volume
var event = studio.project.workspace.addEvent("New Event", true);
var masterTrack = event.masterTrack;
var automationTrack = masterTrack.addAutomationTrack(masterTrack.mixerGroup, "volume");

// adds an automation track for a gain effect's gain
var gainEffect = masterTrack.mixerGroup.effectChain.addEffect("GainEffect");
var automationTrack2 = masterTrack.addAutomationTrack(gainEffect, "gain");

```

See Also: Tracks

## GroupTrack.addSound

Adds an instrument to the track on the model.Parameter specified.

```
GroupTrack.addSound(
    parameter,
    soundType,
    start,
    length
)

```

  parameter The parameter sheet to add the sound to. soundType The type of the model.Sound. Must be model.SingleSound, model.MultiSound, or model.ProgrammerSound. start The numerical position of the new model.Sound. The value must be within the parameter's range. length The numerical length of the new model.Sound.
Returns the model.Sound ManagedObject.

See Also: Tracks

## GroupBus.getItem

Retrieves the mixer bus at the relative path specified.

```
GroupBus.getItem(
    path
)

```

  path Relative path of the entity to get the model.MixerBus of.
Returns the model.MixerBus at the relative `path` specified. Returns `undefined` if the bus cannot be found.

Example:

```
var bus = studio.project.workspace.mixer.masterBus.getItem("sfx/player");

```

## MarkerTrack.addNamedMarker

Adds a destination marker to the marker track at the given position.

```
MarkerTrack.addNamedMarker(
    name,
    position
)

```

  name The `string` value to assign the marker when created. position The numerical position to place marker.
Returns the named marker ManagedObject.

## MarkerTrack.addRegion

Adds a destination region to the marker track at the given position with the given length.

```
MarkerTrack.addRegion(
    position,
    length,
    name,
    loopMode
)

```

  start The numerical start position of the new region. length The numerical length of the new region. name The `string` value to assign the new region. loopMode A number representing the region's loop mode. Defaults to `project.regionLoopMode.Looping` if `loopMode` is `undefined`. The loop mode can be set by passing in a valid `loopMode` argument, as described by the Project.regionLoopMode enum.
Returns the newly created region's ManagedObject.

## MarkerTrack.addSustainPoint

Adds a sustain point to the track at the given position.

```
MarkerTrack.addSustainPoint(
    position
)

```

  position The numerical position to place the new sustain point at.
Returns the `SustainPoint` ManagedObject.

## MarkerTrack.addTransitionMarker

Adds a transition marker to the track at the given position.

```
MarkerTrack.addTransitionMarker(
    position,
    destination
)

```

  position The numerical position to place the new transition marker at. destination A ManagedObject of type `NamedMarker` or `LoopRegion`.
Returns the newly created `TransitionMarker` ManagedObject.

## MarkerTrack.addTransitionRegion

Adds a transition region to the track at the given position with the given length.

```
MarkerTrack.addTransitionRegion(
    position,
    length,
    destination
)

```

  position The numerical position to place the new transition region at. length The numerical length of the new transition region. destination Either a `NamedMarker` or a `LoopRegion`.
Returns the `TransitionRegion` ManagedObject.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
