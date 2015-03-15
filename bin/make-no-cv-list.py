#!/usr/bin/env python3

import sys
import os
import csv
import codecs
import collections
import requests
import urllib.request

sys.path.append(os.getcwd())
import main
import identity
import lookups

main.app.config['SERVER_NAME'] = 'cv.democracyclub.org.uk'

with main.app.app_context():

    url = "https://yournextmp.com/media/candidates.csv"
    stream = urllib.request.urlopen(url)
    rows = csv.DictReader(codecs.iterdecode(stream, 'utf-8'))
    rows = lookups.augment_if_has_cv(main.app.config, list(rows))

    fields = ['name', 'email', 'id', 'party', 'constituency', 'upload_url']
    writer = csv.DictWriter(sys.stdout, fields)
    writer.writeheader()

    for row in rows:
        if row['has_cv']:
            continue

        out = collections.OrderedDict()
        out['name'] = row['name']
        out['email'] = row['email']
        out['id'] = row['id']
        out['party'] = row['party']
        out['constituency'] = row['constituency']

        link = identity.generate_upload_url(main.app.secret_key, row['id'])
        out['upload_url'] = link

        writer.writerow(out)



