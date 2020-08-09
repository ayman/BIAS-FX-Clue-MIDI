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


MIDI_CHANNEL = 1
MODE_SETTING = 0
CC_X_NUM = 71
CC_Y_NUM = 72
CC_PROX_NUM = 73
PATCH_HOME = 0
PRESET_LETTERS = ["A", "B", "C", "D"]
PATCH_COUNT = 10

CC_X = 0
CC_Y = 0
CC_PROX = 0

MIDI_SERVICE = adafruit_ble_midi.MIDIService()
ADVERTISEMENT = ProvideServicesAdvertisement(MIDI_SERVICE)

BLE = adafruit_ble.BLERadio()
if BLE.connected:
    for c in BLE.connections:
        c.disconnect()

MIDI = adafruit_midi.MIDI(midi_out=MIDI_SERVICE, out_channel=MIDI_CHANNEL - 1)

print("Advertising")
BLE.name = "BIAS FX CLUE BLE MIDI"
BLE.start_advertising(ADVERTISEMENT)

clue.display.brightness = 1.0
clue.pixel.brightness = 0.2
SCREEN = displayio.Group(max_size=17)

COLORS = {"BLACK": 0x000000,
          "BLUE": 0x668190,
          "BROWN": 0x805D40,
          "GREEN_DARK": 0x004400,
          "GRAY": 0x080808,
          "GREEN": 0x008800,
          "ORANGE": 0xCE6136,
          "SILVER": 0xAAAAAA,
          "WHITE": 0xFFFFFF}

# Debounce needs to be at least 0.05
DEBOUNCE_TIME = 0.075
DEBOUNCE_TOUCH = 0.10

# Setup screen
COLOR_BITMAP = displayio.Bitmap(240, 240, 1)
COLOR_PALETTE = displayio.Palette(1)
COLOR_PALETTE[0] = COLORS["GRAY"]
BG_SPRITE = displayio.TileGrid(COLOR_BITMAP,
                               x=0,
                               y=0,
                               pixel_shader=COLOR_PALETTE)
SCREEN.append(BG_SPRITE)
COLUMN_A = 20
COLUMN_B = 168
# positions that are distributed relative to CC_X and CC_PROX y
# positions
ROW_A = 80
ROW_C = 170
ROW_B = int(ROW_A + ((ROW_C - ROW_A) / 2))
LINE_ROW_A = int(ROW_A + ((ROW_B - ROW_A) / 2))
LINE_ROW_B = int(ROW_B + ((ROW_C - ROW_B) / 2))
PICKER_BOX_ROW = [ROW_A, ROW_B, ROW_C]

# SCREEN boxes
TITLE_BOX = Rect(0, 0, 240, 60, fill=COLORS["GREEN_DARK"], outline=None)
SCREEN.append(TITLE_BOX)
TOP_TRIM_BOX = Rect(0, 54, 240, 8, fill=COLORS["GREEN"], outline=None)
SCREEN.append(TOP_TRIM_BOX)
BOTTOM_TRIM_BOX = Rect(0, 195, 240, 8, fill=COLORS["GREEN"], outline=None)
SCREEN.append(BOTTOM_TRIM_BOX)
FOOTER_BOX = Rect(0, 203, 240, 50, fill=COLORS["GREEN_DARK"], outline=None)
SCREEN.append(FOOTER_BOX)

# cc x num
CC_X_NUM_LABEL = label.Label(terminalio.FONT,
                             # text=("CC {}".format(CC_X_NUM)),
                             text=(" "),
                             scale=3,
                             color=COLORS["ORANGE"],
                             max_glyphs=6)
CC_X_NUM_LABEL.x = COLUMN_A
CC_X_NUM_LABEL.y = ROW_A
SCREEN.append(CC_X_NUM_LABEL)

# cc x value
CC_X_LABEL = label.Label(terminalio.FONT,
                         text=(" "),
                         scale=3,
                         color=COLORS["ORANGE"],
                         max_glyphs=3)
CC_X_LABEL.x = COLUMN_B
CC_X_LABEL.y = ROW_A
SCREEN.append(CC_X_LABEL)

