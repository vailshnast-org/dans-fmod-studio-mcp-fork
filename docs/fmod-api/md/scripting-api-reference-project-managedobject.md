# 26. Scripting API Reference | Project.ManagedObject

Project level data in Studio is represented as a graph of managed objects. A managed object is comprised of:

- ManagedObject.id: The unique identifier (GUID).

- ManagedObject.entity: A description of the object type (e.g. `Event`, `MixerGroup`, `Snapshot`).

- ManagedObject.properties: Each property is a simple data field (e.g. float, bool, string) with a value.

- ManagedObject.relationships: Links to other `ManagedObject`s, known as `destinations`. These can be `ToOne` or `ToMany`, and may or may not be ordered.

Beyond the generic interface presented for each `ManagedObject`, a number of extension functions are available for `ManagedObject`s of a particular project.Entity type.

The root managed object of a project can be retrieved using studio.project.workspace. Objects within a project of a particular project.Entity can be retrieved using Entity.findInstances.

### ManagedObject

Properties:

- ManagedObject.entity A string representing the object's `project.Entity` type.

- ManagedObject.id The object's unique ID.

- ManagedObject.isValid Returns whether an object is in a valid state.

- ManagedObject.properties Provides access to an object's properties.

- ManagedObject.%property_name% Provides access to a `ManagedObject` property's value.

- ManagedObject.%relationship_name% Provides access to a `ManagedObject` relationship's destinations.

- ManagedObject.relationships Provides access to an object's relationships.

Methods:

- ManagedObject.document Returns a string describing this `ManagedObject`'s entity type.

- ManagedObject.dump Logs all members.

- ManagedObject.isOfExactType Returns true if the object type matches the provided entity name.

- ManagedObject.isOfType Returns true if the object has an entity that matches the entity name, or is of a derived type.

### ManagedPropertyMap

Properties:

- ManagedPropertyMap.parent The owning `ManagedObject` of the property map.

- ManagedPropertyMap.%property_name% Returns a `ManagedProperty` for the given property name.

Methods:

- ManagedPropertyMap.dump Logs all members.

### ManagedProperty

Properties:

- ManagedProperty.dataType The type of data stored by this managed property's value.

- ManagedProperty.defaultValue The default value that the `ManagedProperty` was initialized with.

- ManagedProperty.name The name of the property.

- ManagedProperty.parent The owning `ManagedObject` of the property.

Methods:

- ManagedProperty.dump Logs all members.

- ManagedProperty.setValue Sets the value stored by the property.

- ManagedProperty.value The value stored by the property.

### ManagedRelationshipMap

Properties:

- ManagedRelationshipMap.parent The owning `ManagedObject` of the relationship map.

- ManagedRelationshipMap.%relationship_name% Returns a `ManagedRelationship` for the given relationship name.

Methods:

- ManagedRelationshipMap.dump Logs all members.

### ManagedRelationship

Properties:

- ManagedRelationship.cardinality A string representing the object's cardinality.

- ManagedRelationship.destinations An array of `ManagedObject` destinations.

- ManagedRelationship.name The name of the relationship.

- ManagedRelationship.isOrdered A constant boolean value that is set to true if the relationship is ordered.

- ManagedRelationship.parent The owning `ManagedObject` of the relationship.

Methods:

- ManagedRelationship.add Appends a new destination to a relationship.

- ManagedRelationship.dump Logs all members.

- ManagedRelationship.insert Inserts a new destination to a relationship at a given index.

- ManagedRelationship.remove Removes a destination from a relationship.

## ManagedObject.entity

A string representing the object's project.Entity type.

Lookup project.model to inspect details about the entity. Immutable.

## ManagedObject.id

The object's unique ID.

Immutable.

## ManagedObject.isValid

Returns whether an object is in a valid state.

An object may become invalid if it is deleted or if it has a `null` value for one or more of its required entity.relationships.

Immutable.

## ManagedObject.properties

Provides access to an object's properties.

Returns a ManagedPropertyMap.

Immutable.

## ManagedObject.%property_name%

Provides access to a ManagedObject property's value.

Setting the property (with the `=` operator) will set the property value.

## ManagedObject.%relationship_name%

Provides access to a ManagedObject relationship's destinations.

Getting a `ToOne` relationship will return the single destination object (or `null` if it is unassigned). Getting a `ToMany` relationship returns an array of destinations (or an empty array if it has no destinations). Setting a `ToOne` relationship (with the `=` operator) will set or replace the current destinations. `ToMany` relationships cannot be modified with the `=` operator.

