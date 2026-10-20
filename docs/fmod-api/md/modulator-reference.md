# 22. Modulator Reference

Modulators provide extended functionality for various FMOD Studio properties.

Modulators allow the value of a property to change dynamically, in a variety of specific ways. They provide methods of ramping in and out of certain values at certain stages of an object's life cycle, generating randomized values to provide more variety, adjusting values based on the volume of a specified output signal, or even automatically pitch instruments up or down depending on a parameter value.

A modulator's value is applied on top of the property's base value and any resolved automation value (i.e. the result of multiple automation curves placed on one property).

When multiple modulators are used on the same property, the resulting values of all the modulators are combined additively.

For information on adding modulators to various properties in your project, see the Authoring Events chapter on automation and modulation.

## 22.1 How to Read This Reference
  Property (Control) The name of the property as it appears in FMOD Studio and the type of control it is manipulated by. The types of controls are:

 Button: Click on a button to execute a command. Some buttons are toggles that are colored yellow to indicate if they are active.

 Dial: A control knob. Click and drag up and down to adjust the property's value.

 Dropdown: A menu where you select a value from a list. The current selection is displayed in the collapsed dropdown menu.

 Menu: A command or set of commands in the modulator's context menu.

 Number Box: A box displaying the value of the property. Click on the box's edit triangle to manually enter a value, or click and drag the value to make adjustments. Double click on the number box to reset its value.

 Ribbon Slider: A pair of horizontal sliders. Click and drag each slider handle left or right to adjust minimum and maximum values. If these values differ then a range is created between them. Click and drag this range to adjust both left and right handles at the same time. Units What the property is measured in. If a property does not use a unit of measurement no unit will be listed. Valid units are:

 st: Semitones

 dB: Decibels

 %: Percentage points

 ms: Milliseconds

 sec: Seconds Range The minimum and maximum values valid for that property. If a property does not use a range this will not be listed.

## 22.2 Random Modulator

A random modulator offsets a property value by an amount that is randomly selected from within a given range.

The random value is only generated when the event or snapshot instance with a modulated property is played, or the instrument whose property is being modulated is triggered.

For example, a random modulator on an event's pitch property will only generate a value when the event instance is started and won't regenerate a new one in the case of the event using a loop region. To generate a new random value, the event instance or snapshot instance must be restarted, or the instrument must be retriggered.

The range of values that a random modulator can generate is defined by modulated property's value and the random modulator's property value. When a random modulator is placed on a property that uses dB, it can generate values within a range whose the maximum value is the value of the modulated property and whose minimum value is the value of the modulated property minus the random modulator's property value. When a random modulator is placed on any other type of property, it can generate values within a range whose size is equal to the random modulator's property value, centered on the modulated property's post-automation value.
  Random (Dial) Provides a range for a random value to offset the modulated property by.

 Units: st, dB, or %

 Range: 0 st to 48 st, 0.00 dB to 80.0 dB, or 0.0% to 100.0%

## 22.3 AHDSR Modulator

An AHDSR modulator defines a modulation that follows an envelope. The envelope moves through states of attack, hold, decay, sustain and release.

In the attack state, the modulated property's value is interpolated from the initial value to the peak value.

In the hold state, the modulated property's value remains at the value set in the peak property.

In the decay state, the modulated property's value is interpolated from the peak value to the sustain value.

In the sustain state, the modulated property's value remains at the value set in the sustain property.