# picker box
PICKER_BOX = Rect(3, ROW_A, 6, 6, fill=COLORS["ORANGE"], outline=None)
PICKER_BOX.y = -10
SCREEN.append(PICKER_BOX)

# mid line
MID_LINE_A = Rect(0, LINE_ROW_A, 240, 2, fill=COLORS["SILVER"], outline=None)
SCREEN.append(MID_LINE_A)

# cc y num
CC_Y_NUM_LABEL = label.Label(terminalio.FONT,
                             # text=("CC {}".format(CC_Y_NUM)),
                             text=("Connect"),
                             scale=3,
                             color=COLORS["BLUE"],
                             max_glyphs=6)
CC_Y_NUM_LABEL.x = COLUMN_A
CC_Y_NUM_LABEL.y = ROW_B
SCREEN.append(CC_Y_NUM_LABEL)

# cc y value text
CC_Y_LABEL = label.Label(terminalio.FONT,
                         text=("BLE"),
                         scale=3,
                         color=COLORS["BLUE"],
                         max_glyphs=3)
CC_Y_LABEL.x = COLUMN_B
CC_Y_LABEL.y = ROW_B
SCREEN.append(CC_Y_LABEL)

# mid line
MID_LINE_B = Rect(0, LINE_ROW_B, 240, 2, fill=COLORS["SILVER"], outline=None)
SCREEN.append(MID_LINE_B)

# cc prox num text
CC_PROX_NUM_LABEL = label.Label(terminalio.FONT,
                                # text=("CC {}".format(CC_PROX_NUM)),
                                text=(" "),
                                scale=3,
                                color=COLORS["SILVER"],
                                max_glyphs=6)
CC_PROX_NUM_LABEL.x = COLUMN_A
CC_PROX_NUM_LABEL.y = ROW_C
SCREEN.append(CC_PROX_NUM_LABEL)

# cc prox value text
CC_PROX_LABEL = label.Label(terminalio.FONT,
                            # text=CC_PROX,
                            text=(" "),
                            scale=3,
                            color=COLORS["SILVER"],
                            max_glyphs=3)
CC_PROX_LABEL.x = COLUMN_B
CC_PROX_LABEL.y = ROW_C
SCREEN.append(CC_PROX_LABEL)


TITLE_LABEL = label.Label(terminalio.FONT,
                          text="BiasFX2 MIDI",
                          scale=3,
                          color=COLORS["SILVER"],
                          max_glyphs=14)
TITLE_LABEL.x = 14
TITLE_LABEL.y = 27
TITLE_LABEL.background_color = COLORS["GREEN_DARK"]
SCREEN.append(TITLE_LABEL)

PATCH_LABEL = label.Label(terminalio.FONT,
                          text="wating",
                          scale=2,
                          color=COLORS["BLUE"],
                          max_glyphs=12)
PATCH_LABEL.x = 4
PATCH_LABEL.y = 220
SCREEN.append(PATCH_LABEL)

FOOTER_LABEL = label.Label(terminalio.FONT,
                           text=("shamur.ai"),
                           scale=2,
                           color=COLORS["SILVER"],
                           max_glyphs=10)
FOOTER_LABEL.x = 130
FOOTER_LABEL.y = 220
SCREEN.append(FOOTER_LABEL)

clue.display.show(SCREEN)

CC_NUM_PICK_TOGGLE = 0  # which cc to adjust w buttons
CC_SEND_TOGGLE = True  # to start and stop sending cc


def init_screen():
    """Set the screen back to waiting for connection.
    """
    PICKER_BOX.y = -10
    # FOOTER_LABEL.x = 110
    TITLE_LABEL.text = "BiasFX2 MIDI"
    CC_X_NUM_LABEL.text = " "
    CC_X_LABEL.text = " "
    CC_Y_NUM_LABEL.text = "Connect"
    CC_Y_LABEL.text = "BLE"
    CC_PROX_NUM_LABEL.text = " "
    CC_PROX_LABEL.text = " "
    PATCH_LABEL.text = "waiting"
    FOOTER_LABEL.text = " shamur.ai"


