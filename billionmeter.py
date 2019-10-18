import os
import time
import RPi.GPIO as GPIO
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne
import urllib2

inky_display = InkyPHAT("red")
inky_display.set_border(inky_display.WHITE)

GPIO.setmode(GPIO.BCM)

halfstep_seq = [
    [1,0,0,0],
    [1,1,0,0],
    [0,1,0,0],
    [0,1,1,0],
    [0,0,1,0],
    [0,0,1,1],
    [0,0,0,1],
    [1,0,0,1]
]


main_gate_control_pins = [2,3,4,14]
pre_gate_control_pins = [6,13,19,26]
extra_5v_pin = 21
for pin in (main_gate_control_pins + pre_gate_control_pins + [extra_5v_pin]):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)
GPIO.output(extra_5v_pin, 1)

DATA_FILENAME = os.path.expanduser("~/balls_dropped.txt")
ROWS_PER_BALL = 2000000
NUM_STEPS=45

def update_display(string):
    font = ImageFont.truetype(FredokaOne, 22)

    img = Image.new("P", (inky_display.WIDTH, inky_display.HEIGHT))
    draw = ImageDraw.Draw(img)

    message = string
    w, h = font.getsize(message)
    x = (inky_display.WIDTH / 2) - (w / 2)
    y = (inky_display.HEIGHT / 2) - (h / 2)

    draw.text((x, y), message, inky_display.RED, font)
    inky_display.set_image(img)
    #inky_display.show()


def store_ball_count(count):
    with open(DATA_FILENAME, "w") as fd:
        fd.write(str(count) + "\n")


def get_current_ball_count():
    if not os.path.exists(DATA_FILENAME):
        return 0
    else:
        with open(DATA_FILENAME, "r") as fd:
            return int(fd.readline().strip())


def get_latest_row_count():
    count = int(urllib2.urlopen("https://pingpometer.common.duco.services/get").read())
    return count


def calculate_balls_to_drop(new_row_count):
    difference = round((new_row_count / ROWS_PER_BALL) - get_current_ball_count())
    if difference < 0:
        difference = 0
    return difference


def new_hi_score():
    update_display("NEW HI-SCORE")

def open_gate(control_pins):
    for i in range(NUM_STEPS):
        for halfstep in range(8):
            for pin in range(4):
                GPIO.output(control_pins[pin], halfstep_seq[halfstep][pin])
            time.sleep(0.001)
    for pin in control_pins:
        GPIO.output(pin, 0)


def shut_gate(control_pins):
    for i in range(NUM_STEPS):
        for halfstep in reversed(range(8)):
            for pin in reversed(range(4)):
                GPIO.output(control_pins[pin], halfstep_seq[halfstep][pin])
            time.sleep(0.001)
    for pin in control_pins:
        GPIO.output(pin, 0)

def drop_ball():
    open_gate(main_gate_control_pins)
    time.sleep(0.5)
    shut_gate(main_gate_control_pins)
    open_gate(pre_gate_control_pins)
    time.sleep(0.5)
    shut_gate(pre_gate_control_pins)

def drop_balls(num_balls, final_count):
    n = 0
    while n < num_balls:
        drop_ball()
        store_ball_count(get_current_ball_count() + 1)
        n += 1
    update_display(str(final_count))

# Get latest count
latest_row_count = get_latest_row_count()

# How many balls
num_balls = calculate_balls_to_drop(latest_row_count)

if num_balls > 0:
    new_hi_score()
else:
    update_display("No increase")

# Drop them & update the final count
drop_balls(num_balls, latest_row_count)