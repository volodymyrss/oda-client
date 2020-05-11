


def test_odahub_pa():
    import oda

    oda.evaluate("odahub", "integral-visibility", "planning-advice", when_utc="2011-11-11T11:11:14", _ntries=10)

def test_odahub():
    import oda

    oda.evaluate("odahub", "integral-observation-summary", "status", when_utc="2011-11-11T11:11:15", _ntries=10)


def test_odahub_returning():
    import oda

    try:
        oda.evaluate("odahub", "integral-observation-summary", "status", when_utc="2011-11-11T11:11:15", _async_return=True)
    except Exception as e:
        assert isinstance(e, oda.exceptions.WorkflowIncomplete)

def test_odakb():
    import oda

    try:
        r = oda.evaluate("kb", "git@gitlab.astro.unige.ch:savchenk/oda-testworkflow.git", induce_fail=1)
    except Exception as e:
        assert 'FAILED to execute test' in e.args[0]
    else:
        raise Exception("did not fail")


