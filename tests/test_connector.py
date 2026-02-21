"""
Tests for MD Files Connector core logic.
"""

import pytest
from pathlib import Path
from md_connector import (
    parse_md_content,
    find_all_md_files,
    find_all_readmes,
    extract_md_references,
    classify_files,
    fix_generic,
    fix_docs,
    MDFile,
)

# Path to the bundled fixture project
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "sample_project"


# ── parse_md_content ───────────────────────────────────────────────────────────

class TestParseMdContent:
    def test_extracts_h1_title(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# My Title\n\nSome description here.\n")
        result = parse_md_content(f)
        assert result["title"] == "My Title"

    def test_extracts_description(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\nThis is the first paragraph.\n")
        result = parse_md_content(f)
        assert result["description"] == "This is the first paragraph."

    def test_extracts_h2_sections(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\n## Installation\n\n## Usage\n")
        result = parse_md_content(f)
        assert "Installation" in result["sections"]
        assert "Usage" in result["sections"]

    def test_counts_words(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("one two three four five")
        result = parse_md_content(f)
        assert result["word_count"] == 5

    def test_fallback_title_from_filename(self, tmp_path):
        f = tmp_path / "my-guide.md"
        f.write_text("No heading here, just plain text.\n")
        result = parse_md_content(f)
        assert result["title"] == "My Guide"

    def test_skips_code_blocks(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Title\n\n```\n## Not A Section\n```\n\n## Real Section\n")
        result = parse_md_content(f)
        assert "Not A Section" not in result["sections"]
        assert "Real Section" in result["sections"]

    def test_truncates_long_description(self, tmp_path):
        f = tmp_path / "doc.md"
        long_para = "word " * 50  # > 160 chars
        f.write_text(f"# Title\n\n{long_para}\n")
        result = parse_md_content(f)
        assert len(result["description"]) <= 160

    def test_missing_file_returns_safe_defaults(self, tmp_path):
        result = parse_md_content(tmp_path / "nonexistent.md")
        assert result["title"] == "nonexistent"
        assert result["word_count"] == 0


# ── extract_md_references ──────────────────────────────────────────────────────

class TestExtractMdReferences:
    def test_finds_markdown_link(self, tmp_path):
        readme = tmp_path / "README.md"
        target = tmp_path / "CONTRIBUTING.md"
        target.write_text("# Contributing\n")
        readme.write_text("See [Contributing](CONTRIBUTING.md) for details.\n")
        refs = extract_md_references(readme, tmp_path)
        assert target.resolve() in refs

    def test_ignores_external_links(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("[External](https://example.com/guide.md)\n")
        refs = extract_md_references(readme, tmp_path)
        assert len(refs) == 0

    def test_finds_html_href(self, tmp_path):
        readme = tmp_path / "README.md"
        target = tmp_path / "docs" / "guide.md"
        target.parent.mkdir()
        target.write_text("# Guide\n")
        readme.write_text('<a href="docs/guide.md">Guide</a>\n')
        refs = extract_md_references(readme, tmp_path)
        assert target.resolve() in refs


# ── classify_files ─────────────────────────────────────────────────────────────

class TestClassifyFiles:
    def test_linked_and_isolated(self, tmp_path):
        readme = tmp_path / "README.md"
        linked_doc = tmp_path / "CONTRIBUTING.md"
        isolated_doc = tmp_path / "ORPHAN.md"

        readme.write_text("# Root\n\nSee [Contributing](CONTRIBUTING.md).\n")
        linked_doc.write_text("# Contributing\n")
        isolated_doc.write_text("# Orphan\n")

        all_md = find_all_md_files(tmp_path, [".git"])
        all_readmes = find_all_readmes(all_md)
        linked, isolated, _ = classify_files(all_md, all_readmes[0], tmp_path)

        linked_names = [m.path.name for m in linked]
        isolated_names = [m.path.name for m in isolated]

        assert "CONTRIBUTING.md" in linked_names
        assert "ORPHAN.md" in isolated_names

    def test_no_readme_means_all_isolated(self, tmp_path):
        doc = tmp_path / "notes.md"
        doc.write_text("# Notes\n")

        all_md = find_all_md_files(tmp_path, [".git"])

        linked, isolated, _ = classify_files(all_md, None, tmp_path)
        assert len(linked) == 0
        assert any(m.path.name == "notes.md" for m in isolated)


# ── Fixture-based integration test ────────────────────────────────────────────

class TestFixtureProject:
    def test_sample_project_coverage(self):
        """End-to-end scan of the bundled sample fixture project."""
        all_md = find_all_md_files(FIXTURE_ROOT, [".git"])
        all_readmes = find_all_readmes(all_md)
        assert len(all_readmes) >= 1, "Fixture must have at least one README"

        root_readme = next(
            (rp for rp in all_readmes if rp.parent.resolve() == FIXTURE_ROOT.resolve()),
            None,
        )
        linked, isolated, _ = classify_files(all_md, root_readme, FIXTURE_ROOT)

        # CONTRIBUTING.md is linked from fixture README
        linked_names = [m.path.name for m in linked]
        assert "CONTRIBUTING.md" in linked_names

        # docs/API.md is intentionally orphaned in the fixture
        isolated_names = [m.path.name for m in isolated]
        assert "API.md" in isolated_names


# ── fix_generic ───────────────────────────────────────────────────────────────

def _make_isolated(tmp_path: Path, filename: str, title: str) -> MDFile:
    """Helper: create a real file and return an MDFile pointing at it."""
    p = tmp_path / filename
    p.write_text(f"# {title}\n", encoding="utf-8")
    return MDFile(path=p, title=title)


class TestFixGeneric:
    def test_creates_new_section(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# My Project\n\nSome intro.\n", encoding="utf-8")
        iso = _make_isolated(tmp_path, "guide.md", "Guide")

        added = fix_generic(readme, [iso])

        content = readme.read_text(encoding="utf-8")
        assert added == 1
        assert "## \U0001f4ce Other Documentation" in content
        assert "- [Guide](guide.md)" in content

    def test_returns_count_of_links_added(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n", encoding="utf-8")
        files = [
            _make_isolated(tmp_path, "a.md", "Alpha"),
            _make_isolated(tmp_path, "b.md", "Beta"),
            _make_isolated(tmp_path, "c.md", "Gamma"),
        ]

        added = fix_generic(readme, files)

        assert added == 3

    def test_appends_only_new_links_when_section_exists(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n## \U0001f4ce Other Documentation\n\n- [Alpha](a.md)\n",
            encoding="utf-8",
        )
        _make_isolated(tmp_path, "a.md", "Alpha")  # already present
        beta = _make_isolated(tmp_path, "b.md", "Beta")  # new

        added = fix_generic(readme, [MDFile(path=tmp_path / "a.md", title="Alpha"), beta])

        content = readme.read_text(encoding="utf-8")
        assert added == 1
        assert content.count("- [Alpha]") == 1   # no duplicate
        assert "- [Beta](b.md)" in content

    def test_returns_zero_when_all_links_already_present(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n## \U0001f4ce Other Documentation\n\n- [Guide](guide.md)\n",
            encoding="utf-8",
        )
        iso = _make_isolated(tmp_path, "guide.md", "Guide")

        added = fix_generic(readme, [iso])

        assert added == 0

    def test_does_not_duplicate_section_heading(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n", encoding="utf-8")
        iso = _make_isolated(tmp_path, "x.md", "X Doc")
        fix_generic(readme, [iso])
        fix_generic(readme, [iso])  # run twice

        content = readme.read_text(encoding="utf-8")
        assert content.count("## \U0001f4ce Other Documentation") == 1


# ── fix_docs ──────────────────────────────────────────────────────────────────

class TestFixDocs:
    def test_finds_documentation_heading_and_appends(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n\n## Documentation\n\nSome text.\n", encoding="utf-8")
        iso = _make_isolated(tmp_path, "api.md", "API Reference")

        added, section = fix_docs(readme, [iso])

        content = readme.read_text(encoding="utf-8")
        assert added == 1
        assert section == "Documentation"
        assert "- [API Reference](api.md)" in content

    def test_finds_docs_heading_variant(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n\n## Docs\n\nLinks go here.\n", encoding="utf-8")
        iso = _make_isolated(tmp_path, "guide.md", "Guide")

        added, section = fix_docs(readme, [iso])

        assert added == 1
        assert section == "Docs"

    def test_returns_zero_and_empty_when_no_docs_section(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n\n## Installation\n\n## Usage\n", encoding="utf-8")
        iso = _make_isolated(tmp_path, "notes.md", "Notes")

        added, section = fix_docs(readme, [iso])

        assert added == 0
        assert section == ""
        # README must be unmodified
        assert "Notes" not in readme.read_text(encoding="utf-8")

    def test_does_not_add_duplicate_links(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n## Documentation\n\n- [Guide](guide.md)\n",
            encoding="utf-8",
        )
        iso = _make_isolated(tmp_path, "guide.md", "Guide")

        added, _ = fix_docs(readme, [iso])

        assert added == 0
        assert readme.read_text(encoding="utf-8").count("- [Guide]") == 1

    def test_does_not_match_docker_or_docstring(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# Project\n\n## Docker Setup\n\n## Docstring Guide\n", encoding="utf-8")
        iso = _make_isolated(tmp_path, "x.md", "X")

        added, section = fix_docs(readme, [iso])

        assert added == 0
        assert section == ""

    def test_inserts_only_into_docs_section_not_after(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text(
            "# Project\n\n## Documentation\n\n## Installation\n",
            encoding="utf-8",
        )
        iso = _make_isolated(tmp_path, "guide.md", "Guide")

        fix_docs(readme, [iso])

        content = readme.read_text(encoding="utf-8")
        doc_pos = content.index("## Documentation")
        install_pos = content.index("## Installation")
        link_pos = content.index("- [Guide]")
        # Link must appear between the two headings
        assert doc_pos < link_pos < install_pos
