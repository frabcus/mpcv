import requests
import json

import constants

def lookup_postcode(postcode):
    data = requests.get("http://mapit.mysociety.org/postcode/" + postcode).json()
    if "error" in data:
        return data
    return data["areas"][str(data["shortcuts"]["WMC"])]

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

def lookup_candidate(candidate_id):
    str_id = str(int(candidate_id))
    data = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/search/persons?q=id:%s" % str_id).json()

    if data["total"] < 1:
        return { "error": "Candidate %s not found" % str_id }
    if data["total"] > 1:
        return { "error": "Candidate %s unexpectedly appears multiple times" % str_id }

    return data['result'][0]

