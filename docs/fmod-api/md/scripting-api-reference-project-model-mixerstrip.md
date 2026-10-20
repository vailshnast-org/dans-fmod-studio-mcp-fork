# 26. Scripting API Reference | Project.Model.MixerStrip

Types:

- model.EventMixerGroup An audio track within a `model.Event`.

- model.EventMixerMaster The master track of an `model.Event`.

- model.EventMixerReturn A return track that can receive signals from within the event.

- model.MixerBus The base class for routable buses.

- model.MixerGroup A `model.MixerBus` that accepts the outputs of other mixer buses as inputs.

- model.MixerInput A `model.MixerBus` that allows output from a `model.Event` to enter the project-level mixer.

- model.MixerMaster The final output bus in the mixer.

- model.MixerPort An output to an external audio port.

- model.MixerReturn A return bus that can receive a signal from a `model.MixerSend`.

- model.MixerStrip The base class for elements represented as a strip.

- model.MixerVCA A `model.MixerStrip` that scales the volume of any other mixer strips assigned to it.

Extension Methods:

- MixerBus.getInputFormat Retrieves the input format of the bus.

- MixerBus.getOutputFormat Retrieves the output format of the bus.

- MixerStrip.getPath Retrieves the mixer strip's unique path identifier.

## model.EventMixerGroup

An audio track within a model.Event.

## model.EventMixerMaster

The master track of an model.Event.

## model.EventMixerReturn

A return track that can receive signals from within the event.

See Also: Sends and Return Buses, Return

## model.MixerBus

The base class for routable buses.

## model.MixerGroup

A model.MixerBus that accepts the outputs of other mixer buses as inputs.

See Also: Group Buses and Routing

## model.MixerInput

A model.MixerBus that allows output from a model.Event to enter the project-level mixer.

Nested events, snapshots and profiler sessions cannot output to a mixer input.

See Also: Mixer Strip

## model.MixerMaster

The final output bus in the mixer.

See Also: model.MixerStrip, Master Bus

## model.MixerPort

An output to an external audio port.

See Also: Port Buses

## model.MixerReturn

A return bus that can receive a signal from a model.MixerSend.

See Also: Sends and Return Buses, Return

## model.MixerStrip

The base class for elements represented as a strip.

## model.MixerVCA

A model.MixerStrip that scales the volume of any other mixer strips assigned to it.

See Also: VCAs

## MixerBus.getInputFormat

Retrieves the input format of the bus.

```
MixerBus.getInputFormat()

```

Returns the effective input format for a model.MixerBus object as an enumeration.

## MixerBus.getOutputFormat

Retrieves the output format of the bus.

```
MixerBus.getOutputFormat()

```

Returns the effective output format for a model.MixerBus object as an enumeration.

## MixerStrip.getPath

Retrieves the mixer strip's unique path identifier.

```
MixerStrip.getPath()

```

Returns the model.MixerStrip's path as a `string`.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
