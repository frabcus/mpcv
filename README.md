[![Build Status](https://travis-ci.org/frabcus/mpcv.svg?branch=master)](https://travis-ci.org/frabcus/mpcv)


Introduction
============

This is the source code to http://cv.democracyclub.org.uk/, which gathers the
Curriculum Vitae of candidates for Member of Parliament of the UK.


Environment
===========

You'll need to set these config variables in the environment:

```sh
# used for signing tokens in emails and sessions
MPCV_SECRET_KEY=somethingfairlyrandom

# set to an email address to send all emails to
MPCV_DEBUG_EMAIL=

# any setting from http://pythonhosted.org//Flask-Mail/
MPCV_MAIL_SERVER=localhost
MPCV_MAIL_USE_SSL=True/False
MPCV_MAIL_USERNAME=
MPCV_MAIL_PASSWORD=

# S3 bucket for storing CVs in
MPCV_S3_BUCKET_NAME=xxxx
MPCV_S3_ACCESS_KEY_ID=
MPCV_S3_SECRET_ACCESS_KEY=
```


Development
===========

To test in development do:

```sh
./main.py
```

ZZ9 9ZZ is a test constituency postcode, which uses fake data without even
calling MaPit.


Testing
=======

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


Production
==========

In production, Heroku uses the config in Procfile.


