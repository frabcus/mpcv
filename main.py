#!/usr/bin/env python3

import os
import traceback
import re
import math
import logging

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

# Log to stderr for Heroku
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)

PAGE_SIZE = 12

#####################################################################
# Sitemap

def sitemap_generator():
    yield 'index', {}
    yield 'about', {}

    all_cvs = _cache_all_cvs()
    max_page = math.ceil(len(all_cvs) / PAGE_SIZE)
    for page in range(1, max_page + 1):
        yield 'all_cvs', { 'page': page }

    for cv in all_cvs:
        yield 'show_cv', { 'person_id': cv['person_id'] }

@app.route('/sitemap.xml')
def sitemap_xml():
    urlset = []
    for name, params in sitemap_generator():
        url = {}
        url['loc'] = flask.url_for(name, _external=True, **params)
        urlset.append(url)

    sitemap_xml = flask.render_template('sitemap.xml', urlset=urlset)
    response = flask.make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"

    return response

#####################################################################
# Global parameters and checks

@app.before_request
def set_globals(*args, **kwargs):
    if "DEBUG_EMAIL" in app.config:
        flask.g.debug_email = app.config["DEBUG_EMAIL"]
    if 'constituency' in flask.session:
        flask.g.constituency = flask.session['constituency']

@app.before_request
def check_ie():
    ua = flask.request.user_agent

    if "/static/" not in flask.request.path:
        if ua.browser == "msie" and float(ua.version) < 9.0:
            flask.flash("This site doesn't work on Internet Explorer versions 8 and earlier. Please use a more recent browser.", 'danger')

# You can force postcode setting on any page
@app.before_request
def look_for_postcode():
    if 'postcode' not in flask.request.args:
        return

    postcode = flask.request.args.get('postcode').strip()
    constituency = lookups.lookup_postcode(postcode)

    if 'error' in constituency:
        if re.search(r"^[A-Z][A-Z]?[0-9][0-9]?[A-Z]?$", postcode, re.IGNORECASE):
            flask.flash("Please use your complete postcode, e.g. NE1 4ST. Partial ones aren't accurate enough to work out your constituency.", 'danger')
        else:
            flask.flash(constituency['error'], 'danger')
        return flask.redirect(flask.url_for('index'))

    flask.session['postcode'] = constituency['postcode']
    flask.session['constituency'] = constituency



#####################################################################
# General routes

def error():
    return flask.render_template('error.html'), 500

@app.route('/about')
def about():
    return flask.render_template('about.html')

@app.route('/exception')
def exception():
    raise Exception("This is a test error")


#####################################################################
# Postcode entry

@cache.cached(600, key_prefix="all_cvs")
def _cache_all_cvs():
    return lookups.all_cvs(app.config)

@app.route('/')
def index():
    recent_cvs = _cache_all_cvs()[0:4]
    return flask.render_template('index.html', recent_cvs=recent_cvs)

@app.route('/all_cvs/page/<int:page>')
def all_cvs(page):
    all_cvs = _cache_all_cvs()
    page_cvs = all_cvs[(page-1)*PAGE_SIZE : (page-1)*PAGE_SIZE+PAGE_SIZE]

    max_page = math.ceil(len(all_cvs) / PAGE_SIZE)

    start = page - 5
    end = page + 5
    if start < 1:
        end += (1 - start)
        start += (1 - start)
    if end > max_page:
        start -= (end - max_page)
        end -= (end - max_page)
    if start < 1:
        start = 1

    return flask.render_template('all_cvs.html',
            page = page,
            page_cvs = page_cvs,
            max_page = max_page,
            numbers = range(start, end + 1)
    )

# The lookup_postcode before request does the actual setting
@app.route('/set_postcode')
def set_postcode():
    return flask.redirect("/candidates")

#####################################################################
# Clear data

@app.route('/clear_all')
def clear_all():
    # clear postcode
    if 'postcode' in flask.session:
        del flask.session['postcode']
    # clear constituency
    if 'constituency' in flask.session:
        del flask.session['constituency']
    # clear email
    if 'email' in flask.session:
        del flask.session['email']

    return flask.redirect("/")

