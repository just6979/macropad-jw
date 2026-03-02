import time
import fontio
import displayio
import terminalio
from adafruit_display_shapes.rect import Rect
from adafruit_display_text import label
from adafruit_macropad import MacroPad, Keycode, ConsumerControlCode
from adafruit_ticks import ticks_ms, ticks_add, ticks_less


BLACK=0x000000
WHITE=0xFFFFFF

DISPLAY_KEY_MS = 1000

KNOB_CCW = 0
KNOB_PRESS = 1
KNOB_CW = 2

KNOB_COUNT = 3
KEY_COUNT = 12

TEXT = 0
CONTROL = 1
COLOR = 2

buttons = [
    # knob
    ('Vol-',    ConsumerControlCode.VOLUME_DECREMENT),
    ('Mute ',   ConsumerControlCode.MUTE),
    ('Vol+',    ConsumerControlCode.VOLUME_INCREMENT),
    # 1st row
    ('<<',      [[ConsumerControlCode.SCAN_PREVIOUS_TRACK]], 0x000020),
    ('>/|| ',   [[ConsumerControlCode.PLAY_PAUSE]], 0x402000),
    ('>>',      [[ConsumerControlCode.SCAN_NEXT_TRACK]], 0x002000),
    # 2nd row
    ('Undo',    [Keycode.CONTROL, 'z'], 0x202000),
    ('Redo ',   [Keycode.CONTROL, Keycode.SHIFT, 'z'], 0x002000),
    ('S-Paste', [Keycode.CONTROL, Keycode.SHIFT, 'v'], 0x400020),
    # 3rd row
    ('Cut',     [Keycode.CONTROL, 'x'], 0x200000),
    ('Copy ',   [Keycode.CONTROL, 'c'], 0x002020),
    ('Paste',   [Keycode.CONTROL, 'v'],  0x200040),
    # 4th row
    ('Back',    [[0x224]], 0x000020),
    ('Fwd  ',   [[0x225]], 0x002000),
    ('Calc',    [[0x192]], 0x101010)
]


def displayMap(macropad):
    group = displayio.Group()

    # top row, knob controls, white background
    group.append(Rect(0, 0, macropad.display.width, 13, fill=WHITE))

    for key in range(KNOB_COUNT + KEY_COUNT):
        color = BLACK
        if key >= 3:
            color = WHITE
            macropad.pixels[key - KNOB_COUNT] = buttons[key][COLOR]

        x = key % 3
        y = key // 3
        group.append(label.Label(
            terminalio.FONT,
            text=buttons[key][TEXT],
            color=color,
            anchored_position=(
                (macropad.display.width - 1) * x / 2,
                (y + 1) * 12
            ),
            anchor_point=(
                x / 2,
                1.0
            )
        ))

    macropad.display.root_group = group
    macropad.display.refresh()
    macropad.pixels.show()
    macropad.red_led = False


def displayKey(macropad, key):
    group = displayio.Group()
    group.append(Rect(0, 0, macropad.display.width, macropad.display.height, fill=BLACK))

    group.append(label.Label(
        terminalio.FONT,
        text=buttons[key][TEXT],
        color=WHITE,
        scale=2,
        anchored_position=(
            macropad.display.width / 2,
            macropad.display.height / 2,
        ),
        anchor_point=(
            0.5,
            0.5
        )
    ))

    macropad.display.root_group = group
    macropad.display.refresh()
    macropad.red_led = True


def main():
    print('Starting...')

    macropad = MacroPad()
    macropad.display.auto_refresh = False
    macropad.pixels.auto_write = False

    macropad.keyboard.release_all()
    macropad.consumer_control.release()
    macropad.mouse.release_all()
    macropad.stop_tone()

    displayMap(macropad)

    last_position = 0
    start_time = 0
    print('Ready...')
    deadline = ticks_add(ticks_ms(), DISPLAY_KEY_MS)

    while True:
        if not ticks_less(ticks_ms(), deadline):
            displayMap(macropad)
            deadline = ticks_add(ticks_ms(), DISPLAY_KEY_MS)

        # knob rotation
        position = macropad.encoder
        if position != last_position:
            if position < last_position:
                displayKey(macropad, KNOB_CCW)
                macropad.consumer_control.send(buttons[KNOB_CCW][CONTROL])
            if position > last_position:
                displayKey(macropad, KNOB_CW)
                macropad.consumer_control.send(buttons[KNOB_CW][CONTROL])
            last_position = position
            continue

        # knob press
        macropad.encoder_switch_debounced.update()
        encoder_switch = macropad.encoder_switch_debounced.pressed
        if encoder_switch:
            displayKey(macropad, KNOB_PRESS)
            macropad.consumer_control.send(buttons[KNOB_PRESS][CONTROL])
            continue

        event = macropad.keys.events.get()
        if not event or event.key_number >= len(buttons):
            continue # No event, or no macro
        key_number = event.key_number + KNOB_COUNT
        pressed = event.pressed

        if pressed:
            displayKey(macropad, key_number)
            macropad.pixels[key_number - KNOB_COUNT] = 0x999999
            macropad.pixels.show()
            sequence = buttons[key_number][CONTROL]
            for item in sequence:
                if isinstance(item, int):
                    if item >= 0:
                        macropad.keyboard.press(item)
                    else:
                        macropad.keyboard.release(-item)
                if isinstance(item, str):
                    macropad.keyboard_layout.write(item)
                elif isinstance(item, list):
                    for code in item:
                        if isinstance(code, int):
                            macropad.consumer_control.release()
                            macropad.consumer_control.press(code)
                        if isinstance(code, float):
                            time.sleep(code)
        else:
            # Release any still-pressed keys, consumer codes, mouse buttons
            # Keys and mouse buttons are individually released this way (rather
            # than release_all()) because pad supports multi-key rollover, e.g.
            # could have a meta key or right-mouse held down by one macro and
            # press/release keys/buttons with others. Navigate popups, etc.
            for item in sequence:
                if isinstance(item, int):
                    if item >= 0:
                        macropad.keyboard.release(item)
            macropad.consumer_control.release()
            if key_number >= KNOB_COUNT:
                macropad.pixels[key_number - KNOB_COUNT] = buttons[key_number][COLOR]
                macropad.pixels.show()


if __name__ == '__main__':
    main()
