#!/usr/bin/env python3

dry_run = True

import sys
import os
import urllib.parse
import textwrap
import datetime

import flask_mail
import inflect

sys.path.append(os.getcwd())
import app
import identity
import lookups

app.app.config['SERVER_NAME'] = 'cv.democracyclub.org.uk'

p = inflect.engine()

# Get list of all volunteers from S3
subscribers = lookups.slow_updates_list(app.app.config)

# Loop over them
for subscriber in subscribers:
    # Only mail to ones we haven't mailed recently
    back_to = datetime.datetime.now() - datetime.timedelta(days=1)
    if subscriber['last_modified'] > back_to:
        print("skipping too recent", subscriber['email'], subscriber['last_modified'], ">", back_to)
        continue

    # Subject: 100 CVs now in, let's get more!
    body = """Hello!

"""
    assert subscriber['no_cv_count'] > 0

#    body += "UPDATED: " + repr(subscriber['candidates_cv_updated'])

    if len(subscriber['candidates_cv_created']) > 0:
        body += """Since we last emailed, these candidates have added their CV!
Well done, and thanks for helping persuade them.

"""
        for c in subscriber['candidates_cv_created']:
            body += "   " + c['name'] + ", " + c['party'] + "\n   http://cv.democracyclub.org.uk/show_cv/" + str(c['id']) + "\n\n"


    body += """We've still got {no__count} {candidate} in {constituency_name}
to get CVs from!

""".format(
        constituency_name=subscriber['constituency']['name'],
        no__count=subscriber['no_cv_count']+subscriber['no_email_count'],
        iss=p.plural('is', subscriber['no_cv_count']+subscriber['no_email_count']),
        candidate=p.plural('candidate', subscriber['no_cv_count']+subscriber['no_email_count'])
    )

    if subscriber['no_cv_count'] == 1:
        body += """Could you Tweet them? This link makes it easy.

"""
    else:
        body += """Could you Tweet them all? This link makes it easy.

"""

    body += """http://cv.democracyclub.org.uk/tweet_candidates?postcode={postcode}

We've found asking in public puts extra pressure on!

""".format(
        postcode=urllib.parse.quote(subscriber['postcode'])
    )

    # PS you can look at all the CVs!
    body += """Francis Irving
Volunteer
Democracy Club


To unsubscribe, reply to this email and just ask."""

    # Print / send mail
    print("========================================")
    print("To:", subscriber['email'])
    print()
    print(body)
    print("----------------------------------------")

    msg = flask_mail.Message(body=body,
            subject="Easily Tweet to ask MP candidates for their CVs!",
            sender=("Democracy Club CV", "cv@democracyclub.org.uk"),
            recipients=[subscriber['email']]
          )

    if not dry_run:
        with app.app.app_context():
            app.mail.send(msg)
            print("mail sent!")
            # Touch the timestamp so we don't mail them again until time passes
            lookups.updates_join(app.app.config, subscriber['email'], subscriber['postcode'])
            print("touched stamp!")
    else:
        print("Dry run aborted just before send")

    print("========================================")


