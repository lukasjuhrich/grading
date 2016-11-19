"""

mail.py
~~~~~~~

© Lukas Juhrich.

"""
# pylint: disable=invalid-name
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
    """return filepath fo thunderbird profile

    :param str profile: profile name
    :param str folder: Path to the inbox, relative to ``ImapMail``.

    :returns: The joined, absolute path
    :rtype: str
    """
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
    if not os.path.exists(path):
        os.makedirs(path)
    filename = attachment.get_filename()
    if name_converter is not None:
        filename = name_converter(filename)
    full_path = os.path.join(path, filename)

    print("Writing to '{}'…".format(full_path))
    with open(full_path, 'wb') as fd:
        fd.write(attachment.get_payload(decode=True))


ENCODINGS = ('utf-8', 'latin-1')
def attempt_decoding(payload):
    """Try to decode a bytes object by a list of encodings.

    :param bytes payload: the bytes object to decode

    :raises UnicodeDecodeError: If every decoding fails.

    :returns: The decoded string
    :rtype: str
    """
    for encoding in ENCODINGS:
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError("Every attempted encoding failed ('{}')"
                             .format("', '".join(ENCODINGS)))


def decode_attachment(attachment):
    """Try to decode an attachment.

    :param bytes attachment: an attachment

    :returns: The decoded attachment
    :rtype: str
    """
    # ``decode=True`` only decodes possible base64, returns bytes
    payload = attachment.get_payload(decode=True)
    try:
        return attempt_decoding(payload)
    except UnicodeDecodeError:
        print("Attachment '{}' could not be decoded".format(attachment.get_filename()))
        exit(1)
