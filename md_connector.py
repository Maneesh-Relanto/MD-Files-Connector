#!/usr/bin/env python3
"""
MD Files Connector
------------------
Scans a project folder for ALL Markdown files and checks which ones are
explicitly referenced in the ROOT README.md (strict mode).

Every .md file — including any nested READMEs — must appear in the root
README to be counted as "linked". Files absent from the root README are
reported as "isolated".

Features:
  - Content-aware scanning: title, first paragraph, word count, H2 sections
  - Strict root-README-only classification
  - Rich terminal dashboard and MD_REPORT.md summary

Outputs:
  - Terminal dashboard (via rich, with plain fallback)
  - MD_REPORT.md summary file
"""

import os
import re
import sys
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# ── Data model ─────────────────────────────────────────────────────────────────

@dataclass
class MDFile:
    path: Path
    title: str           = ""
    description: str     = ""   # first non-heading paragraph, truncated
    word_count: int      = 0
    sections: list[str]  = field(default_factory=list)   # H2 headings
    is_readme: bool      = False


# ── Content parsing ────────────────────────────────────────────────────────────

def parse_md_content(path: Path) -> dict:
    """
    Extract metadata from a Markdown file:
      - title     : first H1 line, or filename stem
      - description: first non-empty, non-heading paragraph (≤ 160 chars)
      - word_count : total words in file
      - sections   : list of H2 headings
    """
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return {"title": path.stem, "description": "", "word_count": 0, "sections": []}

    lines = content.splitlines()
    title = ""
    description = ""
    sections = []
    desc_lines = []
    in_code_block = False
    past_title = False

    for line in lines:
        stripped = line.strip()

        # Track fenced code blocks so we don't parse inside them
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # H1 → title
        if not title and stripped.startswith("# "):
            title = stripped[2:].strip()
            past_title = True
            continue

        # H2 → sections list
        if stripped.startswith("## "):
            sections.append(stripped[3:].strip())
            if description:
                continue   # already have description, just collect sections
            past_title = True
            continue

        # Skip badges/shields lines and HTML tags
        if re.match(r'^\[!\[', stripped) or re.match(r'^<', stripped):
            continue

        # Collect description from first real paragraph after title
        if past_title and stripped and not description:
            desc_lines.append(stripped)
            # Paragraph ends at blank line
        elif past_title and not stripped and desc_lines:
            description = " ".join(desc_lines)
            desc_lines = []
        elif not past_title and stripped:
            # File has no H1 yet but has content — treat as potential title
            # only if it looks like a heading (short line)
            if len(stripped) < 80 and not stripped.startswith("-") and not stripped.startswith("*"):
                past_title = True

    # Fallback: description from accumulated lines
    if not description and desc_lines:
        description = " ".join(desc_lines)

    # Truncate description
    if len(description) > 160:
        description = description[:157] + "..."

    # Fallback title
    if not title:
        title = path.stem.replace("-", " ").replace("_", " ").title()

    word_count = len(re.findall(r'\w+', content))

    return {
        "title": title,
        "description": description,
        "word_count": word_count,
        "sections": sections[:6],   # cap at 6 to keep report tidy
    }


# ── File discovery ─────────────────────────────────────────────────────────────

def find_all_md_files(root: Path, exclude_dirs: list[str]) -> list[MDFile]:
    """Recursively find all .md files, parse content, return MDFile list."""
    results = []
    for path in sorted(root.rglob("*.md")):
        parts = path.relative_to(root).parts
        if any(part in exclude_dirs for part in parts):
            continue
        meta = parse_md_content(path)
        is_readme = path.stem.lower() == "readme"
        results.append(MDFile(
            path=path,
            title=meta["title"],
            description=meta["description"],
            word_count=meta["word_count"],
            sections=meta["sections"],
            is_readme=is_readme,
        ))
    return results


def find_all_readmes(md_files: list[MDFile]) -> list[Path]:
    """Return paths of all README files found, sorted root-first."""
    return sorted(
        [f.path for f in md_files if f.is_readme],
        key=lambda p: len(p.parts),
    )


