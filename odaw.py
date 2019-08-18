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
    print("unable to setup logstash: ignoring",repr(e))

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
    print('exploiting workflow routes', os.environ.get('WORKFLOW_ROUTES',''))

    if os.environ.get('WORKFLOW_ROUTES'):
        workflow_routes = dict([ r.split("=") for r in os.environ.get('WORKFLOW_ROUTES','').split(",") ])
    else:
        workflow_routes = {}

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

        ntries = 100

        output = None

        while ntries > 0:
            try:
                print("towards",ntries,url,kwargs)
                c=requests.get(
                    url=url,
                    params={**kwargs, '_async_request': True},
                    auth=requests.auth.HTTPBasicAuth("cdci", open("/cdci-resources/reproducible").read().strip())
                )
                print("decoding",c.text)

                try:
                    c_j = c.json()
                    if c_j.get('workflow_status') != 'done':
                        time.sleep(5)
                        ntries -= 1
                        continue
                    output = c_j.get('data').get('output')
                except Exception as ed:
                    print("problem decoding:", repr(ed))
                    print("raw output:",c.text)
                    logstasher.log(dict(event='failed to decode output',raw_output=c.text, exception=repr(ed)))
                    raise

                break

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

    if logstasher and output is None:
        logstasher.log(dict(event='output is None'))

    if logstasher:
        logstasher.log(dict(event='done'))

    cache.set(key, output)
    print("stored to cache", key)

    return output

def evaluate_console():
    import argparse

    argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("router")
        
    args, ukargs = parser.parse_known_args()

    print(args, ukargs)

    pargs=[]
    kwargs={}
    for a in ukargs:
        if a.startswith("--"):
            k, v = a[2:].split("=", 1)
            kwargs[k] = v
        else:
            pargs.append(a)

    print(pargs, kwargs)
    
    return evaluate(args.router, *pargs, **kwargs)

def rdf():
    pass

def apidocs():
    pass


def module():
    pass

if __name__ == "__main__":
    evaluate_console()
