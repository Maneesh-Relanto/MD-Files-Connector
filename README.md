# 📋 MD Files Connector

[![CI](https://github.com/Maneesh-Relanto/MD-Files-Connector/actions/workflows/ci.yml/badge.svg)](https://github.com/Maneesh-Relanto/MD-Files-Connector/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/Maneesh-Relanto/MD-Files-Connector?color=orange&label=release)](https://github.com/Maneesh-Relanto/MD-Files-Connector/releases)
[![Works with any language](https://img.shields.io/badge/works%20with-any%20language-blueviolet)](#-privacy--security)

A lightweight CLI tool + GitHub Action that scans your project for Markdown files
and tells you which ones are **referenced in your root README** — and which ones
are **isolated and invisible** to readers.

Every `.md` file — including nested `README.md` files in sub-directories — must
be linked from the **root `README.md`** to be considered covered. This keeps
your root README the single source of truth for all project documentation.

---

## Why?

As projects grow, docs accumulate. `CONTRIBUTING.md`, `ARCHITECTURE.md`,
`docs/API.md` — they get written and then forgotten. This tool keeps your
README honest.

---

## Features

- 🔍 Recursively scans your entire project for `.md` files
- 📖 Checks coverage against the **root `README.md` only** (strict mode)
- ✅ Classifies each file as **linked** or **isolated**
- 📊 Outputs a terminal dashboard with coverage stats
- 📄 Generates an `MD_REPORT.md` with a full breakdown
- 🤖 Runs as a **GitHub Action** on every push or PR
- � Interactive fix menu — auto-links isolated files into your README
- 💡 No install, no config — one file, one command- 🌐 **Language agnostic** — works with any project regardless of tech stack

---

## 🔒 Privacy & Security

- **Nothing leaves your machine.** The tool reads file paths and Markdown content locally to build the coverage report. No data is collected, transmitted, or stored anywhere outside your project.
- **No code is read or copied.** Only `.md` files are scanned — your source code, configs, and secrets are never touched.
- **No network calls.** The CLI runs entirely offline. The GitHub Action only uses the GitHub-provided runner environment; it does not call any external service.
- **Read-only by default.** The tool never modifies any file unless you explicitly choose a fix option (G or D) in the interactive menu — and even then, only your root `README.md` is updated.
- **Open source.** The full source is a single readable file — [`md_connector.py`](md_connector.py). You can audit every line before running it.
---

## 🚀 Quickest Way to Start — 60 seconds

**No package manager. No install. Just copy one file.**

### Step 1 — Download the script into your project

```bash
# with curl
curl -O https://raw.githubusercontent.com/Maneesh-Relanto/md-connector/main/md_connector.py

# or with wget
wget https://raw.githubusercontent.com/Maneesh-Relanto/md-connector/main/md_connector.py
```

Or just [download md_connector.py](https://raw.githubusercontent.com/Maneesh-Relanto/md-connector/main/md_connector.py) and drop it anywhere in your project.

### Step 2 — Install the only dependency

```bash
pip install rich
```

> `rich` is optional — the tool works without it (plain text output). But you want it for the coloured dashboard.

### Step 3 — Run it

```bash
# scan current directory
python md_connector.py .

# scan a specific project
python md_connector.py /path/to/your/project

# skip writing MD_REPORT.md
python md_connector.py . --no-report
```

That's it. You'll see a dashboard, a report file, and an interactive prompt to fix any isolated files.

---

## 🤖 Add to CI — GitHub Action

Paste this into `.github/workflows/md-check.yml` in your repo:

```yaml
name: MD Files Connector Check

on:
  push:
    paths: ["**.md"]
  pull_request:
    paths: ["**.md"]

jobs:
  md-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run MD Files Connector
        id: md-connector
        uses: Maneesh-Relanto/md-connector@v1
        with:
          project-root: "."
          exclude-dirs: "node_modules .git venv .venv __pycache__ dist build"
          report-path: "MD_REPORT.md"

      - name: Show coverage summary
        run: |
          echo "Coverage : ${{ steps.md-connector.outputs.coverage }}%"
          echo "Isolated : ${{ steps.md-connector.outputs.isolated-files }} file(s)"
```

On every push or PR that touches a `.md` file, the action will:
1. Scan your repo for all Markdown files
2. Check which ones are linked from your root `README.md`
3. Post a summary to the GitHub Actions step summary panel
4. Upload `MD_REPORT.md` as a downloadable artifact

### Action Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `project-root` | Root directory to scan | `.` |
| `exclude-dirs` | Space-separated dirs to skip | `node_modules .git venv ...` |
| `report-path` | Output path for MD report | `MD_REPORT.md` |
| `skip-report` | Skip generating report file | `false` |
| `fail-on-isolated` | Exit code 1 if isolated files found | `false` |

### Action Outputs

| Output | Description |
|--------|-------------|
| `total-md-files` | Total MD files found (excl. root README) |
| `linked-files` | Files referenced in root README |
| `isolated-files` | Files NOT in root README |
| `coverage` | Percentage linked |

---

## 📋 Sample Output

```
╭───────────────────────────────────────────────────────╮
│ 📋 MD Files Connector                                 │
│ Project root: /my-project                             │
╰───────────────────────────────────────────────────────╯

  📄 Root README                        README.md
  📁 Total MD files (excl. root README)  7
  ✅ Linked in root README               5
  ⚠️  Isolated (not in root README)       2
  📊 README coverage                    71.4%

╭─ ✅ Linked Files ──────────────────────────────────────╮

  #  File                       Title             Words  Sections
  ────────────────────────────────────────────────────────────────
  1  docs/CONTRIBUTING.md       Contributing      210    Setup, Guidelines
  2  docs/ARCHITECTURE.md       Architecture      540    Overview, Components
  ...

╭─ ⚠️  Isolated Files ───────────────────────────────────╮

  #  File                  Title          Words  First line / description
  ────────────────────────────────────────────────────────────────────────
  1  docs/OLD_API.md        Old Api        890    Deprecated. Use v2 API.
  2  SCRATCH_NOTES.md       Scratch Notes   42    Notes from planning sess

💡 Add these to your root README.md to improve discoverability.

╭─────────────────────────────────────────╮
│ 🔧  Fix isolated files?                 │
│ 2 file(s) are not linked in README.md   │
╰─────────────────────────────────────────╯

  [G]  Generic  Append a new "📎 Other Documentation" section
  [D]  Docs     Looks for any heading matching "docs / documentation"
  [M]  Manual   I'll update the README myself — no changes made

  Enter choice (G / D / M):
```

---

## 🔧 Fix Options

When isolated files are found, the tool prompts you interactively:

| Option | What it does |
|--------|-------------|
| **G — Generic** | Appends a `## 📎 Other Documentation` section at the end of your README with all missing links |
| **D — Docs** | Finds the first heading in your README that contains the word `doc` or `documentation` and appends the missing links there |
| **M — Manual** | Does nothing — you handle it yourself |

> The fix menu only appears in an interactive terminal. It is automatically skipped in CI.

---

## ⚙️ CLI Reference

```
usage: md_connector.py [-h] [--exclude [...]] [--report REPORT] [--no-report] [root]

positional arguments:
  root               Project root directory (default: current directory)

options:
  --exclude [...]    Directory names to exclude from scan
  --report REPORT    Output path for markdown report (default: MD_REPORT.md)
  --no-report        Skip generating the MD_REPORT.md file
  --fail-on-isolated Exit with code 1 if any isolated MD files are found
```

**Examples:**

```bash
# Scan current directory, generate report
python md_connector.py .

# Scan a specific folder, no report file
python md_connector.py /path/to/project --no-report

# Exclude extra directories
python md_connector.py . --exclude node_modules .git venv dist tests

# Save report to a custom path
python md_connector.py . --report docs/coverage-report.md
```

---

## 📄 Generated Report

Running without `--no-report` writes `MD_REPORT.md` (into the scanned project root) containing:

- Summary stats table (total, linked, isolated, coverage %)
- Full linked files table with title, word count, and sections
- Full isolated files table with content preview
- Ready-to-paste markdown link snippets for your root README

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

---

## License

[MIT](LICENSE) © 2025 Maneesh Thakur
