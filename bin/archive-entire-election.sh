#!/bin/sh

set -x

# mkdir archive-2015
# cd archive-2015

wget --exclude-domains apis.google.com,fonts.googleapis.com,fonts.gstatic.com,docs.google.com,www.gstatic.com,yournextmp.com,candidates.democracyclub.org.uk --header "Cookie: mpcv_archive=1" --page-requisites --adjust-extension --convert-links --span-hosts -r --level=inf http://127.0.0.1:5000/

mv 127.0.0.1:5000 cv.democracyclub.org.uk

# cd ..
# zip -r democracy-club-cvs-archive-2015.zip archive-2015 
# s3cmd put -P democracy-club-cvs-archive-2015.zip s3://mpcv/archive/democracy-club-cvs-archive-2015.zip

