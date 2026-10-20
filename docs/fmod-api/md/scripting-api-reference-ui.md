# 26. Scripting API Reference | UI

- Module: UI

- ui.showModalDialog(description)

- ui.showModelessDialog(description)

- ui.widgetType

- ui.layoutType

- ui.alignment

- ui.sizePolicy

- ui.orientation

- ui.echoMode

- ui.pathType

## Module: UI

The `studio.ui` module allows you to create user interfaces.

### ui.showModalDialog(description)

Displays a dialog window. The function returns once the dialog has been closed.

See ui.showModelessDialog(description) for further information about the widget `description` argument.

### ui.showModelessDialog(description)

Displays a dialog window. The function returns once the dialog is shown.

The layout of the dialog is based on a widget `description` object, which contains the following attributes:

- `widgetType`: A studio.ui.widgetType. A required attribute.

- `widgetId`: A `string` used to reference this widget. Immutable.

- `isVisible`: A `Boolean` which sets widget visiblity.

- `isEnabled`: A `Boolean` which sets whether a widget is interactive.

- `minimumWidth`: The minimum width in pixels for a widget (`number`).

- `minimumHeight`: The minimum height in pixels for a widget (`number`).

- `sizePolicy`: A studio.ui.sizePolicy.

- `onConstructed`: A `Function` which is called after the widget is constructed.

- `onTimerEvent(timerId)`: A callback `Function`. This will be called periodically after calling `startTimer()` on a widget. The `timerId` matches a corresponding `timerId` returned by `startTimer()`.

Applicable to the root widget description in a dialog:

- `windowTitle`: A `string` for the window title.

- `windowWidth`: Width of the window (`number`).

- `windowHeight`: Height of the window (`number`).

- `onClose`: A `Function` which is called as the widget is destroyed.

Applicable to `widgetType.Layout`:

- `layout`: A studio.ui.layoutType. A required attribute.

- `items`: An `Array` of deck widget descriptions to nest in this layout.

- `contentsMargins`: Describes the margins around a layout. An `Object` with the format `{ left:[number], top:[number], right:[number], bottom:[number] }`.

- `spacing`: Spacing between items in pixels (`number`).

Applicable to items within a `layoutType.HBoxLayout` or `layoutType.VBoxLayout`:

- `stretchFactor`: Determines how much space an item consumes relative to its siblings (`number`). Immutable.

- `alignment`: A studio.ui.alignment. Immutable.

Applicable to items within a `layoutType.GridLayout`:

- `row`: Row index in grid (`number`). Immutable.

- `column`: Column index in grid (`number`). Immutable.

- `rowSpan`: `number` of rows for item to span. Immutable.

- `columnSpan`: `number` of columns for item to span. Immutable.

- `alignment`: A studio.ui.alignment. Immutable.

Applicable to `widgetType.Label`:

- `text`: A `string`.

- `wordWrap`: A `boolean`.

Applicable to `widgetType.PushButton`:

- `text`: A `string`.

- `onClicked`: A callback `Function`.

Applicable to `widgetType.LineEdit`:

- `text`: A `string`.

- `isReadOnly`: A `bool`.

- `echoMode`: A studio.ui.echoMode.

- `onTextEdited`: A callback `Function`.

- `onEditingFinished`: A callback `Function`.

Applicable to `widgetType.TextEdit`:

- `text`: The contents of the text edit, as plain text `string`. Alternatively, use the `html` attribute to specify HTML formatted text.

- `html`: The contents of the text edit, as a HTML formatted `string`. This can be used instead of `text`.

- `isReadOnly`: A `boolean`.

Applicable to `widgetType.ComboBox`:

- `items`: An array of objects with the format `{ text:[string], userData:[]}`. Write-only.

- `currentIndex`: A `number`.

- `currentText`: A `string`. Read-only.

- `currentUserData`: Read-only.

- `onCurrentIndexChanged`: A callback `Function`.

Applicable to `widgetType.CheckBox`:

- `text`: A `string`.

- `isChecked`: A `boolean`.

- `onToggled`: A callback `Function`.

Applicable to `widgetType.Slider`:

- `orientation`: A studio.ui.orientation.

- `value`: A `number`.

- `range`: An object with the format `{ minimum:[int], maximum:[int] }`.

- `onValueChanged`: A callback `Function`.

Applicable to `widgetType.SpinBox`:

- `value`: A `number`.

- `range`: An object with the format `{ minimum:[int], maximum:[int] }`.

- `onValueChanged`: A callback `Function`.

Applicable to `widgetType.PathLineEdit`:

- `text`: A `string`.

- `label`: A `string`. Immutable.

- `caption`: A `string`. Immutable.

- `pathType`: A studio.ui.pathType. Immutable.

