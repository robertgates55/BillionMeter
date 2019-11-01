import os
import time
import RPi.GPIO as GPIO
from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw
import urllib2
import base64
import datetime

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

main_gate_control_pins = [6,13,19,26]
pre_gate_control_pins = [2,3,4,14]
BUTTON_POWER_PIN=20
BUTTON_INPUT_PIN=21
REFILL_FILENAME = os.path.expanduser("~/needs_refill.txt")

GPIO.setup(BUTTON_POWER_PIN, GPIO.OUT)
GPIO.output(BUTTON_POWER_PIN, 1)
GPIO.setup(BUTTON_INPUT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

def button_pressed_callback(channel):
    """
    Triggers when the button is pressed. Deletes the data file if one exists.
    Button should be connected to 3.3v on one side and to BUTTON_INPUT_PIN on
    the other side.
    """
    if os.path.exists(REFILL_FILENAME):
        os.remove(REFILL_FILENAME)

GPIO.add_event_detect(BUTTON_INPUT_PIN, GPIO.RISING, callback=button_pressed_callback, bouncetime=300)

for pin in (main_gate_control_pins + pre_gate_control_pins):
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)

DATA_FILENAME = os.path.expanduser("~/balls_dropped.txt")
ROWS_PER_BALL = 2000000
NUM_STEPS=45

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
    request = urllib2.Request("https://pingpometer.common.duco.services/get")

    base64string = base64.b64encode('%s:%s' % ('duco', os.environ['PINGPOMETER_PASSWORD']))
    request.add_header("Authorization", "Basic %s" % base64string)

    count = int(urllib2.urlopen(request).read())
    return count


def calculate_balls_to_drop(new_row_count):
    difference = round((new_row_count / ROWS_PER_BALL) - get_current_ball_count())
    if difference < 0:
        difference = 0
    return int(difference)


def new_hi_score():
    update_display("HI-SCORE")


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
    time.sleep(1)
    shut_gate(main_gate_control_pins)
    open_gate(pre_gate_control_pins)
    time.sleep(1)
    shut_gate(pre_gate_control_pins)

def drop_balls(num_balls, final_count):
    n = 0
    balls_dropped = 0
    while n < num_balls:
        if balls_dropped >= 10:
            with open(REFILL_FILENAME, "w") as fd:
                fd.write("refill me!")
            update_display('REFILL ME')

        # Sleep until the button is pressed
        while os.path.exists(REFILL_FILENAME):
            sleep(1)
            balls_dropped = 0

        drop_ball()
        store_ball_count(get_current_ball_count() + 1)
        n += 1
        balls_dropped += 1

    update_display('{:,}'.format(final_count))


print("Syncing. Current ball count = " + str(get_current_ball_count()))
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

print("Dropped. New ball count = " + str(get_current_ball_count()))
