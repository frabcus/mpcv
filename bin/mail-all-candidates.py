#!/usr/bin/env python3

import sys
import os
import collections

import flask_mail
import boto.s3.key

sys.path.append(os.getcwd())
import main
import identity
import lookups

main.app.config['SERVER_NAME'] = 'cv.democracyclub.org.uk'

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

            link = identity.generate_upload_url(main.app.secret_key, candidate['id'])

            body = '''Hi!

Hundreds of thousands of voters are looking at candidate
CVs on Who Can I Vote For!

To make sure they see your CV, follow this link
and upload it.

{link}

If you're having trouble, reply to this email with an
attachment!

Many thanks,

Francis
Volunteer, Democracy Club CVs
http://cv.democracyclub.org.uk/
'''.format(link=link, linkedin_url=candidate['linkedin_url'], name=candidate['name'])

            print("=========================\n" + body)

            #candidate['email'] = 'frabcus@fastmail.fm'

            msg = flask_mail.Message(body=body,
                    subject="Your voters would like to see your CV!",
                    sender=("Democracy Club CVs", "cv@democracyclub.org.uk"),
                    recipients=[
                        (candidate['name'], candidate['email'])
                    ]
                  )

            main.mail.send(msg)

