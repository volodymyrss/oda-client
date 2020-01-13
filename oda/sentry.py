import os
import logging

try:
    import sentry_sdk
    sentry_sdk.init(os.environ.get("SENTRY_URI", open("/cdci-resources/sentry-uri").read().strip()))
except ImportError:
    sentry_sdk = None
except Exception as e:
    logging.debug("unable to load sentry:",repr(e))
    sentry_sdk = None