In the release state, the modulated property's value is interpolated from the peak value to the final value.
  Attack (Number Box) Adjusts how quickly the peak value is reached once the event or snapshot instance with a modulated property is played, or when the instrument whose property is being modulated has been triggered.

 Units: ms, sec

 Range: 0.00 ms to 60.0 sec Initial (Number Box) Adjusts the starting value of the property being modulated when the associated event, snapshot, or instrument has been triggered.

 Units: dB or %

 Range: -80.0 dB to 10.0 dB or -100% to 100% Hold (Number Box) Adjusts the period for which the modulated property's value remains at the peak value after reaching that value.

 Units: ms, sec

 Range: 0.00 ms to 60.0 sec Peak (Number Box) Adjusts the value of the property once the attack duration has finished. This value is ramped into from the initial value, remains at this value for the duration of the hold period, and ramps out to the sustain value.

 Units: dB or %

 Range: -80.0 dB to 10.0 dB or -100% to 100% Decay (Number Box) Adjusts the period for which the modulated property's value ramps between the peak and sustain values.

 Units: ms, sec

 Range: 0.00 ms to 60.0 sec Sustain (Number Box) Adjusts the value of the property being modulated once the decay duration has finished. This value is ramped into from the peak value and remains at this value before being released.

 Units: dB or %

 Range: -80.0 dB to 10.0 dB or -100% to 100% Release (Number Box) Adjusts the time it takes for the property being modulated to ramp out to the final value. Release happens when the event or snapshot instance with a modulated property has a non-immediate stop called on it, or when the instrument of the property being modulated has been untriggered. A synchronous instrument can only have its release play out if the playback cursor is still within the instrument's trigger region, and its trigger conditions no longer meet their requirement.

 Units: ms, sec

 Range: 0.00 ms to 60.0 sec Final (Number Box) Adjusts the final value of the property being modulated once the release duration has finished. This value is ramped into from the sustain value.

 Units: dB or %

 Range: -80.0 dB to 10.0 dB or -100% to 100% Clock Source (Menu)  Specifies whether the modulator bases its time-sensitive behavior on the global clock or the event instance's clock. The instance's clock may move faster than the global clock if the instance's pitch is adjusted up, and slower if its pitch is adjusted down.

 Range: Instance, Global

## 22.4 LFO Modulator

An LFO modulator automatically updates the value of a property over time, oscillating based on its shape, phase, direction, depth, and rate.

The modulator's graph gives a visual representation of how the modulator will affect the property over time. The vertical axis displays the possible values of the property and the horizontal axis displays the time or beats from when the modulator has started. The colored line indicates what the value of that property will be at the time indicated on the graph.

An LFO modulator begins oscillating when the parent object of the property being modulated is instantiated. For example, if a track volume fader is being modulated, it begins oscillating when the event instance is created. If a group bus volume fader is being modulated, it begins oscillating when an event routed into it has an instance created. If an instrument's volume is being modulated, it begins oscillating when the instrument is triggered.
  Shape (Dropdown) The waveform shape that the property value oscillates by between its minimum value and its maximum value.

 Range: Sine, Square, Triangle, Saw Up, Saw Down, Noise (Stepped), Noise (Ramped) Phase (Number Box) Controls at which point in the LFO waveform the modulator starts.

 Units: Deg

 Range: -180 deg to 180 deg Direction (Number Box) Shifts the value range up and down, proportionate to the current depth.

 Units: %

 Range: -100% to 100% Depth (Dial) Controls the value range that the modulator oscillates within.

 Units: st, dB, or %

 Range: 0 st to 48 st, 0.00 dB to 80.0 dB, or 0.0% to 100.0% Rate or Beats (Number Box) Controls the frequency of oscillation when the sync button is disabled, or the number of beats per oscillation when the sync button is enabled.

 Units: Hz or Beats

 Range: 0.00 Hz to 10.0 Hz or 0.02 beats to 64.0 beats Sync (Button) When enabled, the rate will change to a beats number box. This allows for oscillation that is synchronized with the current tempo of an event. If there are no tempo markers in an event, it defaults to 120 BPM and 4/4 time. This is only available to LFO modulators that exist in an event or snapshot. Clock Source (Menu)  Specifies whether the modulator bases its time-sensitive behavior on the global clock or the event instance's clock. The instance's clock may move faster than the global clock if the instance's pitch is adjusted up, and slower if its pitch is adjusted down.

 Range: Instance, Global

