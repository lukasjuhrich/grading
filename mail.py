#!/usr/bin/env python3
import argparse
import os
import re
from collections import deque, namedtuple
from datetime import datetime


PROFILE = "scz1uax0.default"
FOLDER = "msx.tu-dresden.de/test"

RE_MSG_SPLIT = re.compile(r"^From - (.*)\n$", flags=re.MULTILINE)


def get_file_path(profile=PROFILE, folder=FOLDER):
    base = os.path.expanduser("~/.thunderbird/")
    path = os.path.join(base, profile, "ImapMail", folder)
    print("path:", path)
    return path

# Example: "Mon Oct 10 16:40:28 2016"
DATE_FORMAT = "%a %b %d %X %Y"

def grab_one_mail(queue, date_format=DATE_FORMAT):
    date_string = queue.popleft()
    if date_format:
        date = datetime.strptime(date_string, date_format)
    else:
        date = date_string
    return _mail(date, queue.popleft())


_mail = namedtuple("mail", ['date', 'content'])
def iter_mails(string, regex=RE_MSG_SPLIT, options={}):
    res = deque(re.split(regex, string))
    # ignore things before the first separation (usually ``''``)
    res.popleft()

    while len(res) >= 2:
        yield grab_one_mail(res, **options)


def list_mails():
    with open(get_file_path()) as desc:
        content = desc.read()

    for mail in iter_mails(content):
        print("mail:", mail)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract mail.")

    args = parser.parse_args()

    list_mails()
