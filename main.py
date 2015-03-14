#!/usr/bin/env python3

import os
import traceback
import re

import werkzeug
import flask
import flask_appconfig.env
import flask_mail
import flask.ext.cache

import lookups
import identity

app = flask.Flask(__name__)
flask_appconfig.env.from_envvars(app.config, prefix='MPCV_')
mail = flask_mail.Mail(app)
cache = flask.ext.cache.Cache(app,config={'CACHE_TYPE': 'simple'})

#####################################################################
# Global parameters, used in layout.html

@app.before_request
def set_globals(*args, **kwargs):
    if "DEBUG_EMAIL" in app.config:
        flask.g.debug_email = app.config["DEBUG_EMAIL"]

#####################################################################
# General routes

def error():
    return flask.render_template('error.html'), 500

@app.route('/about')
def about():
    return flask.render_template('about.html')


#####################################################################
# Postcode entry

@cache.cached(600, key_prefix="recent_cvs")
def _cache_recent_cvs():
    return lookups.recent_cvs(app.config)

@app.route('/')
def index():
    if 'postcode' in flask.session:
        return flask.redirect("/candidates")

    recent_cvs = _cache_recent_cvs()

    return flask.render_template('index.html', recent_cvs=recent_cvs)

@app.route('/set_postcode')
def set_postcode():
    postcode = flask.request.args.get('postcode')
    constituency = lookups.lookup_postcode(postcode)

    if 'error' in constituency:
        flask.flash(constituency['error'], 'danger')
        return flask.redirect(flask.url_for('index'))

    flask.session['postcode'] = constituency['postcode']
    flask.session['constituency'] = constituency

    return flask.redirect("/candidates")

@app.route('/clear_postcode')
def clear_postcode():
    if 'postcode' in flask.session:
        del flask.session['postcode']
    if 'constituency' in flask.session:
        del flask.session['constituency']

    return flask.redirect("/")


#####################################################################
# List candidates and view their CVs

def split_candidates_by_type(all_candidates):
    all_candidates = lookups.augment_if_has_cv(app.config, all_candidates)

    candidates_no_email = [ candidate for candidate in all_candidates if candidate['email'] is None]
    candidates_have_cv = [ candidate for candidate in all_candidates if candidate['email'] is not None and candidate['has_cv']]
    candidates_no_cv = [ candidate for candidate in all_candidates if candidate['email'] is not None and not candidate['has_cv']]

    return candidates_no_cv, candidates_no_email, candidates_have_cv


@app.route('/candidates')
def candidates():
    if 'postcode' not in flask.session or 'constituency' not in flask.session:
        return flask.redirect("/")

    postcode = flask.session['postcode']
    constituency = flask.session['constituency']

    all_candidates = lookups.lookup_candidates(constituency['id'])
    if 'errors' in all_candidates:
        flask.flash("Error fetching list of candidates from YourNextMP.", 'danger')
        return error()
    (candidates_no_cv, candidates_no_email, candidates_have_cv) = split_candidates_by_type(all_candidates)

    from_email = ""
    if 'email' in flask.session:
        from_email = flask.session['email']
    email_got = False
    if from_email != "":
        email_got = lookups.updates_getting(app.config, from_email)

    return flask.render_template("candidates.html", constituency=constituency,
            candidates_no_cv=candidates_no_cv,
            candidates_have_cv=candidates_have_cv,
            candidates_no_email=candidates_no_email,
            from_email=from_email,
            email_got = email_got
    )


