#!/usr/bin/env python

import os
import flask
import requests
import json

app = flask.Flask(__name__)
app.secret_key = os.getenv('MPCV_SESSION_SECRET')

def lookup_postcode(postcode):
    data = requests.get("http://mapit.mysociety.org/postcode/" + postcode).json()
    if "error" in data:
        return data
    return data["areas"][str(data["shortcuts"]["WMC"])]

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

    return flask.render_template("applicants.html", name=constituency['name'])


if __name__ == '__main__':
    app.config['DEBUG'] = True
    app.run()



