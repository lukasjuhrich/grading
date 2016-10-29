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
    write_config({'persons': [], 'rounds': []})



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
