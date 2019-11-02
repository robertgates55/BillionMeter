import os
import time
import RPi.GPIO as GPIO
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
import urllib2
import base64
import datetime

BALLS_DROPPED_FILENAME = os.path.expanduser("~/balls_dropped.txt")
HOPPER_CONTENTS_FILENAME = os.path.expanduser("~/hopper_contents.txt")
ROWS_PER_BALL = 2000000
NUM_STEPS=45
MAIN_GATE_CONTROL_PINS = [6,13,19,26]
PRE_GATE_CONTROL_PINS = [2,3,4,14]
BUTTON_POWER_PIN=20
BUTTON_INPUT_PIN=21
HALFSTEP_SEQ = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1]
]


def button_pressed_callback(channel):
    """
    Triggers when the button is pressed. Resets the hopper count to 10.
    Button should be connected to 3.3v on one side and to BUTTON_INPUT_PIN on
    the other side.
    """
    store_count(HOPPER_CONTENTS_FILENAME, 10)

def setup():
    inky_display = InkyPHAT("red")
    inky_display.set_border(inky_display.WHITE)

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_POWER_PIN, GPIO.OUT)
    GPIO.output(BUTTON_POWER_PIN, 1)
    GPIO.setup(BUTTON_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(BUTTON_INPUT_PIN, GPIO.RISING, callback=button_pressed_callback, bouncetime=300)

    for pin in (MAIN_GATE_CONTROL_PINS + PRE_GATE_CONTROL_PINS):
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, 0)

def update_display(string):
    font = ImageFont.truetype("resources/Minecraft.ttf", 30)
    img = Image.open("resources/inkyphat.png")
    draw = ImageDraw.Draw(img)

    message = string
    w, h = font.getsize(message)
    x = (inky_display.WIDTH / 2) - (w / 2)
    y = (inky_display.HEIGHT / 2) - (h / 2) + 15
    draw.text((x, y), message, inky_display.RED, font)

    inky_display.set_image(img)
    inky_display.show()


def store_count(filename, count):
    with open(filename, "w") as fd:
        fd.write(str(count) + "\n")


def get_current_count(filename):
    if not os.path.exists(filename):
        return 0
    else:
        with open(filename, "r") as fd:
            return int(fd.readline().strip())


def get_latest_row_count():
    request = urllib2.Request("https://pingpometer.common.duco.services/get")

    base64string = base64.b64encode('%s:%s' % ('duco', os.environ['PINGPOMETER_PASSWORD']))
    request.add_header("Authorization", "Basic %s" % base64string)

    count = int(urllib2.urlopen(request).read())
    return count


def calculate_balls_to_drop(new_row_count):
    difference = round((new_row_count / ROWS_PER_BALL) - get_current_count(BALLS_DROPPED_FILENAME))
    if difference < 0:
        difference = 0
    return int(difference)


def new_hi_score():
    update_display("HI-SCORE")


def open_gate(control_pins):
    for i in range(NUM_STEPS):
        for halfstep in range(8):
            for pin in range(4):
                GPIO.output(control_pins[pin], HALFSTEP_SEQ[halfstep][pin])
            time.sleep(0.001)
    for pin in control_pins:
        GPIO.output(pin, 0)


def shut_gate(control_pins):
    for i in range(NUM_STEPS):
        for halfstep in reversed(range(8)):
            for pin in reversed(range(4)):
                GPIO.output(control_pins[pin], HALFSTEP_SEQ[halfstep][pin])
            time.sleep(0.001)
    for pin in control_pins:
        GPIO.output(pin, 0)

def drop_ball():
    open_gate(MAIN_GATE_CONTROL_PINS)
    time.sleep(1)
    shut_gate(MAIN_GATE_CONTROL_PINS)
    open_gate(PRE_GATE_CONTROL_PINS)
    time.sleep(1)
    shut_gate(PRE_GATE_CONTROL_PINS)

def drop_balls(num_balls, final_count):
    n = 0
    while n < num_balls:
        if get_current_count(HOPPER_CONTENTS_FILENAME) == 0:
            update_display('REFILL ME')

        # Sleep until the button is pressed
        while get_current_count(HOPPER_CONTENTS_FILENAME) == 0:
            time.sleep(1)

        drop_ball()
        store_count(BALLS_DROPPED_FILENAME, get_current_count(BALLS_DROPPED_FILENAME) + 1)
        store_count(HOPPER_CONTENTS_FILENAME, get_current_count(HOPPER_CONTENTS_FILENAME) - 1)
        n += 1

    update_display('{:,}'.format(final_count))

setup()

print("Syncing. Current ball count = " + str(get_current_count(BALLS_DROPPED_FILENAME)))
# Get latest count
latest_row_count = get_latest_row_count()

print("Latest row count = " + str(latest_row_count))

# How many balls
num_balls = calculate_balls_to_drop(latest_row_count)

print("Balls to drop = " + str(num_balls))

if num_balls > 0:
    new_hi_score()
else:
    update_display("NO CHANGE")

print("Dropping = " + str(num_balls))

# Drop them & update the final count
drop_balls(num_balls, latest_row_count)

print("Dropped. New ball count = " + str(get_current_count(BALLS_DROPPED_FILENAME)))
