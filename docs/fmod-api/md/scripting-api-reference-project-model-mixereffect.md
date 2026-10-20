# 26. Scripting API Reference | Project.Model.MixerEffect

Types:

- model.ChannelMixEffect An effect that allows custom gain and mixing of each individual channel.

- model.ChorusEffect An effect that uses an LFO modulated delay to create a shimmering sound.

- model.CompressorEffect An effect that reduces the dynamic range of a signal by attenuating peaks in volume.

- model.ConvolutionReverbEffect An effect that convolves the incoming signal with a user-provided impulse response.

- model.DelayEffect An effect that repeats a signal after a user-specified amount of time.

- model.FlangerEffect An effect that uses an LFO modulated delay to create a swirling sound.

- model.GainEffect An effect that attenuates or amplifies a signal.

- model.HighpassEffect An effect that attenuates the low frequencies of a signal.

- model.HighpassSimpleEffect An effect that attenuates the low frequencies of a signal.

- model.ITEchoEffect A stereo delay effect that repeats a signal after a user-specified amount of time.

- model.LimiterEffect An effect that reduces the dynamic range of a signal by attenuating peaks in volume.

- model.LoudnessMeter An effect that displays standardized loudness metrics for an input signal.

- model.LowpassEffect An effect that attenuates the high frequencies of a signal.

- model.LowpassSimpleEffect An effect that attenuates the high frequencies of a signal.

- model.MixerBusEffectChain A mixer bus's signal chain.

- model.MixerBusFader The mixer bus's fader within the signal chain.

- model.MixerBusPanner An effect that modifies the mix balance of a signal in relation to each speaker.

- model.MixerEffect The base class for a signal processing unit.

- model.MixerSend An effect that sends the incoming signal to a return, and allows the signal to flow on through the signal chain.

- model.MultibandEqEffect An effect that attenuates or amplifies multiple bands of a signal.

- model.ObjectSpatialiserEffect An object based spatializer effect.

- model.PannerEffect An effect that modifies the mix balance of a signal in relation to each speaker.

- model.ParamEqEffect An effect that attenuates or amplifies a single band of a signal.

- model.PitchShifterEffect An effect that modifies the pitch of the signal.

- model.SFXReverbEffect An effect that uses a series of delays to apply reverb to a signal.

- model.Sidechain An effect that makes a signal available as an input for effect, parameter, or event property modulation.

- model.SpatialEffect The base class for spatializer effects.

- model.SpatialiserEffect An effect that simulates the positioning of a sound in 3D space.

- model.ThreeEQEffect An effect that attenuates or amplifies the lower, middle, and upper bands of a signal.

- model.TransceiverEffect An effect that can transmit or receive a signal on one of thirty-two different transceiver channels.

- model.TremoloEffect An effect that modulates the volume of a signal with an LFO to create a rhythmic beating sound.

Extension Methods:

- MixerBusEffectChain.addEffect Creates an effect and adds it to the end of the chain.

- ConvolutionReverbEffect.setIRFromFilePath Sets the impulse response for a convolution reverb effect.

## model.ChannelMixEffect

An effect that allows custom gain and mixing of each individual channel.

See Also: Channel Mix

## model.ChorusEffect

An effect that uses an LFO modulated delay to create a shimmering sound.

See Also: Chorus

## model.CompressorEffect

An effect that reduces the dynamic range of a signal by attenuating peaks in volume.

See Also: Compressor

## model.ConvolutionReverbEffect

An effect that convolves the incoming signal with a user-provided impulse response.

See Also: Convolution Reverb

## model.DelayEffect

An effect that repeats a signal after a user-specified amount of time.

See Also: Delay

## model.FlangerEffect

An effect that uses an LFO modulated delay to create a swirling sound.

See Also: Flange

## model.GainEffect

An effect that attenuates or amplifies a signal.

## model.HighpassEffect

An effect that attenuates the low frequencies of a signal.

This effect differs from model.HighpassSimpleEffect by having a "Resonance" control.

Development Status. Deprecated and will be removed in a future release

See Also: High Pass

## model.HighpassSimpleEffect

An effect that attenuates the low frequencies of a signal.

Development Status. Deprecated and will be removed in a future release.

See Also: High Pass Simple

## model.ITEchoEffect

A stereo delay effect that repeats a signal after a user-specified amount of time.

See Also: IT Echo

## model.LimiterEffect

An effect that reduces the dynamic range of a signal by attenuating peaks in volume.

