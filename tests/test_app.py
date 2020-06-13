from api.app import app


def webhook_get():
    response = app.test_client().get("/webhook")
    print(response.json)
    assert response.status_code == 200
    assert response.data == b"Waiting for verification"


# def inc(x):
#     return x + 1


# def test_answer():
#     assert inc(3) == 5
