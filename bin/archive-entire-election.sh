#!/bin/sh

set -x

ELECTION=parl.2019-12-12

mkdir archive-$ELECTION
cd archive-$ELECTION

wget --exclude-domains apis.google.com,fonts.googleapis.com,fonts.gstatic.com,docs.google.com,www.gstatic.com,yournextmp.com,candidates.democracyclub.org.uk --header "Cookie: mpcv_archive=1" --page-requisites --adjust-extension --convert-links --span-hosts -r --level=inf http://127.0.0.1:5000/

mv 127.0.0.1:5000 cv.democracyclub.org.uk

cd ..
zip -r democracy-club-cvs-archive-$ELECTION.zip archive-$ELECTION 
s3cmd put -P democracy-club-cvs-archive-$ELECTION.zip s3://mpcv/archive/democracy-club-cvs-archive-$ELECTION.zip

