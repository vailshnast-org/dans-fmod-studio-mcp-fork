# 26. Scripting API Reference | Project

The `studio.project` module provides access to objects within the project model.

Methods:

- project.build Builds all the banks to all the platforms listed in the build tab of the preferences dialog.

- project.create Returns a new instance of a `ManagedObject` of the given entity name.

- project.deleteObject Deletes the `ManagedObject` and its references, if any, from the project.

- project.exportGUIDs Exports project "guids.txt".

- project.findAvailablePlugins Returns an array of strings that lists all available plugins.

- project.importAudioFile Imports an audio asset into the project.

- project.lookup Lookup a `ManagedObject` by path or GUID.

- project.save Saves the project.

Callbacks:

- project.audioFileImportedConnect Sets a function to be called when an audio file is imported, with the signature `function(audioFile)`.

- project.audioFileImportedDisconnect Disconnects the `connectFunction` once it is no longer needed.

- project.buildEndedConnect Sets a function to be called after banks are built, with the signature `function(success)`.

- project.buildEndedDisconnect Disconnects the `connectFunction` once it is no longer needed.

- project.buildStartedConnect Sets a function to be called before banks are built, with the signature `function()`.

- project.buildStartedDisconnect Disconnects the `connectFunction` once it is no longer needed.

Properties:

- project.filepath The absolute path to the project's ".fspro` file on disk.

Types:

- project.distanceRolloffType An enum corresponding to different distance attenuation roll-off types available to spatial effects.

- project.parameterType An enum corresponding to different `model.Parameter` types available.

- project.regionLoopMode An enum corresponding to different loop modes of a loop region.

- parameterDefinition Describes a `model.Parameter`.

## project.build

Builds all the banks to all the platforms listed in the build tab of the preferences dialog.

```
project.build();

project.build(
    build_options
)

```

  build_options Builds the project with options object `{ banks, platforms }`.
Returns `true` if the operation succeeds, or `false` otherwise. Building individual banks also builds and updates your project's master banks and master bank strings files.

Example:

```
// Single banks
    studio.project.build({ banks: 'Weapons' }); // Build the "Weapons" bank to all platforms
    studio.project.build({ banks: 'Music', platforms: ['Desktop', 'PlayStation 4'] }); // Build the "Music" bank for only the "Desktop" and "PlayStation 4" platforms

// Multiple banks
    studio.project.build({ banks: ['Weapons', 'Characters'], platforms: 'Desktop' }); // Build the "Weapons" and "Characters" banks only for the "Desktop" platform
    studio.project.build({ banks: ['Weapons', 'Music'], platforms: ['Desktop', 'PlayStation 4'] }); // Build the "Weapons" and "Music" banks to the "Desktop" and "PlayStation 4" platforms

// Platforms
    studio.project.build({ platforms: 'Desktop' }); // Builds all banks for the "Desktop" platform
    studio.project.build({ platforms: ['Desktop', 'PlayStation 4'] }); // Builds all banks for the "Desktop" and "PlayStation 4" platforms

```

## project.create

Returns a new instance of a ManagedObject of the given entity name.

```
project.create(
    entityName
)

```

  entityName The name of the entity to create.
This will create any required child objects for the object (e.g. creating an `Event` will create and attach its `EventMixer`).

## project.deleteObject

Deletes the ManagedObject and its references, if any, from the project.

```
project.deleteObject(
    managedObject
)

```

  managedObject The managed object to delete.
Returns `true` if the operation succeeds, or `false` otherwise.

 This is the equivalent to deleting an item in the user interface.

## project.exportGUIDs

Exports project "guids.txt".

```
project.exportGUIDs()

```

Returns `true` if the operation succeeds, or `false` otherwise.

## project.findAvailablePlugins

Returns an array of strings that lists all available plugins.

```
project.findAvailablePlugins()

```

## project.importAudioFile

Imports an audio asset into the project.

```
project.importAudioFile(
    filePath
)

```

  filePath The absolute path to the file's location.
Returns an model.AudioFile, ManagedObject, or `null` if importing failed. The file is always imported into the root audio bin folder. Use the `AudioFile.container` relationship to reassign it to another folder.

## project.lookup

Lookup a ManagedObject by path or GUID.

```
project.lookup(
    idOrPath
)

```

  idOrPath GUID or path of the ManageObject.
Returns a ManagedObject found by GUID or path.

Example:

