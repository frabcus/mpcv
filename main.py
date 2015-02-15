import os
from flask import Flask

app = Flask(__name__)

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


@app.route('/')
def hello():
    return enpage("""
                <h1>If you were hiring somebody at work, you'd look at their CVs, right?</h1>
                <h2>So why don't we look at our MP's CV?</h2>

                <p class="lead">Enter your postcode, to start sifting through
                the CVs of people applying for the job of being your MP.</p>

                <form action="/set_postcode" method="POST">
                    <div class="form-group">
                      <input id="postcode" name="postcode">
                    </div>

                    <div class="form-group">
                      <input type="submit" class="button" value="View candidates">
                    </div>
                </form>
    """)


