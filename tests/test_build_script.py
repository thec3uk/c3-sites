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


def test_theme_redirects_come_before_generated_ones(tmp_path):
    # Extracts build.sh's merge step and runs it in a scratch tree.
    script = (ROOT / "scripts/build.sh").read_text()
    start = script.index('generated_redirects="$(mktemp)"')
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/_redirects").write_text("/give https://pay.example 301\n")
    public = tmp_path / "themes/x/public"
    public.mkdir(parents=True)
    (public / "_redirects").write_text("/moodle/* https://moodle.example/:splat 200!\n")

    subprocess.run(["bash", "-c", "SITE=x\n" + script[start:]], cwd=tmp_path, check=True)

    assert (tmp_path / "dist/_redirects").read_text() == (
        "/moodle/* https://moodle.example/:splat 200!\n/give https://pay.example 301\n"
    )


def test_generated_redirects_stand_alone_without_theme_rules(tmp_path):
    script = (ROOT / "scripts/build.sh").read_text()
    start = script.index('generated_redirects="$(mktemp)"')
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/_redirects").write_text("/give https://pay.example 301\n")

    subprocess.run(["bash", "-c", "SITE=x\n" + script[start:]], cwd=tmp_path, check=True)

    assert (tmp_path / "dist/_redirects").read_text() == "/give https://pay.example 301\n"


def run_merge(tmp_path, site):
    script = (ROOT / "scripts/build.sh").read_text()
    start = script.index('generated_redirects="$(mktemp)"')
    subprocess.run(["bash", "-c", f"SITE={site}\n" + script[start:]], cwd=tmp_path, check=True)


def test_theme_redirects_without_a_trailing_newline_do_not_fuse_with_generated_ones(tmp_path):
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/_redirects").write_text("/give https://pay.example 301\n")
    public = tmp_path / "themes/x/public"
    public.mkdir(parents=True)
    (public / "_redirects").write_text("/a /b 301")

    run_merge(tmp_path, "x")

    assert (tmp_path / "dist/_redirects").read_text().splitlines() == ["/a /b 301", "/give https://pay.example 301"]


def test_main_theme_serves_gatsbys_root_files_and_the_sitemap_index_redirect(tmp_path):
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist/_redirects").write_text("/give https://pay.example 301\n")
    (tmp_path / "themes").mkdir()
    (tmp_path / "themes/main").symlink_to(ROOT / "themes/main")

    run_merge(tmp_path, "main")

    lines = (tmp_path / "dist/_redirects").read_text().splitlines()
    assert "/sitemap-index.xml /sitemap.xml 301" in lines
    assert "/give https://pay.example 301" in lines
    assert (tmp_path / "dist/card.jpg").is_file()
    assert (tmp_path / "dist/fonts/Gotcha-Regular.otf").is_file()
