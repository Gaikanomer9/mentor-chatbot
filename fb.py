import requests
import json
import logging_handler
from alphabet_detector import AlphabetDetector
import logging
from datetime import date, timedelta
from config import FB_TOKEN, PROJECT_ID
from gcp import (
    access_secret_version,
    store_skill_request,
    store_context,
    retrieve_context,
    store_progress_skill,
    get_progress_skills,
    get_progress_skill,
    delete_progress_skill,
    save_notification,
)

ACCESS_TOKEN = access_secret_version(PROJECT_ID, FB_TOKEN["name"], FB_TOKEN["version"])

skill_selection_text = "Send me the name of the skill you want to learn or simply select one of the already available skills below: "
level_selection_text = "Perfect! What is your approximate level of knowledge in "
time_selection_text = "How much time for learning this topic do you have per week?"

ad = AlphabetDetector()


def handleOptin(sender_psid, received_message):
    if received_message.get("type") == "one_time_notif_req":
        token = received_message.get("one_time_notif_token")
        payload = received_message.get("payload")
        skill = payload.split("_")[3]
        assignment = payload.split("_")[4]
        user_time = float(payload.split("_")[5])
        course_time = float(payload.split("_")[6])
        time_per_day = user_time / 7.0
        days_to_complete = int(course_time / time_per_day)
        if days_to_complete > 10:
            days_to_complete = 10
        notif_date = date.today() + timedelta(days=days_to_complete)
        notif_date = str(notif_date.year) + str(notif_date.month) + str(notif_date.day)
        save_notification(sender_psid, skill, assignment, notif_date, token)
        request = {
            "text": "All right! I will check up on you after "
                    + str(days_to_complete)
                    + " days."
        }
        callSendAPI(sender_psid, request)


def handleMessage(sender_psid, received_message):
    context = retrieve_context(sender_psid)
    store_context(sender_psid, "")
    if received_message.get("quick_reply"):
        payload = received_message["quick_reply"]["payload"]
        if "next_page" in payload:
            generate_quick_reply_pagination(payload, sender_psid)
            return
        elif "previous_page" in payload:
            generate_quick_reply_pagination(payload, sender_psid)
            return
        elif "skill_selection" in payload:
            generate_quick_reply_skill(payload, sender_psid)
            return
        elif "level" in payload:
            generate_quick_reply_level(payload, sender_psid)
            return
        elif "time" in payload:
            generate_template_time_picker(payload, sender_psid)
            return
    elif received_message.get("text"):
        if check_latin(sender_psid, received_message.get("text")):
            pass
        elif context["context"] == "submit_skill":
            generate_template_skill_submission(sender_psid, received_message)
            return
        elif received_message["text"] == "my skills":
            template_skills_progress(sender_psid)
            return
        elif received_message["text"] == "show skills":
            generate_template_show_skills(sender_psid)
            return
        else:
            # default request
            request = {"text": "I'm not that good with understanding human speech now. " +
                               "Can you try using the menu, please?"}
            callSendAPI(sender_psid, request)
            generate_template_show_skills(sender_psid)
    return


def handlePostback(sender_psid, received_postback):
    payload = received_postback.get("payload")
    # context = retrieve_context(sender_psid)
    store_context(sender_psid, "")
    if payload == "get_started":
        gen_temp_get_started(sender_psid)
        return
    elif payload == "show_skills":
        generate_template_show_skills(sender_psid)
        return
    elif payload == "my_skills":
        template_skills_progress(sender_psid)
        return
    elif "apply_for" in payload:
        template_skills_apply(sender_psid)
        return
    elif "showdetailtask" in payload:
        template_skills_task(sender_psid, payload.split("_")[1])
        return
    elif "completed" in payload:
        generate_template_complete_task(sender_psid, payload)
        # template_skills_progress(sender_psid)
        return
    elif "startagain" in payload:
        gen_temp_get_start_again(sender_psid, payload)
        return
    elif "remove" in payload:
        gen_temp_remove(sender_psid, payload)
        return
    elif payload == "submit_skill":
        gen_temp_submit_skill(sender_psid)
        return
    return


def check_latin(sender_psid, text):
    if not ad.is_latin(text):
        request = {"text": "Sorry! I can only speak in English!"}
        callSendAPI(sender_psid, request)
        return True
    else:
        return False


