# 20. Instrument Reference

Instruments are fundamental to playing audio content in FMOD Studio, as well as for triggering certain kinds of behavior. This chapter describes the various types of instrument, as well as detailed information about their properties, behaviors, and features.

The properties of instruments are found in several different parts of FMOD Studio's interface.

 An instrument trigger region.

All instruments are displayed as trigger regions on the tracks and action sheets of events. These trigger regions display certain important properties of the instrument at all times.

 An instrument deck panel.

In addition to the properties displayed on their trigger regions, instruments have properties that appear in the deck while the instrument's trigger region is selected in the editor.

Finally, additional properties can be found in instruments' trigger behavior drawers. Instrument trigger behavior drawers are divided into two sections, "Conditions" and "Delay & Quantization." These sections define the circumstances in which the instrument can be triggered.

There are three kinds of trigger condition: Probability, parameter, and event. Instruments can be given all three kinds, in any combination. For information about how to add trigger conditions to events, see the Trigger Conditions section of the Working with Instruments chapter.

## 20.1 Common Instrument Properties

While each type of instrument has a unique list of controls and properties, there are some features that all instruments have in common.

### 20.1.1 Name (Text field)

 The name of an instrument appears at the top of its trigger region. By default, instruments are named after their instrument type or content. If an instrument's name is something other than its instrument type, its type is parenthetically appended to the name displayed on the trigger region.

### 20.1.2 Color (Color)

 The color of an instrument's trigger region has no effect on in-game behavior, but can make the instrument easier to identify at a glance in FMOD Studio. When first created, an instrument's color is determined by its type.

### 20.1.3 Sheet (Tab)

 The action sheet or parameter sheet on which an instrument's trigger region appears determines which parameter or event states can trigger the instrument.

### 20.1.4 Position (Multiple means of editing)

For instruments on parameter sheets, the horizontal position and length of the trigger region defines the range of parameter values that can trigger the instrument. For synchronous instruments, the horizontal position of the trigger region also determines which part of the associated asset plays when the instrument is overlapped by the timeline's playback position.

 Units: Parameter units.

### 20.1.5 Length (Multiple means of editing)

For instruments on parameter sheets, the horizontal position and length of the trigger region defines the range of parameter values that can trigger the instrument. For synchronous instruments, the length of the trigger region also determines when the timeline's playback position stops overlapping the instrument, and thus when the instrument must stop playing.

 Units: Parameter units.

### 20.1.6 Probability (Toggle button)

 If toggled on, the instrument has a probability trigger condition. If toggled off, the instrument does not, and the value of the chance property is ignored.

A probability trigger condition means that there's a chance (defined by the chance property, below) that the instrument triggers each time the instrument's other trigger behavior dictates that it should be triggered, i.e.: when the instrument is overlapped by the playback position, the playback position is at a bar or beat to which the instrument is quantized, and either all the instrument's parameter and event trigger conditions are met (if the instrument's AND/OR buttons are set to "AND") or at least one of the instrument's parameter and event trigger conditions are met (if the instrument's AND/OR buttons are set to "OR"). An instrument can have no more than one probability trigger condition.

### 20.1.7 Chance (Number box)

 This is the percentage chance that the instrument is triggered. This property is checked against a random number each time the instrument's other trigger behavior dictates it should be triggered.

 Units: Percentage Points.

 Automatable.

### 20.1.8 Conditions list (Multiple means of editing)

 The conditions list contains all the parameter and event conditions associated with the instrument. It does not include the instrument's probability trigger condition, if any. Each event or parameter trigger condition has properties of its own.

Parameter trigger conditions specify a parameter and a range of values into which that parameter's value must fall for the condition to be true. Event trigger conditions specify event states that the event must be in for the condition to be true. An instrument can have any number of event or parameter trigger conditions.

### 20.1.9 AND/OR (Radio buttons)

 These buttons determine which event or parameter conditions must be met for the instrument to be triggered when there are multiple event or parameter conditions present. If "OR" is selected, only one of the instrument's event or parameter conditions must be met; whereas if "AND" is selected, all of the instrument's event and parameter conditions must be met.

### 20.1.10 Parameter Name (Text field)
   The name of the parameter used by a parameter condition. Changing this property alters the name of the parameter, not the name of the condition.

### 20.1.11 Parameter Range (Ribbon slider)

 The range of values that the parameter must have for the parameter condition to be met (or not met, if the condition is inverted). This property only appears for parameter conditions based on built-in parameters and discrete and continuous user parameters.

### 20.1.12 Parameter Value (Dropdown menu)

 The specific value that the parameter must have for the parameter condition to be met (or not met, if the condition is inverted). This property only appears for parameter conditions based on labeled parameters.

