# 26. Scripting API Reference | Project.Model.Sound

Types:

- model.CommandSound An instrument that triggers an API command.

- model.EventSound An instrument that references a `model.Event` or snapshot to play.

- model.MultiSound A container instrument that selects from a playlist of other `model.Sound`s.

- model.PluginSound An instrument that uses an external DSP to generate sound.

- model.ProgrammerSound An instrument that can be assigned an asset at runtime.

- model.SilenceSound An instrument that plays nothing for a specified amount of time.

- model.SingleSound An instrument that plays a single audio asset.

- model.Sound The base class for all instrument types.

- model.SoundScatterer A container instrument that applies temporal and spatial randomization to a playlist of other instruments.

Extension Methods:

- Sound.setFadeInCurve Sets the fade-in curve of the instrument to the specified length and curve shape.

- Sound.setFadeOutCurve Sets the fade-out curve of the instrument to the specified length and curve shape.

## model.CommandSound

An instrument that triggers an API command.

See Also: Command Instrument

## model.EventSound

An instrument that references a model.Event or snapshot to play.

See Also: Event Instrument, Snapshot Instrument

## model.MultiSound

A container instrument that selects from a playlist of other model.Sounds.

See Also: Multi Instrument

## model.PluginSound

An instrument that uses an external DSP to generate sound.

See Also: Plug-in Reference

## model.ProgrammerSound

An instrument that can be assigned an asset at runtime.

See Also: Programmer Instrument

## model.SilenceSound

An instrument that plays nothing for a specified amount of time.

See Also: Silence Instrument

## model.SingleSound

An instrument that plays a single audio asset.

See Also: Single Instrument

## model.Sound

The base class for all instrument types.

Instruments can be placed on a track, or within a model.MultiSound playlist.

## model.SoundScatterer

A container instrument that applies temporal and spatial randomization to a playlist of other instruments.

See Also: Scatterer Instrument

## Sound.setFadeInCurve

Sets the fade-in curve of the instrument to the specified length and curve shape.

```
Sound.setFadeInCurve(
    length,
    curveShape
)

```

  length The numerical duration of the new fade-in curve. curveShape The numerical velocity of the curve. A value of 0 creates a linear fade-in, a positive value creates an accelerating fade-in, and a negative negative value creates a decelerating fade-in.
If no fade-in curve exists on the sound, one is created. If `length` is approaching zero, no curve is added. If the curve has an existing fade-in curve, it is removed. If no `curveShape` is provided, the default shape is used instead.

## Sound.setFadeOutCurve

Sets the fade-out curve of the instrument to the specified length and curve shape.

```
Sound.setFadeInCurve(
    length,
    curveShape
)

```

  length The numerical duration of the new fade-out curve. curveShape The numerical velocity of the curve. A value of 0 creates a linear fade-out, a positive value creates an accelerating fade-out, and a negative negative value creates a decelerating fade-out.
If no fade-out curve exists on the sound, one is created. If `length` is approaching zero, no curve is added. If the curve has an existing fade-out curve, it is removed. If no `curveShape` is provided, the default shape is used instead.

See Also: Instrument

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
