from config.urls import urlpatterns


def test_404_route_writes_404_html_and_expects_a_404_status():
    pattern = next(p for p in urlpatterns if p.name == "not-found")

    assert str(pattern.pattern) == "404.html"
    assert pattern.distill_file == "404.html"
    assert pattern.distill_status_codes == (404,)


def test_404_page_renders_with_404_status(documents, client):
    response = client.get("/404.html")

    assert response.status_code == 404
    assert "Page not found" in response.content.decode()


def test_academy_404_title_uses_the_plain_text_of_a_rich_text_site_title():
    from django.template.loader import render_to_string

    from content.models import Page, RichText

    title = RichText(({"type": "paragraph", "text": "The Academy", "spans": []},))
    config = Page(id="c", type="site_config", uid=None, url="/", fields={"title": title})

    html = render_to_string("404.html", {"site_config": config, "site": None})

    assert "<title>Page not found | The Academy</title>" in html
