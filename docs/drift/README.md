# Schema drift

When a source's field-set hash changes, ingestion fails loudly and writes the diff here.

This directory being empty means no source has changed shape since the last run. It is not a sign that drift detection is unimplemented — check `src/ingest/` for that.
