#!/usr/bin/env python3

import os
import subprocess
import traceback
import sys

import flask_mail
import PIL.Image

import lookups
import main

def gen_thumbs():
    # find all the CVs with out of date thumbnail
    cvs_bad_thumbs = lookups.all_cvs_bad_thumbnails(main.app.config)
    for x in cvs_bad_thumbs:
        print("cron missing thumb:", x)
        filename = "tmp/{0}.png".format(x["person_id"])

        # generate thumbnail with phantom
        try:
            subprocess.check_call(["phantomjs", "screenshot.js", x["url"], filename])
            # make a JPEG, they're smaller
            img = PIL.Image.open(filename)
            # remove alpha channel, which JPEG doesn't support
            img = img.convert("RGB")
            img.save(filename + ".jpg", option='optimize')
            # add the thumbnail to S3
            lookups.add_thumb(main.app.config, filename + ".jpg", x['name'].replace("cvs/", "thumbs/") + ".jpg", extension="jpg")
            os.remove(filename)
            os.remove(filename + ".jpg")
        except subprocess.CalledProcessError:
            print("Failed to make thumb for person ", str(x["person_id"]))
            print(traceback.format_exc())
            msg = flask_mail.Message(body=traceback.format_exc(),
                    subject="Failed to make thumb for person " + str(x["person_id"]),
                    sender=("Democracy Club CV", "cv@democracyclub.org.uk"),
                    recipients=[("Democracy Club CV", "cv@democracyclub.org.uk")]
                  )
            with main.app.app_context():
                main.mail.send(msg)




# generate missing thumbnails
gen_thumbs()