### 20.1.13 Inverted (Toggle button)

 This toggle button determines whether the parameter's value must match or not match the parameter condition's parameter range or parameter value for the condition to be met. If inverted is toggled off, the parameter's value must match the parameter condition's parameter range or value; if it is toggled on, the parameter's value must not match the parameter condition's range or value.

### 20.1.14 Polyphony (Number box)

 Polyphony defines the maximum number of simultaneously playing instances of the instrument that can be triggered by the parent event instance. If the event instance attempts to trigger a new instance of the instrument while the number of playing instances of that instrument triggered by the same event instance is equal to the polyphony, whether a new instance is played and an existing one culled depends on the instrument's stealing behavior.

### 20.1.15 Stealing (Dropdown menu)

 The stealing mode of an instrument determines what happens when the instrument is triggered and playing a new instance of the instrument would cause the number of simultaneously playing instances of that instrument triggered by the same event instance to exceed the instrument's polyphony. If stealing is set to oldest, the oldest instance of the instrument immediately stops as the new instance begins; whereas if stealing is set to none, no instance of the instrument is stopped and no new instance of the instrument begins playing.

### 20.1.16 Time/Tempo control (Radio buttons)

 If this control is set to time, the instrument waits to play for a period of time after being triggered defined by the delay interval property: If the instrument is asynchronous, it waits for the period of time specified by the delay interval property before playing; and if it is synchronous, it waits for the period of time specified by the delay interval property and then only plays if it is still overlapped by the parameter playback position. If this control is instead set to tempo, the instrument only triggers on specific beats or bars specified by the quantization interval property.

### 20.1.17 Delay Interval (Ribbon slider)

 Delay interval defines the period of time that must elapse after the instrument is triggered before it begins playing. If the minimum and maximum values of the ribbon slider are the same, the period of time's length is fixed. If the minimum and maximum values of the ribbon slider differ, the period of time's length is randomized within that range each time the instrument's trigger conditions are met.

 Units: Milliseconds or seconds.

### 20.1.18 Quantization Interval (Radio buttons)

 An instrument's quantization interval specifies on which of the timeline's beats or bars the instrument's trigger conditions are checked while the instrument is overlapped by the playback position. The bar and beat numbers used by this property are those that appear on the timeline when the editor is set to beats mode, as defined by the event's tempo markers.

## 20.2 Single Instrument

Single instruments are a kind of instrument that can hold only one audio file. As such, single instruments lack playlists, but otherwise closely resemble multi instruments. Single instruments are the foundation of most other instrument types.

 A single instrument trigger region.

 A single instrument deck panel.

### 20.2.1 Content Graphic (Graphic)

 The waveform of the audio asset associated with a single instrument is displayed on its trigger region. If the instrument is asynchronous, this content is surrounded by a border. If the instrument is synchronous and its play count is greater than one, multiple copies of the waveform may be displayed, provided the trigger region is long enough.

### 20.2.2 Fade Curves (Mouse-editable graphics)

 A fade curve defines how an instrument's volume ramps from silence to full volume when the playback position moves onto the instrument, or how it ramps from full volume to silence when the playback position moves off the instrument. Instruments on action sheets can not have fade curves. Each instrument on a parameter sheet can have one fade curve for its left side, and one fade curve for its right. Instruments do not have fade curves by default.

### 20.2.3 Volume (Dial)

 Volume defines the gain applied to the instrument's output.

 Units: Decibels.

 Automatable and Modulatable.

### 20.2.4 Pitch (Number box)

 Pitch defines the amount of pitch adjustment applied to the instrument's output. The pitch properties of instruments on parameter sheets other than the timeline sheet are compatible with autopitch modulators.

 Units: Semitones.

 Automatable and Modulatable.

### 20.2.5 Start Offset (Number box)

 The start offset of a single instrument determines the point within its associated audio asset from which it starts playing when the instrument is triggered, expressed as a percentage of the length of the audio file associated with the instrument. For asynchronous instruments, this directly determines the position from which the associated audio file begins to play when the instrument is triggered. For synchronous instruments, this offset is added to the position of the playback position inside the instrument's waveform, and so is an exception to the rule that the part of a single instrument's waveform that plays is the part of the waveform that's overlapped by the playback position.

 Units: Percentage points.

 Automatable and Modulatable.

### 20.2.6 Async (Toggle button)

 A single instrument's synchronous or asynchronous state determines whether it is possible to seek or scrub within the waveform displayed on its trigger region. If an instrument is synchronous, the section of the waveform underneath the timeline playback position is the part of the asset that plays while the instrument is triggered; whereas if the instrument is asychronous, the playback position's location on the instrument has no effect on which part of the associated asset plays. Instruments on parameters other than the timeline are always asynchronous. For more information about synchronous and asynchronous instruments, see the Synchronous and Asynchronous Instruments section of the Working With Instruments chapter.

### 20.2.7 Cut (Toggle button)

 An asynchronous instrument's cut mode determines whether it stops playing when its trigger conditions cease being met. The cut toggle button only appears in the deck of asynchronous instruments.

