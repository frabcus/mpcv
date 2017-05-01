#!/usr/bin/env python3

import sys
import os
import urllib.parse
import textwrap
import datetime

import flask_mail
import inflect

sys.path.append(os.getcwd())
import main
import identity
import lookups

main.app.config['SERVER_NAME'] = 'cv.democracyclub.org.uk'

p = inflect.engine()

# Get list of all volunteers from S3
subscribers = lookups.slow_updates_list(main.app.config)

# Loop over them
for subscriber in subscribers:
    # Only mail to ones we haven't mailed recently
    back_to = datetime.datetime.now() - datetime.timedelta(days=3)
    if subscriber['last_modified'] > back_to:
        print("skipping too recent", subscriber['email'], subscriber['last_modified'], ">", back_to)
        continue

    # Subject: 100 CVs now in, let's get more!
    body = """Hi!

Yay, we've got 100 CVs of people standing for Parliament!

Well done, and thank you for helping make it happen.
"""

    assert subscriber['no_cv_count'] > 0

    # How many you have
    if subscriber['has_cv_count'] == 0:
        body += """
Alas, in your constituency, {constituency_name}, we've still
not got any CVs. There {iss} {no__count} {candidate}!
""".format(
            constituency_name=subscriber['constituency']['name'],
            no__count=subscriber['no_cv_count']+subscriber['no_email_count'],
            iss=p.plural('is', subscriber['no_cv_count']+subscriber['no_email_count']),
            candidate=p.plural('candidate', subscriber['no_cv_count']+subscriber['no_email_count'])
        )
    elif subscriber['has_cv_count'] > 0:
        body += """
In your constituency, {constituency_name}, we have
{has_cv_count} {cvs} so far. There {iss} still {no__count} {candidate} to go!
""".format(
            constituency_name=subscriber['constituency']['name'],
            has_cv_count=subscriber['has_cv_count'],
            cvs=p.plural('CV', subscriber['has_cv_count']),
            no__count=subscriber['no_cv_count']+subscriber['no_email_count'],
            iss=p.plural('is', subscriber['no_cv_count']+subscriber['no_email_count']),
            candidate=p.plural('candidate', subscriber['no_cv_count']+subscriber['no_email_count'])
        )

    if subscriber['no_cv_count'] == 1:
        body += """
Could you write to the candidate with no CV (again)?
"""
    else:
        body += """
Could you write to them (again)? We've recently updated
the site so you can do do it in one go. Super easy.
"""

    body += """
Follow this link and choose "Email them all!":

http://cv.democracyclub.org.uk/set_postcode?postcode={postcode}
""".format(
        postcode=urllib.parse.quote(subscriber['postcode'])
    )

    if subscriber['has_cv_count'] == 1:
        body += """
(That's also how you can look at the CV!)
"""
    elif subscriber['has_cv_count'] > 1:
        body += """
(That's also how you can look at the CVs)
"""

    # TODO: If there are any without email, add to mail to say get emails

    # PS you can look at all the CVs!
    body += """
I'll be writing again soon...

Francis Irving
Volunteer
Democracy Club

P.S. You can look at all the CVs nationally here
http://cv.democracyclub.org.uk/all_cvs/page/1

P.P.S. To unsubscribe, reply to this email and just ask.
"""

    # Print / send mail
    print("========================================")
    print("To:", subscriber['email'])
    print()
    print(body)
    print("----------------------------------------")

    msg = flask_mail.Message(body=body,
            subject="We've got 100 MP candidate CVs!",
            sender=("Democracy Club CV", "cv@democracyclub.org.uk"),
            recipients=[subscriber['email']]
          )

    print("DEBUG aborted just before send")
    sys.exit(1)

    with main.app.app_context():
        main.mail.send(msg)
        print("mail sent!")
        # Touch the timestamp so we don't mail them again until time passes
        lookups.updates_join(main.app.config, subscriber['email'], subscriber['postcode'])
        print("touched stamp!")

    print("========================================")


