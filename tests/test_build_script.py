import subprocess
from pathlib import Path

import pytest
from django.conf import settings


def test_build_skips_dev_dependencies():
    # Netlify runs build.sh; Playwright and pytest aren't needed there.
    script = (Path(settings.BASE_DIR) / "scripts/build.sh").read_text()

    assert "run --frozen --no-dev python manage.py distill generate" in script


ROOT = Path(settings.BASE_DIR)
THEME_CSS = sorted(ROOT.glob("themes/*/css/site.css"))
TAILWIND = ROOT / ".bin/tailwindcss-v4.3.3"


@pytest.mark.parametrize("css", THEME_CSS, ids=lambda p: p.parts[-3])
def test_each_theme_scans_only_its_own_sources(css):
    # Automatic detection scans the whole repo, so docs and tests leak classes in.
    assert '@import "tailwindcss" source(none);' in css.read_text()


@pytest.mark.skipif(not TAILWIND.exists(), reason="Tailwind binary is downloaded by scripts/build.sh")
def test_academy_css_has_no_classes_from_docs(tmp_path):
    out = tmp_path / "site.css"
    subprocess.run([TAILWIND, "-i", ROOT / "themes/academy/css/site.css", "-o", out], check=True, capture_output=True)
    css = out.read_text()

    # min-h-90 only appears in docs/plans/phase-3/evidence/m2/NOTES.md and main's theme.
    assert ".min-h-90" not in css
    assert ".text-purple-trans" in css  # used by Academy's own template
