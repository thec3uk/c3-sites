"""Raw Prismic documents for main-theme tests."""

BANNER_IMAGE = "https://images.prismic.io/thec3/banner.jpg?auto=format,compress"
SEO_IMAGE = "https://images.prismic.io/thec3/seo.jpg?auto=format,compress"


def image(url):
    return {"dimensions": {"width": 1200, "height": 800}, "alt": None, "url": url}


def page_doc(uid, **data):
    data = {"seo_title": None, "seo_description": None, "seo_image": {}, "body": [], **data}
    return {"id": uid, "type": "page", "uid": uid, "tags": ["domain:thec3.uk"], "data": data}


def link_list(title, *links):
    return {
        "slice_type": "link_list",
        "primary": {"title": title},
        "items": [{"link_title": text, "link_url": url} for text, url in links],
    }


def banner_doc(active):
    return {
        "id": "banner",
        "type": "notification_banner",
        "uid": None,
        "tags": ["domain:thec3.uk"],
        "data": {
            "content": "Global Leadership Summit 2026",
            "url": {"link_type": "Web", "url": "http://www.thec3.uk/gls"},
            "active": active,
        },
    }


def main_documents():
    """Home and about pages, site_config and static_footer for thec3.uk."""
    return [
        page_doc(
            "thec3.uk",
            seo_title="Welcome Home",
            seo_description="A church with locations in Cambridge",
            seo_image=image(SEO_IMAGE),
        ),
        page_doc("thec3.uk_about"),
        {
            "id": "cfg",
            "type": "site_config",
            "uid": None,
            "tags": ["domain:thec3.uk"],
            "data": {
                "title": "The C3 Church",
                "description": "The C3 Church is a church.",
                "twitter_username": "@thec3_church",
                "banner": image(BANNER_IMAGE),
            },
        },
        {
            "id": "footer",
            "type": "static_footer",
            "uid": None,
            "tags": ["domain:thec3.uk"],
            "data": {
                "body": [
                    link_list(
                        "Our Church",
                        ("about", {"link_type": "Document", "type": "page", "uid": "thec3.uk_about"}),
                        ("leaders", {"link_type": "Document", "type": "page", "uid": "ourleaders"}),
                    ),
                    link_list("Our Network", ("Breathe", {"link_type": "Web", "url": "https://breathe.thec3.uk"})),
                ]
            },
        },
    ]
