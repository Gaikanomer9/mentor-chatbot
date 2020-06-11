import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    target = os.environ.get("TARGET", "World Updated")
    return "Hello {}!\n".format(target)


@app.route("/app")
def hello_world_app():
    target = os.environ.get("TARGET", "World Updated")
    return "Small test"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
