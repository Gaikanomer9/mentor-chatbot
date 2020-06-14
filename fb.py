import requests
import json
import logging_handler
import logging
from config import FB_TOKEN, PROJECT_ID
from gcp import access_secret_version

ACCESS_TOKEN = access_secret_version(PROJECT_ID, FB_TOKEN["name"], FB_TOKEN["version"])


def handleMessage(sender_psid, received_message):
    response = {}
    if received_message.get("text"):
        response = {
            "text": "You've sent a message: "
            + received_message.get("text")
            + ". Now send the image"
        }
    callSendAPI(sender_psid, response)
    return


def handlePostback(sender_psid, received_postback):
    return


def callSendAPI(sender_psid, response):
    request = json.dumps({"recipient": {"id": sender_psid}, "message": response})

    params = {"access_token": ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}

    r = requests.post(
        "https://graph.facebook.com/v2.6/me/messages",
        params=params,
        headers=headers,
        data=request,
    )
    if r.status_code != 200:
        logging.error(r.status_code)
        logging.error(r.text)
