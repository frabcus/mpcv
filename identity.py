import os
import base64
import traceback
import email.mime.text
import email.utils

import smtplib
import textwrap
import flask
import hmac

smtp_hostname = os.environ.get("SMTP_HOSTNAME")
smtp_username = os.environ.get("SMTP_USERNAME")
smtp_password = os.environ.get("SMTP_PASSWORD")

debug_email = os.environ.get("DEBUG_EMAIL")

# Given the application's secret key, and a democracy person identifier,
# returns a token suitable for emailing to them to authenticate themselves.
def sign_person_id(secret_key, person_id):
    digest = hmac.new(secret_key.encode('ascii'), str(person_id).encode('ascii')).digest()
    signature_bytes = base64.urlsafe_b64encode(digest)
    signature = signature_bytes.decode("ascii").rstrip("=\n")
    return signature

# Low level mail sending
def mail(to_email, body):
    if debug_email:
        to_email = debug_email

    mailbox, at, host = to_email.partition("@")
    if not all((mailbox, at, host)):
        print("mail: not valid", to_email)
        return False

    if smtp_hostname is None:
        print("mail: smtp_hostname not set; not sending this email:")
        print("To: {}".format(to_email))
        print(body)
        return False

    try:
        with smtplib.SMTP_SSL(smtp_hostname) as smtp:
            if smtp_username != "":
                smtp.login(smtp_username, smtp_password)
            smtp.sendmail("cv@democracyclub.org.uk", [to_email], body)
    except Exception as e:
        print("mail: exception", e)
        print(traceback.format_exc())
        return False

    return True

# Specific confirmation

UPLOAD_CV_MESSAGE = textwrap.dedent("""\
    Hi {name},

    Your future constituents would like to read your Curriculum Vitae
    before deciding how to vote.

    Click the link below to share your CV with the world.

    {link}

    Thanks for your help!

    Democracy Club CV team
""")

def send_upload_cv_confirmation(app, person_id, to_email, to_name):
    signature = sign_person_id(app.secret_key, person_id)
    link = flask.url_for("upload_cv_confirmed", person_id=person_id, signature=signature, _external=True)
    print(to_name, "send_upload_cv_confirmation: ", link)

    return False

    body = UPLOAD_CV_MESSAGE.format(email=to_email, name=to_name, link=link)
    msg = email.mime.text.MIMEText(body)
    msg['Subject'] = "Upload your CV for becoming an MP"
    msg['From'] = email.utils.formataddr(("Democracy Club CVs", "cv@democracyclub.org.uk"))
    msg['To'] = email.utils.formataddr((to_name, to_email))

    return mail(msg, body)


