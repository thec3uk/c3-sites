from scripts.parity_check import normalise_link

HOSTS = {"thec3.uk", "127.0.0.1:8000"}


def test_same_site_links_compare_without_trailing_slash():
    assert normalise_link("https://thec3.uk/about", HOSTS) == "/about"
    assert normalise_link("http://127.0.0.1:8000/about/", HOSTS) == "/about"
    assert normalise_link("http://127.0.0.1:8000/", HOSTS) == "/"


def test_query_and_fragment_kept():
    assert normalise_link("https://thec3.uk/contact/?a=1#form", HOSTS) == "/contact?a=1#form"


def test_other_sites_unchanged():
    assert normalise_link("https://prayer.thec3.uk/", HOSTS) == "https://prayer.thec3.uk/"
