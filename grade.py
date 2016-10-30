#!/usr/bin/env python3
"""

grade.py
~~~~~~~~

© Lukas Juhrich.

"""
# pylint: disable=invalid-name
import argparse
import os
from email import message_from_string

from config import sample_config, add_person, delete_persons, add_round, close_round
from mail import save_attachment, fetch_mails, nice_header, iter_attachments

ROUND = 'Uebung01'
current_round = ROUND


def list_mails():
    """List all available mails in the inbox."""
    for i, mail in enumerate(fetch_mails()):
        message = message_from_string(mail.content)

        subject = nice_header(message.get('subject', "<no subject>"))
        sender = message.get('From', "<no sender>")
        print("{:2d} {date} {sender} »{subj}«"
              .format(i, date=mail.date, sender=sender, subj=subject))


def show_attachments(index):
    """Show all attachments of a given mail

    :param int index: the index of the mail
    """
    for attachment in iter_attachments(index):
        print("{name:=^80}".format(name=attachment.get_filename()))
        print("Is multipart:", ("no", "yes")[attachment.is_multipart()])
        print()

        payload = attachment.get_payload(decode=True)
        # ``decode=True`` only decodes the base64
        file_string = payload.decode('utf-8')
        print(file_string)


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


def init():
    sample_config()
    print("You can now start adding persons either manually or using this program.")


def add_persons(*persons):
    for person in persons:
        try:
            os.mkdir(person)
        except FileExistsError:
            print("Folder for person {} already exists".format(person))
        except OSError:
            print("Error creating person '{}'".format(person))
            continue
        add_person(person)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract mail.")
    parser.add_argument("command")
    parser.add_argument("-i", "--index", type=int, help="The mail to select")
    parser.add_argument("-p", "--person", type=str, help="The person folder to use ")

    parsed, unknown = parser.parse_known_args()
    args = {param: value for param, value in parsed.__dict__.items() if value}
    unknown = [arg for arg in unknown if not arg.startswith('-')]

    command = args.pop('command')

    command_mapping = {
        'init': init,
        'list': list_mails,
        'show_files': show_attachments,
        'save_files': save_attachments_of_person,
        'add_persons': add_persons,
        'delete_persons': delete_persons,
        'add_round': add_round,
        'close_round': close_round,
    }

    try:
        subcommand = command_mapping[command]
    except KeyError:
        print("Invalid command:", command)
        print("Available:", ", ".join(command_mapping.keys()))
        exit(1)

    try:
        subcommand(*unknown, **args)
    except TypeError as e:
        error_string = e.args[0]
        if "unexpected keyword argument" in error_string:
            print("Unexpected argument:", error_string)
        elif "missing" in error_string:
            print("Missing argument:", error_string)
