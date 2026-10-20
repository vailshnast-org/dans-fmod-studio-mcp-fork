# 26. Scripting API Reference | Menu

- Module: Menu

- menu.addMenuItem(description)

- menu.removeMenuItem(description)

- menu.menuItems()

## Module: Menu

The `studio.menu` module provides access to menu bar items.

### menu.addMenuItem(description)

Registers a menu item under the "Scripts" menu, based on the description object:

```
{
    name: [string] (required),
    execute: [function] (required),
    keySequence: [string],
    isEnabled: [bool] (dynamic),
    isChecked: [bool] (dynamic),
    subMenuItems: [array(description)] (dynamic),
}

```

The name property must be a string, but other properties can specify a function to be called dynamically, which returns a value of the expected type (for example, you may want to reevaluate `isEnabled` based on what's selected). Using a '\' character in the item name will place it in a submenu. Adding an item with a name containing all dashes ('-' character) will result in a separator being added.

- `name`: The name of the menu item that appears in the menu.

- `execute`: The function to be called by the menu item.

- `keySequence`: The keyboard shortcut for the menu item.

- `isEnabled`: Determines when the menu item becomes enabled.

- `isChecked`: Determines whether a checkmark appears next to the menu item.

- `subMenuItems`: Specifies the items that appear in the menu item's associated submenu, if any.

Returns `true` if the operation succeeds, or `false` otherwise.

### menu.removeMenuItem(description)

Removes a menu item that was added with menu.addMenuItem(). The `description` argument must match a `description` that the menu item was added with.

Returns `true` if the operation succeeds, or `false` otherwise.

### menu.menuItems()

Returns an `Array` of menu item descriptions added with menu.addMenuItem(). The order of the `Array` matches the order in which the items were added.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
