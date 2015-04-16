# Functions which get data from other APIs

# General policy: We don't return complete data structures,
# just the fields we're using. This is so having test ones
# is easier.

import requests
import json
import datetime
import re
import collections
import csv
import io

import constants
import main

import boto.s3.connection
import boto.s3.key
import boto.utils

import flask.ext.cache


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


# Returns a pair of hashes of data from YourNextMP.
#   by_candidate_id - maps from person id to dictionary about candidate
#   by_constituency_id - maps from constituency id to array of dictionaries about candidate
#
# The fields in the dictionaries about each candidate are:
#   id - the mySociety person_id of the candidate
#   name - name of the candidate
#   email - email address of the candidate (if known)
#   twitter - Twitter account name of the candidate (if known)
#   linkedin_url - LinkedIn page of the candidate (if known)
#   party - political party name of the candidate
#   constituency_id - identifier of constituency
#   constituency_name - name of constituency
@main.cache.memoize(60 * 60)
def _hashes_of_candidates(config):
    print("warming cache _hashes_of_candidates")

    by_candidate_id = {}
    by_constituency_id = collections.defaultdict(list)

    rows = _fetch_candidates(config)
    for row in rows:
        candidate_id = int(row['id'])
        constituency_id = int(row['mapit_id'])

        if row['email'] == '':
            row['email'] = None
        if row['twitter_username'] == '':
            row['twitter_username'] = None

        candidate = {
            'id': candidate_id,
            'name': row['name'],
            'email': row['email'],
            'twitter': row['twitter_username'],
            'linkedin_url': row['linkedin_url'],
            'party': row['party'],
            'constituency_id': constituency_id,
            'constituency_name': row['constituency']
        }

        # XXX reenable this when 546 candidate duplicate fixed
        # assert candidate_id not in by_candidate_id, candidate_id
        by_candidate_id[candidate_id] = candidate

        by_constituency_id[constituency_id].append(candidate)

    return by_candidate_id, by_constituency_id

def _fetch_candidates(config):
    bucket = _get_s3_bucket(config)
    key_name = "cache/candidates.csv"

    url = "https://yournextmp.com/media/candidates.csv"
    r = requests.get(url)

    if r.status_code == 200:
        r.encoding = 'utf-8'
        text = r.text
        # save to bucket
        key = boto.s3.key.Key(bucket)
        key.key = key_name
        key.set_contents_from_string(text)
    else:
        print("couldn't read from YourNextMP; loading candidates from S3")
        key = bucket.get_key(key_name)
        text = key.get_contents_as_string().decode('utf-8')

    return csv.DictReader(io.StringIO(text))

# Takes a constituency identifier and returns a dictionary:
#   error - if there was an error
# Or an array of dictionaries with fields as in _hashes_of_candidates.
def lookup_candidates(config, constituency_id):
    if constituency_id == 8888888:
        return [
            { 'id': 7777777, 'name' : 'Sicnarf Gnivri', 'email': 'frabcus+sicnarf@fastmail.fm', 'twitter': 'frabcus+sicnarf', 'linkedin_url': 'https://www.linkedin.com/in/FrancisIrving', 'party': 'Bunny Rabbits Rule',
                'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
            },
            { 'id': 7777778, 'name' : 'Notlits Esuom', 'email': 'frabcus+notlits@fastmail.fm', 'twitter': 'frabcus+notlits', 'linkedin_url': 'https://www.linkedin.com/in/FrancisIrving', 'party': 'Mice Rule More',
                'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
            },
            { 'id': 7777779, 'name' : 'Ojom Yeknom', 'email': 'frabcus+ojom@fastmail.fm', 'twitter': None, 'linkedin_url': None, 'party': 'Monkeys Are Best',
                'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
            }
        ]

    _, by_constituency_id = _hashes_of_candidates(config)

    if constituency_id not in by_constituency_id:
        return { 'error': "Constituency {} not found".format(constituency_id)}

    current_candidate_list = by_constituency_id[constituency_id]

    # Sort by surname (as best we can -- "Duncan Smith" won't work)
    # so it is same as on ballot paper. So can get used to it.
    def surname(candidate):
        return candidate['name'].split(" ")[-1]
    return sorted(current_candidate_list, key=surname)

