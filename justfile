set dotenv-load

default: test

# Install Python and dependencies
setup:
    uv sync

test:
    uv run pytest

# Build one site to dist/, e.g. `just build academy`
build site="academy":
    SITE={{site}} uv run python manage.py distill generate --output-directory dist --collectstatic --force

# Local dev server for one site
serve site="academy":
    SITE={{site}} DJANGO_DEBUG=1 uv run python manage.py runserver
