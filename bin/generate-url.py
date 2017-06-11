#!/usr/bin/env python

import base64
import os
import sys
import webbrowser

import hashlib
import hmac


'''
Usage:
python generate-url.py [candidate ID]
'''
person_id = sys.argv[1]
digest = hmac.new(os.environ['MPCV_SECRET_KEY'].encode('ascii'), str(person_id).encode('ascii'), hashlib.sha512).digest()
signature_bytes = base64.urlsafe_b64encode(digest)
signature = signature_bytes.decode("ascii").rstrip("=\n")

url = "http://cv.democracyclub.org.uk/upload_cv/{person_id}/c/{secret}".format(person_id=person_id, secret=signature[0:16])
webbrowser.open(url)
