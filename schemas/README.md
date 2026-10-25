# Prismic schemas

These files are the source of truth for the `thec3` Prismic repository's
custom types (`customtypes/<id>.json`) and slice models (`slices/<id>.json`).
They replace Slice Machine in the myc3 repo.

`python manage.py prismic_schemas diff` compares them with live Prismic
(read-only). Pushing them to Prismic is not built yet.