# GET is to show form to upload CV
@app.route('/show_cv/<int:person_id>')
def show_cv(person_id):
    candidate = lookups.lookup_candidate(person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    cvs = lookups.get_cv_list(app.config, person_id)
    if cvs == []:
        flask.flash("We don't yet have a CV for that candidate", 'danger')
        return flask.redirect('/candidates')

    current_cv = cvs[0]

    return flask.render_template("show_cv.html", candidate=candidate, cv=current_cv)


#####################################################################
# Uploading CVs

# GET is to say "you need to confirm email"
# POST when they click the button to send the confirm email
@app.route('/upload_cv/<int:person_id>', methods=['GET','POST'])
def upload_cv(person_id):
    candidate = lookups.lookup_candidate(person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    if flask.request.method == 'POST':
        identity.send_upload_cv_confirmation(app, mail, candidate['id'], candidate['email'], candidate['name'])
        return flask.render_template("check_email.html", candidate=candidate)

    return flask.render_template("upload_cv.html", candidate=candidate)


# GET is to show form to upload CV
@app.route('/upload_cv/<int:person_id>/c/<signature>', methods=['GET'])
def upload_cv_confirmed(person_id, signature):
    candidate = lookups.lookup_candidate(person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    signed_again = identity.sign_person_id(app.secret_key, person_id)
    if signature != signed_again:
        flask.flash("Sorry! That web link isn't right. Can you check you copied it properly from your email?", 'warning')
        return error()

    # this is their default email now
    flask.session['email'] = candidate['email']

    upload_link = flask.url_for('upload_cv_upload', person_id=person_id, signature=signature)

    return flask.render_template("upload_cv_confirmed.html", candidate=candidate,
         upload_link=upload_link)

# POST is actual receiving of CV
@app.route('/upload_cv/<int:person_id>/c/<signature>', methods=['POST'])
def upload_cv_upload(person_id, signature):
    candidate = lookups.lookup_candidate(person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    signed_again = identity.sign_person_id(app.secret_key, person_id)
    if signature != signed_again:
        flask.flash("Sorry! That web link isn't right. Can you check you copied it properly from your email?", 'warning')
        return error()

    f = flask.request.files['files']
    if not f:
        flask.flash("No files were received. Please try again, or contact us for help.", 'danger')
        return flask.redirect(flask.request.path)

    secure_filename = werkzeug.secure_filename(f.filename)
    data = f.read()
    size = len(data)

    print("saving CV to S3: candidate:", person_id, "uploaded file:", secure_filename, f.content_type, size, "bytes")
    file_url = lookups.add_cv(app.config, person_id, data, secure_filename, f.content_type)

    flask.flash("Thanks! Your CV has been successfully uploaded. You can share this page on social media. We'd love it if you tell any friends who are candidates to upload theirs too!", 'success')
    successful_link = flask.url_for('show_cv', person_id=person_id)
    return flask.redirect(successful_link)

#####################################################################

@app.route('/email_candidates', methods=['GET','POST'])
def email_candidate(person_id):
    if 'postcode' not in flask.session:
        flask.flash("Enter your postcode to email candidates", 'success')
        return flask.redirect("/")

    original_message = """Dear {0},




Yours sincerely,

""".format(candidate['name'])
    from_email = ""
    if 'email' in flask.session:
        from_email = flask.session['email']

    postcode = flask.session['postcode']
    message = original_message
    if flask.request.method == 'POST':
        from_email = flask.request.form.get("from_email", "")
        message = flask.request.form.get("message", "").replace("\r\n", "\n")
        if from_email == "" or not re.match("^.*?@.*?\..*?$", from_email):
            flask.flash("Please enter your email", 'danger')
        elif message.strip() == original_message.strip():
            flask.flash("Please enter a message", 'danger')
        else:
            # this is their default email now
            flask.session['email'] = from_email
            identity.send_email_candidate(app, mail,
                candidate['id'], candidate['email'], candidate['name'],
                from_email, postcode, message
            )
            flask.flash("Thanks! Your message has been sent to " + candidate['name'] + '.', 'success')
            return flask.redirect("/candidates")


    return flask.render_template("email_candidate.html",
        candidate=candidate,
        postcode=postcode,
        from_email=from_email,
        message=message
    )


#####################################################################
# List candidates and view their CVs


@app.route('/updates_join', methods=['POST'])
def updates_join():
    email = flask.request.form.get('email', "")
    if email == "" or not re.match("^.*?@.*?\..*?$", email) or "/" in email:
        flask.flash("Please enter your email to subscribe to updates", 'danger')
        return flask.redirect("/candidates")

    if 'postcode' not in flask.session:
        flask.flash("Enter your postcode before signing up for updates", 'success')
        return flask.redirect("/")

    postcode = flask.session['postcode']

    lookups.updates_join(app.config, email, postcode)
    flask.session['email'] = email
    flask.flash("Thanks for subscribing to updates! We'll get back to you. Meanwhile, please tell your friends about this on Twitter, Facebook and so on!", 'success')
    return flask.redirect("/candidates")


#####################################################################
# Main entry point
if __name__ == '__main__':
    app.debug = True
    app.run()