### 20.2.8 Loop Instrument (Toggle button)

 Looping a synchronous instrument causes it to loop in accordance with its play count property. Specifically, the play count of a synchronous instrument is the number of times its content graphic is iterated on that instrument's trigger region, limited by the amount of horizontal space on that trigger region; whereas the play count of an asynchronous instrument is the number of times that instrument plays its associated audio file when triggered. This toggle button is visually identical to the Loop Playlist button found on multi instruments, but differs in function.

### 20.2.9 Play Count (Number box)

 This property is only available for instruments whose loop instrument toggle buttons are enabled. It determines the number of times that instrument can loop, as described in the sections on those toggle buttons. If this property is infinite on an asynchronous instrument, the associated instrument or playlist will finish playing out its current loop when the instrument is untriggered, then stop; but if it is finite, it will loop a number of times equal to play count even if the instrument is untriggered before it is finished.

### 20.2.10 Asset Preview (Graphic)

 The waveform of the audio asset associated with a single instrument is displayed in its asset preview.

## 20.3 Multi Instrument

A multi instrument is a kind of instrument with a playlist. When the instrument is triggered, an item from its playlist is selected for play. A multi instrument's playlist can contain nearly any kind of instrument, including single instruments, event instruments, programmer instruments, command instruments, silence instruments, and other multi instruments.

 A multi instrument trigger region.

 A multi instrument deck panel.

### 20.3.1 Content Graphic (Multiple means of editing)

 The waveforms and timelines of the instruments in a multi instrument's playlist are displayed on its trigger region. If there is enough room, each playlist entry's content is marked by a letter in a circle, corresponding to the letter that appears on that playlist entry in the deck. If the instrument is asynchronous, each playlist entry's content is surrounded by a border.

### 20.3.2 Fade Curves (Mouse-editable graphics)

 A fade curve defines how an instrument's volume ramps from silence to full volume when the playback position moves onto the instrument, or how it ramps from full volume to silence when the playback position moves off the instrument. Instruments on action sheets can not have fade curves. Each instrument on a parameter sheet can have one fade curve for its left side, and one fade curve for its right. Instruments do not have fade curves by default.

### 20.3.3 Volume (Dial)

 Volume defines the gain applied to the instrument's output.

 Units: Decibels.

 Automatable and Modulatable.

### 20.3.4 Pitch (Number box)

 Pitch defines the amount of pitch adjustment applied to the instrument's output. The pitch properties of instruments on parameter sheets other than the timeline sheet are compatible with autopitch modulators.

 Units: Semitones.

 Automatable and Modulatable.

### 20.3.5 Start Offset (Number box)

 The start offset of a multi instrument determines the point within the first playlist entry it selects to play from when the instrument is triggered, expressed as a percentage of the length of that playlist entry. It only affects the first playlist entry selected each time the instrument is triggered. In asynchronous instruments, this directly determines the position from which the associated audio file begins to play when the instrument is triggered. For single, multi, and event instrument playlist entries in synchronous instruments, this offset is added to the position of the playback position inside the instrument's waveform, and so is an exception to the rule that the part of a single instrument's waveform that plays is the part of the waveform that's overlapped by the playback position.

 Units: Percentage points.

 Automatable and Modulatable.

### 20.3.6 Async (Toggle button)

 An instrument's synchronous or asynchronous state determines whether it is possible to seek or scrub within the waveforms displayed on its trigger region. If an instrument is synchronous, the section of the waveform underneath the timeline playback position is the part of the asset that plays while the instrument is triggered; whereas if the instrument is asynchronous, the playback position's location on the instrument has no effect on which part of the associated assets play. Instruments on parameters other than the timeline are always asynchronous. For more information about synchronous and asynchronous instruments, see the Synchronous and Asynchronous Instruments section of the Working With Instruments chapter.

### 20.3.7 Cut (Toggle button)

 An asynchronous instrument's cut mode determines whether it stops playing when its trigger conditions cease being met. The cut toggle button only appears in the deck of asynchronous instruments.

### 20.3.8 Playlist Selection Mode (Dropdown menu)

 This property represents the playlist selection mode of the instrument's playlist. There are four playlist selection modes:

- Shuffle. Items in the playlist are selected for playback in random order. In addition, as long as the playlist contains at least three instruments and does not include play percentages, no instrument in that playlist will be selected twice in a row.

- Randomize. Items in the playlist are selected for playback in random order. The frequency and recency with which items have been selected in the past has no bearing on the probability of those items being selected in future.

- Sequential - play scope. Items in the playlist are selected for playback in the order in which they appear. When determining which items have already been selected, the playlist takes into account items selected in the current event instance and since the start of that event instance.

- Sequential - global scope. Items in the playlist are selected for playback in the order in which they appear. When determining which items have already been selected, the playlist takes into account items selected in all past and present instances of the event.