# ── Reference extraction ───────────────────────────────────────────────────────

def extract_md_references(readme_path: Path, root: Path) -> set[Path]:
    """
    Parse a README.md and extract all internal .md references.
    Handles markdown links, bare paths, and HTML href attributes.
    """
    try:
        content = readme_path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return set()

    link_pattern = re.compile(r'\[.*?\]\(([^)]+\.md[^)]*)\)', re.IGNORECASE)
    bare_pattern = re.compile(r'(?<!\()([^\s\'"<>()\[\]]+\.md)(?!\))', re.IGNORECASE)
    html_pattern = re.compile(r'href=["\']([^"\']+\.md[^"\']*)["\']', re.IGNORECASE)

    raw_refs = set()
    for pat in (link_pattern, bare_pattern, html_pattern):
        for match in pat.finditer(content):
            ref = match.group(1).split("#")[0].strip()
            raw_refs.add(ref)

    resolved = set()
    readme_dir = readme_path.parent
    for ref in raw_refs:
        if ref.startswith("http://") or ref.startswith("https://"):
            continue
        for base in (readme_dir, root):
            candidate = (base / ref).resolve()
            if candidate.exists():
                resolved.add(candidate)
                break

    return resolved


# ── Classification (strict: root README only) ────────────────────────────────

def classify_files(
    all_md: list[MDFile],
    root_readme: Path | None,
    root: Path,
) -> tuple[list[MDFile], list[MDFile], set[Path]]:
    """
    Strict root-README-only classification.

    A file is "linked" only if the root README.md explicitly references it.
    Every other .md file — including nested READMEs — is "isolated" unless
    it appears in the root README.

    Returns:
      linked     - MDFile objects referenced by the root README
      isolated   - MDFile objects not referenced by the root README
      root_refs  - set of resolved paths referenced in the root README
    """
    root_refs: set[Path] = (
        extract_md_references(root_readme, root) if root_readme else set()
    )
    root_readme_resolved = root_readme.resolve() if root_readme else None

    linked, isolated = [], []
    for md in all_md:
        # Skip the root README itself — it is the reference document
        if root_readme_resolved and md.path.resolve() == root_readme_resolved:
            continue
        if md.path.resolve() in root_refs:
            linked.append(md)
        else:
            isolated.append(md)

    return linked, isolated, root_refs


# ── Terminal dashboard ─────────────────────────────────────────────────────────

def print_dashboard_rich(
    root: Path,
    root_readme: Path | None,
    all_md: list[MDFile],
    linked: list[MDFile],
    isolated: list[MDFile],
):
    console = Console()
    total = len(all_md) - (1 if root_readme else 0)   # exclude root README
    coverage = (len(linked) / total * 100) if total > 0 else 0

    console.print()
    console.print(Panel.fit(
        f"[bold cyan]📋 MD Files Connector[/bold cyan]\n"
        f"[dim]Project root: {root}[/dim]",
        border_style="cyan"
    ))

    # ── Summary
    readme_display = str(root_readme.relative_to(root)) if root_readme else "[red]NOT FOUND[/red]"
    summary = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    summary.add_column(style="bold")
    summary.add_column()
    summary.add_row("📄 Root README", readme_display)
    summary.add_row("📁 Total MD files (excl. root README)", str(total))
    summary.add_row("✅ Linked in root README", f"[green]{len(linked)}[/green]")
    summary.add_row("⚠️  Isolated (not in root README)",
                    f"[yellow]{len(isolated)}[/yellow]" if isolated else "[green]0[/green]")
    summary.add_row("📊 README coverage", f"[bold]{coverage:.1f}%[/bold]")
    console.print(summary)

    # ── Linked files with content
    if linked:
        console.print(Panel("[bold green]✅ Linked Files[/bold green]", border_style="green"))
        t = Table(box=box.SIMPLE_HEAD, show_header=True)
        t.add_column("#", style="dim", width=4)
        t.add_column("File", style="green", min_width=28)
        t.add_column("Title", min_width=20)
        t.add_column("Words", justify="right", style="dim", width=7)
        t.add_column("Sections", style="dim")
        for i, md in enumerate(linked, 1):
            sections_str = ", ".join(md.sections[:3]) + ("…" if len(md.sections) > 3 else "")
            t.add_row(
                str(i),
                str(md.path.relative_to(root)),
                md.title[:35] + ("…" if len(md.title) > 35 else ""),
                str(md.word_count),
                sections_str or "—",
            )
        console.print(t)

    # ── Isolated files with content preview
    if isolated:
        console.print(Panel(
            "[bold yellow]⚠️  Isolated Files — not in root README[/bold yellow]",
            border_style="yellow"
        ))
        t = Table(box=box.SIMPLE_HEAD, show_header=True)
        t.add_column("#", style="dim", width=4)
        t.add_column("File", style="yellow", min_width=28)
        t.add_column("Title", min_width=20)
        t.add_column("Words", justify="right", style="dim", width=7)
        t.add_column("First line / description", style="dim")
        for i, md in enumerate(isolated, 1):
            t.add_row(
                str(i),
                str(md.path.relative_to(root)),
                md.title[:35] + ("…" if len(md.title) > 35 else ""),
                str(md.word_count),
                md.description[:55] + ("…" if len(md.description) > 55 else "") or "—",
            )
        console.print(t)
        console.print("[yellow]💡 Add these to your root README.md to improve discoverability.[/yellow]\n")
    else:
        console.print("[bold green]🎉 All MD files are linked in the root README![/bold green]\n")


