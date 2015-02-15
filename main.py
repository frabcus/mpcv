#!/usr/bin/env python

import os
import flask
import requests
import json

year = '2015'

app = flask.Flask(__name__)
app.secret_key = os.getenv('MPCV_SESSION_SECRET')

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
        if year in standing_in and standing_in[year] != None:
            if standing_in[year]['post_id'] == str_id:
                # TODO: remove this got_urls hack which is just there to
                # remove a duplicate Louise Ellman - have asked on Democracy Club list
                m = member['person_id']
                if m['url'] not in got_urls:
                    current_candidate_list.append({
                        'id': m['id'],
                        'name': m['name'],
                        'email': m['email'],
                        'party': m['party_memberships'][year]['name']
                    })
                    got_urls.add(m['url'])

    # Sort by surname (as best we can -- "Duncan Smith" won't work)
    # so it is same as on ballot paper. So can get used to it.
    def surname(candidate):
        return candidate['name'].split(" ")[-1]
    return sorted(current_candidate_list, key=surname)

@app.route('/error')
def error():
    return flask.render_template('error.html')


@app.route('/')
def index():
    if 'postcode' in flask.session:
        return flask.redirect("/applicants")

    return flask.render_template('index.html')

@app.route('/set_postcode')
def set_postcode():
    postcode = flask.request.args.get('postcode')
    constituency = lookup_postcode(postcode)

    if 'error' in constituency:
        flask.flash(constituency['error'], 'danger')
        return flask.redirect(flask.url_for('index'))

    flask.session['postcode'] = postcode
    flask.session['constituency'] = constituency

    return flask.redirect("/applicants")

@app.route('/clear_postcode')
def clear_postcode():
    del flask.session['postcode']
    del flask.session['constituency']

    return flask.redirect("/")


@app.route('/applicants')
def applicants():
    if 'postcode' not in flask.session:
        return flask.redirect("/")

    postcode = flask.session['postcode']
    constituency = flask.session['constituency']

    applicants = lookup_candidates(constituency['id'])
    if 'errors' in applicants:
        flask.flash("Error fetching list of candidates from YourNextMP.", 'danger')
        return flask.redirect(flask.url_for('error'))

    applicants_no_email = [ applicant for applicant in applicants if applicant['email'] is None]
    applicants = [ applicant for applicant in applicants if applicant['email'] is not None]

    return flask.render_template("applicants.html", constituency=constituency,
            applicants=applicants, applicants_no_email=applicants_no_email)


if __name__ == '__main__':
    app.config['DEBUG'] = True
    app.run()



