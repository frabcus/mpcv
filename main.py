#!/usr/bin/env python3

import os
import traceback
import re
import math
import logging
import json
import datetime
import itertools

import werkzeug
import flask
import flask_appconfig.env
import flask_mail
import flask.ext.cache
import flask.ext.compress
import flask.ext.assets

import identity

app = flask.Flask(__name__)
flask_appconfig.env.from_envvars(app.config, prefix='MPCV_')
mail = flask_mail.Mail(app)
cache = flask.ext.cache.Cache(app,config={'CACHE_TYPE': 'simple'})
flask.ext.compress.Compress(app)
assets = flask.ext.assets.Environment(app)

import lookups
import constants

# Log to stderr for Heroku
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
app.logger.addHandler(stream_handler)

#####################################################################
# Sitemap and global API

def sitemap_generator():
    yield 'index', {}
    yield 'about', {}

    for size in ['small', 'medium', 'large']:
        for view in ['recent', 'constituency', 'party']:
            yield 'browse', { 'size': size, 'view': view }

    all_cvs = _cache_all_cvs()
    for cv in all_cvs:
        yield 'show_cv', { 'person_id': cv['person_id'] }

    all_constituencies = _cache_all_constituencies()
    for candidates in all_constituencies:
        yield 'candidates', { 'constituency_id': candidates[0]['constituency_id'] }

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

class DateTimeEncoder(json.JSONEncoder):
    def __init__(self):
        super(DateTimeEncoder, self).__init__(indent=4)
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.timedelta):
            return (datetime.datetime.min + obj).time().isoformat()
        else:
            return super(DateTimeEncoder, self).default(obj)

@app.route('/cvs.json')
def cvs_json():
    all_cvs = _cache_all_cvs()
    output = DateTimeEncoder().encode(all_cvs)

    response = flask.make_response(output)
    response.headers["Content-Type"] = "application/json"
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

@app.before_request
def set_thumbnail():
    all_cvs = _cache_all_cvs()
    flask.g.most_recent_thumbnail = all_cvs[0]['thumb']['url']

# Tracking events
@app.before_request
def track_events_from_cookies():
    if 'emailed_candidates_track' in flask.session:
        flask.g.emailed_candidates_track = flask.session['emailed_candidates_track']
        del flask.session['emailed_candidates_track']

#####################################################################
# General routes

def error():
    return flask.render_template('error.html'), 500

@app.route('/about')
def about():
    return flask.render_template('about.html',
        og_image = flask.url_for('static', filename='what-is-cv.png', _external=True)
    )

@app.route('/exception')
def exception():
    raise Exception("This is a test error")


#####################################################################
# Caches

@cache.memoize(60 * 10)
def _cache_all_cvs():
    return lookups.all_cvs_with_thumbnails(app.config)

@cache.memoize(60 * 10)
def _cache_all_constituencies():
    return lookups.all_constituencies(app.config)

@cache.memoize(60 * 10)
def _cache_candidates_augmented(constituency_id):
    all_candidates = lookups.lookup_candidates(app.config, constituency_id)
    if 'error' in all_candidates:
        return all_candidates
    all_candidates = lookups.augment_if_has_cv(app.config, all_candidates)

    return all_candidates


#####################################################################
# Main pages

@app.route('/')
def index():
    recent_cvs = _cache_all_cvs()[0:4]
    return flask.render_template('index.html', recent_cvs=recent_cvs)

@app.route('/all_cvs/page/<int:page>')
def old_all_cvs(page):
    return flask.redirect(flask.url_for("browse", view="recent", size="large"))
@app.route('/all_cvs/<view>/<size>')
def old_all_cvs_2(view, size):
    return flask.redirect(flask.url_for("browse", view=view, size=size))
@app.route('/browse/alphabet/<size>')
def old_all_cvs_3(size):
    return flask.redirect(flask.url_for("browse", view="constituency", size=size))

