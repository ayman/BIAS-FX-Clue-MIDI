"""
BIAS FX2 CLUE MIDI
Sends MIDI CC values based on accelerometer x & y and proximity sensor
Switch banks and presets.
"""
import time
import simpleio
import adafruit_ble
import adafruit_ble_midi
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_display_shapes.rect import Rect
import displayio
import terminalio
from adafruit_display_text import label
from adafruit_clue import clue
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_midi.program_change import ProgramChange

# from adafruit_midi.note_on import NoteOn
# from adafruit_midi.pitch_bend import PitchBend

DEBUG = False

MIDI_CHANNEL = 1
MODE_SETTING = 0
CC_X_NUM = 71
CC_Y_NUM = 72
CC_PROX_NUM = 73
PATCH_HOME = 0
PATCH_PRESET = 0
PRESET_LETTERS = ["A", "B", "C", "D"]
PATCH_COUNT = 7

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
ROW_A = 80
ROW_C = 170
ROW_B = int(ROW_A + ((ROW_C - ROW_A) / 2))
LINE_ROW_A = int(ROW_A + ((ROW_B - ROW_A) / 2))
LINE_ROW_B = int(ROW_B + ((ROW_C - ROW_B) / 2))
PICKER_BOX_ROW = [ROW_A, ROW_B, ROW_C]

TITLE_BOX = Rect(0, 0, 240, 60, fill=COLORS["GREEN_DARK"], outline=None)
SCREEN.append(TITLE_BOX)
TOP_TRIM_BOX = Rect(0, 54, 240, 8, fill=COLORS["GREEN"], outline=None)
SCREEN.append(TOP_TRIM_BOX)
BOTTOM_TRIM_BOX = Rect(0, 195, 240, 8, fill=COLORS["GREEN"], outline=None)
SCREEN.append(BOTTOM_TRIM_BOX)
FOOTER_BOX = Rect(0, 203, 240, 50, fill=COLORS["GREEN_DARK"], outline=None)
SCREEN.append(FOOTER_BOX)

CC_X_NUM_LABEL = label.Label(terminalio.FONT,
                             text=(" "),
                             scale=3,
                             color=COLORS["ORANGE"],
                             max_glyphs=6)
CC_X_NUM_LABEL.x = COLUMN_A
CC_X_NUM_LABEL.y = ROW_A
SCREEN.append(CC_X_NUM_LABEL)

CC_X_LABEL = label.Label(terminalio.FONT,
                         text=(" "),
                         scale=3,
                         color=COLORS["ORANGE"],
                         max_glyphs=3)
CC_X_LABEL.x = COLUMN_B
CC_X_LABEL.y = ROW_A
SCREEN.append(CC_X_LABEL)

PICKER_BOX = Rect(3, ROW_A, 6, 6, fill=COLORS["ORANGE"], outline=None)
PICKER_BOX.y = -10
SCREEN.append(PICKER_BOX)

MID_LINE_A = Rect(0, LINE_ROW_A, 240, 2, fill=COLORS["SILVER"], outline=None)
SCREEN.append(MID_LINE_A)

CC_Y_NUM_LABEL = label.Label(terminalio.FONT,
                             text=("Connect"),
                             scale=3,
                             color=COLORS["BLUE"],
                             max_glyphs=6)
CC_Y_NUM_LABEL.x = COLUMN_A
CC_Y_NUM_LABEL.y = ROW_B
SCREEN.append(CC_Y_NUM_LABEL)

CC_Y_LABEL = label.Label(terminalio.FONT,
                         text=("BLE"),
                         scale=3,
                         color=COLORS["BLUE"],
                         max_glyphs=3)
CC_Y_LABEL.x = COLUMN_B
CC_Y_LABEL.y = ROW_B
SCREEN.append(CC_Y_LABEL)

MID_LINE_B = Rect(0, LINE_ROW_B, 240, 2, fill=COLORS["SILVER"], outline=None)
SCREEN.append(MID_LINE_B)

CC_PROX_NUM_LABEL = label.Label(terminalio.FONT,
                                text=(" "),
                                scale=3,
                                color=COLORS["SILVER"],
                                max_glyphs=6)