def template_skills_apply(sender_psid):
    request = {"text": "Cool! Will start learning this as soon as it's implemented!"}
    callSendAPI(sender_psid, request)


def gen_temp_submit_skill(sender_psid):
    request = {"text": "Sure, what would you like to learn?"}
    store_context(sender_psid, "submit_skill")
    callSendAPI(sender_psid, request)


def gen_temp_remove(sender_psid, payload):
    delete_progress_skill(sender_psid, payload.split("_")[1])
    request = {"text": "The task was removed"}
    callSendAPI(sender_psid, request)
    template_skills_progress(sender_psid)


def gen_temp_get_start_again(sender_psid, payload):
    skill_progress = get_progress_skill(sender_psid, payload.split("_")[1])
    store_progress_skill(
        sender_psid,
        skill_progress["level"],
        skill_progress["skill"],
        skill_progress["time"],
        0,
        completed=True,
    )
    template_skills_progress(sender_psid)


def gen_temp_get_started(sender_psid):
    name = getName(sender_psid)
    request = {
        "text": "Welcome, "
                + name
                + "! Hello! I'm Raido bot and I will help you learn skills you want. I can coach you on learning the whole knowledge path (like frontend dev or DevOps) or help you get the specific skill (e.g. Photoshop, Docker).",
    }
    callSendAPI(sender_psid, request)
    request = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": "Let's start by choosing the knowledge domain. What would you like to learn?",
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
    callSendAPI(sender_psid, request)


def generate_quick_reply_pagination(payload, sender_psid):
    request = {
        "text": skill_selection_text,
        "quick_replies": generateQuickRepliesSkills(int(payload.split("_")[2])),
    }
    callSendAPI(sender_psid, request)


def generate_quick_reply_skill(payload, sender_psid):
    request = {
        "text": level_selection_text
                + get_skill(int(payload.split("_")[2]))["name"]
                + "?",
        "quick_replies": generateQuickRepliesLevel(int(payload.split("_")[2])),
    }
    callSendAPI(sender_psid, request)


def generate_quick_reply_level(payload, sender_psid):
    request = {
        "text": time_selection_text,
        "quick_replies": generateQuickRepliesTime(
            int(payload.split("_")[0]), payload.split("_")[2]
        ),
    }
    callSendAPI(sender_psid, request)


def generate_template_skill_submission(sender_psid, received_message):
    store_skill_request(sender_psid, received_message.get("text"))
    request = {
        "text": "Great! Would you like to get a one-time notification when I have this skill?"
    }
    callSendAPI(sender_psid, request)


def generate_template_time_picker(payload, sender_psid):
    level = payload.split("_")[0]
    skill = payload.split("_")[1]
    time = payload.split("_")[3]
    assignment = get_next_assignment(skill, level, -1)
    store_progress_skill(sender_psid, level, skill, time, assignment)
    skill_data = get_skill(int(skill))
    task_type = skill_data["assignments"][assignment]["type"]
    task_name = skill_data["assignments"][assignment]["name"]
    course_time = skill_data["assignments"][assignment]["time_hours"]
    request = {
        "text": "Awesome! To check the progress and current task for your skill use the menu."
    }
    callSendAPI(sender_psid, request)
    template_skills_task(sender_psid, skill)
    gen_templ_one_time_req(sender_psid, skill, assignment, time, course_time)


def gen_templ_one_time_req(sender_psid, skill, assignment, user_time, course_time):
    request = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "one_time_notif_req",
                "title": "Check on your progress for the task in a couple of days?",
                "payload": "one_time_request_"
                           + str(skill)
                           + "_"
                           + str(assignment)
                           + "_"
                           + str(user_time)
                           + "_"
                           + str(course_time),
            },
        }
    }
    callSendAPI(sender_psid, request)


