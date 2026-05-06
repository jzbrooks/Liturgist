# Changelog

## Unreleased

### Added
- `--hymnal-dir` score lookup can find songs that are not indexed by number

### Removed
- `--hymnal-dir` PNG support

## 3.0.0 - 2026-05-02

### Added
- `--hymnal-dir`, if specified, will populate an array of musical scores in `HYMN_SCORES` which correspond by index to `HYMNS`. Each score is an object with a `number` field (the hymn number) and a `sheets` field — an array of base64 uris (one rasterized image per page). Entries are `null` for hymns whose score could not be loaded.
- Schedule column headers that build arrays are matched by prefix, so you can add a note about the conventional purpose of data at this index. 
    e.g. `Hymn 1 - Call to Worship`.
- `Extra N` schedule columns are collected into an `EXTRAS` array for arbitrary per-service content (e.g. catechism, baptism announcements). Indexing follows the same convention as hymns and scripture references.
- `Announcement N` schedule columns are collected into an `ANNOUNCEMENTS` array, indexed the same way as `HYMNS`, `SCRIPTURE_REFS`, and `EXTRAS`.

### Changed
- Scripture references are modeled as an array, like hymns.
- Schedules index arrays from one, handlebars from zero. The assumption is non-programmers might be editing the schedule and zero is better in programming contexts.
- If a particular array entry is missing from the schedule, a null value will be written to the array to preserve index pairing for subsequent indices.

### Removed
- Church-specific template keys `CATECHISM_QUESTION`, `CATECHISM_ANSWER`, `BAPTISMS`, `COLLECT`, and `CHURCH_OF_THE_MONTH` (and their corresponding `Question`, `Answer`, `Baptisms`, `Collect`, and `Church of the Month` schedule columns) have been removed in favor of the generic `EXTRAS` array.

### Fixed
- Single chapter book references (e.g. `Jude 1-3`) are correctly parsed

## 2.0.0 - 2025-09-14

Initial public release
