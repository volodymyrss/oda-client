import  pytest

@pytest.mark.skip
def test_simple():
    import oda.evaluator as r
    r.evaluate_graph("image",
                """
    @prefix : <http://odahub.io/local/> .

    :image rdfs:subClassOf an:image;
        owl:onProperty onto:expects;
        owl:someValuesFrom :scwid .
    
    :scwid rdfs:subClassOf an:scwid;
        an:equalTo "032200220010.001" .

                """)

@pytest.mark.skip
def test_simplified():
    import oda.evaluator as r
    r.evaluate_graph("image",
                """
    local:scwid an:equalTo "122200220010.001" .
                """)


@pytest.mark.skip
def test_simplified_url():
    import oda.evaluator as r
    r.evaluate_graph("spiacs-online",
                """
    local:requeststring an:equalTo "3000.00 30" .
                """)

@pytest.mark.skip
def test_graph_from_arg():
    import oda.evaluator as r
    r.evaluate_graph("image",
                """
    local:scwid an:equalTo "122200220010.001" .
                """)

@pytest.mark.skip(reason="no way of currently testing this")
def test_deep2():
    import oda.evaluator as r
    r.evaluate("odahub",
               "oda-image",
                """
    ?image rdfs:subClassOf an:image;
        owl:onProperty onto:expects;
        owl:someValuesFrom ?scwid .
    
    ?scwid rdfs:subClassOf an:scwid;
        onto:hasValue ?scwid_from_time .

    ?scwid_from_time rdfs:subClassOf an:converttime;
        owl:onProperty onto:expects;

    owl:someValuesFrom "2019-01-01T11:11:11".
                """)
