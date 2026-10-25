# Phase 4 M3: Prismic schemas

## Goal
c3-sites holds every custom type and slice model of the `thec3` Prismic repository. A read-only command shows how they differ from what Prismic has live.

## Read first
- Next: `customtypes/*/index.json`, `slices/*/model.json`, `slicemachine.config.json`
- Prismic Custom Types API docs (GET endpoints for custom types and shared slices). Check the docs and cite the URL in the commit; don't work from memory.
- c3-sites: `pages/management/commands/prismic_audit.py` (command style), `.env.example`

## Tasks
1. Copy all 14 custom types to `schemas/customtypes/<id>.json` and the 8 slice models to `schemas/slices/<slice id>.json`, byte for byte as they are in the repo. Don't copy `mocks.json` or screenshots, which only Slice Machine uses. Test that every file parses and that each file's id matches its filename.
2. Add `python manage.py prismic_schemas diff`. It GETs every custom type and shared slice from the Custom Types API (repository `PRISMIC_REPOSITORY`, bearer `PRISMIC_CUSTOM_TYPES_API_TOKEN`, honest user agent) and compares them with `schemas/` as parsed JSON, so key order and formatting are ignored.
   - It prints one line per id: `same`, `changed` (with the changed field paths), `only in schemas/` or `only in Prismic`.
   - It exits 0 when all are the same, and 1 otherwise.
   - A missing token is a clear error.
   - Tests mock the HTTP layer. There are no write methods anywhere in the command.
3. Run `diff` once against live and save its output to `docs/plans/phase-4/evidence/m3/diff.txt`. If anything differs, live wins, because Prismic is what the sites build from today. Before changing anything, save the repo-only side of each difference (the id, the field paths, and the repo's value) to `docs/plans/phase-4/evidence/m3/repo-only.txt`, so Andy can review schema work that may never have been pushed. Then set those `schemas/` files to live's version and say so in the commit. Run `diff` again until it reports all `same`.
4. Add a short `schemas/README.md`: these files are the source of truth, they replace Slice Machine in the myc3 repo, and pushing them to Prismic is not built yet.

## Exit checks
- `uv run pytest` green; the three builds succeed.
- `prismic_schemas diff` against live reports all `same`.

## Out of scope
Pushing schemas to Prismic, and deleting anything from the myc3 repo (Andy archives it at cutover).
