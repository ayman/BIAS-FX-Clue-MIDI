"""
BIAS FX2 CLUE MIDI
Sends MIDI CC values and accelerometer x values.
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

# from adafruit_midi.program_change import ProgramChange
# from adafruit_midi.note_on import NoteOn
# from adafruit_midi.pitch_bend import PitchBend

COLORS = {
    "BLACK": 0x000000,
    "BLUE": 0x668190,
    "BROWN": 0x805D40,
    "GREEN_DARK": 0x004400,
    "GRAY": 0x080808,
    "GREEN": 0x008800,
    "ORANGE": 0xCE6136,
    "SILVER": 0xAAAAAA,
    "WHITE": 0xFFFFFF,
}


# Debounce needs to be at least 0.05
DEBOUNCE_DELAY = 0.10

MODE_SETTING = 0

clue.display.brightness = 1.0
clue.pixel.brightness = 0.2


BUTTONS = {
    "MODE": "MODE",
    "PROXY": "PROXY",
    "CC_0": "CC_0",
    "CC_1": "CC_1",
    "CC_2": "CC_2",
    "CC_MINUS": "CC_MINUS",
    "CC_PLUS": "CC_PLUS",
    "CALIBRATE": "CALIBRATE"
}


class Debouncer:
    def __init__(self, items, t=0.75):
        "A debouncer that has a timeout for buttons."
        stamp = time.monotonic()
        self.buttons = {}
        self.timeout = t
        for i in items:
            self.buttons[i] = stamp
        print(self.buttons)

    def hot(self, button, check=False):
        stamp = time.monotonic()
        result = True
        if stamp - self.buttons[button] > self.timeout:
            result = False
        if not check:
            self.buttons[button] = stamp
        return result


class DisplayManager:
    """ Control the display.
    """

    def __init__(self, clue_board):
        "docstring"
        self.screen = displayio.Group(scale=1)

        title_box = Rect(
            0, 0, 240, 50, fill=COLORS["GREEN_DARK"], outline=None)
        self.screen.append(title_box)
        top_trim_box = Rect(0, 50, 240, 8, fill=COLORS["GREEN"], outline=None)
        self.screen.append(top_trim_box)
        bottom_trim_box = Rect(
            0, 210, 240, 4, fill=COLORS["GREEN"], outline=None)
        self.screen.append(bottom_trim_box)
        footer_box = Rect(
            0, 214, 240, 50, fill=COLORS["GREEN_DARK"], outline=None)
        self.screen.append(footer_box)

        self.top_label = label.Label(terminalio.FONT,
                                     text="^^^",
                                     scale=2,
                                     color=COLORS["SILVER"])
        self.top_label.x = 100
        self.top_label.y = 10

        self.title_label = label.Label(
            terminalio.FONT,
            text="BiasFX2 MIDI",
            scale=3,
            color=COLORS["SILVER"])
        self.title_label.x = 10  # round((240 - self.title_label.width) / 2)
        self.title_label.y = self.top_label.height + 5  # 50
        self.title_label.background_color = COLORS["GREEN_DARK"]

        self.a_label = label.Label(
            terminalio.FONT,
            text="mode",
            scale=2,
            color=COLORS["SILVER"],
            line_spacing=0.8,
        )
        self.a_label.anchor_point = (0.5, 0.5)
        self.a_label.x = 10
        self.a_label.y = 125
        self.a_label.label_direction = "DWR"

        self.b_label = label.Label(
            terminalio.FONT,
            text="init",
            scale=2,
            color=COLORS["SILVER"],
            line_spacing=0.8,
        )
        self.b_label.anchor_point = (0.5, 0.5)
        self.b_label.x = 222
        self.b_label.y = 170
        self.b_label.label_direction = "UPR"

        self.patch_label = label.Label(
            terminalio.FONT,
            text="waiting...",
            scale=2,
            color=COLORS["SILVER"],
        )
        self.patch_label.x = 4
        self.patch_label.y = 224

        self.footer_label = label.Label(
            terminalio.FONT,
            text=("shamur.ai"),
            scale=1,
            color=COLORS["WHITE"],
        )
        self.footer_label.x = 240 - 60
        self.footer_label.y = 228

        self.init_screen()
        self.screen.append(self.title_label)
        self.screen.append(self.top_label)
        self.screen.append(self.a_label)
        self.screen.append(self.b_label)
        self.screen.append(self.footer_label)
        self.screen.append(self.patch_label)
        clue_board.display.show(self.screen)

        self.starting_patch = 70
        self.current_screen = 0
        self.total_screens = 2

    def init_screen(self):
        self.current_screen = -1
        self.patch_label.text = "waiting..."
        self.footer_label.text = "shamur.ai"
        self.title_label.text = "BiasFX2 Clue"

    def patch_screen(self):
        self.patch_label.text = "(0) (1) (2)"
        self.title_label.text = "BiasFX2 Clue"
        self.b_label.text = "alt"

    def cc_inc(self):
        self.set_start_cc(self.starting_patch + 1)

    def cc_dec(self):
        self.set_start_cc(self.starting_patch - 1)

    def set_start_cc(self, cc_code):
        print("Start Patch: %s" % cc_code)
        if cc_code >= 10 or cc_code <= 95:
            self.starting_patch = cc_code
            self.settings_screen()

    def settings_screen(self):
        self.patch_label.text = "(-) (+) (*)"
        self.b_label.text = "info"
        self.title_label.text = "%s: %s..%s" % ("CC",
                                                self.starting_patch,
                                                self.starting_patch + 4)

    def next_screen(self):
        self.current_screen += 1
        if self.current_screen > self.total_screens:
            self.current_screen = 0
        self.show_screen(self.current_screen)

    def show_screen(self, screen):
        if screen == 0:
            self.patch_screen()
        elif screen == 1:
            self.settings_screen()
        elif screen == -1:
            self.init_screen()


def remap(x, in_min, in_max, out_min, out_max, no_float=True):
    res = (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    if res < out_min:
        res = out_min
    if res > out_max:
        res = out_max
    if no_float:
        res = round(res)
    return res


MIDI_CHANNEL = 1
MIDI_SERVICE = adafruit_ble_midi.MIDIService()
BLE_AD = ProvideServicesAdvertisement(MIDI_SERVICE)
MIDI = adafruit_midi.MIDI(midi_out=MIDI_SERVICE,
                          out_channel=MIDI_CHANNEL - 1)


BLE = adafruit_ble.BLERadio()
if BLE.connected:
    print("Remove active BLE connections")
    for c in BLE.connections:
        c.disconnect()
BLE.name = "BIAS FX CLUE BLE MIDI"
print("Advertising BLE")
BLE.start_advertising(BLE_AD)

clue_display = DisplayManager(clue)
debouncer = Debouncer(BUTTONS)
START_RANGE = 0

while True:
    print("Waiting for connection")
    while not BLE.connected:
        pass
    print("Connected")
    clue_display.patch_label.text = "Connecting"
    clue.white_leds = True
    time.sleep(0.5)
    clue.white_leds = False
    clue_display.patch_label.text = "Connected!"
    time.sleep(1.0)
    clue_display.show_screen(0)
    while BLE.connected:
        if clue.button_a:
            if not debouncer.hot(BUTTONS["MODE"]):
                clue_display.next_screen()

        ACCEL_DATA = clue.acceleration
        PROX_DATA = clue.proximity
        ACCEL_X = ACCEL_DATA[0]

        if clue_display.current_screen == 0:
            midi_data = []
            # Remap analog readings to cc range
            cc_x = int(simpleio.map_range(ACCEL_X, -9, 9, 0, 127))
            cc_x = remap(cc_x, START_RANGE, 127, 0, 127)
            midi_data.append(ControlChange(
                clue_display.starting_patch + 4, cc_x))
            # It's easier to map it inverted for a shoe mount...
            # CC_Y = int(simpleio.map_range(ACCEL_Y, -9, 9, 0, 127))
            if clue.white_leds and debouncer.hot(BUTTONS["PROXY"], check=True):
                clue.white_leds = False
            CC_PROX = int(simpleio.map_range(clue.proximity, 0, 255, 0, 127))
            CC_PROX_SWITCH = 127 if CC_PROX > 4 else 0
            if CC_PROX_SWITCH != 0 and not debouncer.hot(BUTTONS["PROXY"]):
                clue.white_leds = True
                midi_data.append(ControlChange(clue_display.starting_patch + 3,
                                               CC_PROX_SWITCH))
            if clue.touch_0:
                if not debouncer.hot(BUTTONS["CC_0"]):
                    print("Touch 0")
                    midi_cc = ControlChange(clue_display.starting_patch, 0)
                    midi_data.append(midi_cc)
            if clue.touch_1:
                if not debouncer.hot(BUTTONS["CC_1"]):
                    print("Touch 1")
                    midi_cc = ControlChange(clue_display.starting_patch + 1, 0)
                    midi_data.append(midi_cc)
            if clue.touch_2:
                if not debouncer.hot(BUTTONS["CC_2"]):
                    print("Touch: 2")
                    midi_cc = ControlChange(clue_display.starting_patch + 2, 0)
                    midi_data.append(midi_cc)
            if len(midi_data) > 0:
                MIDI.send(midi_data)

        if clue_display.current_screen == 1:
            if CC_PROX_SWITCH != 0:
                if not debouncer.hot(BUTTONS["PROXY"]):
                    clue.white_leds = True
                    time.sleep(DEBOUNCE_DELAY)
                    clue.white_leds = False
            if clue.touch_0:
                if not debouncer.hot(BUTTONS["CC_MINUS"]):
                    print("Touch: -")
                    clue_display.cc_dec()
            if clue.touch_1:
                if not debouncer.hot(BUTTONS["CC_PLUS"]):
                    print("Touch: +")
                    clue_display.cc_inc()
            if clue.touch_2:
                if not debouncer.hot(BUTTONS["CALIBRATE"]):
                    print("Touch: *")
                    START_RANGE = int(
                        simpleio.map_range(ACCEL_X, -9, 9, 0, 127))
        time.sleep(0.05)
    print("Disconnected")
    clue_display.init_screen()
    BLE.start_advertising(BLE_AD)
