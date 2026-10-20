# 26. Scripting API Reference | Project.Model.Modulator

Types:

- model.ADSRModulator An AHDSR curve `model.Modulator` applied to a single property of a `model.AutomatableObject`.

- model.AutopitchModulator A `model.Modulator` that affects the pitch of an instrument across the range of `model.GameParameter`s.

- model.LFOModulator A low frequency oscillator `model.Modulator` that applies a function to a single property of a `model.AutomatableObject`.

- model.Modulator The base class for objects which additively affect the value of a `model.AutomatableObject`'s property.

- model.RandomizerModulator A `model.Modulator` that applies random values to a single property of a `model.AutomatableObject`.

- model.SidechainModulator A `model.Modulator` that uses the input signal from an external `model.Sidechain` to apply random values to a single property of a `model.AutomatableObject`.

## model.ADSRModulator

An AHDSR curve model.Modulator applied to a single property of a model.AutomatableObject.

See Also: AHDSR Modulator

## model.AutopitchModulator

A model.Modulator that affects the pitch of an instrument across the range of model.GameParameters.

See Also: Autopitch Modulator

## model.LFOModulator

A low frequency oscillator model.Modulator that applies a function to a single property of a model.AutomatableObject.

See Also: LFO Modulator

## model.Modulator

The base class for objects which additively affect the value of a model.AutomatableObject's property.

See Also: Modulator

## model.RandomizerModulator

A model.Modulator that applies random values to a single property of a model.AutomatableObject.

See Also: Random Modulator

## model.SidechainModulator

A model.Modulator that uses the input signal from an external model.Sidechain to apply random values to a single property of a model.AutomatableObject.

See Also: Sidechain Modulator, Sidechain Effect

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
