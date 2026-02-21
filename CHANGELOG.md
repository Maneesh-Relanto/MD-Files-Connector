# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-02-21

### Added
- Recursive `.md` file scanner with strict root-README-only coverage mode
- Rich terminal dashboard with linked / isolated file breakdown
- Plain-text fallback dashboard (when `rich` is not installed)
- `MD_REPORT.md` generation with summary stats, tables, and ready-to-paste link snippets
- GitHub Actions step summary output (`$GITHUB_STEP_SUMMARY`)
- `$GITHUB_OUTPUT` emission via `md_connector_outputs.py` companion script
- Composite GitHub Action (`action.yml`) with inputs: `project-root`, `exclude-dirs`, `report-path`, `skip-report`, `fail-on-isolated`
- Action outputs: `total-md-files`, `linked-files`, `isolated-files`, `coverage`
- Artifact upload of `MD_REPORT.md` via `actions/upload-artifact@v4`
- Interactive fix menu (Generic / Docs / Manual) with secondary sub-menu for missing docs section
- `--fail-on-isolated` CLI flag — exits with code 1 if isolated files found (CI-friendly)
- `--no-report` CLI flag — skip writing `MD_REPORT.md`
- `--exclude` CLI flag — space-separated directory names to skip
- Whole-word docs heading regex `\b(docs?|documentation)\b` to avoid false positives
- Test suite: unit tests for `parse_md_content`, `extract_md_references`, `classify_files`; integration test against fixture project
- Example workflow in `examples/md-check.yml`
- MIT License

[1.0.0]: https://github.com/Maneesh-Relanto/MD-Files-Connector/releases/tag/v1
