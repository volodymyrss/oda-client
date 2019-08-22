import logging
import os

from workflows import logstash
logstasher = logstash.LogStasher()


def setup_logging():
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)

    root = logging.getLogger()

    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def log(*args, **kwargs):
    level = kwargs.pop('level', logging.INFO)

    logging.getLogger().log(level, *args, **kwargs)

setup_logging()
