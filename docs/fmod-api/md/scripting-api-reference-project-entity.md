# 26. Scripting API Reference | Project.Entity

A `studio.project.Entity` provides information about the type of a ManagedObject.

The entity for a given ManagedObject can be retrieved using ManagedObject.entity. This provides the string representation for an entity, which can then be looked up in the project.model.

Properties:

- entity.isAbstract A constant boolean value that is set to true if an object is the base class of another entity type.

- entity.isGlobal A constant boolean value that is set to true if an entity exists globally, rather than on a per project basis.

- entity.isSingleton A constant boolean value that is set to true if only a single `ManagedObject` instance of the entity can exist at any given time.

- entity.properties Returns an array of property description objects containing named properties that represent each `ManagedObject` property available for this entity.

- entity.superentities An array of strings representing the entity type inherited by this entity.

Methods:

- entity.document Returns a string describing the entity, including its properties and relationships.

- entity.findInstances Returns an array of `ManagedObject` instances of a given entity type.

- entity.singletonInstance Returns the singleton `ManagedObject` instance of a particular entity type.

Objects:

- Relationship Description Object An unnamed data object describing the relationship between two entities.

- Property Description Object An unnamed data object containing the data type and default value of a property.

## entity.isAbstract

A constant boolean value that is set to true if an object is the base class of another entity type.

Abstract entities cannot be instantiated with project.create.

## entity.isGlobal

A constant boolean value that is set to true if an entity exists globally, rather than on a per project basis.

## entity.isSingleton

A constant boolean value that is set to true if only a single ManagedObject instance of the entity can exist at any given time.

## entity.properties

Returns an array of property description objects containing named properties that represent each ManagedObject property available for this entity.

See Also: Property Description Object

## entity.superEntities

An array of strings representing the entity type inherited by this entity.

## entity.document

Returns a string describing the entity, including its properties and relationships.

```
entity.document()

```

## entity.findInstances

Returns an array of ManagedObject instances of a given entity type.

```
entity.findInstances(
    [options]
)

```

You can optionally pass an `options` object `{ searchContext, includeDerivedTypes }`. Passing a managed object for the `searchContext` field confines the search to children of that object. Passing `true` for the `includeDerivedTypes` field will allow derived types of the given entity to be returned.

For example:

```
// find all SingleSounds within the project
studio.project.model.SingleSound.findInstances();

// find all SingleSounds within the currently selected event
studio.project.model.SingleSound.findInstances({ searchContext: studio.window.browserCurrent() });

// find all GroupTracks, ReturnTracks and MasterTracks within the currently selected event
studio.project.model.AudioTrack.findInstances({ searchContext: studio.window.browserCurrent(), includeDerivedTypes: true });

```

## entity.singletonInstance

Returns the singleton ManagedObject instance of a particular entity type.

```
entity.singletonInstance()

```

An error will be thrown if the entity is not a singleton type.

## Relationship Description Object

An unnamed data object describing the relationship between two entities.

```
{
    cardinality: [string],
    destinationType: [string],
    isRequired: [bool]
}

```

  cardinality Description of relationship, e.g. one-to-many, many-to-one. destinationType Entity type the relationship targets. isRequired Indicates whether this relationship is required.

## Property Description Object

An unnamed data object containing the data type and default value of a property.

```
{
    dataType: [string],
    defaultValue: [variant]
}

```

  dataType The type of data the property represents. defaultValue The default value of the property.
This is the object type returned from entity.Properties.

## entity.relationships

Returns an array of relationship description objects, containing named relationships that represents each ManagedObject relationship available for this entity.

See Also: Relationship Description Object

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