# Takes a candidate identifier (mySociety person_id) and returns a dictionary:
#   error - if there's an error
# Or fields as in _hashes_of_candidates.
def lookup_candidate(config, person_id):
    if person_id == 7777777:
        return {
            'id': 7777777, 'name' : 'Sicnarf Gnivri', 'email': 'frabcus+sicnarf@fastmail.fm', 'twitter': 'frabcus+sicnarf', 'linkedin_url': 'https://www.linkedin.com/in/FrancisIrving', 'party': 'Bunny Rabbits Rule',
            'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
        }
    if person_id == 7777778:
        return {
            'id': 7777778, 'name' : 'Notlits Esuom', 'email': 'frabcus+notlits@fastmail.fm', 'twitter': 'frabcus+notlits', 'linkedin_url': 'https://www.linkedin.com/in/FrancisIrving', 'party': 'Mice Rule More',
            'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
        }
    if person_id == 7777779:
        return {
            'id': 7777779, 'name' : 'Ojom Yeknom', 'email': 'frabcus+ojom@fastmail.fm', 'twitter': None, 'linkedin_url': None, 'party': 'Monkeys Are Best',
            'constituency_id': 8888888, 'constituency_name': "Democracy Club Test Constituency"
        }

    by_candidate_id, _ = _hashes_of_candidates(config)

    if person_id not in by_candidate_id:
        return { 'error': "Candidate {} not found".format(person_id) }

    candidate = by_candidate_id[person_id]

    return candidate


# Returns an array of every constituency alphabetically by name.
# Each constituency is an array of candidates, with fields
# from _hashes_of_candidates and from augment_if_has_cv.
def all_constituencies(config):

    _, by_constituency_id = _hashes_of_candidates(config)

    result = []
    for constituency_id, candidates in by_constituency_id.items():
        candidates = augment_if_has_cv(config, candidates)
        result.append(candidates)

    result = sorted(result, key=lambda x: x[0]['constituency_name'])

    return result

###################################################################
# Storing CVs


# Takes the app config (for S3 keys), candidate identifier, file contents, a
# (secured) filename and content type. Saves that new CV in S3. Raises
# an exception if it goes wrong, returns nothing.
def add_cv(config, person_id, contents, filename):
    person_id = str(int(person_id))
    assert person_id != 0

    bucket = _get_s3_bucket(config)

    when = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S-")

    key = boto.s3.key.Key(bucket)
    key.key = "cvs/" + str(person_id) + "/" + when + filename
    key.set_contents_from_string(contents)
    key.set_acl('public-read')


# Takes the app config (for S3 keys), candidate identifier, a local filename, a
# filename in the bucket and the extension to use in mime type. Saves thumbnail
# in S3. Raises an exception if it goes wrong, returns nothing.
def add_thumb(config, local_filename, remote_filename, extension):
    bucket = _get_s3_bucket(config)

    key = boto.s3.key.Key(bucket)
    key.key = remote_filename
    key.set_contents_from_filename(local_filename)
    key.set_metadata('Content-Type', "image/" + extension)
    key.set_acl('public-read')


# Takes a candidate id, and returns most recent CV. Fields of CV
# are as in _hash_by_prefix.
def get_current_cv(config, person_id):
    cv_hash = _hash_by_prefix(config, "cvs/")

    if person_id not in cv_hash:
        return None

    return cv_hash[person_id]

# Takes a candidate id, and returns a thumbnail. Fields of thumbnail
# are as in _hash_by_prefix.
def get_current_thumb(config, person_id):
    thumb_hash = _hash_by_prefix(config, "thumbs/")

    if person_id not in thumb_hash:
        return None

    return thumb_hash[person_id]

# Takes an array of candidates of the same form list_candidates returns.
# Auguments with a variable to say if they have a CV, and when last updated.
def augment_if_has_cv(config, candidates):
    cv_hash = _hash_by_prefix(config, "cvs/")
    thumb_hash = _hash_by_prefix(config, "thumbs/")

    for candidate in candidates:

        if candidate['id'] in cv_hash:

            candidate['has_cv'] = True
            candidate['cv'] = cv_hash[candidate['id']]

            if candidate['id'] in thumb_hash:
                candidate['cv']['has_thumb'] = True
                candidate['cv']['thumb'] = thumb_hash[candidate['id']]
            else:
                candidate['cv']['has_thumb'] = False
        else:
            candidate['has_cv'] = False

    return candidates


# Takes the app config (for S3), returns a list, ordered by reverse time,
# of all CVs which have thumbnails from any candidate, with the following
# fields:
#   all the fields of _hash_by_prefix
#   has_thumb - True
#   thumb - dictionary of details, including all the fields of _hash_by_prefix
def all_cvs_with_thumbnails(config):
    cv_hash = _hash_by_prefix(config, "cvs/")
    thumb_hash = _hash_by_prefix(config, "thumbs/")

    cvs = []
    for person_id, cv in cv_hash.items():
        # strip out the test one
        if person_id == 7777777:
            continue
        if cv['person_id'] in thumb_hash:
            cv['has_thumb'] = True
            cv['thumb'] = thumb_hash[person_id]
            cv['candidate'] = lookup_candidate(config, cv['person_id'])
            # can have CVs for people who aren't candidates (e.g. withdrew)
            if 'error' not in cv['candidate']:
                cvs.append(cv)

    return cvs

