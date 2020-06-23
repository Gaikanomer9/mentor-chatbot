from app import app
from gcp import access_secret_version
from config import FB_CHALLENGE, PROJECT_ID


def test_webhook_challenge_rejected():
    token = "incorrect token bla-bla"
    response = app.test_client().get(
        "/webhook?hub.verify_token="
        + token
        + "&hub.challenge=CHALLENGE_ACCEPTED&hub.mode=subscribe"
    )
    assert response.status_code == 403


# def test_webhook_challenge_accepted():
#     token = access_secret_version(
#         PROJECT_ID, FB_CHALLENGE["name"], FB_CHALLENGE["version"]
#     )
#     response = app.test_client().get(
#         "/webhook?hub.verify_token="
#         + token
#         + "&hub.challenge=CHALLENGE_ACCEPTED&hub.mode=subscribe"
#     )
#     assert response.status_code == 200
#     assert response.data == b"CHALLENGE_ACCEPTED"


# def inc(x):
#     return x + 1


# def test_answer():
#     assert inc(3) == 5
