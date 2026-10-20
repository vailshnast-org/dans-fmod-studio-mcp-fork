# 26. Scripting API Reference | Project.Workspace

The root workspace ManagedObject of the project.

Methods:

- workspace.addEvent Adds an event with the given name to the project.

- workspace.addGameParameter Adds a parameter to the project.

- workspace.addTag Adds a tag with the given name to the project.

- workspace.createPlugin Creates either a plug-in effect or a plug-in instrument.

## workspace.addEvent

Adds an event with the given name to the project.

```
workspace.addEvent(
    name,
    withSpatializer
)

```

  name The `string` value to assign the new event. withSpatializer A `bool` value determining whether to add an FMOD spatializer to the new event's master track.
Returns the event's ManagedObject.

The `withSpatializer` argument should be `true` if a spatializer on the master track is desired and `false` otherwise.

## workspace.addGameParameter

Adds a parameter to the project.

```
workspace.addGameParameter(
    parameterDefinition
)

```

  parameterDefinition The object describing the parameter to add.
Returns the parameter ManagedObject.

The properties of the `parameterDefinition` object match those of the object given as an argument to the Event.addGameParameter function.

## workspace.addTag

Adds a tag with the given name to the project.

```
workspace.addTag(
    name
)

```

  name name of tag to add.
Returns the tag ManagedObject.

If the tag already exists in the project, the existing tag is returned instead.

## workspace.createPlugin

Creates either a plug-in effect or a plug-in instrument.

```
workspace.createPlugin(
    identfier
)

```

  identifier The plug-in to use for the creation. This must match the name of an FMOD_DSP_DESCRIPTION.
Returns the plug-in effect or plug-in instrument ManagedObject.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
