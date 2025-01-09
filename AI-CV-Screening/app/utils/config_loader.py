import configparser
import os

class Config:
    _config = None

    @classmethod
    def load_config(cls, filepath="config.ini"):
        if cls._config is None:
            cls._config = configparser.ConfigParser()
            cls._config.read(filepath)
        return cls._config

    @classmethod
    def get(cls, section, key, fallback=None):
        if cls._config is None:
            cls.load_config()
        return cls._config.get(section, key, fallback=fallback)

    @classmethod
    def getboolean(cls, section, key, fallback=None):
        if cls._config is None:
            cls.load_config()
        return cls._config.getboolean(section, key, fallback=fallback)
