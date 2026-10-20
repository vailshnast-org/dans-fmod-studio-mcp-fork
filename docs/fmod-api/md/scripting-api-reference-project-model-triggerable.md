# 26. Scripting API Reference | Project.Model.Triggerable

Types:

- model.Triggerable The base class for entities that can be triggered.

Extension Methods:

- Triggerable.addParameterCondition Adds a parameter condition for a given parameter to a triggerable object.

## model.Triggerable

The base class for entities that can be triggered.

See Also: Trigger

## Triggerable.addParameterCondition

Adds a parameter condition for a given parameter to a triggerable object.

```
Triggerable.addParameterCondition(
    parameter,
    min,
    max
)

```

  parameter Can be either a model.ParameterPreset or a model.GameParameter. min The minimum value of the parameter condition. max The maximum value of the parameter condition.
Returns the parameter condition ManagedObject.

The range of the parameter condition is specified using the `min` and `max`. If `max` is `undefined`, the maximum of the parameter condition is set to `min`. For a labeled parameter, the `max` argument is ignored.

Example:

```
var continuousCondition = loopRegion.addParameterCondition(studio.project.lookup("parameter:/Distance Parameter"), 0, 1000);
var labeledCondition = singleSound.addParameterCondition(studio.project.lookup("parameter:/Current Country"), "Australia");
labeledCondition = transitionMarker.addParameterCondition(studio.project.lookup("parameter:/Current Country"), "Australia");
labeledCondition = transitionRegion.addParameterCondition(studio.project.lookup("parameter:/Current Country"), "Australia");

```

See Also: Trigger, Parameter Condition, ManagedObject

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
