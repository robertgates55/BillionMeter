import os
from flask import Flask
from waitress import serve

DATA_FILENAME = os.path.expanduser("~/row_count_persistence.txt")
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

print("starting up - 0.0.0.0:5000")
serve(app, host='0.0.0.0', port=5000)