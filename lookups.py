# Functions which get data from other APIs

# General policy: We don't return complete data structures,
# just the fields we're using. This is so having test ones
# is easier.

import requests
import json
import datetime
import itertools
import re

import constants

import boto.s3.connection
import boto.s3.key
import boto.utils

###################################################################
# General helpers

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


###################################################################
# Democracy APIs

# Takes a postcode returns a dict of:
#   error - with a user friendly message, if the lookup failed
#   id - the mySociety identifier of the constituency
#   name - the text name of the constituency
def lookup_postcode(postcode):
    try:
        data = requests.get("http://mapit.mysociety.org/postcode/" + postcode).json()
    except ValueError:
        return { "error": "Postcode is not valid." }
    if "error" in data:
        return data
    if data["postcode"] == "ZZ9 9ZZ":
        return { 'id': 8888888, 'name': "Democracy Club Test Constituency", 'postcode': 'ZZ9 9ZZ' }
    if "shortcuts" not in data:
        return { "error": "Postcode not properly recognised" }
    c = data["areas"][str(data["shortcuts"]["WMC"])]
    return { 'id': c['id'], 'name': c['name'], 'postcode': data['postcode'] }

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
        return [
            { 'id': 7777777, 'name' : 'Sicnarf Gnivri', 'email': 'frabcus@fastmail.fm', 'twitter': 'frabcus', 'party': 'Bunny Rabbits Rule' },
            { 'id': 7777778, 'name' : 'Notlits Esuom', 'email': 'frabcus@fastmail.fm', 'twitter': 'frabcus', 'party': 'Mice Rule More' },
            { 'id': 7777779, 'name' : 'Ojom Yeknom', 'email': 'frabcus@fastmail.fm', 'party': 'Monkeys Are Best' }
        ]

    data = requests.get("https://yournextmp.popit.mysociety.org/api/v0.1/posts/{}?embed=membership.person".format(str_id)).json()
    if "errors" in data:
        return data

    current_candidate_list = []
    for office in data['result']['memberships']:
        if office['start_date'] > constants.election_date or office['end_date'] < constants.election_date:
            continue
        assert office['role'] == 'Candidate'

        member = office['person_id']
        if constants.year not in member["standing_in"]:
            continue
        if member["standing_in"][constants.year] == None:
            continue

        twitter = None
        if 'contact_details' in member:
            for contact_detail in member['contact_details']:
                if contact_detail['type'] == 'twitter':
                    twitter = contact_detail['value']
                    break

        current_candidate_list.append({
            'id': member['id'],
            'name': member['name'],
            'email': member['email'],
            'twitter': twitter,
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
        return {
            'id': 7777777, 'name' : 'Sicnarf Gnivri', 'email': 'frabcus@fastmail.fm', 'party': 'Bunny Rabbits Rule',
            'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
        }
    if str_id == '7777778':
        return {
            'id': 7777778, 'name' : 'Notlits Esuom', 'email': 'frabcus@fastmail.fm', 'party': 'Mice Rule More',
            'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
        }
    if str_id == '7777779':
        return {
            'id': 7777779, 'name' : 'Ojom Yeknom', 'email': 'frabcus@fastmail.fm', 'party': 'Monkeys Are Best',
            'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
        }


    url = "https://yournextmp.popit.mysociety.org/api/v0.1/persons/{}".format(str_id)
    data = requests.get(url).json()

    if "errors" in data:
        return { "error": "Candidate {} not found".format(str_id) }

    c = data['result']

    constituency_id = None
    constituency_name = None
    standing_in = c['standing_in']
    if constants.year in standing_in and standing_in[constants.year] != None:
        constituency_id = standing_in[constants.year]['post_id']
        constituency_name = standing_in[constants.year]['name']

    return {
        'id': c['id'], 'name': c['name'], 'email': c['email'], 'party': c['party_memberships'][constants.year]['name'],
        'constituency_id': constituency_id, 'constituency_name': constituency_name
    }


###################################################################
# Storing CVs

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

def add_thumb(config, person_id, filename):
    person_id = str(int(person_id))
    assert person_id != 0

    bucket = _get_s3_bucket(config)

    key = boto.s3.key.Key(bucket)
    key.key = "thumbs/{0}.png".format(str(person_id))
    key.set_contents_from_filename(filename)
    key.set_metadata('Content-Type', "image/png")
    key.set_acl('public-read')

# Takes the app config (for S3) and candidate identifier. Returns
# a list, ordered by reverse time, of CVs for that candidate with
# the following fields:
#   name - full name of S3 key
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
            'last_modified': boto.utils.parse_ts(key.last_modified),
            'content_type': key.content_type,
            'person_id': person_id
        })
    return result