- Sequential - instance scope. Items in the playlist are selected for playback in the order in which they appear. When determining which items have already been selected, the playlist takes into account items selected in the current event instance, even if they were selected before it was stopped and restarted.

Playlists are set to shuffle by default.

### 20.3.9 Loop Playlist (Toggle button)

 Looping a synchronous multi instrument causes it to play multiple playlist entries in accordance with its play count property. Specifically, the play count of a synchronous multi instrument represents the maximum number of times it can select playlist entries to play, provided it remains triggered; whereas the play count of an asynchronous instrument is the number of times that instrument selects a playlist entry to play when triggered. This toggle button is visually identical to the Loop Instrument button found on single instruments, but differs in function.

### 20.3.10 Play Count (Number box)

 This property is only available for instruments whose loop playlist toggle buttons are enabled. It determines the number of times that instrument can loop, as described in the sections on those toggle buttons. If this property is infinite on an asynchronous instrument, the associated instrument or playlist will finish playing out its current loop then stop looping when the instrument is untriggered; but if it is finite, it will loop a number of times equal to play count even if the instrument is untriggered before it is finished.

### 20.3.11 Playlist (Playlist)

 A list of all the instruments that the multi instrument can select to spawn. Each instrument has a letter that corresponds to the letters that appear on the multi instrument's content graphic, a name, and a play percentage that weights selection when the instrument's playlist selection mode is shuffle or randomize.

 Selecting a playlist entry causes the corresponding instrument to be displayed in the deck to the right of the multi instrument.

 Selecting multiple playlist entries causes one of the instruments to be displayed in the deck to the right of the multi instrument, and highlights properties common to all the selected playlist entries' instruments in gold. Changes made to a property highlighted in gold change that property for every playlist entry in the selection.

## 20.4 Event Instrument

An event instrument (also known as an 'event reference instrument') is a kind of instrument that plays an instance of a specified event elsewhere in the project when triggered. The resultant instance's output is routed into the track that holds the event reference instrument.

 An event instrument trigger region.

 An event instrument deck panel.

### 20.4.1 Content Graphic (Multiple means of editing)

 If the event referenced by an event instrument has a parameter sheet for its timeline, the content of that sheet is displayed on the instrument's trigger region, surrounded by a border.

### 20.4.2 Fade Curves (Mouse-editable graphics)

 A fade curve defines how an instrument's volume ramps from silence to full volume when the playback position moves onto the instrument, or how it ramps from full volume to silence when the playback position moves off the instrument. Instruments on action sheets can not have fade curves. Each instrument on a parameter sheet can have one fade curve for its left side, and one fade curve for its right. Instruments do not have fade curves by default.

### 20.4.3 Volume (Dial)

 Volume defines the gain applied to the master track volume fader of any instance of the associated event created by the event instrument. This means that the fader volume of an event instance created by an event instrument may differ from that of an instance of the same event created by your game's code.

 Units: Decibels.

 Automatable and Modulatable.

### 20.4.4 Pitch (Number box)

 Pitch defines the amount of pitch adjustment applied to the instrument's output. The pitch properties of instruments on parameter sheets other than the timeline sheet are compatible with autopitch modulators.

 Units: Semitones.

 Automatable and Modulatable.

### 20.4.5 Start Offset (Number box)

 The start offset of an event instrument determines the point within its associated event's timeline at which the timeline playback position should start when the instrument is triggered, expressed as a percentage of the length of the associated event's timeline. For this purpose, the associated event's timeline is assumed to start at position 0:00.000 and to end at the right edge of the rightmost instrument or logic marker on the event's timeline sheet.

 Units: Percentage points.

 Automatable and Modulatable.

### 20.4.6 Cut (Toggle button)

 An instrument's cut mode determines whether it stops playing when its trigger conditions cease being met.

### 20.4.7 Parameter value (Dial)

 If the event referenced by the event instrument has any user parameters, those parameters are displayed as dials in the deck when the event instrument is selected. If such a parameter is subject to parameter linking, a small hollow circle is displayed next to its dial to indicate that it is linked. The referenced event's built-in parameters and timeline parameter are not displayed in the deck when the event instrument is selected.

 Automatable and Modulatable.

## 20.5 Scatterer Instrument

The scatterer instrument is a type of instrument with features that permit spatial and temporal randomization.

 A scatterer instrument trigger region.

 A scatterer instrument deck panel.

When a scatterer instrument is triggered, an item from its playlist is selected for play. A scatterer instrument's playlist can contain single instruments, event instruments, programmer instruments, multi instruments, command instruments, and silence instruments.

A scatterer instrument can select and spawn an instrument from its playlist regardless of when the previous one it spawned finishes playing, can randomize the volume and pitch of each spawned instance individually, and can assign a random offset to the position of each spawned instance for the purposes of panning and other 3D behaviors.

