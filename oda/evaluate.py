#TODO versions!

import json
import os
import requests
import time
import rdflib
import tempfile
import itertools
import hashlib
from collections import OrderedDict

import oda.cache as cache

from oda.exceptions import WorkflowIncomplete 

from oda.graph import subgraph_from

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

def get_default_graphs():
    graphs = []


    for odahub_workflow in "oda-image", "integral-visibility", "integral-observation-summary":
        url_base = "https://oda-workflows-{}.odahub.io".format(odahub_workflow)
        graphs.append(url_base + "/api/v1.0/rdf")
    
        G = rdflib.Graph()

        print("will load", graphs[-1])
        load_graph(G, graphs[-1])

        for w in G.query("SELECT ?w WHERE { ?w rdfs:subClassOf anal:WebDataAnalysis }"):
            wns, wn = w[0].toPython().split("#")

            log("in %s found %s", odahub_workflow, wn)
            graphs.append("an:"+wn+" an:url \""+url_base+"/api/v1.0/get/"+wn+"\" .")
            graphs.append("an:"+wn+" an:odahubService \""+odahub_workflow+"\" .")

    return graphs


default_prefix="""
@prefix an: <http://ddahub.io/ontology/analysis#> .
@prefix onto: <https://w3id.org/function/ontology#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

@prefix : <http://local#> .

"""

def parse_shortcuts(graph_serial):
    g = graph_serial.replace("="," an:equalTo ")
    if not g.strip().endswith("."):
        g += " ."

    return g

def load_graph(G, serial):
    if serial.startswith("https://"):
        G.load(serial)
    else:
        log("will load: %s", serial, level="DEBUG")
        G.parse(
            data=default_prefix + parse_shortcuts(serial), 
            format="turtle"
        )

def evaluate_graph(target, *graphs):
    """
    """

    G = rdflib.Graph()

    for graph in list(graphs) + list(get_default_graphs()):
        print("will load", graph)
        load_graph(G, graph)
    
    load_graph(G, ":{t} rdfs:subClassOf an:{t} .".format(t=target))

    q = "SELECT ?parent_analysis WHERE { :%s rdfs:subClassOf ?parent_analysis . }"%target
    print(q)

    parentname=None
    for s, in G.query(q):
        parent = s.toPython()
        log("useful parent: %s",parent)
        parentns, parentname = parent.split("#")

    if parentname is None:
        warn("no useful parent!")
        return
            
    for url_uri in G.query("""SELECT DISTINCT ?url WHERE {an:%s an:url ?url}"""%parentname):
        url = url_uri[0].toPython()
        log("url: %s", url)
    
    odahub_services = []

    for uri in G.query("""SELECT DISTINCT ?url WHERE {an:%s an:odahubService ?url}"""%parentname):
        odahub_service = uri[0].toPython()
        log("found comptatible odahub service: %s", odahub_service)
        odahub_services.append(odahub_service)

    if odahub_services == []:
        raise Exception("no services found for", target, parentname)

    params={}
    
    for param in G.query("""SELECT DISTINCT ?param WHERE {an:%s rdfs:subClassOf ?b . ?b owl:onProperty onto:expects . ?b owl:someValuesFrom ?param .}"""%parentname):
        ns, paramname = param[0].split("#")
        log("expects some values from: %s, %s", ns, paramname)
        
        for r in itertools.chain(G.query("""SELECT ?value WHERE {an:%s an:equalTo ?value .}"""%(paramname)),
                                 G.query("""SELECT ?value WHERE {:%s an:equalTo ?value .}"""%(paramname)),
                                 G.query("""SELECT ?value WHERE {?a an:equalTo ?value . ?a rdfs:subClassOf an:%s .}"""%(paramname))):

            value = r[0].toPython()

            log("with value %s %s", r, value)

            params[paramname] = value
        
            if isinstance(r[0], rdflib.URIRef):# determine authority; local or remote
                name = r[0].split("#")[1] # assume local
                print("request to another defined graph", name)
                #evaluate_graph_workflow(qg, name)

    import odahub
    r = odahub.evaluate_retry(odahub_service, target, **params)

    r_str = json.dumps(r)

    r_h = hashlib.md5(r_str.encode('utf-8')).hexdigest()[:8]

    load_graph(G, ":%s an:equalTo an:%s ."%(target, r_h))

    G.serialize(target+".ttl", format="turtle")

    nG = subgraph_from(G, ":"+target)
    nG.serialize(target+"-connected.ttl", format="turtle")
    
    

    

def evaluate(router, *args, **kwargs):
    if router == "graph":
        return evaluate_graph(*args)    

    ntries = 100

    _async_return = kwargs.get("_async_return", False)

    key = json.dumps((router, args, OrderedDict(sorted(kwargs.items()))))

    log_context(dict(router=router, args=args, kwargs=kwargs))

    if router.startswith("oda"):
        module_name = router
    else:
        module_name = 'oda'+router

    odamodule = importlib.import_module(module_name)

    while ntries > 0:
        try:
            output = odamodule.evaluate(*args, **kwargs)
            break
        except WorkflowIncomplete as e:
            log("workflow incomplete:", e)
            
            if _async_return:
                raise
        except Exception as e:
            log(dict(event='problem evaluating',exception=repr(e)))

        if ntries <= 1:
            #if sentry_sdk:
            #    sentry_sdk.capture_exception()
            raise

        time.sleep(5)

        ntries -= 1

    log(dict(event='output is None'))

    log(dict(event='done'))

    return output


def rdf():
    pass

def apidocs():
    if router == "odahub":
        return requests.get("https://oda-workflows-fermilat.odahub.io/apispec_1.json").json()

def module():
    #symmetric interoperability with astroquery
    pass

