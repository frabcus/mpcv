import os
import subprocess

from main import app
import lookups


def gen_thumbs():
    # fetch all the person_ids with a CV thumbnail
    thumbs = [x["person_id"] for x in lookups.all_thumbnails(app.config)]
    # find all the CVs missing a thumbnail
    cvs_missing_thumbs = [x for x in lookups.all_cvs(app.config) if x["person_id"] not in thumbs]
    for x in cvs_missing_thumbs:
        filename = "tmp/{0}.png".format(x["person_id"])
        # generate thumbnail with phantom
        subprocess.call(["phantomjs", "screenshot.js", x["url"], filename])
        # add the thumbnail to S3
        lookups.add_thumb(app.config, x["person_id"], filename)
        os.remove(filename)

# generate missing thumbnails
gen_thumbs()