The item selected from a scatterer instrument's playlist depends on the instrument's playlist selection mode. By default, a scatterer instrument's playlist selection mode is set to shuffle. To change it, use the playlist selection mode dropdown menu.

### 20.5.1 Fade Curves (Mouse-editable graphics)

 A fade curve defines how an instrument's volume ramps from silence to full volume when the playback position moves onto the instrument, or how it ramps from full volume to silence when the playback position moves off the instrument. Instruments on action sheets can not have fade curves. Each instrument on a parameter sheet can have one fade curve for its left side, and one fade curve for its right. Instruments do not have fade curves by default.

### 20.5.2 Volume (Dial)

 Volume defines the gain applied to the instrument's output. If a random modulator is attached to this property, the adjustment applied by that modulator is randomized once each time the instrument is triggered. To randomize the volume of individual spawned playlist entry instances, see the Vol Rnd property, below.

 Units: Decibels.

 Automatable and Modulatable.

### 20.5.3 Pitch (Dial)

 Pitch defines the amount of pitch adjustment applied to the instrument's output. The pitch properties of instruments on parameter sheets other than the timeline sheet are compatible with autopitch modulators. If a random modulator is attached to this property, the adjustment applied by that modulator is randomized once each time the instrument is triggered. To randomize the pitch of individual playlist entry instances, see the Pitch Rnd property, below.

 Units: Semitones.

 Automatable and Modulatable.

### 20.5.4 Time/Tempo (Radio buttons)

 These buttons determine whether the scatterer instrument selects playlist entries to play sounds based on the passage of time, or on specific bars and beats. If time is selected, it selects entries to play in intervals determined by the min & max spawn interval property, below. If tempo is selected, it instead selects entries to play at intervals determined by the quantization interval property, below.

### 20.5.5 Min & Max Spawn Interval (Ribbon slider)

 Min & max spawn interval define the range of duration that can pass between the start of one playlist entry instance spawned by that scatterer instrument and the start of the next. These values are divided by the value of the spawn rate property, below. This property only appears if the time/tempo property is set to time.

 Units: Milliseconds or seconds.

### 20.5.6 Quantization Interval (Radio buttons)

 A scatterer instrument's quantization interval specifies on which of the timeline's beats or bars the instrument can select an entry from its playlist to spawn. The bar and beat numbers used by this property are those that appear on the timeline when the editor is set to beats mode, as defined by the event's tempo markers. These values are influenced by the value of the spawn rate property, below. This property only appears if the time/tempo property is set to tempo.

### 20.5.7 Spawn Rate (Dial)

 This property scales the frequency with which the instrument selects a playlist entry to spawn. If the time/tempo property is set to time, the min and max spawn interval properties are divided by the spawn rate to determine the amount of time that passes between one playlist entry being selected to spawn and the next being selected. If the time/tempo property is set to tempo, the spawn rate instead represents the amount by which the instrument progresses towards a playlist entry being selected on each beat or bar to which the instrument is quantized; when progress equals or exceeds 100%, a playlist entry is selected to spawn and progress is reduced by 100 percentage points.

 Units: Percentage points.

 Automatable and Modulatable.

### 20.5.8 Spawn Total (Dial)

 This property specifies the maximum number of times the instrument may select an entry from its playlist to spawn each time it becomes triggered. If the instrument is untriggered before it reaches this spawn count, it stops selecting playlist entries.

### 20.5.9 Vol Rnd (Dial)

 This property acts like a randomization modulator on the volume of each entry in the scatterer instrument's playlist: Each time the instrument selects a playlist entry to spawn, it adjusts the volume of that spawned sound by a random amount between the value of this property and 0 dB.

 Units: Decibels.

### 20.5.10 Pitch Rnd (Dial)

 This property acts like a randomization modulator on the pitch of each entry in the scatterer instrument's playlist: Each time the instrument selects a playlist entry to spawn, it adjusts the pitch of that spawned sound to a random value within the specified range of values, centered on the property's base value.

 Units: Semitones.

### 20.5.11 Min & Max Scatter Distance (Ribbon slider)

 These properties define the spatial randomization applied by the scatterer instrument. Each time the scatterer instrument selects a playlist entry to spawn, the position of the spawned sound is set to a random location in 3D space that's no closer to the event emitter than the min scatter distance and no further from the event emitter than the max scatter distance. This randomized position is used to calculate the spawned sound's 3D attributes for the purposes of spatialization and other 3D behavior. These properties only affect the scatterer instrument instance itself and are unrelated to the event's Min and Max Distance macros. Regardless of how the Min and Max Distance macros are configured, the scatterer instrument spawns its playlist entries within a range defined by the Min & Max Scatter Distance. If a spatializing effect is affecting the output of the spatializer instrument, the min and max distance of that effect affects the range at which the scatterer instrument's spawned sounds become audible, as it does for any audio signal passed into it, but it does not affect the Min & Max Scatter Distance at all.