```
var item = project.lookup("{3a731ab3-ce6d-453d-862e-32050cecf68a}");
var event = project.lookup("event:/path/to/eventname");
var eventFolder = project.lookup("event:/path/to/foldername");
var bank = project.lookup("bank:/path/to/bank");
var snapshot = project.lookup("snapshot:/snapshotname");
var vca = project.lookup("vca:/vcaname");

```

Paths are formatted using the pattern `type:/path/to/item`, where `type` is one of:

- `event`

- `snapshot`

- `bank`

- `bus`

- `vca`

- `asset`

- `parameter`

- `effect`

- `tag`

- `profilersession`

Paths can also be used to find container items, such as finding a folder in the event hierarchy.

## project.save

Saves the project.

```
project.save()

project.save(
    filepath
)

```

Returns `true` if the operation succeeds, or `false` otherwise.

## project.audioFileImportedConnect

Sets a function to be called when an audio file is imported, with the signature `function(audioFile)`.

The `audioFile` argument is a model.AudioFile object.

```
project.audioFileImportedConnect(
    callback
)

```

  callback A callback function that will be called when an audio file import has completed.

## project.audioFileImportedDisconnect

Disconnects the `connectFunction` once it is no longer needed.

It is important to disconnect the connected signals when they are no longer needed, otherwise they can accumulate and cause unexpected behavior.

```
project.audioFileImportedDisconnect(
    connectFunction
)

```

  connectionFunction The callback to disconnect from audio file imported notification.

## project.buildEndedConnect

Sets a function to be called after banks are built, with the signature `function(success)`.

The `success` argument will be `false` if a build error occurs or the build is cancelled by the user, and `true` otherwise.

```
project.buildEndedConnect(
    callback
)

```

  callback A callback function that will be called when the build has ended.
Example:

```
function buildEnd() {
    alert("Build about to end");
}

studio.project.buildEndedConnect(buildEnd);

```

## project.buildEndedDisconnect

Disconnects the `connectFunction` once it is no longer needed.

It is important to disconnect the connected signals when they are no longer needed, otherwise they can accumulate and cause unexpected behavior.

```
project.buildEndedDisconnect(
    connectFunction
)

```

  connectionFunction The callback to disconnect from build ended notification.
Example:

```
function buildEnd() {
    alert("Build about to end");
}

studio.project.buildEndedDisconnect(buildEnd);

```

## project.buildStartedConnect

Sets a function to be called before banks are built, with the signature `function()`.

```
project.buildStartedConnect(
    callback
)

```

  callback A callback function that will be called when the build has started.
Example:

```
function buildStart() {
    alert("Build about to start");
};

studio.project.buildStartedConnect(buildStart);

```

## project.buildStartedDisconnect

Disconnects the `connectFunction` once it is no longer needed.

It is important to disconnect the connected signals when they are no longer needed, otherwise they can accumulate and cause unexpected behavior.

```
project.buildStartedDisconnect(
    connectFunction
)

```

  connectionFunction The callback to disconnect from build started notification.
Example:

```
function buildStart() {
    alert("Build about to start");
};

studio.project.buildStartedDisconnect(buildStart);

```

## project.filePath

The absolute path to the project's ".fspro` file on disk.

## project.distanceRolloffType

An enum corresponding to different distance attenuation roll-off types available to spatial effects.

```
distanceRolloffType: {
    LinearSquared: 0,
    Linear: 1,
    Inverse: 2,
    InverseTapered: 3,
    Custom: 4,
}

```

## project.parameterType

An enum corresponding to different model.Parameter types available.

```
parameterType: {
    Invalid: -1,
    User: 0,
    UserDiscrete: 1,
    UserEnumeration: 2,
    Distance: 3,
    Direction: 4,
    Elevation: 5,
    EventConeAngle: 6,
    EventOrientation: 7,
    Speed: 8,
    SpeedAbsolute: 9,
    DistanceNormalized: 10
}

```

## project.regionLoopMode

An enum corresponding to different loop modes of a loop region.

```
regionLoopMode: {
    None: 0,
    Looping: 1,
    Magnet: 2
}

```

## parameterDefinition

Describes a model.Parameter.

```
    name: [string],
    type: [number],
    min: [number],
    max: [number],
    enumerationLabels: [array]

```

  name The name of the parameter. type The project.parameterType of the parameter. min The minimum value of the parameter range. max The maximum value of the parameter range. enumerationLabels A string array of labels to apply to each index of the parameter. (Type UserEnumeration only).
See Also: Event.addGameParamater, workspace.addGameParameter

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