def generate_template_complete_task(sender_psid, payload):
    skill_progress = get_progress_skill(sender_psid, payload.split("_")[1])
    if skill_progress == None:
        print("Skill is not existing")
        logging.error("Skill is not existing for user" + str(sender_psid))
    assignment = get_next_assignment(
        skill_progress["skill"],
        skill_progress["level"],
        skill_progress["cur_assignment"],
    )
    if assignment == skill_progress["cur_assignment"]:
        store_progress_skill(
            sender_psid,
            skill_progress["level"],
            skill_progress["skill"],
            skill_progress["time"],
            skill_progress["cur_assignment"],
            completed=True,
        )
        request = {
            "text": "Congratulations! You completed learning of the "
                    + get_skill(skill_progress["skill"])["name"]
        }
        callSendAPI(sender_psid, request)
    else:
        store_progress_skill(
            sender_psid,
            skill_progress["level"],
            skill_progress["skill"],
            skill_progress["time"],
            assignment,
        )
        template_skills_task(sender_psid, skill_progress["skill"])
        skill_data = get_skill(int(skill_progress["skill"]))
        course_time = skill_data["assignments"][assignment]["time_hours"]
        gen_templ_one_time_req(
            sender_psid,
            skill_progress["skill"],
            assignment,
            skill_progress["time"],
            course_time,
        )


def generate_template_show_skills(sender_psid):
    request = {
        "text": skill_selection_text,
        "quick_replies": generateQuickRepliesSkills(0),
    }
    store_context(sender_psid, "skill_selection")
    callSendAPI(sender_psid, request)


def find_skill(progress_list, skill_num):
    for pr in progress_list:
        if str(pr["skill"]) == str(skill_num):
            return pr


def template_skills_task(psid, skill_num):
    buttons = []
    skills = get_progress_skills(psid)
    print(skills)
    print(skill_num)
    skill = find_skill(skills, int(skill_num))
    skill_data = get_skill(int(skill_num))
    print(skill_data)
    print("cur asignment" + str(skill["cur_assignment"]))
    asign_type = skill_data["assignments"][int(skill["cur_assignment"])]["type"]
    asign_name = skill_data["assignments"][int(skill["cur_assignment"])]["name"]
    asign_author = skill_data["assignments"][int(skill["cur_assignment"])]["author"]
    asign_rating = skill_data["assignments"][int(skill["cur_assignment"])]["rating"]
    asign_url = skill_data["assignments"][int(skill["cur_assignment"])]["url"]
    asign_started = skill["timestamp_creation"]

    text = (
            "Your new assignment is the "
            + asign_type
            + ' "'
            + asign_name
            + '" by '
            + asign_author
            + ". \n\n"
    )
    text += (
            "Rating: " + str(asign_rating) + "\n\n" + "Started: " + str(asign_started)[:10]
    )

    buttons = [
        {
            "type": "web_url",
            "title": "Go to task",
            "url": asign_url,
            "webview_height_ratio": "full",
        },
        {
            "type": "postback",
            "title": "Mark as done",
            "payload": "completed_" + str(skill["skill"]),
        },
    ]
    request = {
        "attachment": {
            "type": "template",
            "payload": {"template_type": "button", "text": text, "buttons": buttons, },
        }
    }
    callSendAPI(psid, request)


def template_skills_progress(psid):
    elements = []
    skills = get_progress_skills(psid)
    for skill in skills:
        skill_data = get_skill(skill["skill"])
        progress = (
                str(
                    int(
                        float(skill["cur_assignment"])
                        / float(len(skill_data["assignments"]))
                        * 100
                    )
                ).zfill(1)
                + "%"
        )
        asign_type = skill_data["assignments"][int(skill["cur_assignment"])]["type"]
        asign_name = skill_data["assignments"][int(skill["cur_assignment"])]["name"]
        asign_url = skill_data["assignments"][int(skill["cur_assignment"])]["url"]
        task_text = "Task: " + asign_type + ' "' + asign_name + '".'
        completed_text = "Course is completed. Good job!"
        progress_text = "Progress: " + progress + " \n\n"
        buttons = [
            {
                "type": "web_url",
                "title": "Go to " + asign_type,
                "url": asign_url,
                "webview_height_ratio": "full",
            },
            # {
            #     "type": "postback",
            #     "title": "Mark as completed",
            #     "payload": "completed_" + str(skill["skill"]),
            # },
            {
                "type": "postback",
                "title": "Show current task",
                "payload": "showdetailtask_" + str(skill["skill"]),
            },
        ]
        if skill["completed"] == True:
            add_text = completed_text
            progress_text = ""
            buttons = [
                {
                    "type": "postback",
                    "title": "Start again",
                    "payload": "startagain_" + str(skill["skill"]),
                },
                {
                    "type": "postback",
                    "title": "Remove from list",
                    "payload": "remove_" + str(skill["skill"]),
                },
            ]
        else:
            add_text = task_text
        elements.append(
            {
                "title": skill_data["name"],
                "image_url": skill_data["image_url"],
                "subtitle": progress_text + add_text,
                "default_action": {
                    "type": "web_url",
                    "url": asign_url,
                    "webview_height_ratio": "COMPACT",
                },
                "buttons": buttons,
            }
        )
    if len(elements) == 0:
        request = {
            "text": "Currently, you don't have any active skills. Start be selecting the skill you want to learn. You can see the list of available skills in the menu."
        }
    else:
        request = {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "image_aspect_ratio": "square",
                    "elements": elements,
                },
            }
        }
    callSendAPI(psid, request)


