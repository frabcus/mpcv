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

```sh
./main\_tests.py
```


Production
==========

In production, Heroku uses the config in Procfile.


Environment
===========

You'll need to set these config variables in the environment:

```sh
MPCV\_SESSION\_SECRET=somethingfairlyrandom

DEBUG\_EMAIL= # set to an email address to send all emails to

SMTP\_HOSTNAME=localhost
SMTP\_USERNAME=
SMTP\_PASSWORD=
```