@app.route('/browse/<view>/<size>')
def browse(view, size):
    if size not in ['small', 'medium', 'large']:
        return flask.redirect(flask.url_for("browse", view=view, size="large"))
    if view not in ['recent', 'constituency', 'party']:
        return flask.redirect(flask.url_for("browse", view="recent", size=size))

    if view == 'recent':
        all_cvs = _cache_all_cvs()
        return flask.render_template('browse.html',
                cv_groups = [{ 'heading': None, 'cvs': all_cvs }],
                size = size,
                view = view
        )
    elif view == 'constituency':
        all_constituencies = _cache_all_constituencies()
        return flask.render_template('browse.html',
                constituencies = all_constituencies,
                size = size,
                view = view
        )
    if view == 'party':
        all_cvs = _cache_all_cvs()
        # sort parties alphabetically
        all_cvs = sorted(all_cvs, key=lambda k: k['candidate']['party'])
        cv_groups = []
        for party, cvs in itertools.groupby(all_cvs, key=lambda k: k['candidate']['party']):
            # sort within each party in forewards data order of uploading CV
            cv_groups.append({'heading': party, 'cvs': sorted(list(cvs), key=lambda k: k['last_modified'])})
        return flask.render_template('browse.html',
                cv_groups = cv_groups,
                size = size,
                view = view
        )



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
# List candidates

@app.route('/candidates')
@app.route('/email_candidates')
@app.route('/tweet_candidates')
def candidates_your_constituency():
    if 'constituency' not in flask.session:
        return flask.redirect("/")

    from_front_page = flask.request.args.get("from-front-page", None)

    constituency = flask.session['constituency']
    return flask.redirect(
        flask.url_for(
            flask.request.url_rule.rule.replace("/", ""),
            constituency_id = constituency['id'],
            from_front_page = from_front_page
        )
    )

def _can_tweet(candidates_no_cv):
    for candidate in candidates_no_cv:
        if 'twitter' in candidate and candidate['twitter'] is not None:
           return True
    return False

@app.route('/candidates/<int:constituency_id>')
def candidates(constituency_id = None):
    all_candidates = _cache_candidates_augmented(constituency_id)
    if 'error' in all_candidates:
        flask.flash("Error looking up candidates in YourNextMP.", 'danger')
        return error()
    (candidates_no_cv, candidates_no_email, candidates_have_cv) = lookups.split_candidates_by_type(app.config, all_candidates)

    constituency = {
        'id': constituency_id,
        'name': all_candidates[0]['constituency_name']
    }
    show_twitter_button = _can_tweet(candidates_no_cv)

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
    # when to show subscribe form prominently at top
    show_subscribe = not dismiss and (from_email or force_show)

    # thumbnail defaults to first person in constituency to have submitted CV!
    og_image = None
    if len(candidates_have_cv) > 0:
        if candidates_have_cv[0]['cv']['has_thumb']:
            og_image = candidates_have_cv[0]['cv']['thumb']['url']
    else:
        og_image = flask.url_for('static', filename='what-is-cv.png', _external=True)
    og_description = "Before you vote, look at CVs like these in {}! This site helps MP candidates share their CV with voters.".format(
        constituency['name']
    )

    postcode = flask.session.get('postcode', None)

    return flask.render_template("candidates.html", constituency=constituency,
            candidates_no_cv=candidates_no_cv,
            candidates_have_cv=candidates_have_cv,
            candidates_no_email=candidates_no_email,
            from_email=from_email,
            postcode=postcode,
            show_subscribe=show_subscribe,
            show_twitter_button=show_twitter_button,
            email_got=email_got,
            og_image=og_image,
            og_description=og_description
    )


#####################################################################
# Viewing individual CVs


