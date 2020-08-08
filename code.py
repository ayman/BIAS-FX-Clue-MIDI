"""
CLUE BLE MIDI
Sends MIDI CC values based on accelerometer x & y and proximity sensor
Touch #0 switches Bank/Preset patches
Touch #1 picks among the three CC lines w A&B buttons adjusting CC numbers
Touch #2 starts/stops sending CC messages (still allows Program Change)
"""
import time
from adafruit_clue import clue
import adafruit_ble
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
import adafruit_ble_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange

# from adafruit_midi.note_on import NoteOn
# from adafruit_midi.pitch_bend import PitchBend
import simpleio
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect

# Mode Setting
MODE_SETTING = 0

# --- Pick your midi out channel here ---
MIDI_CHANNEL = 1

# --- Pick your MIDI CC numbers here ---
CC_X_NUM = 71
CC_Y_NUM = 72
CC_PROX_NUM = 73

# --- Pick Bank & Preset pairs here ---
PATCH_HOME = 1
# first number is the Bank, second is the Preset
TOUCH_PATCH = [(PATCH_HOME, 1),
               (PATCH_HOME, 2),
               (PATCH_HOME, 3),
               (PATCH_HOME, 4)]

PATCH_COUNT = len(TOUCH_PATCH)
# start on the last one so first time it is pressed it goes to first
PATCH_INDEX = (PATCH_COUNT - 1)

CC_X = 0
CC_Y = 0
CC_PROX = 0

# Use default HID descriptor
MIDI_SERVICE = adafruit_ble_midi.MIDIService()
ADVERTISEMENT = ProvideServicesAdvertisement(MIDI_SERVICE)

BLE = adafruit_ble.BLERadio()
if BLE.connected:
    for c in BLE.connections:
        c.disconnect()

MIDI = adafruit_midi.MIDI(midi_out=MIDI_SERVICE, out_channel=MIDI_CHANNEL - 1)

print("advertising")
BLE.name = "BIAS FX CLUE BLE MIDI"
BLE.start_advertising(ADVERTISEMENT)

clue.display.brightness = 1.0
clue.pixel.brightness = 0.2
screen = displayio.Group(max_size=17)

ORANGE = 0xCE6136
GRAY = 0x080808
BLACK = 0x121212
BLUE = 0x668190
SILVER = 0xAAAAAA
BROWN = 0x805D40
GREEN = 0x008800
DARK_GREEN = 0x004400

# Debounce needs to be at least 0.05
DEBOUNCE_TIME = 0.075
DEBOUNCE_TOUCH = 0.10

# --- Setup screen ---
# BG
color_bitmap = displayio.Bitmap(240, 240, 1)
color_palette = displayio.Palette(1)
color_palette[0] = GRAY
BG_SPRITE = displayio.TileGrid(color_bitmap,
                               x=0,
                               y=0,
                               pixel_shader=color_palette)
screen.append(BG_SPRITE)
column_a = 20
column_b = 168
# positions that are distributed relative to CC_X and CC_PROX y positions
row_a = 80
row_c = 170
row_b = int(row_a + ((row_c - row_a) / 2))
line_row_a = int(row_a + ((row_b - row_a) / 2))
line_row_b = int(row_b + ((row_c - row_b) / 2))
PICKER_BOX_ROW = [row_a, row_b, row_c]

# trim
top_trim_box = Rect(0, 0, 240, 8, fill=GREEN, outline=None)
screen.append(top_trim_box)
bottom_trim_box = Rect(0, 232, 240, 8, fill=GREEN, outline=None)
screen.append(bottom_trim_box)

# title box
title_box = Rect(0, 54, 240, 8, fill=DARK_GREEN, outline=None)
screen.append(title_box)

# cc x num
CC_X_NUM_LABEL = label.Label(terminalio.FONT,
                             text=("CC {}".format(CC_X_NUM)),
                             scale=3,
                             color=ORANGE,
                             max_glyphs=6)
CC_X_NUM_LABEL.x = column_a
CC_X_NUM_LABEL.y = row_a
screen.append(CC_X_NUM_LABEL)

# cc x value
CC_X_LABEL = label.Label(terminalio.FONT,
                         text=(CC_X),
                         scale=3,
                         color=ORANGE,
                         max_glyphs=3)
CC_X_LABEL.x = column_b
CC_X_LABEL.y = row_a
screen.append(CC_X_LABEL)

# picker box
PICKER_BOX = Rect(3, row_a, 6, 6, fill=ORANGE, outline=None)
screen.append(PICKER_BOX)

# mid line
MID_LINE_A = Rect(0, line_row_a, 240, 2, fill=SILVER, outline=None)
screen.append(MID_LINE_A)

# cc y num
CC_Y_NUM_LABEL = label.Label(terminalio.FONT,
                             text=("CC {}".format(CC_Y_NUM)),
                             scale=3,
                             color=BLUE,
                             max_glyphs=6)
