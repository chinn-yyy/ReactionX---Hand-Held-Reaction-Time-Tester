import time
import random
import board
import digitalio
import neopixel
import displayio
import terminalio
import busio
from adafruit_display_text import label
import adafruit_ssd1306

# ---------------- PIN SETUP ----------------
# CHANGE THESE IF YOUR PCB USES DIFFERENT PINS

READY_PIN = board.D1      # top button
REACT1_PIN = board.D2     # bottom button
REACT2_PIN = board.D3     # bottom button
RESET_PIN = board.D4      # reset button

LED_PIN = board.D0
LED_COUNT = 8

I2C_SDA = board.SDA
I2C_SCL = board.SCL

# ---------------- BUTTON SETUP ----------------
def make_button(pin):
    b = digitalio.DigitalInOut(pin)
    b.direction = digitalio.Direction.INPUT
    b.pull = digitalio.Pull.UP
    return b

ready_btn = make_button(READY_PIN)
react1_btn = make_button(REACT1_PIN)
react2_btn = make_button(REACT2_PIN)
reset_btn = make_button(RESET_PIN)

# ---------------- LED SETUP ----------------
pixels = neopixel.NeoPixel(
    LED_PIN,
    LED_COUNT,
    brightness=0.3,
    auto_write=False
)

def set_all(color):
    pixels.fill(color)
    pixels.show()

# ---------------- OLED SETUP ----------------
displayio.release_displays()

i2c = busio.I2C(I2C_SCL, I2C_SDA)
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_ssd1306.SSD1306(display_bus, width=128, height=32)

group = displayio.Group()
display.root_group = group

def show_text(line1="", line2=""):
    group = displayio.Group()

    t1 = label.Label(terminalio.FONT, text=line1, x=0, y=10)
    t2 = label.Label(terminalio.FONT, text=line2, x=0, y=26)

    group.append(t1)
    group.append(t2)

    display.root_group = group

# ---------------- STORAGE ----------------
highscore = None

# ---------------- STATES ----------------
HOME = 0
WAITING = 1
TIMING = 2
RESULT = 3

state = HOME
start_time = 0
reaction_time = 0
go_time = 0
blink_timer = 0
blink_state = False

# ---------------- HELPERS ----------------
def pressed(btn):
    return not btn.value

def any_react_pressed():
    return pressed(react1_btn) or pressed(react2_btn)

# ---------------- STARTUP ----------------
show_text("Reaction X", "High Score: --")
set_all((255,255,255))

# ---------------- MAIN LOOP ----------------
while True:

    # ---------- HOME SCREEN ----------
    if state == HOME:

        # blink white LEDs
        if time.monotonic() - blink_timer > 0.5:
            blink_timer = time.monotonic()
            blink_state = not blink_state
            set_all((255,255,255) if blink_state else (0,0,0))

        hs = "--" if highscore is None else str(highscore)+"ms"
        show_text("Reaction X", "High Score: " + hs)

        if pressed(ready_btn):
            time.sleep(0.2)
            set_all((255,0,0))  # red
            show_text("Get Ready...", "")
            go_time = time.monotonic() + random.uniform(3,7)
            state = WAITING


    # ---------- WAITING FOR GO ----------
    elif state == WAITING:

        # early press detection (optional)
        if any_react_pressed():
            show_text("Too Early!", "")
            set_all((255,255,255))
            time.sleep(2)
            state = HOME

        if time.monotonic() >= go_time:
            set_all((0,255,0))  # green
            start_time = time.monotonic()
            state = TIMING


    # ---------- TIMER RUNNING ----------
    elif state == TIMING:

        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        show_text("GO!", str(elapsed_ms) + " ms")

        if any_react_pressed():
            reaction_time = elapsed_ms
            set_all((255,255,255))  # white

            if highscore is None or reaction_time < highscore:
                highscore = reaction_time

            state = RESULT
            time.sleep(0.3)


    # ---------- RESULT ----------
    elif state == RESULT:

        show_text(
            "Score: " + str(reaction_time) + "ms",
            "Best: " + str(highscore) + "ms"
        )

        if pressed(reset_btn):
            time.sleep(0.2)
            state = HOME

        if pressed(ready_btn):
            time.sleep(0.2)
            set_all((255,0,0))
            show_text("Get Ready...", "")
            go_time = time.monotonic() + random.uniform(3,7)
            state = WAITING

    time.sleep(0.01)
