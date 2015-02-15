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
    return flask.render_template('index.html')

@app.route('/constituency')
def constituency():
    postcode = flask.request.args.get('postcode')
    constituency = lookup_postcode(postcode)

    if 'error' in constituency:
        flask.flash("bad postcode haha")
        return flask.redirect(flask.url_for('index'))

    return """
            Hi: %s
    """ % json.dumps(constituency)


if __name__ == '__main__':
    app.config['DEBUG'] = True
    app.run()