CC_Y_NUM_LABEL.x = column_a
CC_Y_NUM_LABEL.y = row_b
screen.append(CC_Y_NUM_LABEL)

# cc y value text
CC_Y_LABEL = label.Label(terminalio.FONT,
                         text=CC_Y,
                         scale=3,
                         color=BLUE,
                         max_glyphs=3)
CC_Y_LABEL.x = column_b
CC_Y_LABEL.y = row_b
screen.append(CC_Y_LABEL)

# mid line
mid_line_b = Rect(0, line_row_b, 240, 2, fill=SILVER, outline=None)
screen.append(mid_line_b)

# cc prox num text
CC_PROX_NUM_LABEL = label.Label(
    terminalio.FONT,
    text=("CC {}".format(CC_PROX_NUM)),
    scale=3,
    color=SILVER,
    max_glyphs=6,
)
CC_PROX_NUM_LABEL.x = column_a
CC_PROX_NUM_LABEL.y = row_c
screen.append(CC_PROX_NUM_LABEL)

# cc prox value text
CC_PROX_LABEL = label.Label(terminalio.FONT,
                            text=CC_PROX,
                            scale=3,
                            color=SILVER,
                            max_glyphs=3,)
CC_PROX_LABEL.x = column_b
CC_PROX_LABEL.y = row_c
screen.append(CC_PROX_LABEL)

# footer line
footer_line = Rect(0, 192, 240, 2, fill=SILVER, outline=None)
screen.append(footer_line)

# Labels
TITLE_LABEL = label.Label(terminalio.FONT,
                          text="BiasFX2 MIDI",
                          scale=3,
                          color=SILVER,
                          max_glyphs=14)
TITLE_LABEL.x = 14
TITLE_LABEL.y = 27
screen.append(TITLE_LABEL)

# patch label
PATCH_LABEL = label.Label(terminalio.FONT,
                          text="Waiting: ",
                          scale=2,
                          color=BLUE,
                          max_glyphs=12,)
PATCH_LABEL.x = 4
PATCH_LABEL.y = 216
screen.append(PATCH_LABEL)

# footer label
FOOTER_LABEL = label.Label(terminalio.FONT,
                           text=("Connect BLE"),
                           scale=2,
                           color=ORANGE,
                           max_glyphs=14)
FOOTER_LABEL.x = 110
FOOTER_LABEL.y = 216
screen.append(FOOTER_LABEL)

# show the screen
clue.display.show(screen)

CC_NUM_PICK_TOGGLE = 0  # which cc to adjust w buttons
cc_send_toggle = True  # to start and stop sending cc

