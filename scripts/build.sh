#!/usr/bin/env bash
# Builds one site into dist/. Usage: scripts/build.sh academy (or set SITE).
set -euo pipefail
export SITE="${1:-${SITE:?Set SITE or pass a site name}}"
TAILWIND_VERSION=v4.3.3
cd "$(dirname "$0")/.."

case "$(uname -s)-$(uname -m)" in
  Darwin-arm64) asset=tailwindcss-macos-arm64 ;;
  Linux-x86_64) asset=tailwindcss-linux-x64 ;;
  *) echo "No Tailwind binary for $(uname -sm)" >&2; exit 1 ;;
esac
tailwind=".bin/tailwindcss-$TAILWIND_VERSION"
if [ ! -x "$tailwind" ]; then
  mkdir -p .bin
  curl -fsSL -o "$tailwind" "https://github.com/tailwindlabs/tailwindcss/releases/download/$TAILWIND_VERSION/$asset"
  chmod +x "$tailwind"
fi

"$tailwind" -i "themes/$SITE/css/site.css" -o "themes/$SITE/static/css/site.css" --minify
# collectstatic never removes old files, so start from empty.
rm -rf staticfiles
# UV lets Netlify run a pip-installed uv as "python3 -m uv".
${UV:-uv} run --frozen python manage.py distill generate --output-directory dist --collectstatic --force
# Files served from the site root: favicon, Netlify _redirects.
if [ -d "themes/$SITE/public" ]; then cp -R "themes/$SITE/public/." dist/; fi