### 20.5.12 Polyphony (Dial)

 This dial sets the maximum number of spawned sounds that an instance of the scatterer instrument may play simultaneously. If the number of simultaneously playing spawned sounds is equal to this number when the instrument attempts to select a playlist entry to spawn, it will fail to span the new sound or cull one of its existing sounds as per the instrument's spawn stealing property, below.

### 20.5.13 Spawn Stealing (Radio buttons)

 These buttons determine how a scatterer instrument behaves when it attempts the select a new playlist entry to spawn when the number of concurrently-playing spawned sounds is equal to the instrument's polyphony. If spawn stealing is set to oldest, the oldest playing spawned sound is culled, and the selected playlist entry is spawned normally. If spawn stealing is set to none, none of the playing spawned sounds are culled, and the selected playlist entry is not spawned.

### 20.5.14 Cut (Toggle button)

 An asynchronous instrument's cut mode determines whether it stops playing when its trigger conditions cease being met. The cut toggle button only appears in the deck of asynchronous instruments.

### 20.5.15 Playlist Selection Mode (Dropdown menu)

 This property represents the playlist selection mode of the instrument's playlist. There are four playlist selection modes:

- Shuffle. Items in the playlist are selected for playback in random order. In addition, as long as the playlist contains at least three instruments and does not include play percentages, no instrument in that playlist will be selected twice in a row.

- Randomize. Items in the playlist are selected for playback in random order. The frequency and recency with which items have been selected in the past has no bearing on the probability of those items being selected in future.

- Sequential - play scope. Items in the playlist are selected for playback in the order in which they appear. When determining which items have already been selected, the playlist takes into account items selected in the current event instance and since the start of that event instance.

- Sequential - global scope. Items in the playlist are selected for playback in the order in which they appear. When determining which items have already been selected, the playlist takes into account items selected in all past and present instances of the event.

- Sequential - instance scope. Items in the playlist are selected for playback in the order in which they appear. When determining which items have already been selected, the playlist takes into account items selected in the current event instance, even if they were selected before it was stopped and restarted.

Playlists are set to shuffle by default.

### 20.5.16 Playlist (Playlist)

 A list of all the instruments that the scatterer instrument can select to spawn. Each instrument has a letter that corresponds to the letters that appear on the scatterer instrument's content graphic, a name, and a play percentage that weights selection when the instrument's playlist selection mode is shuffle or randomize.

 Selecting a playlist entry causes the corresponding instrument to be displayed in the deck to the right of the scatterer instrument.

 Selecting multiple playlist entries causes one of the instruments to be displayed in the deck to the right of the scatterer instrument, and highlights properties common to all the selected playlist entries' instruments in gold. Changes made to a property highlighted in gold change that property for every playlist entry in the selection.

## 20.6 Programmer Instrument

A programmer instrument is kind of instrument that's a placeholder for a sound to be selected at run time. When a programmer instrument is triggered in your game, it generates a callback which is passed to your game's code. Your game's code can then specify an audio file for the FMOD Engine to play. Programmer instruments otherwise function similarly to single instruments.

 A programmer instrument trigger region.

 A programmer instrument deck panel.

For an example of how programmer instruments can be used in a game's code, see the Dialog and Localization section of the FMOD Engine User Manual.

For the purposes of auditioning in FMOD Studio, programmer instruments can be assigned placeholder audio files. These placeholder files are not built into banks and do not play when the instrument is triggered in your game. They exist purely so that programmer instruments can make a sound when auditioned in FMOD Studio.

### 20.6.1 Placeholder Graphic (Multiple means of editing)

 The waveform of the placeholder audio file associated with a programmer instrument is displayed on its trigger region. If the instrument is asynchronous, this content is surrounded by a border. If the instrument is synchronous and its play count is greater than one, multiple copies of the waveform may be displayed, provided the trigger region is long enough. This graphic has no impact on in-game behavior, but may be a useful guide when positioning instruments, automation, and logic markers.

### 20.6.2 Fade Curves (Mouse-editable graphics)

 A fade curve defines how an instrument's volume ramps from silence to full volume when the playback position moves onto the instrument, or how it ramps from full volume to silence when the playback position moves off the instrument. Instruments on action sheets can not have fade curves. Each instrument on a parameter sheet can have one fade curve for its left side, and one fade curve for its right. Instruments do not have fade curves by default.

### 20.6.3 Volume (Dial)

 Volume defines the gain applied to the instrument's output.

 Units: Decibels.

 Automatable and Modulatable.

### 20.6.4 Pitch (Number box)

 Pitch defines the amount of pitch adjustment applied to the instrument's output. The pitch properties of instruments on parameter sheets other than the timeline sheet are compatible with autopitch modulators.

 Units: Semitones.

 Automatable and Modulatable.

