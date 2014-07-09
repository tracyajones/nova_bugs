#!/bin/bash
python infra_bugday.py
cp bugs-refresh.json /var/www/bugs.json