# Takes the app config (for S3), returns a list, ordered by reverse time,
# of all CVs from any candidate which don't have an up to date thumbnails, with
# the following fields:
#   all the fields of _hash_by_prefix
#   has_thumb - False
def all_cvs_bad_thumbnails(config):
    cv_hash = _hash_by_prefix(config, "cvs/")
    thumb_hash = _hash_by_prefix(config, "thumbs/")

    cvs = []
    for person_id, cv in cv_hash.items():
        # strip out the test one
        if person_id == 7777777:
            continue
        # no thumb at all
        if person_id not in thumb_hash:
            cv['has_thumb'] = False
            cvs.append(cv)
            continue
        # latest thumb doesn't match name of CV file using
        cv_name = cv['name']
        thumb_name = thumb_hash[person_id]['name']
        if cv_name.replace("cvs/", "thumbs/") + ".jpg" != thumb_name:
            cv['has_thumb'] = False
            cvs.append(cv)
            continue

    return cvs


# Given a prefix, returns a hash from integer person_id to
# a dictionary with the following fields:
#   name - full name of S3 key
#   url - publically accessible address of the file
#   last_modified - when it was uploaded
#   person_id - id of the person the CV is for
# Caches for 10 minutes for speed.
@main.cache.memoize(60 * 10)
def _hash_by_prefix(config, prefix):
    print("warming cache _hash_by_prefix", prefix)

    bucket = _get_s3_bucket(config)

    cvs = bucket.list(prefix)
    cvs = reversed(sorted(cvs, key=lambda k: k.last_modified))

    person_ids = []
    result = collections.OrderedDict()
    for key in cvs:
        # we use .jpg thumbnails now (and don't accept images as CVs)
        if key.name.endswith(".png"):
            continue

        key_last_modified = boto.utils.parse_ts(key.last_modified)
        person_id = int(re.match(prefix + "([0-9]+)[^0-9]", key.name).group(1))
        if person_id not in result:
            result[person_id] =  {
                'name': key.name,
                'url': key.generate_url(expires_in=0, query_auth=False),
                'last_modified': key_last_modified,
                'created': key_last_modified,
                'person_id': person_id
            }
        result[person_id]['created'] = key_last_modified

    return result


###################################################################
# Combinations of things

def split_candidates_by_type(config, all_candidates):
    candidates_no_email = [ candidate for candidate in all_candidates if candidate['email'] is None]
    candidates_have_cv = [ candidate for candidate in all_candidates if candidate['email'] is not None and candidate['has_cv']]
    # sort chronologically by time CV was first uploaded
    candidates_have_cv.sort(key=lambda x: x['cv']['created'])
    candidates_no_cv = [ candidate for candidate in all_candidates if candidate['email'] is not None and not candidate['has_cv']]

    return candidates_no_cv, candidates_no_email, candidates_have_cv

def split_candidates_by_updates(config, all_candidates, since):
    candidates_cv_created = [ candidate for candidate in all_candidates if candidate['has_cv'] and candidate['cv']['created'] >= since ]
    candidates_cv_updated = [ candidate for candidate in all_candidates if candidate['has_cv'] and candidate['cv']['last_modified'] >= since and candidate['cv']['last_modified'] < since]

    # sort chronologically by time CV was first uploaded
    candidates_cv_created.sort(key=lambda x: x['cv']['created'])
    candidates_cv_updated.sort(key=lambda x: x['cv']['created'])

    return candidates_cv_created, candidates_cv_updated


###################################################################
# Volunteer mailing list

# Subscribe to updates - we store the postcode in a file names
# after the email address.
def updates_join(config, email, postcode):
    email = email.lower().replace("/", "_")
    bucket = _get_s3_bucket(config)

    key = boto.s3.key.Key(bucket)
    key.key = "updates/" + str(email)
    key.set_contents_from_string(postcode)

    url = key.generate_url(expires_in=0, query_auth=False)

# Is the email already getting updates?
def updates_getting(config, email):
    email = email.lower().replace("/", "_")
    bucket = _get_s3_bucket(config)

    prefix = "updates/" + str(email)
    results = bucket.list(prefix)

    for result in results:
        if result.name == "updates/" + str(email):
            return True

    return False

# Used for sending the mailings out, slow. Last modified of
# the subscription S3 file is the last sent to date.
def slow_updates_list(config):
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

        candidates = lookup_candidates(config, constituency['id'])
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