### 20.6.5 Start Offset (Number box)

 The start offset of a programmer instrument determines the point within an audio asset from which it starts playing when the instrument is triggered, expressed as a percentage of the length of the audio asset. For asynchronous instruments, this directly determines the position from which the audio file begins to play when the instrument is triggered. For synchronous instruments, this offset is added to the position of the playback position inside the instrument's waveform, and so is an exception to the rule that the part of a synchronous instrument's waveform that plays is the part of the waveform that's overlapped by the playback position.

 Units: Percentage points.

### 20.6.6 Async (Toggle button)

 A programmer instrument's synchronous or asynchronous state determines whether it is possible to seek or scrub within the waveform displayed on its trigger region. If an instrument is synchronous, the part of the asset that plays while the instrument is triggered depends on the position of the playback position on the instrument's trigger region; whereas if the instrument is asynchronous, the playback position's location on the instrument has no effect on which part of the associated asset plays. Instruments on parameter sheets other than the timeline are always asynchronous. For more information about synchronous and asynchronous instruments, see the Synchronous and Asynchronous Instruments section of the Working With Instruments chapter.

### 20.6.7 Cut (Toggle button)

 An asynchronous instrument's cut mode determines whether it stops playing when its trigger conditions cease being met. The cut toggle button only appears in the deck of asynchronous instruments.

### 20.6.8 Loop Instrument (Toggle button)

 Looping a programmer instrument causes it to loop in accordance with its play count property. Specifically, the play count of a synchronous programmer instrument is the number of times its placeholder graphic is iterated on that instrument's trigger region, limited by the amount of horizontal space on that trigger region, and also determines how many times an audio file played by the instrument will play as if the instrument were a single instrument; whereas the play count of an asynchronous instrument is the number of times that instrument plays an audio file when triggered. This toggle button is visually identical to the Loop Playlist button found on multi instruments, but differs in function.

### 20.6.9 Play Count (Number box)

 This property is only available for instruments whose loop instrument or loop playlist toggle buttons are enabled. It determines the number of times that instrument plays, as described in the sections on those toggle buttons. If this property is infinite on an asynchronous instrument, the associated instrument or playlist will finish playing out its current loop then stop looping when the instrument is untriggered; but if it is finite, it will loop a number of times equal to play count even if the instrument is untriggered before it is finished.

### 20.6.10 Placeholder Preview (Multiple means of editing)

 The waveform of an audio asset associated with a programmer instrument is displayed in the instrument's placeholder preview. This placeholder has no impact on in-game behavior, but can be useful when auditioning the event in FMOD Studio.

## 20.7 Command Instrument

A command instrument is a kind of instrument that does not produce audio output. Instead, when a command instrument is triggered, it issues a command to some part of your FMOD Studio project. Commands can be used to change parameter values and to stop and start events and snapshots.

 A command instrument trigger region.

 Several command instrument deck panels, each set to a different command.

### 20.7.1 Command Type (Dropdown menu)

 The type of command associated with the instrument. Each command type does something different, as described below.

- Start event. Creates a new instance of the target event or snapshot.

- Stop event. Causes all instances of the target event or snapshot to enter the stopping event state.

- Stop event - immediate. Causes all instances of the target event or snapshot to enter the stopped event state.

- Set parameter. Sets the value of the target parameter. If the target parameter is a local parameter, its value is set only in the local event instance; if the target parameter is a global parameter, its value is set globally.

- Increment parameter. Increases or decreases the target parameter by a specific amount, capped by the minimum and maximum values of the parameter. If the target parameter is a local parameter, its value is incremented only in the local event instance; if the target parameter is a global parameter, the global parameter's value is incremented.

### 20.7.2 Target (Dropdown menu)

 The target of the command. If the command type is start event, stop event, or stop event - immediate, the target must be an event or snapshot. If the command type is set parameter or increment parameter, the target must be a parameter.

### 20.7.3 Value (Number box)

 The value to which the target parameter is to be set. This property is only available if the command type is set parameter.

### 20.7.4 Delta Value (Number box)

 The value by which the target parameter is to be incremented (or decremented, if the delta value is negative). This property is only available if the command type is increment parameter.

## 20.8 Silence Instrument

A silence instrument is a kind of instrument that does not produce any output. When added to a consecutive action sheet or the playlist of a multi instrument or scatterer instrument, a silence instrument allows you define a circumstance in which the action sheet or instrument does not produce any sound.

Silence instruments are always asynchronous.

 A silence instrument trigger region.

 A silence instrument deck panel.

### 20.8.1 Duration (Dial)

 Duration defines the time for which the silence instrument remains active after being triggered. The value of this property is meaningful only if something is waiting for the silence instrument to finish playing.

 Units: Milliseconds or seconds.

 Automatable and Modulatable.