# GET is to show form to upload CV
@app.route('/show_cv/<int:person_id>')
def show_cv(person_id):
    candidate = lookups.lookup_candidate(app.config, person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    current_cv = lookups.get_current_cv(app.config, candidate['id'])
    if current_cv is None:
        return flask.redirect(flask.url_for('upload_cv', person_id=person_id))

    current_thumb = lookups.get_current_thumb(app.config, candidate['id'])
    og_image = current_thumb['url'] if current_thumb is not None else False
    og_description = "Before you vote, look at CVs like {}'s! This site helps MP candidates share their CV with voters.".format(
        candidate['name']
    )

    # Go back to where we came from if that was our site
    # (e.g. to all page, home page or candidates page)
    # Default to candidates page.
    more_link = flask.url_for("candidates", constituency_id=candidate['constituency_id'])
    refer = flask.request.referrer
    host_url = flask.request.host_url
    if refer and host_url:
        if refer.startswith(host_url):
            more_link = refer

    return flask.render_template("show_cv.html",
            candidate=candidate,
            cv=current_cv,
            og_image=og_image,
            og_description=og_description,
            tw_large_card=True,
            more_link=more_link
        )


#####################################################################
# Uploading CVs

# GET is to say "you need to confirm email"
# POST when they click the button to send the confirm email
@app.route('/upload_cv/<int:person_id>', methods=['GET','POST'])
def upload_cv(person_id):
    candidate = lookups.lookup_candidate(app.config, person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    if flask.request.method == 'POST':
        identity.send_upload_cv_confirmation(app, mail, candidate['id'], candidate['email'], candidate['name'])
        return flask.render_template("check_email.html", candidate=candidate)

    already_got = False
    if lookups.get_current_cv(app.config, person_id):
        already_got = True

    return flask.render_template("upload_cv.html", candidate=candidate,
        og_image = flask.url_for('static', filename='what-is-cv.png', _external=True),
        already_got = already_got
    )

# Administrator get a confirm link
@app.route('/upload_cv/<int:person_id>/<admin_key>')
def upload_cv_admin(person_id, admin_key):
    if admin_key != app.config['ADMIN_KEY']:
        flask.flash("Administrator permissions denied.", 'danger')
        return error()

    candidate = lookups.lookup_candidate(app.config, person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    link = identity.generate_upload_url(app.secret_key, person_id)
    return flask.redirect(link)


# GET is to show form to upload CV
@app.route('/upload_cv/<int:person_id>/c/<signature>', methods=['GET'])
def upload_cv_confirmed(person_id, signature):
    candidate = lookups.lookup_candidate(app.config, person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    if not identity.check_signature(app.secret_key, person_id, signature):
        flask.flash("Sorry! That web link isn't right. Can you check you copied it properly from your email?", 'warning')
        return error()

    current_cv = lookups.get_current_cv(app.config, candidate['id'])

    if candidate['email'] is not None:
        # this is their default email now
        flask.session['email'] = candidate['email']

    upload_link = flask.url_for('upload_cv_upload', person_id=person_id, signature=signature)

    return flask.render_template("upload_cv_confirmed.html", candidate=candidate,
         upload_link=upload_link, current_cv=current_cv)

# POST is actual receiving of CV
@app.route('/upload_cv/<int:person_id>/c/<signature>', methods=['POST'])
def upload_cv_upload(person_id, signature):
    candidate = lookups.lookup_candidate(app.config, person_id)
    if 'error' in candidate:
        flask.flash(candidate['error'], 'danger')
        return error()

    if not identity.check_signature(app.secret_key, person_id, signature):
        flask.flash("Sorry! That web link isn't right. Can you check you copied it properly from your email?", 'warning')
        return error()

    f = flask.request.files['files']
    if not f:
        flask.flash("No files were received. Please try again, or contact us for help.", 'danger')
        return flask.redirect(flask.request.path)

    secure_filename = werkzeug.secure_filename(f.filename)
    data = f.read()
    size = len(data)

    print("saving CV to S3: candidate:", person_id, "uploaded file:", secure_filename, size, "bytes")
    file_url = lookups.add_cv(app.config, person_id, data, secure_filename)

    # force reloading of all data for now, so CV appears in the redirect
    with app.app_context():
        cache.clear()

    flask.flash("Thanks! Your CV has been successfully uploaded. It will take about half an hour to appear on the site.", 'success')
    flask.flash("Friends who are also candidates? Please tell them to upload their CV too!", 'info')
    return flask.redirect("/about")


#####################################################################
# Ask candidates to upload their CV

@app.route('/email_candidates/<int:constituency_id>', methods=['GET','POST'])
def email_candidates(constituency_id):
    all_candidates = _cache_candidates_augmented(constituency_id)
    if 'error' in all_candidates:
        flask.flash("Error looking up candidates in YourNextMP.", 'danger')
        return error()
    (candidates_no_cv, candidates_no_email, candidates_have_cv) = lookups.split_candidates_by_type(app.config, all_candidates)

    if len(candidates_no_cv) == 0:
        return flask.redirect(flask.url_for("candidates", constituency_id=constituency_id))

    constituency = {
        'id': constituency_id,
        'name': all_candidates[0]['constituency_name']
    }

    emails_list = ", ".join([c['email'] for c in candidates_no_cv])
    names_list = ", ".join([c['name'] for c in candidates_no_cv])

    show_twitter_button = _can_tweet(candidates_no_cv)

    original_message = """I'm a resident of your constituency.

I have been looking at candidates' CVs on the Democracy Club website to help me decide who to vote for.

I'd be grateful if you could add your CV too. Please click on the link at the bottom of this email to upload your CV now.

Thank you very much.

Yours sincerely,

"""

    if len(candidates_have_cv) > 1:
        original_message = """I'm a resident of your constituency.

{count} other candidates have shared their CV with voters using the Democracy Club website. This helps me decide who to vote for.

I'd be grateful if you could add your CV too. Please click on the link at the bottom of this email to upload your CV now.

Thank you very much.

Yours sincerely,

""".format(count=len(candidates_have_cv))

    from_email = ""
    if 'email' in flask.session:
        from_email = flask.session['email']

    # if came from front page, and they emailed before, don't force it
    from_front_page = flask.request.args.get("from_front_page")
    if from_email and from_front_page:
        return flask.redirect(flask.url_for("candidates", constituency_id=constituency_id))

    tempt_text = False
    if len(candidates_have_cv) > 0 and from_front_page:
        tempt_text = True

    message = original_message
    subject = ""
    if flask.request.method == 'POST':
        from_email = flask.request.form.get("from_email", "")
        subject = flask.request.form.get("subject", "")
        message = flask.request.form.get("message", "").replace("\r\n", "\n")
        if from_email == "" or not re.match("^.*?@.*?\..*?$", from_email):
            flask.flash("Please enter your email.", 'danger')
        elif subject.strip() == "":
            flask.flash("Please write a subject for your email. Candidates pay more attention if it is unique and local!", 'danger')
        elif message.strip() == original_message.strip():
            flask.flash("Please edit the message - say something unique!", 'danger')
        elif re.search("Yours sincerely,$", message.strip()):
            flask.flash("Please sign your message. Put your address in, to show you really could vote for them!", 'danger')
        else:
            # this is their default email now
            flask.session['email'] = from_email
            # prompt for signup again
            flask.session['dismiss'] = False
            # send the mail
            identity.send_email_candidates(app, mail,
                candidates_no_cv, from_email,
                subject, message
            )
            # track it via Google analytics in next page load
            flask.session['emailed_candidates_track'] = json.dumps([str(c['id']) for c in candidates_no_cv])

            flask.flash("Thanks! Your message has been sent to " + names_list + '.', 'success')
            return flask.redirect("/candidates/" + str(constituency_id))

    return flask.render_template("email_candidates.html",
        constituency=constituency,
        emails_list=emails_list,
        names_list=names_list,
        from_email=from_email,
        subject=subject,
        message=message,
        show_twitter_button=show_twitter_button,
        tempt_text=tempt_text
    )

@app.route('/tweet_candidates/<int:constituency_id>')
def tweet_candidates(constituency_id):
    all_candidates = _cache_candidates_augmented(constituency_id)
    if 'error' in all_candidates:
        flask.flash("Error looking up candidates in YourNextMP.", 'danger')
        return error()
    (candidates_no_cv, candidates_no_email, candidates_have_cv) = lookups.split_candidates_by_type(app.config, all_candidates)

    constituency = {
        'id': constituency_id,
        'name': all_candidates[0]['constituency_name']
    }

    return flask.render_template("tweet_candidates.html",
        constituency=constituency,
        candidates_no_cv=candidates_no_cv,
        have_cvs_count=len(candidates_have_cv)
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
        flask.flash("Please enter your email to subscribe to updates.", 'danger')
        return flask.redirect("/candidates")

    if 'postcode' not in flask.session:
        flask.flash("Enter your postcode before signing up for updates.", 'success')
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

