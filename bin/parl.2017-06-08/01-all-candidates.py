#!/usr/bin/env python3

import sys
import os
import collections
import datetime

import flask_mail
import boto.s3.key

sys.path.append(os.getcwd())
import main
import identity
import lookups

main.app.config['SERVER_NAME'] = 'cv.democracyclub.org.uk'

# Get list of when last sent
last_sent_by_email = lookups.candidate_mail_last_sent(main.app.config)


with main.app.app_context():
    for constituency in lookups.all_constituencies(main.app.config):
        for candidate in constituency:
            if candidate['id'] in [5819]:
                print("unsubscribed", candidate)
                continue
            if candidate['has_cv']:
                continue
            if not candidate['email']:
                continue

            # Only mail to ones we haven't mailed recently
            if candidate['email'] in last_sent_by_email:
                back_to = datetime.datetime.now() - datetime.timedelta(days=14)
                last_sent = last_sent_by_email[candidate['email']]
                if last_sent > back_to:
                    print("skipping too recent", candidate['email'], last_sent, ">", back_to)
                    continue

            link = identity.generate_upload_url(main.app.secret_key, candidate['id'])

            body = '''Hi!

Great that you're standing for Parliament again!

At the last General Election, we found voters love to
learn more about you by seeing the career history on your
CV.

To share your CV with voters, follow this link.

{link}

If you're having trouble, reply to this email with an
attachment!

Many thanks,

Francis
Volunteer, Democracy Club CVs
http://cv.democracyclub.org.uk/
'''.format(link=link, linkedin_url=candidate['linkedin_url'], name=candidate['name'])

            print("sending to: " + candidate['email'])

            # For debugging:
            #print("\n" + body)
            #candidate['email'] = 'frabcus@fastmail.fm'

            msg = flask_mail.Message(body=body,
                    subject="Your voters would like to see your CV!",
                    sender=("Democracy Club CVs", "cv@democracyclub.org.uk"),
                    recipients=[
                        (candidate['name'], candidate['email'])
                    ]
                  )
            main.mail.send(msg)
            lookups.candidate_mail_sent(main.app.config, candidate['email'])

