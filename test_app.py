from app import app
from gcp import access_secret_version
from config import FB_CHALLENGE
import json

data_file = "skills.json"


def test_webhook_challenge_rejected():
    token = "incorrect token bla-bla"
    response = app.test_client().get(
        "/webhook?hub.verify_token="
        + token
        + "&hub.challenge=CHALLENGE_ACCEPTED&hub.mode=subscribe"
    )
    assert response.status_code == 403


def test_webhook_challenge_accepted():
    token = FB_CHALLENGE
    response = app.test_client().get(
        "/webhook?hub.verify_token="
        + token
        + "&hub.challenge=CHALLENGE_ACCEPTED&hub.mode=subscribe"
    )
    assert response.status_code == 200
    assert response.data == b"CHALLENGE_ACCEPTED"


def test_check_data_file():
    with open(data_file) as json_file:
        skills = json.load(json_file)["skills"]
        assert len(skills) > 0
        for skill in skills:
            assert skill.get("name")
            assert skill.get("image_url")
            assert skill.get("assignments")
            has_advanced_level = False
            for assignment in skill.get("assignments"):
                assert assignment.get("type")
                assert assignment.get("name")
                assert assignment.get("author")
                assert assignment.get("release_date")
                assert assignment.get("level") >= 0
                assert assignment.get("rating")
                assert assignment.get("url")
                assert assignment.get("time_hours")
                if assignment.get("level") == 2:
                    has_advanced_level = True
            print(skill.get("name"))
            assert has_advanced_level == True


# def inc(x):
#     return x + 1


# def test_answer():
#     assert inc(3) == 5
