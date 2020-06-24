import os
from flask import request
from flask import Flask
from gcp import access_secret_version, get_notifications, delete_notifications
from config import FB_CHALLENGE
import logging_handler
import logging
from fb import handleMessage, handlePostback, handleOptin, generate_one_time_template
from datetime import date, timedelta

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
                elif messaging_event.get("optin"):
                    handleOptin(psid, messaging_event.get("optin"))

        return "ok", 200
    else:
        return "Unknown object in body", 404


@app.route("/notifications", methods=["GET"])
def notifications():
    today = date.today()
    yesterday = date.today() - timedelta(days=1)
    today = str(today.year) + str(today.month) + str(today.day)
    yesterday = str(yesterday.year) + str(yesterday.month) + str(yesterday.day)
    notifications = get_notifications(today)
    y_notifs = get_notifications(yesterday)
    delete_notifications(today)
    delete_notifications(yesterday)
    notifications = notifications + y_notifs
    for notif in notifications:
        generate_one_time_template(
            notif["token"], int(notif["cur_assignment"]), int(notif["skill"])
        )
    return "ok", 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8081)))
