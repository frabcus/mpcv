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

url = "https://yournextmp.com/media/candidates.csv"
stream = urllib.request.urlopen(url)
rows = csv.DictReader(codecs.iterdecode(stream, 'utf-8'))
writer = csv.DictWriter(sys.stdout, ['name', 'email', 'id', 'party', 'constituency', 'upload_url'])

for row in rows:
    out = collections.OrderedDict()
    out['name'] = row['name']
    out['email'] = row['email']
    out['id'] = row['id']
    out['party'] = row['party']
    out['constituency'] = row['constituency']

    link = identity.generate_upload_url(main.app.secret_key, row['id'])
    out['upload_url'] = link

    writer.writerow(out)



