#!/usr/bin/env python3

import os
import subprocess

import lookups
import main


def gen_thumbs():
    # find all the CVs missing a thumbnail
    cvs_missing_thumbs = lookups.all_cvs_no_thumbnails(main.app.config)
    for x in cvs_missing_thumbs:
        print("cron missing thumb:", x)
        filename = "tmp/{0}.png".format(x["person_id"])
        # generate thumbnail with phantom
        subprocess.call(["phantomjs", "screenshot.js", x["url"], filename])
        # add the thumbnail to S3
        lookups.add_thumb(main.app.config, x["person_id"], filename)
        os.remove(filename)

# generate missing thumbnails
gen_thumbs()
