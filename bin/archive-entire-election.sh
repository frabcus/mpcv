#!/bin/sh

wget --header "Cookie: mpcv_archive=1" --page-requisites --adjust-extension --convert-links --span-hosts -r --level=inf http://127.0.0.1:5000/

