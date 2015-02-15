#!/usr/bin/env python

import os
import flask
import requests
import json

app = flask.Flask(__name__)

def header():
    return """
            <!DOCTYPE html>
            <html lang="en">
                <head>

                <link href="/static/bootstrap.min.css" rel="stylesheet">
                <link href="/static/style.css" rel="stylesheet">

                </head>

                <body>

                    <div id="wrap">

                        <div id="masthead">
                          <div class="container">
                              <div class="row">
                                <div class="col-md-2 col-lg-3">
                                </div>
                                <div class="col-md-8 col-lg-6">
            """

def footer():
    return """
                                </div>
                                <div class="col-md-2 col-lg-3">
                                </div>
                              </div>
                           </div>
                        </div>
                    </div>
                </body>
            </html>"""

def enpage(content):
    return header() + content + footer()

def lookup_postcode(postcode):
    data = requests.get("http://mapit.mysociety.org/postcode/" + postcode).json()
    if "error" in data:
        return data
    return data["areas"][str(data["shortcuts"]["WMC"])]

@app.route('/')
def index():
    return enpage("""
                <h1>If you were hiring somebody at work, you'd look at their CVs, right?</h1>
                <h2>So why don't we look at our MP's CV?</h2>

                <p class="lead">Enter your postcode, to start sifting through
                the CVs of people applying for the job of being your MP.</p>

                <form action="/constituency" method="GET">
                    <div class="form-group">
                      <input id="postcode" name="postcode" placeholder="Postcode" class="form-control">
                    </div>

                    <div class="form-group">
                      <button type="submit" class="btn btn-default">View candidates</button>
                    </div>
                </form>
    """)

@app.route('/constituency')
def constituency():
    postcode = flask.request.args.get('postcode')
    constituency = lookup_postcode(postcode)

    if 'error' in constituency:
        return flask.redirect(flask.url_for('index'))

    return enpage("""
            Hi: %s
    """ % json.dumps(constituency))


if __name__ == '__main__':
    app.config['DEBUG'] = True
    app.run()



