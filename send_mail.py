import mimetypes
import os
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from smtplib import SMTP

from config import GLOBAL_FOLDER_NAME, GLOBAL_MAIL_NAME, GLOBAL_FILENAME, \
    GRADING_FILENAME, get_person_mail
from secret import pw as PASSWORD, login as USERNAME


def format_mail(person, round, email=None):
    if email is None:
        email = get_person_mail(person)
        if not email:
            print("{} has no Mail!".format(person))
            exit(1)

    message = MIMEMultipart()

    mail_filename = os.path.join(GLOBAL_FOLDER_NAME, round, GLOBAL_MAIL_NAME)
    with open(mail_filename) as file:
        message.attach(MIMEText(file.read()))

    from_ = "Lukas Juhrich <lukas.juhrich@tu-dresden.de>"
    message['From'] = from_
    message['CC'] = from_
    message['Subject'] = "Bewertung {}".format(round)
    message['To'] = email
    message['X-Grading-Round'] = round

    specific_filename = os.path.join(person, round, GRADING_FILENAME)
    with open(specific_filename) as file:
        message.attach(MIMEText(file.read()))

    global_remarks_filename = os.path.join(GLOBAL_FOLDER_NAME, round, GLOBAL_FILENAME)
    with open(global_remarks_filename) as file:
        message.attach(MIMEText(file.read()))

    fixed_dir = os.path.join(person, round, 'fixed')

    for filename in os.listdir(fixed_dir):
        path = os.path.join(fixed_dir, filename)
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
        message.attach(msg)

    s = SMTP('msx.tu-dresden.de', port=587)
    # s.set_debuglevel(1)
    s.starttls()
    s.login(USERNAME, PASSWORD)
    s.send_message(message, from_addr=from_, to_addrs=[email, from_])
