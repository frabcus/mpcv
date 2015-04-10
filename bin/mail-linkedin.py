#!/usr/bin/env python3

import sys
import os
import collections

import flask_mail

sys.path.append(os.getcwd())
import main
import identity
import lookups

main.app.config['SERVER_NAME'] = 'cv.democracyclub.org.uk'

with main.app.app_context():
    for constituency in lookups.all_constituencies(main.app.config):
        for candidate in constituency:
            if candidate['has_cv']:
                continue
            if not candidate['linkedin_url']:
                continue
            if not candidate['email']:
                continue

            link = identity.generate_upload_url(main.app.secret_key, candidate['id'])

            body = '''Dear {name},

We're helping Parliamentary candidates share their CV
with voters.

To make it easy, you can give us permission to use your
LinkedIn page as your CV.

Just press "reply", and say "yes"!

You might first want to quickly check your LinkedIn page is up
to date, and has your full career and education history.

{linkedin_url}

Thanks!

Francis
Volunteer, Democracy Club CVs

P.S. If you want to upload something else as your CV, make
a Word or PDF document, and go here:
{link}
'''.format(link=link, linkedin_url=candidate['linkedin_url'], name=candidate['name'])

            print("=========================\n" + body)

            candidate['email'] = 'frabcus@fastmail.fm'

            msg = flask_mail.Message(body=body,
                    subject="Easily share your LinkedIn CV with your voters!",
                    sender=("Democracy Club CVs", "cv@democracyclub.org.uk"),
                    recipients=[
                        candidate['name'],
                        candidate['email']
                    ]
                  )

            with main.app.app_context():
                main.mail.send(msg)

            sys.exit(0)


