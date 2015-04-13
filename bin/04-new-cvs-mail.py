#!/usr/bin/env python3

dry_run = False

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
    #if subscriber['email'] != 'frabcus+skate@fastmail.fm':
    #    continue

    # Only mail to ones we haven't mailed recently
    back_to = datetime.datetime.now() - datetime.timedelta(days=1)
    if subscriber['last_modified'] > back_to:
        print("skipping too recent", subscriber['email'], subscriber['last_modified'], ">", back_to)
        continue

    # Subject: 100 CVs now in, let's get more!
    body = """"""

    #assert subscriber['no_cv_count'] > 0

#    body += "UPDATED: " + repr(subscriber['candidates_cv_updated'])

    if len(subscriber['candidates_cv_created']) > 0:
        body += """Ace! We've got some new CVs in {constituency_name}
for you.

""".format(constituency_name=subscriber['constituency']['name'])
    else:
        print("Skipping, no new CVs")
        continue

    for c in subscriber['candidates_cv_created']:
        body += "   " + c['name'] + ", " + c['party'] + "\n   http://cv.democracyclub.org.uk/show_cv/" + str(c['id']) + "\n\n"

    body += """Let's get the others to share theirs too!

Could you email or Tweet the other candidates
again?

http://cv.democracyclub.org.uk/candidates?postcode={postcode}

Tell them others have already shared their CV,
and ask them why they don't share theirs too!

You're a star.

""".format(
        constituency_name=subscriber['constituency']['name'],
        no__count=subscriber['no_cv_count']+subscriber['no_email_count'],
        iss=p.plural('is', subscriber['no_cv_count']+subscriber['no_email_count']),
        candidate=p.plural('candidate', subscriber['no_cv_count']+subscriber['no_email_count']),
        postcode=urllib.parse.quote(subscriber['postcode'])
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
            subject="More MP candidate CVs have arrived!",
            sender=("Democracy Club CVs", "cv@democracyclub.org.uk"),
            recipients=[subscriber['email']]
          )

    if not dry_run:
        with main.app.app_context():
            main.mail.send(msg)
            print("mail sent!")
            # Touch the timestamp so we don't mail them again until time passes
            lookups.updates_join(main.app.config, subscriber['email'], subscriber['postcode'])
            print("touched stamp!")
    else:
        print("Dry run aborted just before send")

    print("========================================")


