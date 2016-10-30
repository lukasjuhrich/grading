import os
import subprocess
from datetime import datetime

from yaml import dump, load

CONFIG_FILENAME = '.grade'


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
        filename = os.path.join(person, round_name, 'remarks.org')
        # creates the file
        open(filename, 'a').close()
        subprocess.call('git', 'add', filename)

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