## ManagedObject.relationships

Provides access to an object's relationships.

Returns a ManagedRelationshipMap.

Immutable.

## ManagedObject.document

Returns a string describing this ManagedObject's entity type.

```
ManagedObject.document()

```

As an example, calling `studio.project.workspace.mixer.masterBus.volume = 2`, would walk through the `Workspace`'s relationship to the global `Mixer`, then the `Mixer`'s relationship to the `MasterBus`, and finally sets the volume property on the `MasterBus` to 2 dB.

See Also: project.Entity

## ManagedObject.dump

Logs all members.

```
ManagedObject.dump()

```

Use this function to see what functions and properties are available on any ManagedObject. This is particularly useful for finding undocumented functionality.

## ManagedObject.isOfExactType

Returns true if the object type matches the provided entity name.

```
ManagedObject.isOfExactType(
    entityName
)

```

  entityName The name of the project.Entity type to compare against.
This does not include derived types.

## ManagedObject.isOfType

Returns true if the object has an entity that matches the entity name, or is of a derived type.

```
ManagedObject.isOfType(
    entityName
)

```

  entityName The name of the project.Entity type to compare against.

## ManagedPropertyMap.parent

The owning ManagedObject of the property map.

Immutable.

## ManagedPropertyMap.%property_name%

Returns a ManagedProperty for the given property name.

Immutable.

## ManagedPropertyMap.dump

Logs all members.

```
ManagedPropertyMap.dump()

```

Use this function to see what functions and properties are available on any managed property map. This is particularly useful for finding undocumented functionality.

## ManagedProperty.dataType

The type of data stored by this managed property's value.

Immutable.

## ManagedProperty.defaultValue

The default value that the ManagedProperty was initialized with.

Immutable.

## ManagedProperty.name

The name of the property.

Immutable.

## ManagedProperty.parent

The owning ManagedObject of the property.

Immutable.

## ManagedProperty.dump

Logs all members.

```
ManagedProperty.dump()

```

Use this function to see what functions and properties are available on any property. This is particularly useful for finding undocumented functionality.

## ManagedProperty.setValue

Sets the value stored by the property.

```
ManagedProperty.setValue(
    value
)

```

  value Value to set managed property to.
Returns `true` if the operation succeeds, or `false` otherwise.

## ManagedProperty.value

The value stored by the property.

Immutable.

## ManagedRelationshipMap.parent

The owning ManagedObject of the relationship map.

Immutable.

## ManagedRelationshipMap.%relationship_name%

Returns a ManagedRelationship for the given relationship name.

Immutable.

## ManagedRelationshipMap.dump

Logs all members.

```
ManagedRelationshipMap.dump()

```

Use this function to see what functions and properties are available on any managed relationship map. This is particularly useful for finding undocumented functionality.

## ManagedRelationship.cardinality

A string representing the object's cardinality.

Either `ToOne` or `ToMany`.

Immutable.

## ManagedRelationship.destinations

An array of ManagedObject destinations.

Immutable.

## ManagedRelationship.name

The name of the relationship.

Immutable.

## ManagedRelationship.isOrdered

A constant boolean value that is set to true if the relationship is ordered.

## ManagedRelationship.parent

The owning ManagedObject of the relationship.

Immutable.

## ManagedRelationship.add

Appends a new destination to a relationship.

```
ManagedRelationship.add(
    managedObject
)

```

  managedObject ManagedObject to add to relationship.
Replaces the current destination for a `ToOne` relationship. Returns `true` if the operation succeeds, or `false` otherwise.

## ManagedRelationship.dump

Logs all members.

```
ManagedRelationship.dump()

```

Use this function to see what functions and properties are available on any managed relationship. This is particularly useful for finding undocumented functionality.

## ManagedRelationship.insert

Inserts a new destination to a relationship at a given index.

```
ManagedRelationship.insert(
    index,
    managedObject
)

```

  index Index to insert at. Must be in range [0, destinations.length]. managedObject The ManagedObject to add to the relationship.
Returns `true` if the operation succeeds, or `false` otherwise.

## ManagedRelationship.remove

Removes a destination from a relationship.

```
ManagedRelationship.remove(
    managedObject
)

```

  managedObject ManagedObject to remove from relationship.
Returns `true` if the operation succeeds, or `false` otherwise.

## ManagedRelationship.isOrdered

A constant boolean value that is set to true if the relationship is ordered.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
