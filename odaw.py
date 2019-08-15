import json
import os
import requests
import time
from collections import OrderedDict

from diskcache import Cache

cache = Cache('data/default-cache')
enable_cache = False

try:
    logstash_entrypoint = os.environ.get("LOGSTASH_ENTRYPOINT", open("/cdci-resources/logstash-entrypoint").read().strip())

    import logstash
    logstasher = logstash.LogStasher(logstash_entrypoint)
except Exception as e:
    print("unable to setup logstash",repr(e))

    logstasher = None

try:
    import sentry_sdk
    sentry_sdk.init(os.environ.get("SENTRY_URI", open("/cdci-resources/sentry-uri").read().strip()))
except ImportError:
    sentry_sdk = None
except Exception as e:
    print("big problem with sentry:",repr(e))
    sentry_sdk = None


def get_workflow_url(workflow):
    workflow_routes = dict([ r.split("=") for r in os.environ.get('WORKFLOW_ROUTES','').split(",") if len(r.split("=")) == 2 ])

    if workflow in workflow_routes:
        return workflow_routes[workflow]+"/api/v1.0/get/{}"

    if workflow in os.environ.get('STAGING_WORKFLOWS','').split(','):
        return "https://oda-workflows-"+workflow+"-staging.odahub.io/api/v1.0/get/{}"
    else:
        return "https://oda-workflows-"+workflow+".odahub.io/api/v1.0/get/{}"
    

def evaluate(router, *args, **kwargs):
    key = json.dumps((router, args, OrderedDict(sorted(kwargs.items()))))


    if logstasher:
        logstasher.set_context(dict(router=router, args=args, kwargs=kwargs))
        logstasher.log(dict(event='starting'))

    if enable_cache and key in cache:
        v = cache.get(key)
        print("restored from cache, key:", key)
        print("restored from cache, value:", v)

        if v == {} or v is None:
            print("this value is empty, regenerate")
        else:
            return v

    if router == "odahub":
        kwargs['_async_request'] = 'yes'

        url_template = get_workflow_url(args[0])

        url = url_template.format(*args[1:])
        print("url:",url)

        ntries = 30
        while ntries > 0:
            try:
                print("towards",ntries,url,kwargs)
                c=requests.get(
                    url=url,
                    params=kwargs,
                    auth=requests.auth.HTTPBasicAuth("cdci", open("/cdci-resources/reproducible").read().strip())
                )
                print("decoding text",c.text[:1000])

                try:
                    raw = c.json()
                    output = raw.get('output', raw['data']['output'])
                except Exception as ed:
                    print("problem decoding:", repr(ed))
                    print("raw output:",c.text)
                    logstasher.log(dict(event='failed to decode output',raw_output=c.text, exception=repr(ed)))
                    raise

                if raw.get('workflow_status') == "done":
                    print("done, status", raw.get('workflow_status'))
                    print("keys in raw", raw.keys())
                    print("output",repr(output))
                    break
                else:
                    print("not done", raw.get('workflow_status'))

            except Exception as e:
                print("problem from service", repr(e))

                logstasher.log(dict(event='problem evaluating',exception=repr(e)))
                
            if ntries <= 1:
                if sentry_sdk:
                    sentry_sdk.capture_exception()
                raise

            time.sleep(5)

            ntries -= 1

                #raise
    else:
        raise NotImplemented


    if logstasher:
        logstasher.log(dict(event='done'))

    cache.set(key, output)
    print("stored to cache", key)

    return output

