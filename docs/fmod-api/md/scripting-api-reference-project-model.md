# 26. Scripting API Reference | Project.Model

The project model type representation applicable for this version.

 The `studio.project.model` provides access to information about the available model types. Data within the model is represented as a collection of project.Entity types upon which ManagedObjects are based. You can look entities up by name. For example:

```
studio.project.model.Event.findInstances(); // find all Event instances

```

## model.document

Returns a `string` describing every project.Entity.

```
model.document()

```

## model.%entity_name%

The following are common entities used for scripting. More enity types can be accessed through `model.%entity_name%`.

- project.model.asset

- project.model.automatableobject

- project.model.automationcurve

- project.model.automator

- project.model.bank

- project.model.event

- project.model.folder

- project.model.mixereffect

- project.model.mixerstrip

- project.model.modulator

- project.model.parameter

- project.model.sound

- project.model.track

- project.model.triggerable

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
