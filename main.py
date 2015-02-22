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

# GET is to say "you need to confirm email"
# POST when they click the button to send the confirm email
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


# GET is to show form to upload CV
@app.route('/upload_cv/<int:person_id>/c/<signature>', methods=['GET'])
def upload_cv_confirmed(person_id, signature):
    candidate = lookups.lookup_candidate(person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return flask.redirect(flask.url_for('error'))

    signed_again = identity.sign_person_id(app.secret_key, person_id)
    if signature != signed_again:
        flask.flash("Sorry! That web link isn't right. Can you check you copied it properly from your email?", 'warning')
        return flask.redirect(flask.url_for('error'))

    upload_link = flask.url_for('upload_cv_upload', person_id=person_id, signature=signature)

    return flask.render_template("upload_cv_confirmed.html", candidate=candidate,
         upload_link=flask.request.path)

# POST is actual receiving of CV
@app.route('/upload_cv/<int:person_id>/c/<signature>', methods=['POST'])
def upload_cv_upload(person_id, signature):
    candidate = lookups.lookup_candidate(person_id)
    if 'error' in candidate:
        print("error in candidate", person_id)
        return json.dumps({ 'error': candidate['error']})

    signed_again = identity.sign_person_id(app.secret_key, person_id)
    if signature != signed_again:
        print("error in signature", person_id, signature)
        return json.dumps({ 'error': 'Signature token wrong'})

    f = flask.request.files['file']
    if not f:
        print("upload missing", person_id)
        return json.dumps({ 'error': 'Upload not received'})

    print("filename", f.filename)
    print("content_type", f.content_type)

    return "{ 'moo': 1 }"

#####################################################################
# Debugging entry point

if __name__ == '__main__':
    app.debug = True
    app.run()


