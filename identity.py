import os
import base64
import traceback

import textwrap
import flask
import flask_mail
import hmac
import hashlib

# Given the application's secret key, and a democracy person identifier,
# returns a token suitable for emailing to them to authenticate themselves.
def sign_person_id(secret_key, person_id):
    digest = hmac.new(secret_key.encode('ascii'), str(person_id).encode('ascii'), hashlib.sha512).digest()
    signature_bytes = base64.urlsafe_b64encode(digest)
    signature = signature_bytes.decode("ascii").rstrip("=\n")
    return signature[0:16]

# Confirmation they're a candidate who can upload a CV

UPLOAD_CV_MESSAGE = textwrap.dedent("""\
    Hi {name},

    Your future constituents would like to read your Curriculum Vitae
    before deciding how to vote.

    Click the link below to share your CV with the world.

    {link}

    Thanks for your help!

    Democracy Club CV team
    (we were behind TheyWorkForYou)
""")

def send_upload_cv_confirmation(app, mail, person_id, to_email, to_name):
    if "DEBUG_EMAIL" in app.config:
        to_email = app.config["DEBUG_EMAIL"]
        print("DEBUG_EMAIL", to_email)

    signature = sign_person_id(app.secret_key, person_id)
    link = flask.url_for("upload_cv_confirmed", person_id=person_id, signature=signature, _external=True)
    print("confirm email:", to_email, link)

    # return False # temporarily disabled until all workflow works

    body = UPLOAD_CV_MESSAGE.format(email=to_email, name=to_name, link=link)
    msg = flask_mail.Message(body=body,
            subject="Upload your CV to apply to be an MP",
            sender=("Democracy Club CV", "cv@democracyclub.org.uk"),
            recipients=[(to_name, to_email)]
          )

    mail.send(msg)


