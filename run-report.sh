#!/bin/bash
#
# This script is used by a cron job to run the report on a regular basis and refresh the data in a place
# where the apache server to pick up

cd ~ubuntu/bugs
python nova-bugs.py
cp bugs-refresh.json /var/www/bugs.json
