# 26. Scripting API Reference | Window

- Module: Window

- window.open(windowType)

- window.navigateTo(managedObject)

- window.browserCurrent([tabName])

- window.browserSelection([tabName])

- window.editorCurrent()

- window.editorSelection()

- window.deckCurrent()

- window.deckSelection()

- window.actions

- window.triggerAction(actionType)

## Module: Window

The `studio.window` module allows for interaction with the window context.

### window.open(windowType)

Opens a new window of the given window type (e.g. "Event Editor").

Returns `true` if the window request is valid, or `false` otherwise.

### window.navigateTo(managedObject)

Attempts to navigate to a ManagedObject in the UI. Will open a new window if required. Returns `true` if successful.

### window.browserCurrent([tabName])

Returns the currently selected ManagedObject in the active browser tab of the last active window. A `tabName` can optionally be specified to select from a different browser tab.

### window.browserSelection([tabName])

Returns an `Array` of selected ManagedObjects in the active browser tab of the last active window. A `tabName` can optionally be specified to select from a different browser tab.

### window.editorCurrent()

Returns the currently selected ManagedObject in the last active editor (e.g. in the multitrack view).

### window.editorSelection()

Returns an array of selected ManagedObjects in the last active editor (e.g. in the multitrack view).

### window.deckCurrent()

Returns the currently selected ManagedObject in the deck of the last active window.

### window.deckSelection()

Returns an array of selected ManagedObjects in the deck of the last active window.

### window.actions

An enumeration used with studio.window.triggerAction() to trigger the execution of an action. Possible values are:

- `AddTransitionTimeline`

- `BringToFront`

- `Build`

- `BuildAllPlatforms`

- `ClearRecentFiles`

- `CloseProject`

- `CloseTab`

- `ContinuousZoomToFit`

- `Copy`

- `CopyGuid`

- `CopyPath`

- `DecreaseDefaultTrackHeight`

- `Delete`

- `Duplicate`

- `ExitApplication`

- `ExportGuids`

- `Find`

- `FlattenBrowserFolders`

- `FollowPlaybackPosition`

- `ImportAudioFiles`

- `IncreaseDefaultTrackHeight`

- `LoopPlayback`

- `MergeConflictingAsset`

- `MoveTo`

- `MoveToCursor`

- `NewBrowserFolder`

- `NewBrowserItem`

- `NewMixerGroup`

- `NewMixerReturn`

- `NewParameter`

- `NewProject`

- `NewTab`

- `OpenInExternal`

- `OpenInFileSystem`

- `OpenInNewWindow`

- `OpenMostRecentFile`

- `OpenProject`

- `PackageProject`

- `Paste`

- `Redo`

- `RefreshModifiedAssets`

- `RemoveTransitionTimeline`

- `Rename`

- `RevertToSaved`

- `SandboxToggleEmitter_01`

- `SandboxToggleEmitter_02`

- `SandboxToggleEmitter_03`

- `SandboxToggleEmitter_04`

- `SandboxToggleEmitter_05`

- `SandboxToggleEmitter_06`

- `SandboxToggleEmitter_07`

- `SandboxToggleEmitter_08`

- `SandboxToggleEmitter_09`

- `SandboxToggleEmitter_10`

- `Save`

- `SaveAs`

- `ScriptReload`

- `SendToBack`

- `ShowAbout`

- `ShowAutomationValues`

- `ShowCompactStrips`

- `ShowFMODio`

- `ShowLogicTracks`

- `ShowMarkerLines`

- `ShowOverlappingInstrumentsInLanes`

- `ShowPreferences`

- `ShowQuestionsPage`

- `ShowQuickStartTutorial`

- `ShowSupportEmail`

- `ShowUserManual`

- `ShowWelcome`

- `SnapToItems`

- `SnapToRuler`

- `SourceControlBrowseForProject`

- `SourceControlCommit`

- `SourceControlIdentifyLocalChanges`

- `SourceControlRevert`

- `SourceControlSync`

- `Split`

- `ToggleBulkEdit`

- `ToggleConnectToGame`

- `ToggleFilePlayback`

- `ToggleTransitionTimelineVisibility`

- `Undo`

- `ValidateProject`

- `ViewBrowser`

- `ViewDeck`

- `ViewProperties`

- `WindowBringAllToFront`

- `WindowClose`

- `WindowCycle`

- `WindowMaximize`

- `WindowMinimize`

- `ZoomIn`

- `ZoomOut`

- `ZoomToFit`

### window.triggerAction(actionType)

Attempts to trigger the `actionType` action for the last active window. The available options are described by the window.actions enum.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
