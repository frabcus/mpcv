#!/usr/bin/env python3

import os
import flask
import json

import lookups
import identity

app = flask.Flask(__name__)
app.secret_key = os.getenv('MPCV_SESSION_SECRET')


#####################################################################
# Global parameters, used in layout.html

@app.before_request
def set_globals(*args, **kwargs):
    flask.g.debug_email = identity.debug_email

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
        return flask.redirect("/candidates")

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

    return flask.redirect("/candidates")

@app.route('/clear_postcode')
def clear_postcode():
    del flask.session['postcode']
    del flask.session['constituency']

    return flask.redirect("/")


#####################################################################
# List of candidates

@app.route('/candidates')
def candidates():
    if 'postcode' not in flask.session:
        return flask.redirect("/")

    postcode = flask.session['postcode']
    constituency = flask.session['constituency']

    candidates = lookups.lookup_candidates(constituency['id'])
    if 'errors' in candidates:
        flask.flash("Error fetching list of candidates from YourNextMP.", 'danger')
        return flask.redirect(flask.url_for('error'))

    candidates_no_email = [ candidate for candidate in candidates if candidate['email'] is None]
    candidates = [ candidate for candidate in candidates if candidate['email'] is not None]

    return flask.render_template("candidates.html", constituency=constituency,
            candidates=candidates, candidates_no_email=candidates_no_email)


#####################################################################
# Uploading CVs

@app.route('/upload_cv/<int:person_id>', methods=['GET','POST'])
def upload_cv(person_id):
    candidate = lookups.lookup_candidate(person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return flask.redirect(flask.url_for('error'))

    if flask.request.method == 'POST':
        if identity.send_upload_cv_confirmation(app, candidate['id'], candidate['email'], candidate['name']):
            return flask.render_template("check_email.html")
        else:
            flask.flash("Failed to send email, please try again.", 'danger')

    return flask.render_template("upload_cv.html", candidate=candidate)


@app.route('/upload_cv/<int:person_id>/c/<signature>')
def upload_cv_confirmed(person_id, signature):
    data = lookups.lookup_candidate(person_id)
    if 'error' in data:
        flask.flash(data['error'], 'danger')
        return flask.redirect(flask.url_for('error'))

    signed_again = identity.sign_person_id(app.secret_key, person_id)
    if signature != signed_again:
        flask.flash("Sorry! That web link isn't right. Can you check you copied it properly from your email?", 'warning')
        return flask.redirect(flask.url_for('error'))

    return flask.render_template("upload_cv_confirmed.html", candidate=data)



#####################################################################
# Debugging entry point

if __name__ == '__main__':
    app.debug = True
    app.run()


