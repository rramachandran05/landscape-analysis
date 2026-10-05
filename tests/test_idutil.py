from landscape.idutil import (
    canonical_id,
    make_bibtex,
    normalize_arxiv_id,
    normalize_doi,
    normalize_repo,
)


def test_normalize_arxiv_id_variants():
    assert normalize_arxiv_id("http://arxiv.org/abs/2301.00001v2") == "2301.00001"
    assert normalize_arxiv_id("arXiv:2301.00001") == "2301.00001"
    assert normalize_arxiv_id("2301.00001") == "2301.00001"
    assert normalize_arxiv_id("cs.AI/0701001") == "cs.ai/0701001"
    assert normalize_arxiv_id(None) is None
    assert normalize_arxiv_id("not an id") is None


def test_normalize_doi_strips_prefixes():
    assert normalize_doi("https://doi.org/10.1/AbC") == "10.1/abc"
    assert normalize_doi("doi:10.1234/xyz") == "10.1234/xyz"
    assert normalize_doi("10.1234/xyz") == "10.1234/xyz"
    assert normalize_doi("nonsense") is None


def test_normalize_repo():
    assert normalize_repo("https://github.com/Owner/Repo") == "owner/repo"
    assert normalize_repo("Owner/Repo.git") == "owner/repo"
    assert normalize_repo("single") is None


def test_canonical_id_precedence():
    # arXiv beats DOI beats repo beats native.
    assert canonical_id(arxiv_id="2301.00001", doi="10.1/x") == "arXiv:2301.00001"
    assert canonical_id(doi="10.1/x", repo="o/r") == "doi:10.1/x"
    assert canonical_id(repo="o/r", source="github") == "github:o/r"
    assert canonical_id(source="zenodo", source_native_id="42") == "zenodo:42"


def test_bibtex_is_deterministic():
    bib1 = make_bibtex(
        entry_type="article", authors=["Ada Lovelace"], year=2023,
        title="On Foundation Models", venue_or_repo="J", doi="10.1/x",
    )
    bib2 = make_bibtex(
        entry_type="article", authors=["Ada Lovelace"], year=2023,
        title="On Foundation Models", venue_or_repo="J", doi="10.1/x",
    )
    assert bib1 == bib2
    assert "@article{Lovelace2023foundation" in bib1
    assert "doi = {10.1/x}" in bib1
