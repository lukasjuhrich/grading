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
GLOBAL_MAIL_NAME = 'mail.txt'
GLOBAL_FILENAME = "remarks.org"
GLOBAL_TEMPLATE = """\
Generelle Anmerkungen:
~~~~~~~~~~~~~~~~~~~~~~

* Tipps / Tricks

* Wichtige Dinge

* Kleinere Fehler

* Sonstiges

"""


class GradingConfig:
    """A class representing the YML config.

    Perhaps to be used as a singleton.
    """
    def __init__(self, filename=CONFIG_FILENAME):
        self.filename = filename
        self.config_dict = self._load_yml_config(filename)

    @staticmethod
    def _load_yml_config(filename):
        """Parse a file as yml and return the python object"""
        with open(filename) as stream:
            return load(stream)

    def _write_config(self):
        """Dump the config dict to :py:attr:`filename`"""
        with open(self.filename, 'w') as stream:
            stream.write(dump(self.config_dict, default_flow_style=False))

    def create_sample_config(self):
        """Create a sample config and write it.

        :raises: ValueError if config dict not empty
        """
        if self.config_dict:
            raise ValueError("Nonempty Config")

        self.config_dict = {'persons': {}, 'rounds': {}}
        self._write_config()

    def add_person(self, name, email=""):
        if name in self.config_dict['persons']:
            print("Person {} already exists, skipping.".format(name))

        self.config_dict['persons'][name] = email
        self._write_config()

    def delete_persons(self):
        self.config_dict['persons'] = {}
        self._write_config()


    def get_person_mail(self, person):
        return self.config_dict['persons'].get(person)

    @property
    def open_rounds(self):
        """Determine the number of open rounds.

        If more than one round is open, print an error message nad exit.

        :returns: The number of open rounds
        :rtype: int
        """
        # rounds = {'exercise01': {'opened': 0, 'closed': 0}}
        count = sum((not r.get('closed')) for r in self.config_dict['rounds'].values())

        if count > 1:
            print("Inconsistent config: More than one round open.")
            print("Aborting.")
            exit(1)
        return count

    @property
    def current_round_name(self):
        """Return the name of the currently open round"""
        # pylint: disable=pointless-statement
        self.open_rounds  # causes an exit if inconsistent

        names = [name for name, data in self.config_dict['rounds'].items()
                 if not 'closed' in data]
        return names.pop()



    def add_round(self, round_name):
        """Add a round given a name.

        Write it to the config setting ``opened`` to now.

        :param str round_name: The name of the new round
        """
        if self.open_rounds:
            print("Another round is open.")
            print("Aborting.")
            exit(1)

        self.config_dict['rounds'][round_name] = {'opened': datetime.now()}

        for person in self.config_dict['persons']:
            prepare_person_grading(person, round_name)

        prepare_global_grading(round_name)

        self._write_config()


    def close_round(self):
        """Close the currently open round.

        If no round is open, print an error message and exit.  Else, Write
        the close date to the config.
        """
        if not self.open_rounds:
            print("No round open!")
            print("Aborting.")
            exit(1)

        for name, data in self.config_dict['rounds'].items():
            if not data.get('closed'):
                self.config_dict['rounds'][name]['closed'] = datetime.now()

        self._write_config()



config = GradingConfig()


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

    filename = os.path.join(path, GLOBAL_FILENAME)
    with open(filename, 'w') as file:
        file.write(GLOBAL_TEMPLATE)
    subprocess.call(['git', 'add', filename])