# set debug mode True to test raw values, set False to run BLE MIDI
debug = False
while True:
    if debug:
        ACCEL_DATA = clue.acceleration  # get accelerometer reading
        ACCEL_X = ACCEL_DATA[0]
        ACCEL_Y = ACCEL_DATA[1]
        PROX_DATA = clue.proximity
        print("x:{} y:{}".format(ACCEL_X, ACCEL_Y,))
        print("proximity: {}".format(clue.proximity))
        time.sleep(0.2)

    else:
        print("Waiting for connection")
        while not BLE.connected:
            pass
        print("Connected")
        MODE_SETTING = 1
        FOOTER_LABEL.x = 120
        FOOTER_LABEL.color = BLUE
        FOOTER_LABEL.text = "Connected!"
        time.sleep(2)
        TITLE_LABEL.text = "BiasFX2   M1"
        # PATCH_LABEL.text = "Patch {}".format(PATCH_INDEX + 1)

        FOOTER_LABEL.x = 120
        FOOTER_LABEL.color = SILVER
        FOOTER_LABEL.text = "        CC"        

        while BLE.connected:
            if MODE_SETTING == 1:
                # Clue sensor readings to CC
                ACCEL_DATA = clue.acceleration  # get accelerometer reading
                ACCEL_X = ACCEL_DATA[0]
                ACCEL_Y = ACCEL_DATA[1]
                PROX_DATA = clue.proximity

                # Remap analog readings to cc range
                CC_X = int(simpleio.map_range(ACCEL_X, -9, 9, 0, 127))

                # Remap this to invert for an expression pedal like function
                CC_Y = int(simpleio.map_range(ACCEL_Y, 0, 6, 127, 0))

                CC_PROX = int(simpleio.map_range(PROX_DATA, 0, 255, 0, 127))

                # send all the midi messages in a list
                if cc_send_toggle:
                    MIDI.send(
                        [
                            ControlChange(CC_X_NUM, CC_X),
                            ControlChange(CC_Y_NUM, CC_Y),
                            ControlChange(CC_PROX_NUM, CC_PROX),
                        ]
                    )
                CC_X_LABEL.text = CC_X
                CC_Y_LABEL.text = CC_Y
                CC_PROX_LABEL.text = CC_PROX

                # If you want to send NoteOn or Pitch Bend, here are examples:
                # midi.send(NoteOn(44, 1column_a))  # G sharp 2nd octave
                # a_pitch_bend = PitchBend(random.randint(0, 16383))
                # midi.send(a_pitch_bend)

                if clue.button_a:
                    if CC_NUM_PICK_TOGGLE == 0:
                        CC_X_NUM = CC_X_NUM - 1
                        CC_X_NUM_LABEL.text = "CC {}".format(CC_X_NUM)
                        time.sleep(DEBOUNCE_TIME)
                    elif CC_NUM_PICK_TOGGLE == 1:
                        CC_Y_NUM = CC_Y_NUM - 1
                        CC_Y_NUM_LABEL.text = "CC {}".format(CC_Y_NUM)
                        time.sleep(DEBOUNCE_TIME)
                    else:
                        CC_PROX_NUM = CC_PROX_NUM - 1
                        CC_PROX_NUM_LABEL.text = "CC {}".format(CC_PROX_NUM)
                        time.sleep(DEBOUNCE_TIME)

                if clue.button_b:
                    if CC_NUM_PICK_TOGGLE == 0:
                        CC_X_NUM = CC_X_NUM + 1
                        CC_X_NUM_LABEL.text = "CC {}".format(CC_X_NUM)
                        time.sleep(DEBOUNCE_TIME)
                    elif CC_NUM_PICK_TOGGLE == 1:
                        CC_Y_NUM = CC_Y_NUM + 1
                        CC_Y_NUM_LABEL.text = "CC {}".format(CC_Y_NUM)
                        time.sleep(DEBOUNCE_TIME)
                    else:
                        CC_PROX_NUM = CC_PROX_NUM + 1
                        CC_PROX_NUM_LABEL.text = "CC {}".format(CC_PROX_NUM)
                        time.sleep(DEBOUNCE_TIME)

                if clue.touch_1:
                    CC_NUM_PICK_TOGGLE = (CC_NUM_PICK_TOGGLE + 1) % 3
                    PICKER_BOX.y = PICKER_BOX_ROW[CC_NUM_PICK_TOGGLE]
                    time.sleep(DEBOUNCE_TOUCH)

                if clue.touch_0:
                    cc_send_toggle = not cc_send_toggle
                    if cc_send_toggle:
                        FOOTER_LABEL.x = 110
                        FOOTER_LABEL.color = SILVER
                        FOOTER_LABEL.text = "sending CC"
                    else:
                        FOOTER_LABEL.x = 114
                        FOOTER_LABEL.color = ORANGE
                        FOOTER_LABEL.text = " CC paused"
                    time.sleep(0.1)
                if clue.touch_2:
                    MODE_SETTING = 2
                    TITLE_LABEL.text = "BiasFX2   M2"
                    PATCH_LABEL.text = "Banks {}".format(PATCH_INDEX + 1)                    
                    FOOTER_LABEL.text = "     Banks"
                    time.sleep(DEBOUNCE_TOUCH)
            elif MODE_SETTING == 2:
                print("Mode 2")
                if clue.touch_0:
                    PATCH_INDEX = (PATCH_INDEX + 1) % PATCH_COUNT
                    MIDI.send(  # Bank select
                        [
                            ControlChange(0, 0),  # MSB
                            ControlChange(32,
                                          TOUCH_PATCH[PATCH_INDEX][0]),  # LSB
                        ]
                    )
                    # Program Change
                    MIDI.send(ProgramChange(TOUCH_PATCH[PATCH_INDEX][1]))
                    PATCH_LABEL.text = "Patch {}".format(PATCH_INDEX + 1)
                    time.sleep(0.2)
                if clue.touch_2:
                    MODE_SETTING = 3
                    TITLE_LABEL.text = "BiasFX2   M3"
                    PATCH_LABEL.text = "Preset {}".format(PATCH_INDEX + 1)                                        
                    FOOTER_LABEL.text = "   Presets"
                    time.sleep(DEBOUNCE_TOUCH)
            elif MODE_SETTING == 3:
                print("Mode 3")
                if clue.touch_0:
                    PATCH_INDEX = (PATCH_INDEX + 1) % PATCH_COUNT
                    MIDI.send(  # Bank select
                        [
                            ControlChange(0, 0),  # MSB
                            ControlChange(32,
                                          TOUCH_PATCH[PATCH_INDEX][0]),  # LSB
                        ]
                    )
                    # Program Change
                    MIDI.send(ProgramChange(TOUCH_PATCH[PATCH_INDEX][1]))
                    PATCH_LABEL.text = "".format(PATCH_INDEX + 1)
                    time.sleep(0.2)
                if clue.touch_2:
                    MODE_SETTING = 1
                    TITLE_LABEL.text = "BiasFX2   M1"
                    FOOTER_LABEL.text = "        CC"
                    time.sleep(DEBOUNCE_TOUCH)
        print("Disconnected")
        MODE_SETTING = 0
        print()
        PATCH_LABEL.text = "Waiting: "
        FOOTER_LABEL.x = 110
        FOOTER_LABEL.text = "Connect BLE"
        BLE.start_advertising(ADVERTISEMENT)
