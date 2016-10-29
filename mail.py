#!/usr/bin/env python3
import argparse
import os
import re
from collections import deque, namedtuple
from datetime import datetime
from email import message_from_string
from email.header import decode_header
from operator import attrgetter


PROFILE = "scz1uax0.default"
FOLDER = "msx.tu-dresden.de/Prog"

RE_MSG_SPLIT = re.compile(r"^From - (.*)\n", flags=re.MULTILINE)


def get_file_path(profile=PROFILE, folder=FOLDER):
    base = os.path.expanduser("~/.thunderbird/")
    path = os.path.join(base, profile, "ImapMail", folder)
    return path

# Example: "Mon Oct 10 16:40:28 2016"
DATE_FORMAT = "%a %b %d %X %Y"

def grab_one_mail(queue, date_format=DATE_FORMAT):
    """Format two elments of a queue to a mail namedtuple

    :param deque queue: the queue
    :param str date_format: the date format specifier
    """
    date_string = queue.popleft()
    if date_format:
        date = datetime.strptime(date_string, date_format)
    else:
        date = date_string
    return _mail(date, queue.popleft())


_mail = namedtuple("mail", ['date', 'content'])
def iter_mails(string, regex=RE_MSG_SPLIT, options=None):
    """Split a string with a regex and iterate over the chunks.

    The regex is supposed to have one capture group, which makes
    ``re.split`` return information in chunks of two list elements.
    Now, ``grab_one_mail`` is used to yield the chunk.

    :param str string: The string containing the mails
    :param re regex: The regex to apply.  Must have one capture group.
    :param dict options: A dict being passed to ``grab_one_mail`` as
        kwargs

    :return: An iterator over the chunks as a _mail namedtuple
    :rtype: iterator[_mail]
    """
    if options is None:
        options = {}

    res = deque(re.split(regex, string))
    # ignore things before the first separation (usually ``''``)
    res.popleft()

    while len(res) >= 2:
        yield grab_one_mail(res, **options)


def nice_header(encoded_string):
    decoded_words = decode_header(encoded_string)
    word = [w for w in decoded_words if w][0]

    string_like = word[0]  # may be bytes or str

    if isinstance(string_like, str):
        return string_like

    return string_like.decode(word[1])


def fetch_mails():
    with open(get_file_path()) as desc:
        content = desc.read()
    return sorted(iter_mails(content), key=attrgetter('date'))


def list_mails():
    for i, mail in enumerate(fetch_mails()):
        message = message_from_string(mail.content)

        subject = nice_header(message.get('subject', "<no subject>"))
        sender = message.get('From', "<no sender>")
        print("{:2d} {date} {sender} »{subj}«"
              .format(i, date=mail.date, sender=sender, subj=subject))


def iter_attachments(id):
    mail_string = list(fetch_mails())[id].content
    mail = message_from_string(mail_string)
    for part in mail.walk():
        filename = part.get_filename()
        if not filename:
            continue
        yield part

def show_attachments(id):
    for attachment in iter_attachments(id):
        print(attachment.get_filename())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract mail.")
    parser.add_argument("command")
    parser.add_argument("-i", "--index", type=int, help="The mail to select")

    args = parser.parse_args()

    if args.command == 'list':
        list_mails()
    elif args.command == 'extract':
        show_attachments(args.index)
