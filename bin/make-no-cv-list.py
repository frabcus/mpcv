#!/usr/bin/env python3

import sys
import os
import csv
import codecs
import collections
import requests
import urllib.request

sys.path.append(os.getcwd())
import app
import identity
import lookups

app.app.config['SERVER_NAME'] = 'cv.democracyclub.org.uk'

with app.app.app_context():

    url = lookups.candidates_csv_url()
    stream = urllib.request.urlopen(url)
    rows = csv.DictReader(codecs.iterdecode(stream, 'utf-8'))
    rows = lookups.augment_if_has_cv(app.app.config, list(rows))

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
        out['party'] = row['party_name']
        out['constituency'] = row['post_label']

        link = identity.generate_upload_url(app.app.secret_key, row['id'])
        out['upload_url'] = link

        writer.writerow(out)



