#! /usr/bin/env python
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# nova_bugs.py pulls out all the bugs from the nova project in
# launchpad and writes them to a file in JSON format.  This is based on
# infra_bugday.py from the CI team

import datetime
import json
from optparse import OptionParser
import os
import re

from launchpadlib.launchpad import Launchpad
import requests

LPCACHEDIR = os.path.expanduser(os.environ.get('LPCACHEDIR',
                                               '~/.launchpadlib/cache'))
LPPROJECT = os.environ.get('LPPROJECT',
                           'nova')
LPSTATUS = ('New', 'Confirmed', 'Triaged', 'In Progress')
LPIMPORTANCE = ('Critical', 'High', 'Medium', 'Undecided', 'Low', 'Wishlist')

RE_LINK = re.compile(' https://review.openstack.org/(\d+)')


def get_reviews_from_bug(bug):
    """Return a list of gerrit reviews extracted from the bug's comments."""
    reviews = set()
    for comment in bug.messages:
        reviews |= set(RE_LINK.findall(comment.content))
    return reviews


def get_review_status(review_number):
    """Return status of a given review number."""
    r = requests.get("https://review.openstack.org:443/changes/%s"
                     % review_number)
    # strip off first few chars because 'the JSON response body starts with a
    # magic prefix line that must be stripped before feeding the rest of the
    # response body to a JSON parser'
    # https://review.openstack.org/Documentation/rest-api.html
    status = None
    try:
        status = json.loads(r.text[4:])['status']
    except ValueError:
        status = r.text
    return status


def delta(date_value):
    delta = datetime.date.today() - date_value.date()
    return delta.days


def main():


    parser = OptionParser()
    parser.add_option("-p", "--project", dest="project", default="nova",
                      help="generate a report for a project")
    parser.add_option("-o", "--output", dest="output_file",
                      help="Output file")
    parser.add_option("-l", "--limit", dest="limit", default=None,
                      help="Limit - default is none")


    (options, args) = parser.parse_args()
    if options.output_file is None:
        exit('Output File is required')

    launchpad = Launchpad.login_anonymously('OpenStack Infra Bugday',
                                            'production',
                                            LPCACHEDIR)
    project = launchpad.projects[options.project]
    counter = 0

    nova_status = "Unknown"

    outfile = options.output_file + '/bugs-refresh.json'
    f = open(outfile, 'w')
    f.write('{"date": "%s", "bugs": [' % datetime.datetime.now())

    for task in project.searchTasks(status=LPSTATUS, importance=LPIMPORTANCE,
                                    omit_duplicates=True,
                                    order_by='-importance'):

        if options.limit and counter == int(options.limit):
            break
        bug = launchpad.load(task.bug_link)

        nova_status = 'Unknown'
        nova_owner = 'Unknown'

        for task in bug.bug_tasks:
            if task.bug_target_name == 'nova':
                nova_status = task.status
                nova_owner = task.assignee
                break
        try:
            if counter != 0:
                bug_data = ','
            else:
                bug_data = ""
            title = bug.title.replace('"', "'")
            title = title.replace("\n", "")
            title = title.replace("\t", "")
            bug_data += ('{"index": %d, "id": %d, "importance": "%s", '
                         '"status": "%s", '
                         '"owner": "%s", '
                         '"title": "%s", '
                         '"link": "%s"' % (
                             counter,
                             bug.id,
                             task.importance,
                             nova_status,
                             nova_owner,
                             title,
                             task.web_link))

        except (TypeError, UnicodeEncodeError):
            # TODO: fix this
            print 'Error on bug %d', bug.id
            counter += 1
            continue

        age = delta(bug.date_created)
        updated = delta(bug.date_last_updated)
        stale = False
        if updated > 30 and age > 30:
            if nova_status == 'In Progress':
                stale = True
        bug_data += (',"age": %d, "update": %d, "stale": %d, '
                     '"never_touched": %d' %
                     (age, updated, 1 if stale else 0, 1 if (age ==
                                                             updated) else 0))

        i = 0
        bug_data += ( ',"projects": [')

        for line in map(lambda x: '{"target": "%s", "status": '
                                  '"%s"}' %
                (x.bug_target_name, x.status),
                        bug.bug_tasks):
            if i != 0:
                bug_data += (",")
            i += 1
            bug_data += (line)

        bug_data += ('] ,"reviews": [')

        i = 0
        for review in get_reviews_from_bug(bug):
            review_status = get_review_status(review)
            if i != 0:
                bug_data += (",")
            i += 1
            review_status = review_status.replace("\n", "")
            bug_data += ('{"review": '
                         '"https://review.openstack.org/%s",'
                         '"status": "%s"}'
                         % (review, review_status))
        bug_data += (']}')

        try:

            if counter == 0:
                json.loads(bug_data)
            else:
                json.loads(bug_data[1:])
            f.write(bug_data)
        except ValueError, e:
            print e, bug_data
        counter += 1

    f.write(']}')
    f.close()


if __name__ == "__main__":
    main()