## 20.9 Snapshot Instrument

Snapshot instruments are a type of event instrument. Triggering a snapshot instrument causes a new instance of the corresponding snapshot to begin playing. When the playback position leaves the snapshot instrument, the instrument is untriggered, and the corresponding snapshot instance stops.

 A snapshot instrument trigger region.

 The snapshot instrument deck panel.

Each time a snapshot instrument is triggered, a new instance of the snapshot begins to play. This means that multiple simultaneous instances of the same snapshot can play at the same time, whether by multiple different snapshot instruments or as a result of the same snapshot instrument being triggered more than once in one or more instances of its parent event. Snapshot instances can also be started and stopped by your game's code.

The property values of a snapshot instance started by a snapshot instrument are affected by the snapshot instrument's intensity.

For more information about snapshots, see the snapshots and the tracks view section of the mixing chapter.

### 20.9.1 Fade Curves (Mouse-editable graphics)

 A snapshot instrument's fade curve defines how the snapshot instance's intensity ramps from zero to the value of its intensity property when the playback position moves onto the instrument, or how it ramps from the value of its intensity property to zero when the playback position moves off the instrument. Instruments on action sheets can not have fade curves. Each instrument on a parameter sheet can have one fade curve for its left side, and one fade curve for its right. Instruments do not have fade curves by default.

### 20.9.2 Snapshot (Dropdown menu)

 This property indicates which snapshot plays when the instrument is triggered.

### 20.9.3 Intensity (Dial)

 This property acts as a multiplier to the intensity of any instance of the associated snapshot created by the instrument.

## 20.10 AudioMotors2 Instrument

AudioMotors2 instruments are a type of instrument designed for vehicle engine sound synthesis. This instrument type is developed and maintained by Le Sound.

For more information about this plug-in, see Le Sound's documentation.

## 20.11 AudioRain Instrument

AudioRain instruments are a type of instrument designed for rain sound synthesis. This instrument type is developed and maintained by Le Sound.

For more information about this plug-in, see Le Sound's documentation.

## 20.12 AudioWeather Instrument

AudioWeather instruments are a type of instrument designed for weather sound synthesis. This instrument type is developed and maintained by Le Sound.

For more information about this plug-in, see Le Sound's documentation.

## 20.13 AudioWind Instrument

AudioWind instruments are a type of instrument designed for wind sound synthesis. This instrument type is developed and maintained by Le Sound.

For more information about this plug-in, see Le Sound's documentation.

## 20.14 Haptics Instrument

Haptics instruments are a type of instrument designed for synthesizing device vibrations from a haptic file created in Meta Haptics Studio.

### 20.14.1 Auditioning Support

The haptics instrument can be auditioned by connecting a controller to your computer and auditioning an event containing a haptics instrument.

 Auditioning is supported with the following devices and platforms:

  |   | Windows  | Mac  | Linux

  | PS5  | ✓  |   |

  | PS4  | ✓  |   |

  | PSVR2  |   |   |

  | Quest 3  |   |   |

  | Switch 1/2  |   |   |

  | Xbox Series X/S  | ✓  |   |

  | Xbox One  | ✓  |   |

### 20.14.2 Advanced Haptics Support

Haptics support is available in `simple` vs `advanced` varieties.

 Simple haptics provide basic vibration by changing only the strength (amplitude) of a motor, resulting in a general “rumble” sensation that is not very detailed.

 Advanced haptics use both amplitude and frequency to drive more precise actuators, allowing vibrations to feel sharper, smoother, or more textured.

 This enables more expressive and localized feedback, such as simulating surfaces, impacts, or subtle motion.

 Advanced haptics is supported with the following devices:

  |   | Advanced haptics  | Simple haptics

  | PS5  | ✓  |

  | PS4  |   | ✓

  | PSVR2  | ✓  |

  | Quest 3  | ✓  |

  | Switch 1/2  |   | ✓

  | Xbox Series X/S  |   | ✓

  | Xbox One  |   | ✓

 A haptics instrument trigger region.

 A haptics instrument deck panel.

### 20.14.3 Clip (Data drop)

 Use this widget to specify the haptic clip to synthesize. You can either use drag and drop, or select "Browse" and navigate to the file in the browser provided.

### 20.14.4 Left (Dial)

 Left defines the output strength of the synthesized vibration on the left device or motor. Lower percentage values soften the vibration, and a value of 100% plays the vibration back at the original strength.

 Units: Percentage.

 Automatable and Modulatable.

### 20.14.5 Right (Dial)

 Right defines the output strength of the synthesized vibration on the right device or motor. Lower percentage values soften the vibration, and a value of 100% plays the vibration back at the original strength.

 Units: Percentage.

 Automatable and Modulatable.

FMOD Studio User Manual 2.03.15 (2026-09-21). © 2026 Firelight Technologies Pty Ltd.