- `onEditingFinished`: A callback `Function`.

Note that all attributes are optional except for those marked as required.

Widget callbacks functions are called with the `this` value set to the corresponding widget. You can dynamically get and set the various attributes available in the widget description using the corresponding 'getter' and 'setter' (e.g. calling `widget.setVisible()` will modify the `widget.isVisible()` attribute). Attributes marked as immutable do not have a 'setter' function. For example:

```
{
    widgetType: ui.widgetType.PushButton,
    text: "Show Alert",
    onClicked: function() {
        // displays an alert with the text of the button that was clicked
        alert("The button's text is: "; + this.text());
    },
}

```

From the context of a callback, a number of additional member functions are available for widgets:

- `findWidget(widgetId)`: Returns a sibling widget with the matching `widgetId`.

- `closeDialog()`: Closes the parent window.

- `startTimer(intervalInMs)`: Starts a timer with the `intervalInMs` and returns a `timerId`. Once a timer is started, the `onTimerEvent()` function of the widget description will be called periodically. The `timerId` can be used to differentiate between timers when multiple timers have been started.

- `stopTimer(timerId)`: Stops a timer with the given `timerId`.

For an in-depth example of writing your own widgets, see the `EngineDesigner.js` example in the Scripts folder of the FMOD Studio install directory.

### ui.widgetType

An enumeration corresponding to different widget types available within a UI widget description. Possible values are:

- `Spacer`: A blank widget.

- `Layout`: A container widget. Must specify a corresponding layout type.

- `Label`: A text label.

- `PushButton`: A clickable button.

- `LineEdit`: A single-line text entry widget.

- `TextEdit`: A multi-line text entry widget. Supports plain text and HTML.

- `ComboBox`: A drop down.

- `CheckBox`: A boolean check box with a text label.

- `Slider`: A slider that with an integer range.

- `SpinBox`: A number box with an integer range.

- `PathLineEdit`: A convenience widget providing a single-line text entry widget and a "Browse" push button to allow user to input a file or a directory path.

### ui.layoutType

An enumeration corresponding to different layout types available within a UI widget description of `widgetType.Layout`. Possible values are:

- `HBoxLayout`: A horizontal layout. Items are spaced evenly, unless a `stretchFactor` is specified.

- `VBoxLayout`: A vertical layout. Items are spaced evenly, unless a `stretchFactor` is specified.

- `GridLayout`: A grid layout. Items can specify a `row`, `column`, `rowSpan` and `columnSpan`.

### ui.alignment

An enumeration corresponding to the alignment of an item within a layout widget. Possible values are:

- `AlignLeft`

- `AlignRight`

- `AlignHCenter`

- `AlignJustify`

- `AlignAbsolute`

- `AlignTop`

- `AlignBottom`

- `AlignVCenter`

- `AlignBaseline`

- `AlignCenter`

### ui.sizePolicy

An enumeration corresponding to the size policy of a widget. This determines how much space it will try to consume within its layout, and how it will react when more or less space is made available.

Separate vertical and horizontal size policies will need to be specified. For example: `sizePolicy: { horizontalPolicy: studio.ui.sizePolicy.Fixed, verticalPolicy: studio.ui.sizePolicy.Fixed }`.

Please note that the size policy only applies to the individual widgets and not to the size of the dialog window.

Possible values are:

- `Fixed` - the widget can never grow or shrink

- `Minimum` - the widget can expand but not get smaller than the `minimumWidth`/`minimumHeight` specified in the widget description object

- `Maximum` - the widget can get smaller but can not expand beyond the `maximumWidth`/`maximumHeight` specified in the widget description object

- `Preferred` - the widget can be expanded or shrunk, but there is no advantage to it being larger than the `minimumWidth`/`minimumHeight` specified in the widget description object

- `MinimumExpanding` - the widget can make use of extra space, so it should get as much space as possible, with a preferred `minimumWidth`/`minimumHeight` specified in the widget description object

- `Expanding` - the widget can make use of extra space, so it should get as much space as possible

- `Ignored` - the widget will get as much space as possible

### ui.orientation

An enumeration representing an orientation. Possible values are:

- `Horizontal`

- `Vertical`

### ui.echoMode

An enumeration corresponding to the echo mode of a `LineEdit` widget. This can be used to display asterisks instead of characters when entering a password. Possible values are:

- `Normal`

- `NoEcho`

- `Password`

- `PasswordEchoOnEdit`

### ui.pathType

An enumeration corresponding to the different path types the `PathLineEdit` supports. This controls the behavior of browser dialog presented. Possible values are:

- `OpenFile`: User will be able to select an existing file.

- `SaveFile`: User will be able to specify a new file name at a given directory.

- `Directory`: User will be able to select an existing directory.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
