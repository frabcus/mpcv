[![Build Status](https://travis-ci.org/frabcus/mpcv.svg?branch=master)](https://travis-ci.org/frabcus/mpcv)


Introduction
============

This is the source code to http://cv.democracyclub.org.uk/, which gathers the
Curriculum Vitae of candidates for Member of Parliament of the UK.


Development
===========

To test in development do:

```sh
./main.py
```

Will show stack traces and stuff.

ZZ9 9ZZ is a test constituency postcode.


Testing
=======

Python unit tests
-----------------

```sh
./main_tests.py
```

You can find a line coverage report in `covhtml/index.html`.

Casper integration tests
------------------------

```sh
casperjs test test_casper.js --address=http://localhost:5000/
```

You can find screen shots of every page in `screenshots/`.

On a Mac I had to install casperjs and phantomjs of particular versions from
Homebrew, so they worked together.

```sh
brew install casperjs --devel
brew switch phantomjs 1.9.2
```


Production
==========

In production, Heroku uses the config in Procfile.


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



