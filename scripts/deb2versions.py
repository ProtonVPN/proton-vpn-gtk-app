#!/usr/bin/env python
'''
Use this when you need to create the initial versions.yml file from a debian package.

This program takes a debian changelog file and converts it into a yml versions file.
The debian changelog file is read from stdin.
The output yml file is written to stdout.
'''

import yaml
import sys
import re
import datetime

re_release = re.compile("([a-zA-Z-_]+) \(([a-zA-Z0-9.~_]+)\) (unstable|stable); urgency=([a-zA-Z0-9]+)")
re_author = re.compile("\s+--([a-zA-Z0-9 ]+)<([a-zA-Z.@]+)>  ([a-zA-Z0-9:, +]+)")
re_description = re.compile("\s+ \*(.*)")

# The releases
releases=[]

# A single release
name = None
version = None
stability = None
urgency = None
author = None
email = None
time=None
description=[]

def convert_time(date):
    dt = datetime.datetime.strptime(date, '%a, %d %b %Y %H:%M:%S %z').astimezone(datetime.timezone.utc)
    return(dt.strftime("%Y/%m/%d %H:%M"))

def add_version():
   global releases
   if version:
    releases.append(
        dict(
            version=version.strip().replace("~", ""),
            time=convert_time(time.strip()),
            author=author.strip(),
            email=email.strip(),
            urgency=urgency.strip(),
            stability=stability.strip(),
            description=description
        )
      )

def main():
    for i in sys.stdin.read().splitlines():
        release_elems = re_release.match(i)
        author_elems = re_author.match(i)
        description_elems = re_description.match(i)
        if release_elems:
            if version:
                add_version()
                description = []
                version=None
            name, version, stability, urgency = release_elems.groups()
        elif author_elems:
            author, email, time = author_elems.groups()
        elif description_elems:
            description.append( description_elems.groups()[0].strip() )

    add_version()
    print(yaml.dump_all(releases, sort_keys=False))

if __name__ == "__main__":
   main()