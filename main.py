#!/usr/bin/env python3

import os
import flask
import json

import lookups

app = flask.Flask(__name__)
app.secret_key = os.getenv('MPCV_SESSION_SECRET')


#####################################################################
# General utility routes

@app.route('/error')
def error():
    return flask.render_template('error.html')


#####################################################################
# Postcode entry

@app.route('/')
def index():
    if 'postcode' in flask.session:
        return flask.redirect("/applicants")

    return flask.render_template('index.html')

@app.route('/set_postcode')
def set_postcode():
    postcode = flask.request.args.get('postcode')
    constituency = lookups.lookup_postcode(postcode)

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


#####################################################################
# List of applicants

@app.route('/applicants')
def applicants():
    if 'postcode' not in flask.session:
        return flask.redirect("/")

    postcode = flask.session['postcode']
    constituency = flask.session['constituency']

    applicants = lookups.lookup_candidates(constituency['id'])
    if 'errors' in applicants:
        flask.flash("Error fetching list of candidates from YourNextMP.", 'danger')
        return flask.redirect(flask.url_for('error'))

    applicants_no_email = [ applicant for applicant in applicants if applicant['email'] is None]
    applicants = [ applicant for applicant in applicants if applicant['email'] is not None]

    return flask.render_template("applicants.html", constituency=constituency,
            applicants=applicants, applicants_no_email=applicants_no_email)


#####################################################################
# Uploading CVs

@app.route('/upload_cv/<int:person_id>')
def upload_cv(person_id):
    data = lookups.lookup_candidate(person_id)

    if 'error' in data:
        flask.flash(data['error'], 'danger')
        return flask.redirect(flask.url_for('error'))

    return flask.render_template("upload_cv.html", applicant=data)

#####################################################################
# Debugging entry point

if __name__ == '__main__':
    app.config['DEBUG'] = True
    app.run()



