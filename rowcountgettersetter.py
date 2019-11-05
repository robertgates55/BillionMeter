import os
from flask import Flask
from waitress import serve

DATA_FILENAME = os.path.expanduser("/home/worker/gettersetter/row_count_persistence.txt")
app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, World!"


@app.route("/set/<count>", methods=['PUT'])
def set(count):
    with open(DATA_FILENAME, "w") as fd:
        fd.write(str(count) + "\n")
    return ''


@app.route("/get", methods=['GET'])
def get():
    with open(DATA_FILENAME, "r") as fd:
        return fd.readline().strip()


@app.route("/<id>/set/<count>", methods=['PUT'])
def set_device_count(id, count):
    DEVICE_COUNT_FILENAME = "/home/worker/gettersetter/%s.txt" % id
    with open(DEVICE_COUNT_FILENAME, "w") as fd:
        fd.write(str(count) + "\n")
    return ''


@app.route("/<id>/get", methods=['GET'])
def get_device_count(id):
    DEVICE_COUNT_FILENAME = "/home/worker/gettersetter/%s.txt" % id
    if os.path.exists(DEVICE_COUNT_FILENAME):
        with open(DEVICE_COUNT_FILENAME, "r") as fd:
            override_count = fd.readline().strip()
            os.remove(DEVICE_COUNT_FILENAME)
            return override_count
    else:
        return '', 418


print("starting up - 0.0.0.0:5000")
serve(app, host='0.0.0.0', port=5000)