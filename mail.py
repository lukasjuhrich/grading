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

ROUND = 'Uebung01'
current_round = ROUND


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
    """Readably format an encoded mail header string

    Mail strings can come either in plain or in encoded form like
    ``"=?UTF-8?B?NC4gw5xidW5n?="``

    Take the first non-nil word (``== (text, encoding)``) of the
    decoded header.  If it is an instance of ``str``, return it.
    Else, decode it with the given encoding.

    :param encoded_string: A non-decoded header value.

    :returns: The decoded header
    :rtype: str
    """
    decoded_words = decode_header(encoded_string)
    word = [w for w in decoded_words if w][0]

    string_like = word[0]  # may be bytes or str

    if isinstance(string_like, str):
        return string_like

    return string_like.decode(word[1])


def fetch_mails():
    """Return mails of the inbox sorted by date.

    Sort :py:func:`iter_mails` by ``getattr('date')``.  Note that the
    latter might differ from the actual ``"From:"``-header of the
    mail.

    :returns: A sorted list of mails
    :rtype: list
    """
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


def iter_attachments(index):
    """Iterate over a mail's attachments

    :param index: The index of the mail.

    :returns: An iterator over the MIME-parts where ``get_filename()``
              evaluates to ``True``
    :rtype: iterator[part]
    """
    mail_string = list(fetch_mails())[index].content
    mail = message_from_string(mail_string)
    for part in mail.walk():
        filename = part.get_filename()
        if not filename:
            continue
        yield part


def show_attachments(index):
    for attachment in iter_attachments(index):
        print("{name:=^80}".format(name=attachment.get_filename()))
        print("Is multipart:", ("no", "yes")[attachment.is_multipart()])
        print()

        payload = attachment.get_payload(decode=True)
        # ``decode=True`` only decodes the base64
        file_string = payload.decode('utf-8')
        print(file_string)


def save_attachment(attachment, path, name_converter=None):
    """Save an attachment in a given folder

    Writes the Message payload to a file of name 'path' to the
    filename.

    :param Message attachment: The Mime-Part containing the
        attachment.
    :param str path: The path to the folder to save the attachments
        in.
    :param callable name_converter: A callable converting the filename
    """
    filename = attachment.get_filename()
    if name_converter is not None:
        filename = name_converter(filename)
    full_path = os.path.join(path, filename)

    print("Writing to '{}'…".format(full_path))
    with open(full_path, 'wb') as fd:
        fd.write(attachment.get_payload(decode=True))


def save_attachments_of_person(index, person):
    """The main subroutine for saving a person's attachments

    :param int index: The message's index
    :param str person: The name of the person folder to use
    """
    if not person:
        print("Person missing")
        exit(1)

    path = os.path.join(person, current_round)

    for attachment in iter_attachments(index):
        save_attachment(attachment, path=path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract mail.")
    parser.add_argument("command")
    parser.add_argument("-i", "--index", type=int, help="The mail to select")
    parser.add_argument("-p", "--person", type=str, help="The person folder to use ")

    args = {param: value for param, value in parser.parse_args().__dict__.items()
            if value}
    command = args.pop('command')

    command_mapping = {
        'list': list_mails,
        'show_files': show_attachments,
        'save_files': save_attachments_of_person,
    }

    try:
        subcommand = command_mapping[command]
    except KeyError:
        print("Invalid command:", command)
        print("Available:", ", ".join(command_mapping.keys()))
        exit(1)

    try:
        subcommand(**args)
    except TypeError as e:
        error_string = e.args[0]
        if "unexpected keyword argument" in error_string:
            print("Unexpected argument:", error_string)
        elif "missing" in error_string:
            print("Missing argument:", error_string)
