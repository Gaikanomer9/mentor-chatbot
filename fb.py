import requests
import json
import logging_handler
import logging
from config import FB_TOKEN, PROJECT_ID
from gcp import access_secret_version, store_skill_request

ACCESS_TOKEN = access_secret_version(PROJECT_ID, FB_TOKEN["name"], FB_TOKEN["version"])


def handleMessage(sender_psid, received_message):
    response = {}
    if received_message.get("text"):
        response = {
            "text": "You've sent a message: "
            + received_message.get("text")
            + ". Now send the image"
        }
    elif received_message.get("attachments"):
        attachment_url = received_message["attachments"][0].get("payload").get("url")
        response = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [
                        {
                            "title": "Is this the right picture?",
                            "subtitle": "Tap a button to answer.",
                            "image_url": attachment_url,
                            "buttons": [
                                {
                                    "type": "postback",
                                    "title": "Yes!",
                                    "payload": "yes",
                                },
                                {"type": "postback", "title": "No!", "payload": "no",},
                            ],
                        }
                    ],
                },
            }
        }
    callSendAPI(sender_psid, response)
    return


def handlePostback(sender_psid, received_postback):
    response = {}
    payload = received_postback.get("payload")

    if payload == "yes":
        response = {"text": "Thanks!"}
    elif payload == "no":
        response = {"text": "Oops, try sending another image."}
    elif payload == "get_started":
        name = getName(sender_psid)
        response = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "Welcome, "
                    + name
                    + "! I will assist you in learning skills you need. Let's start by choosing the knowledge area you are interested in.",
                    "buttons": [
                        {
                            "type": "postback",
                            "title": "Show skills",
                            "payload": "show_skills",
                        }
                    ],
                },
            }
        }
    elif payload == "show_skills":
        response = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "Select the interesting knowledge area for you or submit the desired skill and get notified when it's available",
                    "buttons": [
                        {
                            "type": "postback",
                            "title": "Kubernetes",
                            "payload": "apply_for_kubernetes",
                        },
                        {
                            "type": "postback",
                            "title": "Digital Marketing",
                            "payload": "apply_for_digital_marketing",
                        },
                        {
                            "type": "postback",
                            "title": "Submit new",
                            "payload": "submit_skill",
                        },
                    ],
                },
            }
        }
    elif "apply_for" in payload:
        response = {
            "text": "Cool! Will start learning this as soon as it's implemented!"
        }
    elif payload == "submit_skill":
        response = {"text": "Sure, what would you like to learn?"}
    callSendAPI(sender_psid, response)
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


def getName(sender_psid):
    r = requests.get(
        "https://graph.facebook.com/"
        + sender_psid
        + "?fields=first_name&access_token="
        + ACCESS_TOKEN
    )
    return r.json().get("first_name")
