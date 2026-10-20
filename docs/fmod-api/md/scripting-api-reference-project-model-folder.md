# 26. Scripting API Reference | Project.Model.Folder

Types:

- model.Folder The base class for an item container visible in browsers.

- model.MasterAssetFolder The root folder of a folder-structure containing assets.

Extension Methods:

- Folder.getItem Retrieves the item at the relative path specified.

- MasterAssetFolder.getAsset Retrieves the asset at the path specified.

## model.Folder

The base class for an item container visible in browsers.

## model.MasterAssetFolder

The root folder of a folder-structure containing assets.

See Also: model.Asset

## Folder.getItem

Retrieves the item at the relative path specified.

```
Folder.getItem(
    path
)

```

  path Relative path of the item to retrieve.
Returns the item at the relative `path` specified. Returns `undefined` if the item cannot be found.

Example:

```
var event = studio.project.workspace.masterEventFolder.getItem("sfx/explosion_event");

```

See Also: Folders

## MasterAssetFolder.getAsset

Retrieves the asset at the path specified.

```
MasterAssetFolder.getAsset(
    path
)

```

  path Relative path of the asset to retrieve.
Returns the model.Asset at the relative path specified. Returns `undefined` if the item cannot be found.

Example:

```
studio.project.workspace.masterAssetFolder.getAsset("music/level_01.wav");

```

See Also: The Assets Folder

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
