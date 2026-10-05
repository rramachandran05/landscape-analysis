from landscape.sources.openalex import _reconstruct_abstract, _best_pdf


def test_reconstruct_abstract_orders_by_position():
    inverted = {"Foundation": [0], "models": [1, 4], "scale": [2], "well": [3]}
    assert _reconstruct_abstract(inverted) == "Foundation models scale well models"


def test_reconstruct_abstract_empty():
    assert _reconstruct_abstract(None) == ""
    assert _reconstruct_abstract({}) == ""


def test_best_pdf_prefers_oa_location():
    work = {
        "best_oa_location": {"pdf_url": "http://x/a.pdf", "is_oa": True},
        "primary_location": {"pdf_url": "http://x/b.pdf"},
    }
    url, is_oa = _best_pdf(work)
    assert url == "http://x/a.pdf" and is_oa is True


def test_best_pdf_none_when_closed():
    work = {"primary_location": {"pdf_url": None}, "open_access": {"is_oa": False}}
    url, is_oa = _best_pdf(work)
    assert url == "" and is_oa is False
