import configparser
import os

DEFAULT_CONFIG_FILE = 'config.ini'


def create_default_config(config_file: str = DEFAULT_CONFIG_FILE):
    print('Creating a default config file...')

    # Create a ConfigParser object
    config = configparser.ConfigParser()

    # Add sections and key-value pairs
    config['DEFAULT']['UpdateInterval'] = '30'  # Update interval in minutes

    # Write the INI file
    with open(config_file, 'w') as configfile:
        config.write(configfile)
        print('Config file created:', config_file)


def read_config_value(key: str, section: str = 'DEFAULT', config_file: str = DEFAULT_CONFIG_FILE) -> str:
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    # Check if the INI file exists
    if not os.path.exists(config_file):
        print('Config file does not exist.')
        create_default_config(config_file)

    # Read the INI file
    config.read(config_file)

    # Get a value from the INI file
    return config[section][key]


def write_config_value(key: str, value: str, section: str = 'DEFAULT', config_file: str = DEFAULT_CONFIG_FILE):
    # Create a ConfigParser object
    config = configparser.ConfigParser()

    # Check if the INI file exists
    if not os.path.exists(config_file):
        print('Config file does not exist.')
        print('Creating a default config file...')
        create_default_config(config_file)

    # Read the INI file
    config.read(config_file)

    # Set a value in the INI file
    config[section][key] = value

    # Write the INI file
    with open(config_file, 'w') as configfile:
        config.write(configfile)