#####################################################################
# List candidates and view their CVs

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
    all_candidates = lookups.augment_if_has_cv(app.config, all_candidates)
    (candidates_no_cv, candidates_no_email, candidates_have_cv) = lookups.split_candidates_by_type(app.config, all_candidates)

    show_twitter_button = False
    for candidate in candidates_no_cv:
        if 'twitter' in candidate and candidate['twitter'] is not None:
            show_twitter_button = True
            break

    # should we show subscribe button?
    from_email = ""
    if 'email' in flask.session:
        from_email = flask.session['email']
    email_got = False
    if from_email != "":
        email_got = lookups.updates_getting(app.config, from_email)
    dismiss = False
    if 'dismiss' in flask.session and flask.session['dismiss']:
        dismiss = True
    # ... this is set after tweeting them
    force_show = False
    if 'show_subscribe' in flask.request.args:
        force_show = True

    show_subscribe = not email_got and ((from_email and not dismiss) or force_show)

    return flask.render_template("candidates.html", constituency=constituency,
            candidates_no_cv=candidates_no_cv,
            candidates_have_cv=candidates_have_cv,
            candidates_no_email=candidates_no_email,
            from_email=from_email,
            show_subscribe=show_subscribe,
            show_twitter_button=show_twitter_button
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

    if candidate['email'] is not None:
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
# Ask candidates to upload their CV

@app.route('/email_candidates', methods=['GET','POST'])
def email_candidates():
    if 'postcode' not in flask.session:
        flask.flash("Enter your postcode to email candidates", 'success')
        return flask.redirect("/")
    constituency = flask.session['constituency']

    all_candidates = lookups.lookup_candidates(constituency['id'])
    if 'errors' in all_candidates:
        flask.flash("Error fetching list of candidates from YourNextMP.", 'danger')
        return error()
    all_candidates = lookups.augment_if_has_cv(app.config, all_candidates)
    (candidates_no_cv, _, _) = lookups.split_candidates_by_type(app.config, all_candidates)

    emails_list = ", ".join([c['email'] for c in candidates_no_cv])
    names_list = ", ".join([c['name'] for c in candidates_no_cv])

    original_message = """


Yours sincerely,

"""
    from_email = ""
    if 'email' in flask.session:
        from_email = flask.session['email']

    postcode = flask.session['postcode']
    message = original_message
    subject = ""
    if flask.request.method == 'POST':
        from_email = flask.request.form.get("from_email", "")
        subject = flask.request.form.get("subject", "")
        message = flask.request.form.get("message", "").replace("\r\n", "\n")
        if from_email == "" or not re.match("^.*?@.*?\..*?$", from_email):
            flask.flash("Please enter your email", 'danger')
        elif subject.strip() == "":
            flask.flash("Please write a subject for your email. Candidates pay more attention if it is unique and local!", 'danger')
        elif message.strip() == original_message.strip():
            flask.flash("Please enter a message", 'danger')
        elif re.search("Yours sincerely,$", message.strip()):
            flask.flash("Please sign your message.", 'danger')
        else:
            # this is their default email now
            flask.session['email'] = from_email
            # prompt for signup again
            flask.session['dismiss'] = False
            # send the mail
            identity.send_email_candidates(app, mail,
                candidates_no_cv, from_email, postcode,
                subject, message
            )
            flask.flash("Thanks! Your message has been sent to " + names_list + '.', 'success')
            return flask.redirect("/candidates")

    return flask.render_template("email_candidates.html",
        constituency=constituency,
        emails_list=emails_list,
        names_list=names_list,
        postcode=postcode,
        from_email=from_email,
        subject=subject,
        message=message
    )

@app.route('/tweet_candidates')
def tweet_candidates():
    if 'postcode' not in flask.session:
        flask.flash("Enter your postcode to tweet candidates", 'success')
        return flask.redirect("/")
    constituency = flask.session['constituency']

    all_candidates = lookups.lookup_candidates(constituency['id'])
    if 'errors' in all_candidates:
        flask.flash("Error fetching list of candidates from YourNextMP.", 'danger')
        return error()
    all_candidates = lookups.augment_if_has_cv(app.config, all_candidates)
    (candidates_no_cv, _, _) = lookups.split_candidates_by_type(app.config, all_candidates)

    return flask.render_template("tweet_candidates.html",
        constituency=constituency,
        candidates_no_cv=candidates_no_cv
    )


#####################################################################
# Subscribing

@app.route('/updates_join', methods=['POST'])
def updates_join():
    if 'dismiss' in flask.request.form:
        flask.session['dismiss'] = True
        return flask.redirect("/candidates")

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

