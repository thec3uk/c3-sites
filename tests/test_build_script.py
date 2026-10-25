from pathlib import Path

from django.conf import settings


def test_build_skips_dev_dependencies():
    # Netlify runs build.sh; Playwright and pytest aren't needed there.
    script = (Path(settings.BASE_DIR) / "scripts/build.sh").read_text()

    assert "run --frozen --no-dev python manage.py distill generate" in script
