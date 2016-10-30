import os
import subprocess
from datetime import datetime

from yaml import dump, load

CONFIG_FILENAME = '.grade'
GRADING_FILENAME = 'grading.org'
GRADING_TEMPLATE = """\
# -*- mode: org; -*-

* Bewertung


* Ergebnis

#BEGIN result
a/10+1
#END result
"""

GLOBAL_FOLDER_NAME = "global"
GLOBAL_FILENAME = "remarks.org"
GLOBAL_TEMPLATE = """\
Generelle Anmerkungen:
~~~~~~~~~~~~~~~~~~~~~~

* Tipps / Tricks

* Wichtige Dinge

* Kleinere Fehler

* Sonstiges

"""


def load_config(file=CONFIG_FILENAME):
    with open(file) as stream:
        return load(stream)


def write_config(config, file=CONFIG_FILENAME):
    with open(file, 'w') as stream:
        stream.write(dump(config, default_flow_style=False))
    print("Config written to", file)


def sample_config():
    """Create a sample config"""
    write_config({'persons': [], 'rounds': {}})


def add_person(name):
    config = load_config()

    if name in config['persons']:
        print("Person {} already exists, skipping.".format(name))

    config['persons'].append(name)
    write_config(config)


def delete_persons():
    config = load_config()
    config['persons'] = []
    write_config(config)


def open_rounds():
    """Determine the number of open rounds.

    If more than one round is open, print an error message nad exit.

    :returns: The number of open rounds
    :rtype: int
    """
    config = load_config()
    # rounds = {'exercise01': {'opened': 0, 'closed': 0}}
    count = sum((not r.get('closed')) for r in config['rounds'].values())

    if count > 1:
        print("Inconsistent config: More than one round open.")
        print("Aborting.")
        exit(1)
    return count


def prepare_person_grading(person, round_):
    """Populate a folder with default grading files.

    Expect only the ``person`` folder to be present.  The ``round``
    folder is created if necessary.

    At the end, Stage the file with git.

    :param str person: The person
    :param str round_: The round
    """
    path = os.path.join(person, round_)
    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    filename = os.path.join(path, GRADING_FILENAME)
    with open(filename, 'w') as file:
        file.write(GRADING_TEMPLATE)
        print("Created", file.name)
    subprocess.call(['git', 'add', filename])


def prepare_global_grading(round_name):
    path = os.path.join(GLOBAL_FOLDER_NAME, round_name)
    try:
        os.makedirs(path)
    except FileExistsError:
        pass

    with open(os.path.join(path, GLOBAL_FILENAME), 'w') as file:
        file.write(GLOBAL_TEMPLATE)


def add_round(round_name):
    """Add a round given a name.

    Write it to the config setting ``opened`` to now.

    :param str round_name: The name of the new round
    """
    if open_rounds():
        print("Another round is open.")
        print("Aborting.")
        exit(1)

    config = load_config()
    config['rounds'][round_name] = {'opened': datetime.now()}

    for person in config['persons']:
        prepare_person_grading(person, round_name)

    prepare_global_grading(round_name)

    write_config(config)


def close_round():
    """Close the currently open round.

    If no round is open, print an error message and exit.  Else, Write
    the close date to the config.
    """
    if not open_rounds():
        print("No round open!")
        print("Aborting.")
        exit(1)

    config = load_config()
    for name, data in config['rounds'].items():
        if not data.get('closed'):
            config['rounds'][name]['closed'] = datetime.now()

    write_config(config)
