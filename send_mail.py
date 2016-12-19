import mimetypes
import os
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from smtplib import SMTP

from config import GLOBAL_FOLDER_NAME, GLOBAL_MAIL_NAME, GLOBAL_FILENAME, \
    GRADING_FILENAME, config
from secret import pw as PASSWORD, login as USERNAME


def iter_folder_attachments(path):
    """Yield the contents of `path` as MIME messages"""
    for filename in os.listdir(path) if os.path.isdir(path) else []:
        path = os.path.join(path, filename)
        if not os.path.isfile(path) or path.endswith('~'):
            continue
        # Guess the content type based on the file's extension.  Encoding
        # will be ignored, although we should check for simple things like
        # gzip'd or compressed files.
        ctype, encoding = mimetypes.guess_type(path)
        if ctype is None or encoding is not None:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
            ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
        if maintype == 'text':
            with open(path) as fp:
                # Note: we should handle calculating the charset
                msg = MIMEText(fp.read(), _subtype=subtype)
        else:
            with open(path, 'rb') as fp:
                msg = MIMEBase(maintype, subtype)
                msg.set_payload(fp.read())
                # Encode the payload using Base64
            encoders.encode_base64(msg)
            # Set the filename parameter
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        yield msg


DEFAULT_SENDER = "Lukas Juhrich <lukas.juhrich@tu-dresden.de>"

def send_mail_to_person(person, subject, sender=DEFAULT_SENDER, attachments=None, args=None):
    email = config.get_person_mail(person)
    print("choosing mail:", email)
    if not email:
        print("{} has no Mail!".format(person))
        exit(1)

    message = MIMEMultipart()
    message['From'] = sender
    message['CC'] = sender
    message['Subject'] = subject
    message['To'] = email
    message['X-Delivered-By'] = 'grading'
    if args:
        for key, value in args.items():
            message[key] = value

    for attachment in attachments:
        message.attach(attachment)

    s = SMTP('msx.tu-dresden.de', port=587)
    # s.set_debuglevel(1)
    s.starttls()
    s.login(USERNAME, PASSWORD)
    print("email:", email)
    print("sender:", sender)
    print("message:", message)
    s.send_message(message, from_addr=sender, to_addrs=[email, sender])


def format_mail(person, round, email=None, sender=DEFAULT_SENDER):
    if email is None:
        email = config.get_person_mail(person)
        print("choosing mail:", email)
        if not email:
            print("{} has no Mail!".format(person))
            exit(1)

    attachments = []
    mail_filename = os.path.join(GLOBAL_FOLDER_NAME, round, GLOBAL_MAIL_NAME)
    with open(mail_filename) as file:
        attachments.append(MIMEText(file.read()))

    subject = "Bewertung {}".format(round)

    specific_filename = os.path.join(person, round, GRADING_FILENAME)
    with open(specific_filename) as file:
        attachments.append(MIMEText(file.read()))

    global_remarks_filename = os.path.join(GLOBAL_FOLDER_NAME, round, GLOBAL_FILENAME)
    with open(global_remarks_filename) as file:
        attachments.append(MIMEText(file.read()))

    for attachment in iter_folder_attachments(os.path.join(person, round, 'fixed')):
        attachments.append(attachment)

    send_mail_to_person(person, subject, sender,
                        attachments,
                        args={'X-Grading-Round': round})