The attenuation ratio of this effect is more extreme than that of a model.CompressorEffect.

See Also: Limiter

## model.LoudnessMeter

An effect that displays standardized loudness metrics for an input signal.

## model.LowpassEffect

An effect that attenuates the high frequencies of a signal.

This effect differs from model.HighpassSimpleEffect by having a "Resonance" control.

Development Status. Deprecated and will be removed in a future release

See Also: Low Pass

## model.LowpassSimpleEffect

An effect that attenuates the high frequencies of a signal.

Development Status. Deprecated and will be removed in a future release

See Also: Low Pass Simple

## model.MixerBusEffectChain

A mixer bus's signal chain.

A single model.MixerBusFader is required to be placed within the chain.

See Also: model.MixerBus

## model.MixerBusFader

The mixer bus's fader within the signal chain.

See Also: Fader, model.MixerBus

## model.MixerBusPanner

An effect that modifies the mix balance of a signal in relation to each speaker.

This effect appears automatically in the deck when the event's speaker configuration is set to stereo or higher, and cannot be manually added or removed.

See Also: The Panner

## model.MixerEffect

The base class for a signal processing unit.

Mixer effects encapsulate the functionality of DSP effects.

See Also: Effect

## model.MixerSend

An effect that sends the incoming signal to a return, and allows the signal to flow on through the signal chain.

See Also: Sends and Return Buses, Send, model.MixerReturn

## model.MultibandEqEffect

An effect that attenuates or amplifies multiple bands of a signal.

See Also: Multiband Equalizer

## model.ObjectSpatialiserEffect

An object based spatializer effect.

The signal routed to this effect is directed straight to the hardware output.

See Also: The FMOD Object Spatializer Effect, Object Panner

## model.PannerEffect

An effect that modifies the mix balance of a signal in relation to each speaker.

See Also: Pan

## model.ParamEqEffect

An effect that attenuates or amplifies a single band of a signal.

Development Status. Deprecated and will be removed in a future release.

See Also: Parametric EQ

## model.PitchShifterEffect

An effect that modifies the pitch of the signal.

See Also: Pitch Shifter

## model.SFXReverbEffect

An effect that uses a series of delays to apply reverb to a signal.

See Also: SFX Reverb

## model.Sidechain

An effect that makes a signal available as an input for effect, parameter, or event property modulation.

See Also: Sidechain Modulator, Sidechain Effect, model.SidechainModulator

## model.SpatialEffect

The base class for spatializer effects.

## model.SpatialiserEffect

An effect that simulates the positioning of a sound in 3D space.

See Also: The FMOD Spatializer Effect, Pan

## model.ThreeEQEffect

An effect that attenuates or amplifies the lower, middle, and upper bands of a signal.

See Also: Three EQ

## model.TransceiverEffect

An effect that can transmit or receive a signal on one of thirty-two different transceiver channels.

See Also: Transceiver

## model.TremoloEffect

An effect that modulates the volume of a signal with an LFO to create a rhythmic beating sound.

See Also: Tremolo

## MixerBusEffectChain.addEffect

Creates an effect and adds it to the end of the chain.

```
MixerBusEffectChain.addEffect(
    effectDefinition
)

```

  effectDefinition Either an `EffectPreset`, a model.MixerEffect that is a shared effect, or one of the following strings:

 - `ThreeEQEffect`

 - `ChannelMixEffect`

 - `ChorusEffect`

 - `CompressorEffect`

 - `ConvolutionReverbEffect`

 - `DistortionEffect`

 - `DelayEffect`

 - `FlangerEffect`

 - `GainEffect`

 - `LimiterEffect`

 - `MultibandEqEffect`

 - `PitchShifterEffect`

 - `SFXReverbEffect`

 - `TransceiverEffect`

 - `TremoloEffect`

 - `HighpassEffect`

 - `HighpassSimpleEffect`

 - `LowpassEffect`

 - `LowpassSimpleEffect`

 - `ParamEqEffect`

 - `SpatialiserEffect`

 - `ObjectSpatialiserEffect`

 - `LoudnessMeter`
Returns the effect ManagedObject.

See Also: Signal Chain

## ConvolutionReverbEffect.setIRFromFilePath

Sets the impulse response for a convolution reverb effect.

```
ConvolutionReverbEffect.setIRFromFilePath(
    filePath
)

```

  filePath The absolute path to an audio data file.

## model.DistortionEffect

An effect that applies clipping to a signal to affect the harmonic envelope.

See Also: Distortion

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
