import requests

import constants

def lookup_postcode(postcode):
    data = requests.get("http://mapit.mysociety.org/postcode/" + postcode).json()
    if "error" in data:
        return data
    return data["areas"][str(data["shortcuts"]["WMC"])]

def lookup_candidates(constituency_id):
    str_id = str(int(constituency_id))

    data = requests.get("http://yournextmp.popit.mysociety.org/api/v0.1/posts/%s?embed=membership.person" % str_id).json()
    if "errors" in data:
        return data

    current_candidate_list = []
    got_urls = set()
    for member in data['result']['memberships']:
        standing_in = member['person_id']['standing_in']
        if constants.year in standing_in and standing_in[constants.year] != None:
            if standing_in[constants.year]['post_id'] == str_id:
                # TODO: remove this got_urls hack which is just there to
                # remove a duplicate Louise Ellman - have asked on Democracy Club list
                m = member['person_id']
                if m['url'] not in got_urls:
                    current_candidate_list.append({
                        'id': m['id'],
                        'name': m['name'],
                        'email': m['email'],
                        'party': m['party_memberships'][constants.year]['name']
                    })
                    got_urls.add(m['url'])

    # Sort by surname (as best we can -- "Duncan Smith" won't work)
    # so it is same as on ballot paper. So can get used to it.
    def surname(candidate):
        return candidate['name'].split(" ")[-1]
    return sorted(current_candidate_list, key=surname)


