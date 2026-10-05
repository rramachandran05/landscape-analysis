import datetime as dt

from landscape.models import DateWindow, Record


def test_date_window_contains():
    w = DateWindow(since="2023-01", until="2023-06")
    assert w.contains("2023-03-15T00:00:00Z")
    assert w.contains("2023-01-01")
    assert w.contains("2023-06-30")
    assert not w.contains("2022-12-31")
    assert not w.contains("2023-07-01")
    assert w.contains(dt.date(2023, 4, 1))


def test_date_window_unbounded_and_unparseable():
    assert DateWindow().contains("whatever")  # no bounds -> everything in
    # unparseable date with bounds -> treated as inside (tool never silently drops)
    assert DateWindow(since="2023").contains("n/a")


def test_year_bound_with_int():
    w = DateWindow(since="2020", until="2022")
    assert w.contains(2021)
    assert not w.contains(2019)
    assert not w.contains(2023)


def test_record_to_dict_drops_transient_and_keeps_agent_defaults():
    r = Record(id="arXiv:1", title="t", pdf_url="http://x/p.pdf")
    d = r.to_dict()
    assert "pdf_url" not in d  # transient, never persisted
    assert d["status"] == "raw"
    assert d["dimensions"] == {}
    assert d["cluster_id"] is None


def test_record_roundtrip_ignores_unknown_keys():
    d = {"id": "x", "title": "t", "bogus": 1, "status": "curated"}
    r = Record.from_dict(d)
    assert r.id == "x" and r.status == "curated"
