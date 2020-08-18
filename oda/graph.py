import rdflib # type: ignore

import logging

logger = logging.getLogger("graph")

def lengthen(t, G):    
 #   print("lengthening",t, type(t))
    
    if type(t) in (rdflib.term.URIRef, rdflib.term.Literal, rdflib.term.BNode):
        return t
    
    ns,tm = t.split(":")
    
    ns = str(dict(G.namespaces())[ns])
    
    if not ns.endswith("#"):
        ns = ns+"#"
    
    return rdflib.term.URIRef(ns+tm)
    

def subgraph_from(G, t, nG=None):
    if nG is None:
        nG = rdflib.Graph()
        ns_rmap = {u.toPython():a for a,u in G.namespaces()}
        for a,b in ns_rmap.items():
            nG.bind(b,a)

    t = lengthen(t, G)
    logger.debug(repr(t))

    
    #if lengthen(t, G) in nG.predicates():
    #    return
        
                
    for p, o in G.predicate_objects(t):
        logger.debug("%s ... %s %s",t,p,o)                
        
        nG.add([lengthen(t, G), p, o])
        
        nG = subgraph_from(G, p, nG)
        nG = subgraph_from(G, o, nG)

    return nG

    