def get_next_assignment(skill, level, cur_assignment):
    with open("skills.json") as json_file:
        skills = json.load(json_file)["skills"]
        new_assignment = cur_assignment
        for i, assignment in enumerate(skills[int(skill)]["assignments"]):
            if int(assignment["level"]) < int(level) or i <= cur_assignment:
                continue
            else:
                new_assignment = i
                break
        return new_assignment


def get_skill(num):
    with open("skills.json") as json_file:
        skills = json.load(json_file)["skills"]
        return skills[int(num)]


def generateQuickRepliesTime(skill_num, level):
    quick_replies = [
        {
            "content_type": "text",
            "title": "3 Hours",
            "payload": str(level) + "_" + str(skill_num) + "_time_1",
        },
        {
            "content_type": "text",
            "title": "5 Hours",
            "payload": str(level) + "_" + str(skill_num) + "_time_3",
        },
        {
            "content_type": "text",
            "title": "8 Hours",
            "payload": str(level) + "_" + str(skill_num) + "_time_7",
        },
        {
            "content_type": "text",
            "title": "13 Hours",
            "payload": str(level) + "_" + str(skill_num) + "_time_15",
        },
        {
            "content_type": "text",
            "title": "21 Hours",
            "payload": str(level) + "_" + str(skill_num) + "_time_15",
        },
    ]
    return quick_replies


def generateQuickRepliesLevel(skill_num):
    quick_replies = [
        {
            "content_type": "text",
            "title": "Beginner",
            "payload": str(skill_num) + "_level_0",
        },
        {
            "content_type": "text",
            "title": "Middle",
            "payload": str(skill_num) + "_level_1",
        },
        {
            "content_type": "text",
            "title": "Advanced",
            "payload": str(skill_num) + "_level_2",
        },
    ]
    return quick_replies


def generateQuickRepliesSkills(page):
    pagination = 5  # 5 skills per page
    quick_replies = []
    with open("skills.json") as json_file:
        skills = json.load(json_file)["skills"]
        skills_n = len(skills)
        if page > 0:
            quick_replies.append(
                {
                    "content_type": "text",
                    "title": "Previous page",
                    "payload": "previous_page_" + str(page - 1),
                }
            )
        for i in range(page * pagination, page * pagination + pagination):
            if i >= skills_n:
                break
            quick_replies.append(
                {
                    "content_type": "text",
                    "title": skills[i]["name"],
                    "payload": "skill_selection_" + str(i)
                    # "image_url":"http://example.com/img/red.png"
                }
            )
        if (page * pagination + pagination - 1) < skills_n:
            quick_replies.append(
                {
                    "content_type": "text",
                    "title": "Next page",
                    "payload": "next_page_" + str(page + 1),
                }
            )
    return quick_replies


def generate_one_time_template(token, assignment, skill):
    skill_data = get_skill(int(skill))
    asign_name = skill_data["assignments"][int(assignment)]["name"]
    request = {
        "attachment": {
            "type": "template",
            "payload": {
                "template_type": "button",
                "text": 'Hey! This is a reminder for the task "'
                        + str(asign_name)
                        + " you had. Did you make it and ready for a new challenge?",
                "buttons": [
                    {
                        "type": "postback",
                        "title": "Show my skills",
                        "payload": "my_skills",
                    },
                    {
                        "type": "postback",
                        "title": "Mark as done",
                        "payload": "completed_" + str(skill),
                    },
                ],
            },
        }
    }
    callOneTimeNotif(token, request)


def callOneTimeNotif(token, _request):
    request = json.dumps(
        {"recipient": {"one_time_notif_token": token}, "message": _request}
    )

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


def callSendAPI(sender_psid, _request):
    request = json.dumps({"recipient": {"id": sender_psid}, "message": _request})

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
