#TODO versions!

import json
import os
import base64
import requests
import time
import rdflib # type: ignore
import tempfile
import itertools
import hashlib
from collections import OrderedDict

import oda.cache as cache

from oda.exceptions import WorkflowIncomplete 

from oda.graph import subgraph_from

import odakb.sparql  # type: ignore
from odakb.sparql import load_graph, parse_shortcuts


#import oda.sentry as sentry

import pkgutil

from oda.logs import log, warn, log_context
            
import importlib

# find by ontology
    # Workflow-function signature (https://w3id.org/function/spec/)
    # Workflow heritage (class hierarchy)
    # Structural relations (module)
    # Workflow history (git commit history)
    # Induced by node content(e.g. methods used)
    # Embedding in the literature (“is useful in Crab”)
    # Explicit developer intent annotation

# evaluation is done by reasoner:
#  something is dataanalysis, has all parameters =>
#       equivalence of data        



def find_worflow_route_modules():
    workflow_modules = [m for m in pkgutil.iter_modules() if m.name.startswith("oda") and m.name != "oda"]
    log("oda workflow modules: %s", workflow_modules)
    return workflow_modules



def evaluate_graph(target, *graphs):
    """
    """

    G = rdflib.ConjunctiveGraph()  
    #G = rdflib.Graph()  

    #get_default_graphs(G)
    odakb.sparql.process_graph_loaders(G)

    for graph in graphs:
        print("loading local graph", graph)
        load_graph(G, graph)

    print("will load standard assumption")
    load_graph(G, "local:{t} rdfs:subClassOf an:{t} .".format(t=target))

    G.serialize("debug.ttl", format="turtle")

    for c in G.quads():
        print("quad:", c)

    q = "SELECT ?parent_analysis WHERE {{ local:{} rdfs:subClassOf ?parent_analysis . }}".format(target)
    print(q)

    parentname=None
    for s, in G.query(q):
        parent = s.toPython()
        log("useful parent: %s",parent)
        parentns, parentname = parent.split("#")

    if parentname is None:
        warn("no useful parent for {}!".format(target))
        return
            
    #for url_uri in G.query("""SELECT DISTINCT ?url WHERE {an:%s an:url ?url}"""%parentname):
    #    url = url_uri[0].toPython()
    #    log("url: %s", url)
    
    workflows=[]

    for uri in G.query("""
            SELECT DISTINCT ?workflowClass WHERE {
                an:%s rdfs:subClassOf ?workflowClass .
                ?workflowClass rdfs:subClassOf an:Workflow .
            }
        """%parentname):

        workflowClass = uri[0].toPython()

        print("found workflowClass", workflowClass)

        workflows.append(dict(parent="an:%s"%parentname, workflow_class=workflowClass))


    if workflows == []:
        raise Exception("no services found for", target, parentname)

    if len(workflows) == 0:
        raise Exception("no workflows found")
        
    if len(workflows) > 1:
        raise Exception("too many workflows found: %s"%str(workflows))
    
    workflow = workflows[0]

    params={}

    for param in G.query("""SELECT DISTINCT ?param WHERE {an:%s rdfs:subClassOf ?b . ?b owl:onProperty onto:expects . ?b owl:someValuesFrom ?param .}"""%parentname):
        ns, paramname = param[0].split("#")
        log("expects some values from: %s, %s", ns, paramname)
        
        for r in itertools.chain(G.query("""SELECT ?value WHERE {an:%s an:equalTo ?value .}"""%(paramname)),
                                 G.query("""SELECT ?value WHERE {local:%s an:equalTo ?value .}"""%(paramname)),
                                 G.query("""SELECT ?value WHERE {?a an:equalTo ?value . ?a rdfs:subClassOf an:%s .}"""%(paramname))):

            value = r[0].toPython()

            log("with value %s %s", r, value)

            params[paramname] = value
        
            if isinstance(r[0], rdflib.URIRef):# determine authority; local or remote
                name = r[0].split("#")[1] # assume local
                print("request to another defined graph", name)
                #evaluate_graph_workflow(qg, name)

    if workflow['workflow_class'] == "http://ddahub.io/ontology/analysis#odahubService":
        for uri in G.query("""
            SELECT DISTINCT ?odahubname WHERE {
                %s an:odahubService ?odahubname .
            }"""%workflow['parent']):

            odahub_service = uri[0].toPython()

            log("found comptatible odahub service: %s", odahub_service)
            break

        import odahub # type: ignore
        r = odahub.evaluate_retry(odahub_service, target, **params, _ntries=20)

    elif workflow['workflow_class'] == "http://ddahub.io/ontology/analysis#HTTPAnalysis":
        for uri in G.query("""
            SELECT DISTINCT ?url WHERE {
                %s oda:url ?url .
            }"""%workflow['parent']):

            url = uri[0].toPython()

            log("found url: \"%s\"", url)
            break

        c = requests.get(url, params=params)
        
        try:
            r = c.json()
        except Exception as e:
            print("failed to get json response %s"%(str(e)))
            r=dict(response_content=base64.b64encode(c.content).decode())

    r_str = json.dumps(r)

    r_h = hashlib.md5(r_str.encode('utf-8')).hexdigest()[:8]

    load_graph(G, "local:%s an:equalTo an:%s ."%(target, r_h))

    G.serialize(target+".ttl", format="turtle")

    nG = subgraph_from(G, ":"+target)
    nG.serialize(target+"-connected.ttl", format="turtle")
    
    

