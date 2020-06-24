from google.cloud import secretmanager
from google.cloud import firestore

# Project ID is determined by the GCLOUD_PROJECT environment variable
db = firestore.Client()


def delete_notifications(date):
    notif_refs = db.collection("notifications")
    query = notif_refs.where("notif_date", "==", str(date))
    docs = query.stream()
    for doc in docs:
        doc.reference.delete()


def get_notifications(date_today):
    notif_refs = db.collection("notifications")
    query = notif_refs.where("notif_date", "==", str(date_today))
    docs = query.stream()
    notifs = []
    for doc in docs:
        notifs.append(doc.to_dict())
    return notifs


def save_notification(psid, skill, assignment, notif_date, token):
    db.collection("notifications").add(
        {
            "psid": psid,
            "skill": skill,
            "cur_assignment": assignment,
            "notif_date": notif_date,
            "timestamp_creation": firestore.SERVER_TIMESTAMP,
            "token": token,
        }
    )


def get_progress_skill(psid, skill):
    doc = db.collection("progress_skills").document(str(psid) + "_" + str(skill)).get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None


def get_progress_skills(psid):
    skills_ref = db.collection("progress_skills")
    query = skills_ref.where("psid", "==", str(psid))
    docs = query.stream()
    skills = []
    for doc in docs:
        skills.append(doc.to_dict())
    return skills


def delete_progress_skill(psid, skill):
    db.collection("progress_skills").document(str(psid) + "_" + str(skill)).delete()


def store_progress_skill(psid, level, skill, time, assignment, completed=False):
    db.collection("progress_skills").document(str(psid) + "_" + str(skill)).set(
        {
            "psid": psid,
            "skill": skill,
            "level": level,
            "time": time,
            "cur_assignment": assignment,
            "timestamp_creation": firestore.SERVER_TIMESTAMP,
            "completed": completed,
        }
    )


def retrieve_context(psid):
    doc = db.collection(u"context").document(psid).get()
    if doc.exists:
        return doc.to_dict()
    else:
        return {"context": ""}


def store_context(psid, context):
    db.collection(u"context").document(psid).set({"context": context})


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
