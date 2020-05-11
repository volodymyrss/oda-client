def get_default_graphs(rG):
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

    for graph in graphs:
        load_graph(rG, graph)
        #open("{}.ttl".format(wn), "w").write(graphs[-1])

    return graphs
