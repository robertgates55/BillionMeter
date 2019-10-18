import os
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
control_pins = [2,3,4,14]
for pin in control_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, 0)
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

DATA_FILENAME = os.path.expanduser("~/balls_dropped.txt")
ROWS_PER_BALL = 2000000

def thinking_display(num_seconds):
    t = 0
    while t < num_seconds:
        for char in ['|','/','-','\\']:
            update_display(char * 12)
            time.sleep(0.1)
        t += 0.4

def update_display(string):
    print(string)

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
    return 112000006

def calculate_balls_to_drop(new_row_count):
    difference = round((new_row_count / ROWS_PER_BALL) - get_current_ball_count())
    return difference

def new_hi_score():
    for x in range(5):
        update_display("NEW HI-SCORE")
        time.sleep(0.25)
        update_display("")
        time.sleep(0.25)

def drop_ball():
    for x in range(12):
        update_display((' ' * x) + "0" + (' ' * (11-x)))
        time.sleep(0.05)

    NUM_STEPS=512
    for i in range(NUM_STEPS):
        for halfstep in range(8):
            for pin in range(4):
                GPIO.output(control_pins[pin], halfstep_seq[halfstep][pin])
            time.sleep(0.001)

    for i in range(NUM_STEPS):
        for halfstep in reversed(range(8)):
            for pin in reversed(range(4)):
                GPIO.output(control_pins[pin], halfstep_seq[halfstep][pin])
            time.sleep(0.001)

    GPIO.cleanup()

def drop_balls(num_balls, final_count):
    n = 0
    while n < num_balls:
        drop_ball()
        intermediate_count = final_count - ((num_balls - n) * ROWS_PER_BALL)
        update_display(intermediate_count)
        store_ball_count(get_current_ball_count() + 1)
        thinking_display(1)
        n += 1
    update_display(str(final_count))

#Tension-building drumroll
thinking_display(1)

#Get latest count
latest_row_count = get_latest_row_count()

#How many balls
num_balls = calculate_balls_to_drop(latest_row_count)

if num_balls > 0:
    new_hi_score()

#Drop them & update the final count
drop_balls(num_balls, latest_row_count)
