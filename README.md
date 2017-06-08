[![Build Status](https://travis-ci.org/frabcus/mpcv.svg?branch=master)](https://travis-ci.org/frabcus/mpcv)


Introduction
============

This is the documentation and code for http://cv.democracyclub.org.uk/, which
gathers the Curriculum Vitae of candidates for Member of Parliament of the UK.

There are two main sections in this document, one for site administrators
and one for developers.


Administration
==============

Changing CVs
------------

To change someone's CV as an administrator, go to this URL:

```
/upload_cv/<int:person_id>/<admin_key>
```

Where `<admin_key>` depends on the installation. Ask a developer for the value
of the config variable `MPCV\_ADMIN\_KEY`, they can find it from Heroku.

Our policy is to let candidates for a live election change their CV, and for
ex-candidates to ask for a CV to be removed. This is a useful PDF to upload
in the latter case:

```
dummycvs/removed_after_election_by_candidate.pdf
```

A file with that name is special, as it isn't shown on index pages.

We do however keep copies of the old CVs in S3, for future researchers. 


Archiving an election
---------------------

We publish an archive of the state just after each election day via our
[http://cv.democracyclub.org.uk/archive](archive of old elections). These
archives are not indexed by search engines.

After each election, an administrator needs to archive the site and make it
available as new .zip file. 

Run the script `bin/archive-entire-election.sh` which uses wget on a local copy
of the site to make an archive. This includes all the actual .doc and .pdf CV
files, and thumbnail images.

After it is made, zip it up and put it on S3. Then update the archive page
to link to it.

There are commented commands in the shell script for what to do, but it is a
bit hard coded for the 2017 General Election. This can be generalised.


Development
===========

Democracy Club CV's is a Python application, based on Flask. 

It doesn't have a database. All data that changes is stored in an S3 bucket.
Other data, such as names of candidates, is loaded at startup from other
Democracy Club APIs.


Environment
-----------

You'll need to set these config variables in the environment:

```sh
# used for signing tokens in emails and sessions
MPCV_SECRET_KEY=somethingfairlyrandom

# set to an email address to send all emails to
MPCV_DEBUG_EMAIL=

# any setting from http://pythonhosted.org//Flask-Mail/
MPCV_MAIL_SERVER=localhost
MPCV_MAIL_USE_TLS=True (or empty)
MPCV_MAIL_USERNAME=
MPCV_MAIL_PASSWORD=

# S3 bucket for storing CVs in
MPCV_S3_BUCKET_NAME=xxxx
MPCV_S3_ACCESS_KEY_ID=
MPCV_S3_SECRET_ACCESS_KEY=

# Admin functions accessible with this
MPCV_ADMIN_KEY=xxxx

# Disable asset bundling (for debugging)
MPCV_ASSETS_DEBUG=true
```


Running in Development
----------------------

To run in development do:

```sh
./main.py
```

ZZ9 9ZZ is a test constituency postcode, which uses fake data without even
calling the Democracy Club postcode lookup API.


Python unit tests
-----------------

These aim to test all the Python code.

```sh
./main_tests.py
```

You need the S3 bucket environment variables set, even when testing.
And no other environment variables (`main_tests.py` sets some itself).

```sh
MPCV_S3_BUCKET_NAME=xxxx
MPCV_S3_ACCESS_KEY_ID=
MPCV_S3_SECRET_ACCESS_KEY=
```

You can find a line coverage report in `covhtml/index.html`.


Selenium integration tests
--------------------------

These test the main use paths, and any serious browser-side Javascript.

```sh
./selenium_tests.py http://localhost:5000/
```

The first parameter is the URL the site to test is running on. 

It makes some assumptions about the ZZ9 9ZZ postcode - in particular it will
upload a CV to one of the test users in that postcode.


Running in Production
---------------------

In production, Heroku uses the config in `Procfile`.

We use multiple Heroku buildpacks to install both phantom.js and python stuff.
To set this up, run:

```
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/stomita/heroku-buildpack-phantomjs
```

We use the scheduler add-on to build thumbnails. Install and configure that
with:

```
heroku addons:add scheduler
heroku addons:open scheduler
```

Then add the following to your cron task:

```
python cron.py
```


