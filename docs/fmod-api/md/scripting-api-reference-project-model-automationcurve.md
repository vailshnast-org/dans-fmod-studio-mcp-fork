# 26. Scripting API Reference | Project.Model.AutomationCurve

Types:

- model.AutomationCurve Maps automation values across an associated `model.Parameter`.

Extension Methods:

- AutomationCurve.addAutomationPoint Creates an automation point at the given position.

## model.AutomationCurve

Maps automation values across an associated model.Parameter.

## AutomationCurve.addAutomationPoint

Creates an automation point at the given position.

```
AutomationCurve.addAutomationPoint(
    position,
    value
)

```

  position The timeline position to place the automation point. Must be within the range of the curve's parameter. value The value to assign the automation point. Must be within the value range of the automated property.
Returns the automation point ManagedObject.

See Also: Automation Curves, Automation Point

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
