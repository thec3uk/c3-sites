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
