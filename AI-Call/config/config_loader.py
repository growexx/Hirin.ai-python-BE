import configparser

class ConfigLoader:
    def __init__(self, config_file: str = "config.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get(self, section: str, key: str, fallback=None):
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            if fallback is not None:
                return fallback
            raise KeyError(f"Key '{key}' not found in section '{section}'")
