import os
from flask import request
from flask import Flask
from gcp import access_secret_version
from config import FB_CHALLENGE
import logging_handler
import logging
from fb import handleMessage, handlePostback

app = Flask(__name__)


@app.route("/webhook", methods=["GET"])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get(
        "hub.challenge"
    ):
        if not request.args.get("hub.verify_token") == FB_CHALLENGE:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Waiting for verification", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print(data)
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                psid = messaging_event.get("sender").get("id")

                if messaging_event.get("message"):  # someone sent us a message
                    handleMessage(psid, messaging_event.get("message"))

                elif messaging_event.get("postback"):
                    handlePostback(psid, messaging_event.get("postback"))

        return "ok", 200
    else:
        return "Unknown object in body", 404


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))
