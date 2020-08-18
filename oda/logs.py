import logging
import coloredlogs # type: ignore
import os

from oda import logstash
logstasher = logstash.LogStasher()


def setup_logging():
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)

    root = logging.getLogger()

 #   handler = logging.StreamHandler()
 #   formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
 #   handler.setFormatter(formatter)
 #   root.addHandler(handler)

    coloredlogs.install(level="INFO", logger=root)

def log_context(context):
    if logstasher:
        logstasher.set_context(context)

def log(*args, **kwargs):
    level = kwargs.pop('level', logging.INFO)

    if isinstance(level, str):
        level = getattr(logging, level)

    if isinstance(args[0], dict):
        logging.getLogger().log(level, "%s; %s", repr(args), repr(kwargs))
    else:
        logging.getLogger().log(level, *args, **kwargs)

    if logstasher:
        logstasher.log(dict(event='starting'))

def warn(*args, **kwargs):
    log(*args, **kwargs, level=logging.WARNING)

setup_logging()
