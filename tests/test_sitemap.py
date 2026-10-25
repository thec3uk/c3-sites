from xml.etree import ElementTree

from config.urls import urlpatterns

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def test_route_writes_sitemap_xml():
    pattern = next(p for p in urlpatterns if p.name == "sitemap")

    assert pattern.distill_file == "sitemap.xml"


def test_lists_every_page_with_the_sites_absolute_url(main, client):
    response = client.get("/sitemap.xml")

    assert response["Content-Type"].startswith("application/xml")
    urls = [e.text for e in ElementTree.fromstring(response.content).findall("s:url/s:loc", NS)]
    assert urls == ["https://thec3.uk/", "https://thec3.uk/about/"]


def test_redirects_and_data_documents_are_not_listed(main, client):
    main.append({"id": "r", "type": "redirect", "uid": "give", "tags": [], "data": {"destination": {}}})

    assert "give" not in client.get("/sitemap.xml").content.decode()


def test_main_robots_txt_points_at_the_sitemap():
    from pathlib import Path

    from django.conf import settings

    robots = (Path(settings.BASE_DIR) / "themes/main/public/robots.txt").read_text()

    assert "Sitemap: https://thec3.uk/sitemap.xml" in robots.splitlines()