CC_PROX_NUM_LABEL.x = COLUMN_A
CC_PROX_NUM_LABEL.y = ROW_C
SCREEN.append(CC_PROX_NUM_LABEL)

CC_PROX_LABEL = label.Label(terminalio.FONT,
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
                          text="waiting",
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
    global PATCH_PRESET
    PATCH_PRESET = preset
    MIDI.send(ProgramChange(preset + (PATCH_HOME * 4)))
    CC_PROX_LABEL.text = PRESET_LETTERS[preset]


def debug_loop():
    """Simply print some debug info.
    """
    accel = clue.acceleration  # get accelerometer reading
    accel_x = accel[0]
    accel_y = accel[1]
    print("x:{} y:{}".format(accel_x, accel_y,))
    print("proximity: {}".format(clue.proximity))
    time.sleep(0.2)


def init_mode(mode):
    """Set the device for a given mode.
    """
    if mode == 1:
        TITLE_LABEL.text = "BiasFX2   M1"
        PATCH_LABEL.text = "Mode"
        FOOTER_LABEL.x = 120
        FOOTER_LABEL.color = COLORS["SILVER"]
        FOOTER_LABEL.text = "        CC"
        PICKER_BOX.y = PICKER_BOX_ROW[CC_NUM_PICK_TOGGLE]
        clue.pixel.fill((0, 0, 0))
    elif mode == 2:
        TITLE_LABEL.text = "BiasFX2   M2"
        PICKER_BOX.y = -10
        FOOTER_LABEL.text = "     Banks"

        CC_X_NUM_LABEL.text = "Bank:"
        CC_X_LABEL.text = PATCH_HOME + 1

        CC_Y_LABEL.x = COLUMN_B
        CC_Y_LABEL.y = ROW_B
        CC_Y_NUM_LABEL.x = COLUMN_A - 15
        CC_Y_NUM_LABEL.text = "< DOWN"
        CC_Y_LABEL.text = "UP >"

        CC_PROX_LABEL.x = COLUMN_B
        CC_PROX_LABEL.y = ROW_C
        CC_PROX_NUM_LABEL.text = " "
        CC_PROX_LABEL.text = " "
    elif mode == 3:
        TITLE_LABEL.text = "BiasFX2   M3"
        CC_PROX_NUM_LABEL.text = "Patch:"
        FOOTER_LABEL.text = "   Patches"
        CC_Y_NUM_LABEL.x = COLUMN_A
        CC_Y_NUM_LABEL.text = " "
        CC_Y_LABEL.text = " "
    elif mode == 0:
        # clue.pixel.fill((0, 255, 0))
        FOOTER_LABEL.x = 120
        FOOTER_LABEL.color = COLORS["BLUE"]
        PATCH_LABEL.text = "Yay..."
        FOOTER_LABEL.text = "Connected!"
    return mode


def switch_bank(switch_up):
    """Move bank number up or down (internally, doesn't send CC data).
    """
    global PATCH_HOME, PATCH_COUNT, CC_X_LABEL
    direction = 1 if switch_up is True else -1
    PATCH_HOME = (PATCH_HOME + direction) % PATCH_COUNT
    CC_X_LABEL.text = PATCH_HOME
    return PATCH_HOME


while True:
    if DEBUG:
        debug_loop()
    else:
        print("Waiting for connection")
        # clue.pixel.fill((255, 165, 0))
        while not BLE.connected:
            pass
        print("Connected")
        init_mode(0)
        clue.white_leds = True
        time.sleep(0.5)
        clue.white_leds = False
        time.sleep(1.0)
        MODE_SETTING = init_mode(1)

        while BLE.connected:
            if MODE_SETTING == 1:
                ACCEL_DATA = clue.acceleration
                PROX_DATA = clue.proximity
                ACCEL_X = ACCEL_DATA[0]
                ACCEL_Y = ACCEL_DATA[1]

                # Remap analog readings to cc range
                CC_X = int(simpleio.map_range(ACCEL_X, -9, 9, 0, 127))

                # It's easier to map it inverted for a shoe mount...
                CC_Y = int(simpleio.map_range(ACCEL_Y, -9, 9, 0, 127))

                CC_PROX = int(simpleio.map_range(PROX_DATA, 0, 255, 0, 127))
                CC_PROX_SWITCH = 127 if CC_PROX > 4 else 0

                MIDI_DATA = [ControlChange(CC_X_NUM, CC_X),
                             ControlChange(CC_Y_NUM, CC_Y)]

                if CC_PROX_SWITCH != 0:
                    clue.white_leds = True
                    MIDI_DATA.append(ControlChange(CC_PROX_NUM,
                                                   CC_PROX_SWITCH))

                if CC_SEND_TOGGLE:
                    MIDI.send(MIDI_DATA)

                if CC_PROX_SWITCH != 0:
                    # Since the PROX is a momentary switch, debounce it
                    time.sleep(DEBOUNCE_TOUCH)
                    clue.white_leds = False

                CC_X_NUM_LABEL.text = "CC {}".format(CC_X_NUM)
                CC_X_LABEL.text = CC_X

                CC_Y_NUM_LABEL.text = "CC {}".format(CC_Y_NUM)
                CC_Y_LABEL.text = CC_Y

                CC_PROX_NUM_LABEL.text = "CC {}".format(CC_PROX_NUM)
                CC_PROX_LABEL.text = CC_PROX

                if clue.button_a:
                    if CC_NUM_PICK_TOGGLE == 0:
                        CC_X_NUM = CC_X_NUM - 1
                        CC_X_NUM_LABEL.text = "CC {}".format(CC_X_NUM)
                    elif CC_NUM_PICK_TOGGLE == 1:
                        CC_Y_NUM = CC_Y_NUM - 1
                        CC_Y_NUM_LABEL.text = "CC {}".format(CC_Y_NUM)
                    else:
                        CC_PROX_NUM = CC_PROX_NUM - 1
                        CC_PROX_NUM_LABEL.text = "CC {}".format(CC_PROX_NUM)
                    time.sleep(DEBOUNCE_TIME)
                if clue.button_b:
                    if CC_NUM_PICK_TOGGLE == 0:
                        CC_X_NUM = CC_X_NUM + 1
                        CC_X_NUM_LABEL.text = "CC {}".format(CC_X_NUM)
                    elif CC_NUM_PICK_TOGGLE == 1:
                        CC_Y_NUM = CC_Y_NUM + 1
                        CC_Y_NUM_LABEL.text = "CC {}".format(CC_Y_NUM)
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
                    MODE_SETTING = init_mode(2)
                    time.sleep(DEBOUNCE_TOUCH)
            elif MODE_SETTING == 2:
                print("Mode 2")
                if clue.button_a or clue.touch_0:
                    switch_bank(False)
                    time.sleep(DEBOUNCE_TIME)
                if clue.button_b or clue.touch_1:
                    switch_bank(True)
                    time.sleep(DEBOUNCE_TIME)
                if clue.touch_2:
                    MODE_SETTING = init_mode(3)
                    time.sleep(DEBOUNCE_TOUCH)
            elif MODE_SETTING == 3:
                if clue.button_a:    # or (clue.gesture == 1):
                    do_program_change(0)
                    time.sleep(DEBOUNCE_TIME)
                elif clue.button_b:  # or (clue.gesture == 2):
                    do_program_change(1)
                    time.sleep(DEBOUNCE_TIME)
                elif clue.touch_0:  # or (clue.gesture == 3):
                    do_program_change(2)
                    time.sleep(DEBOUNCE_TOUCH)
                elif clue.touch_1:  # or (clue.gesture == 4):
                    do_program_change(3)
                    time.sleep(DEBOUNCE_TOUCH)
                elif clue.touch_2:
                    MODE_SETTING = init_mode(1)
                    time.sleep(DEBOUNCE_TOUCH)
        print("Disconnected")
        MODE_SETTING = 0
        print()
        init_screen()
        BLE.start_advertising(ADVERTISEMENT)
