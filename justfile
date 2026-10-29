set dotenv-load

default: test

# Install Python and dependencies
setup:
    uv sync

test:
    uv run pytest

# Playwright tests against dist/; run `just build main` first
test-browser:
    uv run pytest -m browser

# Build one site to dist/, e.g. `just build academy`
build site="academy":
    scripts/build.sh {{site}}

# Local dev server for one site
serve site="academy":
    SITE={{site}} DJANGO_DEBUG=1 uv run python manage.py runserver

# Start the dev server in the background; `just logs` follows it, `just stop` ends it.
dev site="academy":
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -f .dev.pid ] && kill -0 "$(cat .dev.pid)" 2>/dev/null; then
        echo "already running (pid $(cat .dev.pid))"; exit 0
    fi
    set -m  # own process group, so stop also ends the server's children
    SITE={{site}} DJANGO_DEBUG=1 nohup uv run python manage.py runserver 8002 > .dev.log 2>&1 &
    echo $! > .dev.pid
    sleep 2
    kill -0 "$(cat .dev.pid)" 2>/dev/null || { cat .dev.log; rm -f .dev.pid; exit 1; }
    echo "{{site}} on http://localhost:8002 (pid $(cat .dev.pid)); just logs to follow"

stop:
    #!/usr/bin/env bash
    [ -f .dev.pid ] || { echo "not running"; exit 0; }
    kill -- -"$(cat .dev.pid)" 2>/dev/null || true
    rm -f .dev.pid

logs:
    tail -f .dev.log

# No database to fill; here so the repo meets the project contract.
seed:
    @echo "no database to seed; content comes from Prismic"