## 22.5 Sidechain Modulator

The sidechain modulator uses an envelope follower to monitor the signal of a sidechain effect, using that signal's strength to boost or reduce the value of the property being modulated. A sidechain modulator can only connect to sidechain inputs within the same event, or from one bus to another in the mixer view.

If the sidechain modulator is attached to a property measured in dB, the sidechain modulator will only lower it. For other property types, the modulation can be positive or negative.

If the amount property is a positive number then the value of the property being modulated will increase, and if the amount property is a negative number then the value of the property being modulated will decrease.

The amount property works in conjunction with the attack and release properties which dictate how fast or slow the sidechaining effect is applied.
  Amount (Dial) Adjusts the extent which the sidechain has on the modulated property when the sidechain signal exceeds the modulator's threshold.

 Units: st, %, dB

 Range: -48.0 dB to 48.0 dB, -100% to 100%, or 0.0 dB to 80.0 dB Attack (Dial) Adjusts how quickly the sidechaining is applied once the sidechain signal reaches the threshold.

 Units: ms

 Range: 10.0 ms to 500 ms Release (Dial) Adjusts how quickly the sidechaining is let go once the sidechain signal goes below the threshold.

 Units: ms, sec

 Range: 10.0 ms to 5.00 sec Threshold (Ribbon Slider) Defines what the volume range of the sidechain source's volume should reach in order to apply the amount property to the modulated property. If the sidechain's source's volume is below the threshold's minimum property, no adjustment is applied to the modulated property. If the sidechain's source's volume is at or above the threshold's maximum threshold, the full value of the amount property is applied. If the sidechain's source's volume is between the minimum and maximum threshold, the amount property is interpolated from zero to the full amount.

 Units: dB

 Range: -80.0 dB to 10.0 dB Clock Source (Menu)  Specifies whether the modulator bases its time-sensitive behavior on the global clock or the event instance's clock. The instance's clock may move faster than the global clock if the instance's pitch is adjusted up, and slower if its pitch is adjusted down.

 Range: Instance, Global

## 22.6 Spectral Sidechain Modulator

The spectral sidechain modulator monitors the signal of a spectral sidechain effect, and uses the strength of that signal to boost or reduce the value of the property being modulated. A spectral sidechain modulator in an event can only connect to spectral sidechain effects within that event, and a spectral sidechain modulator on a bus can only connect to spectral sidechain effects on buses.

The spectral sidechain modulator's amount property determines the maximum amount by which the modulated property can be adjusted. If the modulated property is measured in dB, the modulator can only lower it. For other property types, the modulator can adjust the property both up and down: If the modulator's amount property is a positive number, the modulator will increase the modulated property, and if the amount property is a negative number then the modulator will decrease the modulated property.
  Amount (Number box)  Adjusts the extent which the sidechain has on the modulated property when the sidechain signal exceeds the modulator's threshold.

 Units: st, %, dB

 Range: -48.0 dB to 48.0 dB, -100% to 100%, or 0.0 dB to 80.0 dB Attack (Number box)  Adjusts how quickly the sidechaining is applied once the sidechain signal reaches the threshold.

 Units: ms

 Range: 10.0 ms to 500 ms Release (Number box)  Adjusts how quickly the sidechaining is let go once the sidechain signal goes below the threshold.

 Units: ms, sec

 Range: 10.0 ms to 5.00 sec Threshold (Ribbon Slider)  Defines what the volume range of the sidechain source's volume should reach in order to apply the amount property to the modulated property. If the sidechain's source's volume is below the threshold's minimum property, no adjustment is applied to the modulated property. If the sidechain's source's volume is at or above the threshold's maximum threshold, the full value of the amount property is applied. If the sidechain's source's volume is between the minimum and maximum threshold, the amount property is interpolated from zero to the full amount.

 Units: dB

 Range: -80.0 dB to 10.0 dB Mode (Radio buttons)  Determines what property of the sidechained frequency band is used to adjust the modulated signal. The root mean square (RMS) value of the frequency band represents its level, whereas the spectral centroid is a rough approximation of its pitch.

 Range: RMS or Spectral Centroid Clock Source (Menu)  Specifies whether the modulator bases its time-sensitive behavior on the global clock or the event instance's clock. The instance's clock may move faster than the global clock if the instance's pitch is adjusted up, and slower if its pitch is adjusted down.

 Range: Instance, Global

