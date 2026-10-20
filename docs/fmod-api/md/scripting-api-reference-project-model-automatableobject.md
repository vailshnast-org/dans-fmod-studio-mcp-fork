# 26. Scripting API Reference | Project.Model.AutomatableObject

Types:

- model.AutomatableObject The base class for objects that can be automated or modulated.

Extension Methods:

- AutomatableObject.addAutomator Creates a `model.Automator` for a given property of the automatable object.

- AutomatableObject.addModulator Creates a `model.Modulator` for a given property of the automatable object.

## model.AutomatableObject

The base class for objects that can be automated or modulated.

## AutomatableObject.addAutomator

Creates a model.Automator for a given property of the automatable object.

```
AutomatableObject.addAutomator(
    propertyName
)

```

  propertyName The name of the automator to add.
Returns the automator ManagedObject.

Example:

```
var automator1 = sound.addAutomator("volume"); // adds an automator for the volume property of the sound
var automator2 = sound.addAutomator(sound.pitch); // alternatively, the property can be used as an argument

```

## AutomatableObject.addModulator

Creates a model.Modulator for a given property of the automatable object.

```
AutomatableObject.addModulator(
    modulatorType,
    propertyName
)

```

  modulatorType Type of modulator to add. Must be `RandomizerModulator`, `ADSRModulator`, `SidechainModulator` or `AutopitchModulator`. propertyName The name of the property to modulate with the newly create modulator.
Returns the modulator ManagedObject.

Example:

```
var randModulator = sound.addModulator("RandomizerModulator", "volume"); // adds a randomizer modulator for the volume property of the sound
var ahdsrModulator = sound.addModulator("ADSRModulator", sound.pitch); // alternatively, the property can be used as an argument

```

See Also: Automation

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
