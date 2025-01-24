import configparser
import os

class Config:
    _config = None

    @classmethod
    def load_config(cls, filepath="config.ini"):
        """Loads the config file."""
        if cls._config is None:
            cls._config = configparser.ConfigParser()
            cls._config.read(filepath)
        return cls._config

    @classmethod
    def get(cls, section, key, fallback=None):
        """Fetches a value from the config."""
        if cls._config is None:
            cls.load_config()
        return cls._config.get(section, key, fallback=fallback)

    @classmethod
    def getboolean(cls, section, key, fallback=None):
        """Fetches a boolean value from the config."""
        if cls._config is None:
            cls.load_config()
        return cls._config.getboolean(section, key, fallback=fallback)