## 22.7 Seek Modulator

A seek modulator causes a property's current value to ramp up or down at a fixed rate when it is set to a new value, instead of changing instantaneously.

The rate at which the modulated property's value changes is determined by its speed or ascending and descending properties, and is expressed as the fraction of the modulated property's range by which the property can increase or decrease in one second. For example, if the speed property is set to "0.1 range/s" and the modulated property's range is -24 to 24 semitones, setting the property to a new value will cause its current value to increase or decrease (as appropriate) at a rate of 4.8 semitones per second until it reaches that new value; and if the speed property is set to "1 range/s" and the property's range is -80 dB to 10 dB, setting the property to a new value will cause its current value to increase or decrease at a rate of 90 dB per second until it reaches that new value. Setting the modulator's speed to "Instant" causes the modulated property to jump instantly to its new value when set to a new value, just as if it did not have a seek modulator.

When a parameter is subject to both a seek modulator and velocity, setting the parameter to a new value causes it to ramp to that value at the rate specified by the seek modulator, then to resume moving at the rate specified by its velocity.
  Asymmetric (Radio buttons)  Determines whether the modulator functions in asymmetric mode. If off is selected, the rate at which the modulated property's value changes is based on the speed property, regardless of whether the modulated property's value is increasing or decreasing; whereas if on is selected, the modulated property's value changes at the rate specified by the ascending property when the modulated property's value is increasing, and by the descending property when the modulated property's value is decreasing. Speed/Ascending (Dial/number box)   If the asymmetric property is set to off, this property is displayed as a dial labeled "Speed," and represents the rate at which the modulated property's value changes when set to a value other than its current value. If the asymmetric property is set to on, this property is displayed as a number box labeled "Ascending," and represents the rate at which the modulated property's value changes when set to a value higher than its current value.

 Units: range/s

 Range: Instant or 0 range/s to 25 range/s Descending (Number box)  This property only appears if the asymmetric property is set to on, and represents the rate at which the modulated property's value changes when set to a value lower than its current value.

 Units: range/s

 Range: Instant or 0 range/s to 25 range/s Clock Source (Menu)  Specifies whether the modulator bases its time-sensitive behavior on the global clock or the event instance's clock. The instance's clock may move faster than the global clock if the instance's pitch is adjusted up, and slower if its pitch is adjusted down.

 Range: Instance, Global

## 22.8 Autopitch Modulator

The autopitch modulator automatically adjusts the pitch of the instrument being modulated based on the value of the parameter the instrument is on. It can only be applied to instruments placed on a parameter.

An autopitch modulator has a root pitch. This defines a point on the owning parameter at which the pitch of the instrument has a 0 semitones adjustment. From the root pitch the autopitch modulator adjusts the pitch of the instrument being modulated based on the value of the parameter. When the parameter's playback position is below the root pitch value, the autopitch modulator pitches the instrument being modulated down from the root pitch until it reaches the minimum value of the parameter. When the parameter's playback position is above the root pitch value, the autopitch modulator adjusts the pitch of the instrument being modulated up from the root pitch until it reaches the maximum value of the parameter.

The pitch value when the parameter is at its minimum value can be adjusted using the "min pitch" property.
  Root Pitch (Dial) The parameter value at which the instrument plays at its original pitch.

 Range: The minimum value of the parameter to the maximum value of the parameter. Min Pitch (Dial) The value of the pitch at the parameter's minimum value, expressed as a fraction of the pitch value at the root pitch position.

 Range: 0.00 to 1.00

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