def do_program_change(preset):
    """Execute a program change and update the screen.
    """
    MIDI.send(ProgramChange(preset + (PATCH_HOME * 4)))
    CC_PROX_LABEL.text = PRESET_LETTERS[preset]
    time.sleep(DEBOUNCE_TOUCH)


# set debug mode True to test raw values, set False to run BLE MIDI
DEBUG = False
while True:
    if DEBUG:
        ACCEL_DATA = clue.acceleration  # get accelerometer reading
        ACCEL_X = ACCEL_DATA[0]
        ACCEL_Y = ACCEL_DATA[1]
        PROX_DATA = clue.proximity
        print("x:{} y:{}".format(ACCEL_X, ACCEL_Y,))
        print("proximity: {}".format(clue.proximity))
        time.sleep(0.2)
    else:
        print("Waiting for connection")
        clue.pixel.fill((255, 165, 0))
        while not BLE.connected:
            pass
        print("Connected")
        MODE_SETTING = 1
        FOOTER_LABEL.x = 120
        FOOTER_LABEL.color = COLORS["BLUE"]
        PATCH_LABEL.text = "Yay..."
        FOOTER_LABEL.text = "Connected!"
        clue.white_leds = True
        clue.pixel.fill((0, 255, 0))
        time.sleep(0.5)
        clue.white_leds = False
        time.sleep(2.5)

        # Init for Mode 1
        TITLE_LABEL.text = "BiasFX2   M1"
        PATCH_LABEL.text = "Mode"
        FOOTER_LABEL.x = 120
        FOOTER_LABEL.color = COLORS["SILVER"]
        FOOTER_LABEL.text = "        CC"
        PICKER_BOX.y = PICKER_BOX_ROW[CC_NUM_PICK_TOGGLE]
        clue.pixel.fill((0, 0, 0))

        while BLE.connected:
            if MODE_SETTING == 1:
                # Clue sensor readings to CC
                ACCEL_DATA = clue.acceleration  # get accelerometer reading
                ACCEL_X = ACCEL_DATA[0]
                ACCEL_Y = ACCEL_DATA[1]
                PROX_DATA = clue.proximity

                # Remap analog readings to cc range
                CC_X = int(simpleio.map_range(ACCEL_X, -9, 9, 0, 127))

                # Remap this for an expression pedal like movement
                # CC_Y = int(simpleio.map_range(ACCEL_Y, 0, 6, 127, 0))

                # It's easier to map it inverted for a shoe mount...
                CC_Y = int(simpleio.map_range(ACCEL_Y, -6, 0, 0, 127))

                CC_PROX = int(simpleio.map_range(PROX_DATA, 0, 255, 0, 127))
                CC_PROX_SWITCH = 127 if CC_PROX > 1 else 0

                MIDI_DATA = [ControlChange(CC_X_NUM, CC_X),
                             ControlChange(CC_Y_NUM, CC_Y)]

                if CC_PROX_SWITCH != 0:
                    MIDI_DATA.append(ControlChange(
                        CC_PROX_NUM, CC_PROX_SWITCH))

                if CC_SEND_TOGGLE:
                    MIDI.send(MIDI_DATA)

                if CC_PROX_SWITCH != 0:
                    # Since the PROX is a momentary switch, debounce it
                    time.sleep(DEBOUNCE_TOUCH * 2.5)

                CC_X_LABEL.x = COLUMN_B
                CC_X_LABEL.y = ROW_A
                CC_X_NUM_LABEL.text = "CC {}".format(CC_X_NUM)
                CC_X_LABEL.text = CC_X

                CC_Y_LABEL.x = COLUMN_B
                CC_Y_LABEL.y = ROW_B
                CC_Y_NUM_LABEL.text = "CC {}".format(CC_Y_NUM)
                CC_Y_LABEL.text = CC_Y

                CC_PROX_LABEL.x = COLUMN_B
                CC_PROX_LABEL.y = ROW_C
                CC_PROX_NUM_LABEL.text = "CC {}".format(CC_PROX_NUM)
                CC_PROX_LABEL.text = CC_PROX

                # If you want to send NoteOn or Pitch Bend, here are examples:
                # midi.send(NoteOn(44, 1COLUMN_A))  # G sharp 2nd octave
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
                if clue.touch_0:
                    CC_SEND_TOGGLE = not CC_SEND_TOGGLE
                    if CC_SEND_TOGGLE:
                        FOOTER_LABEL.x = 110
                        FOOTER_LABEL.color = COLORS["SILVER"]
                        FOOTER_LABEL.text = "sending CC"
                    else:
                        FOOTER_LABEL.x = 114
                        FOOTER_LABEL.color = COLORS["ORANGE"]
                        FOOTER_LABEL.text = " CC paused"
                    time.sleep(DEBOUNCE_TOUCH)
                if clue.touch_1:
                    CC_NUM_PICK_TOGGLE = (CC_NUM_PICK_TOGGLE + 1) % 3
                    PICKER_BOX.y = PICKER_BOX_ROW[CC_NUM_PICK_TOGGLE]
                    time.sleep(DEBOUNCE_TOUCH)
                if clue.touch_2:
                    MODE_SETTING = 2
                    TITLE_LABEL.text = "BiasFX2   M2"
                    # PATCH_LABEL.text = "Banks {}".format(PATCH_HOME)
                    PICKER_BOX.y = -10
                    FOOTER_LABEL.text = "     Banks"
                    time.sleep(DEBOUNCE_TOUCH)
            elif MODE_SETTING == 2:
                print("Mode 2")
                CC_X_NUM_LABEL.text = "Bank:"
                CC_X_LABEL.text = PATCH_HOME + 1

                CC_Y_LABEL.x = COLUMN_B
                CC_Y_LABEL.y = ROW_B
                CC_Y_NUM_LABEL.x = COLUMN_A - 15
                CC_Y_NUM_LABEL.text = "< DOWN"
                CC_Y_LABEL.text = "UP >"

                CC_PROX_LABEL.x = COLUMN_B
                CC_PROX_LABEL.y = ROW_C
                # CC_PROX_NUM_LABEL.x = COLUMN_A
                # CC_PROX_NUM_LABEL.y = ROW_C
                CC_PROX_NUM_LABEL.text = " "
                CC_PROX_LABEL.text = " "

                if clue.button_a:
                    PATCH_HOME = (PATCH_HOME - 1) % PATCH_COUNT
                    CC_X_LABEL.text = PATCH_HOME
                    time.sleep(DEBOUNCE_TIME)
                if clue.button_b:
                    PATCH_HOME = (PATCH_HOME + 1) % PATCH_COUNT
                    CC_X_LABEL.text = PATCH_HOME
                    time.sleep(DEBOUNCE_TIME)
                if clue.touch_2:
                    MODE_SETTING = 3
                    TITLE_LABEL.text = "BiasFX2   M3"
                    # PATCH_LABEL.text = "Preset {}".format(PATCH_HOME + 1)
                    CC_PROX_NUM_LABEL.text = "Patch:"
                    FOOTER_LABEL.text = "   Patches"
                    CC_Y_NUM_LABEL.x = COLUMN_A
                    CC_Y_NUM_LABEL.text = " "
                    CC_Y_LABEL.text = " "
                    time.sleep(DEBOUNCE_TOUCH)
            elif MODE_SETTING == 3:
                print("Mode 3")
                if clue.button_a:
                    do_program_change(0)
                if clue.button_b:
                    do_program_change(1)
                if clue.touch_0:
                    do_program_change(2)
                if clue.touch_1:
                    do_program_change(3)
                if clue.touch_2:
                    MODE_SETTING = 1
                    TITLE_LABEL.text = "BiasFX2   M1"
                    FOOTER_LABEL.text = "        CC"
                    PICKER_BOX.y = PICKER_BOX_ROW[CC_NUM_PICK_TOGGLE]
                    time.sleep(DEBOUNCE_TOUCH)
        print("Disconnected")
        MODE_SETTING = 0
        print()
        init_screen()
        BLE.start_advertising(ADVERTISEMENT)
