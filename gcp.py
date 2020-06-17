from google.cloud import secretmanager
from google.cloud import firestore

# Project ID is determined by the GCLOUD_PROJECT environment variable
db = firestore.Client()


def store_skill_request(psid, request):
    db.collection(u"skill_requests").add(
        {"psid": psid, "request": request, "timestamp": firestore.SERVER_TIMESTAMP}
    )


def access_secret_version(project_id, secret_id, version_id):
    """
    Access the payload for the given secret version if one exists. The version
    can be a version number as a string (e.g. "5") or an alias (e.g. "latest").
    """

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = client.secret_version_path(project_id, secret_id, version_id)

    # Access the secret version.
    response = client.access_secret_version(name)

    payload = response.payload.data.decode("UTF-8")
    return payload
