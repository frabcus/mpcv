import requests
import json

import constants

# Takes a postcode returns a dict of:
#   error - with a user friendly message, if the lookup failed
#   id - the mySociety identifier of the constituency
#   name - the text name of the constituency
def lookup_postcode(postcode):
    data = requests.get("http://mapit.mysociety.org/postcode/" + postcode).json()
    if "error" in data:
        return data
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

    data = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/search/persons?q=standing_in.%s.post_id:%s" %
            (constants.year, str_id)).json()
    print(json.dumps(data))
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
def lookup_candidate(candidate_id):
    str_id = str(int(candidate_id))
    data = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/search/persons?q=id:%s" % str_id).json()

    if data["total"] < 1:
        return { "error": "Candidate %s not found" % str_id }
    if data["total"] > 1:
        return { "error": "Candidate %s unexpectedly appears multiple times" % str_id }

    return data['result'][0]

