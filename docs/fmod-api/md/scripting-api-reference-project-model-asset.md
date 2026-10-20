# 26. Scripting API Reference | Project.Model.Asset

Types:

- model.Asset The base class representation for a file asset's metadata.

- model.AudioFile An audio file asset containing sound data.

Extension Methods:

- Asset.getAbsoluteAssetPath Retrieves the absolute path of the file the asset refers to.

- Asset.getAssetPath Retrieves the path of the file the asset refers to, relative to the project assets directory.

- Asset.setAssetPath Sets the path of the file the asset refers to, relative to the project assets directory.

## model.Asset

The base class representation for a file asset's metadata.

## model.AudioFile

An audio file asset containing sound data.

See Also: Audio File, studio.project.importAudioFile.

## Asset.getAbsoluteAssetPath

Retrieves the absolute path of the file the asset refers to.

```
Asset.getAbsoluteAssetPath()

```

Returns the absolute path of the file the asset refers to.

See Also: Managing Assets

## Asset.getAssetPath

Retrieves the path of the file the asset refers to, relative to the project assets directory.

```
Asset.getAssetPath()

```

Returns the path of the file the asset refers to, relative to the project assets directory.

## Asset.setAssetPath

Sets the path of the file the asset refers to, relative to the project assets directory.

```
Asset.setAssetPath(
    filePath
)

```

  filePath The path to move the asset to.
Returns `true` if the operation succeeds, or `false` otherwise.

 Calling this function will move the underlying file asset on disk.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
