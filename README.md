# BIAS-FX-Clue-Midi
Modification of [MIDI CLUE BLE Glove](https://bit.ly/2PBzcX9) for BIAS
FX2.

## Operation

Touch button 3 toggles modes. 

### Mode 1: CC Program (Default)
This mode lets you select CC modes and change the default CC numbers:
71, 72, 73.  X value is returned on the first (tilt left and right)
value, Y value from 0° to 70° is the default (opposite of an
expression pedal, easier for a foot mount), and the proximity sensor
works as a momentary switch.
 * Physical Button 1: Decrease Selected CC Number
 * Physical Button 2: Increase Selected CC Number
 * Touch Button 1: Pause CC Messages 
 * Touch Button 2: Move cursor

### Mode 2 Bank Switch
Doesn't actually move your bank up and down but sets the bank
number...so you'll need some clairvoyance; Just make sure you have a
real bank selected.
 * Physical Button 1: Bank Down
 * Physical Button 2: Bank Up

### Mode 3 Toggle Presets
Toggles within the current bank
 * Physical Button 1: Preset 1
 * Physical Button 2: Preset 2
 * Touch Button 1: Preset 3
 * Touch Button 2: Preset 4

## What you'll need:
 * [Adafruit CLUE - nRF52840 Express with Bluetooth
   LE](https://www.adafruit.com/product/4500)
 * Battery (go rechargable! pick one)
   * Super Tiny[Lithium Ion Polymer Battery - 3.7v
     100mAh](https://www.adafruit.com/product/1570)
   * Tiny [Lithium Ion Polymer Battery with Short Cable - 3.7V
     350mAh](https://www.adafruit.com/product/4237)
 * Charger (pick one)
   * [MicroUSB](https://www.adafruit.com/product/1904)
   * [USB C](https://www.adafruit.com/product/4410)
 * Cable: I assume you have a cable that goes MicroUSB into your
   computer...if you don't go get it.
 
 ## Tutorial Adafruit has this tutorial on the [CLUE BLE MIDI
 Glove](https://learn.adafruit.com/clue-midi-glove), do that first.