def extract_output_files(r):
    for k,v in r.items():
        if k+"_content" in r:
            try:
                bc = base64.b64decode(r[k+'_content'])
                open(v,"wb").write(bc)
            except Exception as e:
                print("problem decoding", k)
            else:
                print("writing", v)
    
def extract_output_json(r):
    o = {}

    for k,v in r.items():
        try:
            print("trying to decode json",k)
            o[k] = json.loads(v)
            print("decoded",o[k])
        except Exception as e:
            #print("failed to decode",e)
            o[k] = v

    return o

def evaluate(router, *args, **kwargs):
    if router == "graph":
        return evaluate_graph(*args)

    print("args", args)
    print("kwargs", kwargs)

    new_args=[]
    for arg in args:
        if "=" in arg:
            k,v = arg.split("=")
            kwargs[k] = v
            print("extracted kw arg", k, v)
        else:
            new_args.append(arg)

    args = new_args
        

    ntries = int(kwargs.pop('_ntries', 1)) # TODO: no need to have tries at this level

    _async_return = kwargs.get("_async_return", False)
    return_metadata = kwargs.get("_return_metadata", False)

    key = json.dumps((router, args, OrderedDict(sorted(kwargs.items()))))

    log_context(dict(router=router, args=args, kwargs=kwargs))

    if router.startswith("oda"):
        module_name = router
    else:
        module_name = 'oda'+router

    odamodule = importlib.import_module(module_name)

    output = None

    while ntries > 0:
        try:
            if hasattr(odamodule, 'evaluate'):
                r = odamodule.evaluate(*args, **kwargs)
            else:
                r = odamodule.evaluator.evaluate(*args, **kwargs)

            if return_metadata:
                metadata, output = r
            else:
                output = r

            break
        except WorkflowIncomplete as e:
            log("workflow incomplete: %s", e)
            
            if _async_return:
                raise
        except Exception as e:
            log(dict(event='problem evaluating',exception=repr(e)))

            if ntries <= 1:
                #if sentry_sdk:
                #    sentry_sdk.capture_exception()
                raise Exception(e)

        time.sleep(5)

        ntries -= 1

    if output is None or isinstance(output, str):
        print("output is string, something failed", output)
        return output

    extract_output_files(output)
    output = extract_output_json(output)

    log(dict(event='done'))

    if return_metadata:
        return metadata, output
    else:
        return output


def rdf():
    pass

#def apidocs():
#    if router == "odahub":
#        return requests.get("https://oda-workflows-fermilat.odahub.io/apispec_1.json").json()

def module():
    #symmetric interoperability with astroquery
    pass