# Takes an array of candidates of the same form list_candidates returns.
# Auguments with a variable to say if they have a CV, and when last updated.
def augment_if_has_cv(config, candidates):
    bucket = _get_s3_bucket(config)

    people_with_cvs = bucket.list("cvs/", "/")
    thumbs = {str(x['person_id']): x for x in all_thumbnails(config)}

    has_cv = {}
    for key in people_with_cvs:
        person_id = str(key.name.replace("cvs/", "").replace("/", ""))
        has_cv[person_id] = 1

    for candidate in candidates:
        cvs = get_cv_list(config, candidate['id'])

        if len(cvs) > 0:
            candidate['has_cv'] = True
            candidate['cv'] = cvs[0]
            candidate['cv_created'] = min(cv['last_modified'] for cv in cvs)
            candidate['cv_updated'] = max(cv['last_modified'] for cv in cvs)

            if str(candidate['id']) in thumbs:
                candidate['cv']['has_thumb'] = True
                candidate['cv']['thumb'] = thumbs[candidate['id']]
            else:
                candidate['cv']['has_thumb'] = False
        else:
            candidate['has_cv'] = False

    return candidates


def all_thumbnails(config):
    return all_by_prefix(config, "thumbs/")

# Takes the app config (for S3), returns a list, ordered by reverse time,
# of all CVs from any candidate, with the following fields:
#   name - full name of S3 key
#   url - publically accessible address of the file
#   date - when it was uploaded
#   content_type - the mime type of the file
#   person_id - id of the person the CV is for
def all_cvs(config):
    thumbs = {x['person_id']: x for x in all_thumbnails(config)}
    cvs = all_by_prefix(config, "cvs/")
    for x in cvs:
        if x['person_id'] in thumbs:
            x['has_thumb'] = True
            x['thumb'] = thumbs[x['person_id']]
        else:
            x['has_thumb'] = False
    return cvs

def all_by_prefix(config, prefix):
    bucket = _get_s3_bucket(config)

    cvs = bucket.list(prefix)
    cvs = reversed(sorted(cvs, key=lambda k: k.last_modified))

    person_ids = []
    result = []
    for key in cvs:
        person_id = int(re.match(prefix + "([0-9]+)[^0-9]", key.name).group(1))
        if person_id == 7777777:
            continue
        if person_id in person_ids:
            continue
        result.append({
            'name': key.name,
            'url': key.generate_url(expires_in=0, query_auth=False),
            'last_modified': boto.utils.parse_ts(key.last_modified),
            'content_type': key.content_type,
            'person_id': person_id
        })
        person_ids.append(person_id)

    return result


###################################################################
# Combinations of things

def split_candidates_by_type(config, all_candidates):
    candidates_no_email = [ candidate for candidate in all_candidates if candidate['email'] is None]
    candidates_have_cv = [ candidate for candidate in all_candidates if candidate['email'] is not None and candidate['has_cv']]
    candidates_no_cv = [ candidate for candidate in all_candidates if candidate['email'] is not None and not candidate['has_cv']]

    return candidates_no_cv, candidates_no_email, candidates_have_cv

def split_candidates_by_updates(config, all_candidates, since):
    candidates_cv_created = [ candidate for candidate in all_candidates if 'cv_created' in candidate and candidate['cv_created'] >= since ]
    candidates_cv_updated = [ candidate for candidate in all_candidates if 'cv_updated' in candidate and candidate['cv_updated'] >= since and candidate['cv_created'] < since]

    return candidates_cv_created, candidates_cv_updated


###################################################################
# Signup to mailings

def updates_join(config, email, postcode):
    email = email.lower().replace("/", "_")
    bucket = _get_s3_bucket(config)

    key = boto.s3.key.Key(bucket)
    key.key = "updates/" + str(email)
    key.set_contents_from_string(postcode)

    url = key.generate_url(expires_in=0, query_auth=False)

def updates_getting(config, email):
    email = email.lower().replace("/", "_")
    bucket = _get_s3_bucket(config)

    prefix = "updates/" + str(email)
    results = bucket.list(prefix)

    for result in results:
        if result.name == "updates/" + str(email):
            return True

    return False

def updates_list(config):
    bucket = _get_s3_bucket(config)

    prefix = "updates/"
    results = bucket.list(prefix)
    results = sorted(results, key=lambda k: k.last_modified)

    for key in results:
        email = re.match("updates/(.*)", key.name).group(1)
        postcode = key.get_contents_as_string().strip().decode('ascii')
        constituency = lookup_postcode(postcode)
        if 'error' in constituency:
            print("ERROR looking up postcode", postcode)
            continue
        last_modified = boto.utils.parse_ts(key.last_modified)

        candidates = lookup_candidates(constituency['id'])
        if 'errors' in candidates:
            print("ERROR looking up candidates", postcode)
            continue

        candidates = augment_if_has_cv(config, candidates)
        candidates_no_cv, candidates_no_email, candidates_have_cv = split_candidates_by_type(config, candidates)
        candidates_cv_created, candidates_cv_updated = split_candidates_by_updates(config, candidates, last_modified)

        subscriber = {
            'email': email,
            'postcode': postcode,
            'constituency': constituency,

            'candidates': candidates,

            'has_cv_count': len(candidates_have_cv),
            'no_cv_count': len(candidates_no_cv),
            'no_email_count': len(candidates_no_email),

            'candidates_cv_created': candidates_cv_created,
            'candidates_cv_updated': candidates_cv_updated,
            'last_modified': last_modified
        }


        yield subscriber

