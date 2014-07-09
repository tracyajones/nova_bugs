#!/bin/bash
cd ~ubuntu/bugs
python nova-bugs.py
cp bugs-refresh.json /var/www/bugs.json