def print_dashboard_plain(
    root: Path,
    root_readme: Path | None,
    all_md: list[MDFile],
    linked: list[MDFile],
    isolated: list[MDFile],
):
    total = len(all_md) - (1 if root_readme else 0)
    coverage = (len(linked) / total * 100) if total > 0 else 0

    print("\n==== MD Files Connector ====")
    print(f"Root         : {root}")
    print(f"Root README  : {root_readme.relative_to(root) if root_readme else 'NOT FOUND'}")
    print(f"Total MD     : {total}")
    print(f"Linked       : {len(linked)}")
    print(f"Isolated     : {len(isolated)}")
    print(f"Coverage     : {coverage:.1f}%")

    if linked:
        print("\n-- Linked Files --")
        for md in linked:
            print(f"  [OK] {md.path.relative_to(root)}  |  {md.title}  |  {md.word_count} words")

    if isolated:
        print("\n-- Isolated Files --")
        for md in isolated:
            print(f"  [!!] {md.path.relative_to(root)}  |  {md.title}  |  {md.word_count} words")
            if md.description:
                print(f"       {md.description[:100]}")
    print()


# ── Markdown report ────────────────────────────────────────────────────────────

def generate_md_report(
    root: Path,
    root_readme: Path | None,
    all_md: list[MDFile],
    linked: list[MDFile],
    isolated: list[MDFile],
    output_path: Path,
):
    total = len(all_md) - (1 if root_readme else 0)
    coverage = (len(linked) / total * 100) if total > 0 else 0
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    readme_display = str(root_readme.relative_to(root)) if root_readme else "NOT FOUND"

    lines = [
        "# 📋 MD Files Connector Report",
        f"\n_Generated: {now}_\n",
        "## 📊 Summary\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| 📄 Root README | `{readme_display}` |",
        f"| 📁 Total MD files (excl. root README) | {total} |",
        f"| ✅ Linked in root README | {len(linked)} |",
        f"| ⚠️ Isolated (not in root README) | {len(isolated)} |",
        f"| 📊 README coverage | **{coverage:.1f}%** |",
        "",
    ]

    # Linked files
    if linked:
        lines += [
            "## ✅ Linked Files\n",
            "| # | File | Title | Words | Sections |",
            "|---|------|-------|-------|----------|",
        ]
        for i, md in enumerate(linked, 1):
            sections = ", ".join(md.sections[:4]) or "—"
            lines.append(
                f"| {i} | `{md.path.relative_to(root)}` | {md.title} | {md.word_count} | {sections} |"
            )
        lines.append("")

    # Isolated files with description
    if isolated:
        lines += [
            "## ⚠️ Isolated Files\n",
            "> These files are **not referenced** by the root `README.md`.\n",
            "| # | File | Title | Words | Description |",
            "|---|------|-------|-------|-------------|",
        ]
        for i, md in enumerate(isolated, 1):
            desc = md.description.replace("|", "\\|") if md.description else "—"
            lines.append(
                f"| {i} | `{md.path.relative_to(root)}` | {md.title} | {md.word_count} | {desc} |"
            )

        lines += [
            "",
            "### 💡 Suggested additions\n",
            "Add the following snippets to your root `README.md`:\n",
            "```markdown",
        ]
        for md in isolated:
            rel = md.path.relative_to(root)
            lines.append(f"- [{md.title}]({rel})")
            if md.description:
                lines.append(f"  _{md.description}_")
        lines += ["```", ""]
    else:
        lines.append("## 🎉 All MD files are linked in the root README!\n")

    lines += [
        "---",
        "_Report generated by [MD Files Connector](https://github.com/Maneesh-Relanto/md-connector)_",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


# ── GitHub Actions summary ─────────────────────────────────────────────────────

def write_github_summary(
    root: Path,
    root_readme: Path | None,
    all_md: list[MDFile],
    linked: list[MDFile],
    isolated: list[MDFile],
):
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_file:
        return

    total = len(all_md) - (1 if root_readme else 0)
    coverage = (len(linked) / total * 100) if total > 0 else 0

    lines = [
        "## 📋 MD Files Connector\n",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total MD files | {total} |",
        f"| ✅ Linked in root README | {len(linked)} |",
        f"| ⚠️ Isolated | {len(isolated)} |",
        f"| Coverage | **{coverage:.1f}%** |",
        "",
    ]
    if isolated:
        lines.append("### ⚠️ Isolated Files\n")
        for md in isolated:
            lines.append(f"- `{md.path.relative_to(root)}` — {md.title}")

    with open(summary_file, "a") as fh:
        fh.write("\n".join(lines))


# ── Auto-fix: write missing links into root README ────────────────────────────

def _build_link_lines(isolated: list[MDFile], root_readme: Path) -> list[str]:
    """Build relative markdown link lines for each isolated file."""
    readme_dir = root_readme.parent
    links = []
    for md in isolated:
        try:
            rel = md.path.relative_to(readme_dir)
        except ValueError:
            rel = md.path
        links.append(f"- [{md.title}]({rel.as_posix()})")
    return links


def fix_generic(root_readme: Path, isolated: list[MDFile]) -> int:
    """
    Append a '## 📎 Other Documentation' section to the root README with
    links to all isolated files. If the section already exists, only new
    links are appended.  Returns the number of links added.
    """
    content = root_readme.read_text(encoding="utf-8")
    link_lines = _build_link_lines(isolated, root_readme)
    SECTION_HEADING = "## 📎 Other Documentation"

    if SECTION_HEADING in content:
        # Section exists — append only links not already present
        new_links = [l for l in link_lines if l not in content]
        if not new_links:
            return 0
        # Insert before the next ## heading after the section, or at EOF
        lines = content.splitlines(keepends=True)
        in_section = False
        insert_at = len(lines)
        for i, line in enumerate(lines):
            if line.strip() == SECTION_HEADING:
                in_section = True
                continue
            if in_section and line.startswith("## "):
                insert_at = i
                break
        new_lines = lines[:insert_at] + [l + "\n" for l in new_links] + lines[insert_at:]
        root_readme.write_text("".join(new_lines), encoding="utf-8")
        return len(new_links)
    else:
        section = "\n\n" + SECTION_HEADING + "\n\n" + "\n".join(link_lines) + "\n"
        root_readme.write_text(content.rstrip() + section, encoding="utf-8")
        return len(link_lines)


def fix_docs(root_readme: Path, isolated: list[MDFile]) -> tuple[int, str]:
    """
    Find an existing 'Documentation' / 'Docs' section in the root README and
    append missing links into it.  Falls back to fix_generic if no such
    section exists.  Returns (links_added, section_name_used).
    """
    content = root_readme.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    link_lines = _build_link_lines(isolated, root_readme)

    # Find a heading containing "doc" (Documentation, Docs, Docs & Guides …)
    heading_re = re.compile(r'^(#{1,3})\s+(.+)', re.IGNORECASE)
    section_start = None
    section_level = 0
    section_title = ""

    for i, line in enumerate(lines):
        m = heading_re.match(line)
        if m and re.search(r'\b(docs?|documentation)\b', m.group(2), re.IGNORECASE):
            section_start = i
            section_level = len(m.group(1))
            section_title = m.group(2).strip()
            break

    if section_start is None:
        # No docs section found — caller is responsible for handling this.
        return 0, ""

    # Find where the section ends (next heading at same or higher level, or EOF)
    section_end = len(lines)
    for i in range(section_start + 1, len(lines)):
        m = heading_re.match(lines[i])
        if m and len(m.group(1)) <= section_level:
            section_end = i
            break

    # Only add links not already mentioned in this section
    section_text = "".join(lines[section_start:section_end])
    new_links = [l for l in link_lines if l not in section_text]
    if not new_links:
        return 0, section_title

    # Insert after the last non-empty line in the section
    insert_at = section_end
    for i in range(section_end - 1, section_start, -1):
        if lines[i].strip():
            insert_at = i + 1
            break

    new_lines = lines[:insert_at] + [l + "\n" for l in new_links] + lines[insert_at:]
    root_readme.write_text("".join(new_lines), encoding="utf-8")
    return len(new_links), section_title


# ── Interactive fix menu ───────────────────────────────────────────────────────

def prompt_fix_menu(
    root_readme: Path,
    isolated: list[MDFile],
):
    """
    Show a colorful interactive menu and apply the chosen fix to root README.
    Only called when rich is available and terminal is interactive.
    """
    from rich.console import Console as _Console
    console = _Console()

    content = root_readme.read_text(encoding="utf-8")

    # Find the actual section heading that contains "docs" / "documentation"
    # (case-insensitive), excluding our own auto-generated heading.
    _heading_re = re.compile(r'^(#{1,3})\s+(.+)', re.MULTILINE)
    found_docs_section: str | None = None
    for m in _heading_re.finditer(content):
        title = m.group(2).strip()
        if re.search(r'\b(docs?|documentation)\b', title, re.IGNORECASE):
            found_docs_section = title
            break
    has_docs = found_docs_section is not None

    console.print()
    console.print(Panel.fit(
        "[bold white]🔧  Fix isolated files?[/bold white]\n"
        f"[dim]{len(isolated)} file(s) are not linked in {root_readme.name}[/dim]",
        border_style="magenta",
    ))

    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column(style="bold magenta", width=5)
    t.add_column(style="bold white", min_width=10)
    t.add_column()

    t.add_row(
        "[G]",
        "Generic",
        '[dim]Append a brand-new [cyan]"📎 Other Documentation"[/cyan] section at the end of README[/dim]',
    )

    if has_docs:
        docs_hint = (
            f'[dim]Looks for any heading matching [cyan]"docs / documentation"[/cyan] — '
            f'found: [green]"{found_docs_section}"[/green] — will append missing links there[/dim]'
        )
    else:
        docs_hint = (
            '[dim]Looks for any heading matching [cyan]"docs / documentation"[/cyan] — '
            '[yellow]none found in README[/yellow] — you will be asked to confirm next step[/dim]'
        )
    t.add_row("[D]", "Docs", docs_hint)
    t.add_row("[M]", "Manual", "[dim]I'll update the README myself — no changes made[/dim]")

    console.print(t)

    while True:
        choice = console.input(
            "[bold cyan]  Enter choice (G / D / M): [/bold cyan]"
        ).strip().upper()
        if choice in ("G", "D", "M"):
            break
        console.print("[red]  ✗ Invalid — please enter G, D, or M.[/red]")

    console.print()

    if choice == "M":
        console.print("[dim]  Manual mode — no changes made. Edit README.md yourself.[/dim]\n")
        return

    # ── D chosen but no docs section exists — ask before acting
    if choice == "D" and not has_docs:
        console.print(
            "[yellow]  ⚠️  No section matching \"docs\" or \"documentation\" was found in README.[/yellow]\n"
            "  [dim]Searched for any heading (##, ###) whose text contains the word [cyan]\"doc\"[/cyan].[/dim]\n"
            "  What would you like to do?"
        )
        sub = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
        sub.add_column(style="bold magenta", width=5)
        sub.add_column(style="bold white", min_width=10)
        sub.add_column()
        sub.add_row("[G]", "Generic", '[dim]Create a new [cyan]"📎 Other Documentation"[/cyan] section instead[/dim]')
        sub.add_row("[M]", "Manual",  "[dim]Cancel — I'll add or rename a section myself[/dim]")
        console.print(sub)
        while True:
            sub_choice = console.input(
                "[bold cyan]  Enter choice (G / M): [/bold cyan]"
            ).strip().upper()
            if sub_choice in ("G", "M"):
                break
            console.print("[red]  ✗ Invalid — please enter G or M.[/red]")
        console.print()
        if sub_choice == "M":
            console.print("[dim]  Manual mode — no changes made.[/dim]\n")
            return
        # User confirmed fallback to Generic
        choice = "G"

    if choice == "G":
        added = fix_generic(root_readme, isolated)
    else:  # D
        added, section_title = fix_docs(root_readme, isolated)

    if added:
        section_label = "📎 Other Documentation" if choice == "G" else section_title
        console.print(
            f"[bold green]  ✅ Done![/bold green] "
            f"Added [bold]{added}[/bold] link(s) under "
            f"[cyan]\"{section_label}\"[/cyan] in [bold]{root_readme.name}[/bold]\n"
        )
    else:
        console.print(
            "[yellow]  ⚠️  No new links added — all isolated files are already present.[/yellow]\n"
        )


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scan a project for MD files and check README coverage (v2)."
    )
    parser.add_argument("root", nargs="?", default=".",
                        help="Project root directory (default: current directory)")
    parser.add_argument("--exclude", nargs="*",
                        default=["node_modules", ".git", "venv", ".venv",
                                 "__pycache__", "dist", "build"],
                        help="Directory names to exclude")
    parser.add_argument("--report", default="MD_REPORT.md",
                        help="Output path for markdown report")
    parser.add_argument("--no-report", action="store_true",
                        help="Skip generating the MD_REPORT.md file")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"Error: '{root}' is not a valid directory.")
        sys.exit(1)

    # 1. Scan & parse all MD files
    all_md = find_all_md_files(root, args.exclude)

    # 2. Locate the root README (single source of truth)
    all_readmes = find_all_readmes(all_md)
    root_readme = next(
        (rp for rp in all_readmes if rp.parent.resolve() == root.resolve()), None
    )
    if not root_readme:
        print("⚠️  No README.md found at project root — all MD files will be isolated.")

    # 3. Classify: strict root-README-only
    linked, isolated, _ = classify_files(all_md, root_readme, root)

    # 4. Terminal dashboard
    if RICH_AVAILABLE:
        print_dashboard_rich(root, root_readme, all_md, linked, isolated)
    else:
        print_dashboard_plain(root, root_readme, all_md, linked, isolated)

    # 5. MD Report
    if not args.no_report:
        report_path = Path(args.report)
        if not report_path.is_absolute():
            report_path = root / report_path
        generate_md_report(root, root_readme, all_md, linked, isolated, report_path)
        print(f"📄 Report written to: {report_path}")

    # 6. GitHub Actions summary (no-op outside CI)
    write_github_summary(root, root_readme, all_md, linked, isolated)

    # 7. Interactive fix menu — only in a real terminal, only when fixes needed
    if RICH_AVAILABLE and isolated and root_readme and sys.stdin.isatty():
        prompt_fix_menu(root_readme, isolated)

    sys.exit(0)


if __name__ == "__main__":
    main()
