import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def hello_world():
    target = os.environ.get("TARGET", "World Updated")
    return "Hello {}!\n".format(target)


@app.route("/error")
def hello_world_error():
    target = os.environ.get("TARGET", "World ")
    raise Exception("special unhandled exception")
    return "Hello {}!\n".format(target)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
