# Functions which get data from other APIs

# General policy: We don't return complete data structures,
# just the fields we're using. This is so having test ones
# is easier.

import requests
import json
import datetime

import constants

import boto.s3.connection
import boto.s3.key

# Takes a postcode returns a dict of:
#   error - with a user friendly message, if the lookup failed
#   id - the mySociety identifier of the constituency
#   name - the text name of the constituency
def lookup_postcode(postcode):
    data = requests.get("http://mapit.mysociety.org/postcode/" + postcode).json()
    if "error" in data:
        return data
    if data["postcode"] == "ZZ9 9ZZ":
        return { 'id': 8888888, 'name': "Democracy Club Test Constituency" }
    if "shortcuts" not in data:
        return { "error": "Postcode not properly recognised" }
    c = data["areas"][str(data["shortcuts"]["WMC"])]
    return { 'id': c['id'], 'name': c['name'] }

# Takes a constituency identifier and returns a dictionary:
#   errors - if there was an error
# Or an array of candidates in the current election:
#   id - the mySociety person_id of the candidate
#   name - name of the candidate
#   email - email address of the candidate (if known)
#   party - political party name of the candidate
def lookup_candidates(constituency_id):
    str_id = str(int(constituency_id))
    if str_id == '8888888':
        return [ { 'id': 7777777, 'name' : 'Sicnarf Gnivri', 'email': 'frabcus@fastmail.fm', 'party': 'Bunny Rabbits Rule' } ]

    data = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/search/persons?q=standing_in.%s.post_id:%s" %
            (constants.year, str_id)).json()
    if "errors" in data:
        return data

    current_candidate_list = []
    for member in data['result']:
        standing_in = member['standing_in']
        if constants.year in standing_in and standing_in[constants.year] != None:
            if standing_in[constants.year]['post_id'] == str_id:
                current_candidate_list.append({
                    'id': member['id'],
                    'name': member['name'],
                    'email': member['email'],
                    'party': member['party_memberships'][constants.year]['name']
                })

    # Sort by surname (as best we can -- "Duncan Smith" won't work)
    # so it is same as on ballot paper. So can get used to it.
    def surname(candidate):
        return candidate['name'].split(" ")[-1]
    return sorted(current_candidate_list, key=surname)

# Takes a candidate identifier (mySociety person_id) and returns a dictionary:
#   error - if there's an error
#   id - the mySociety person_id of the candidate
#   name - name of the candidate
#   email - email address of the candidate (if known)
#   party - political party name of the candidate
def lookup_candidate(person_id):
    str_id = str(int(person_id))
    if str_id == '7777777':
        return { 'id': 7777777, 'name' : 'Sicnarf Gnivri', 'email': 'frabcus@fastmail.fm', 'party': 'Bunny Rabbits Rule' }

    data = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/search/persons?q=id:%s" % str_id).json()

    if data["total"] < 1:
        return { "error": "Candidate %s not found" % str_id }
    if data["total"] > 1:
        return { "error": "Candidate %s unexpectedly appears multiple times" % str_id }

    c = data['result'][0]
    return { 'id': c['id'], 'name': c['name'], 'email': c['email'], 'party': c['party_memberships'][constants.year]['name'] }

conn = None
def _get_s3_bucket(config):
    global conn
    if not conn:
        conn = boto.s3.connection.S3Connection(
            config.get('S3_ACCESS_KEY_ID'),
            config.get('S3_SECRET_ACCESS_KEY')
        )

    bucket_name = config.get('S3_BUCKET_NAME')
    bucket = conn.get_bucket(bucket_name)
    return bucket

# Takes the app config (for S3 keys), candidate identifier, file contents, a
# (secured) filename and content type. Saves that new CV in S3. Raises
# an exception if it goes wrong, returns nothing.
def add_cv(config, person_id, contents, filename, content_type):
    person_id = str(int(person_id))
    assert person_id != 0

    bucket = _get_s3_bucket(config)

    when = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S-")

    key = boto.s3.key.Key(bucket)
    key.key = "cvs/" + str(person_id) + "/" + when + filename
    key.set_contents_from_string(contents)
    key.set_metadata('Content-Type', content_type)
    key.set_acl('public-read')

# Takes the app config (for S3) and candidate identifier. Returns
# a list, ordered by reverse time, of CVs for that candidate with
# the following fields:
#   url - publically accessible address of the file
#   date - when it was uploaded
#   content_type - the mime type of the file
def get_cv_list(config, person_id):
    bucket = _get_s3_bucket(config)

    prefix = "cvs/" + str(person_id) + "/"
    cvs = bucket.list(prefix)
    cvs = reversed(sorted(cvs, key=lambda k: k.last_modified))

    result = []
    for key in cvs:
        result.append({
            'name': key.name,
            'url': key.generate_url(expires_in=0, query_auth=False),
            'date': key.last_modified,
            'content_type': key.content_type,
        })
    return result


