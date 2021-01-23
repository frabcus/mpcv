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
    body = """"""
    assert subscriber['no_cv_count'] > 0

#    body += "UPDATED: " + repr(subscriber['candidates_cv_updated'])

    if len(subscriber['candidates_cv_created']) > 0:
        body += """Congratulations! More CVs of future MPs have arrived where you
live. Thanks for helping get them.

"""
        for c in subscriber['candidates_cv_created']:
            body += "   " + c['name'] + ", " + c['party'] + "\n   http://cv.democracyclub.org.uk/show_cv/" + str(c['id']) + "\n\n"


    body += """Pressure.

We need it on the {no__count} {candidate} in {constituency_name}
who haven't sent in their CV yet. Pressure in all directions.

Do you read any blogs which cover politics?

If so, could you could write to them now and ask them to cover
Democracy Club CVs?

Here are some ideas on what to write:

https://gist.github.com/frabcus/53bd44dc5711d48203fe

Thanks for your help!

""".format(
        constituency_name=subscriber['constituency']['name'],
        no__count=subscriber['no_cv_count']+subscriber['no_email_count'],
        iss=p.plural('is', subscriber['no_cv_count']+subscriber['no_email_count']),
        candidate=p.plural('candidate', subscriber['no_cv_count']+subscriber['no_email_count'])
    )

    # PS you can look at all the CVs!
    body += """Francis Irving
Volunteer, Democracy Club CVs


To unsubscribe, reply to this email and just ask."""

    # Print / send mail
    print("========================================")
    print("To:", subscriber['email'])
    print()
    print(body)
    print("----------------------------------------")

    msg = flask_mail.Message(body=body,
            subject="Read any political blogs?",
            sender=("Democracy Club CVs", "cv@democracyclub.org.uk"),
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


