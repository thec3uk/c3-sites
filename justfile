set dotenv-load

default: test

# Install Python and dependencies
setup:
    uv sync

test:
    uv run pytest

# Build one site to dist/, e.g. `just build academy`
build site="academy":
    scripts/build.sh {{site}}

# Local dev server for one site
serve site="academy":
    SITE={{site}} DJANGO_DEBUG=1 uv run python manage.py runserver
