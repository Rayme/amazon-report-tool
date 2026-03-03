# AGENTS.md - Amazon Report Tool

## Project Overview

This is a Python-based Amazon sales report analyzer that processes CSV files from Amazon Seller Central and generates HTML reports. The project uses only Python 3 standard library (no external dependencies).

## Build & Run Commands

### Running the Application

```bash
# Run with default settings (auto-detect amazon/ directory)
python run.py

# Run with custom directory
python amazon_report_analyzer.py --dir amazon/

# Specify period name
python amazon_report_analyzer.py --dir amazon/ --period "2026年2月"

# Specify output file
python amazon_report_analyzer.py -d amazon/ -o my_report.html

# View help
python amazon_report_analyzer.py --help
```

### Testing

There are no formal tests in this project. To test manually:
```bash
# Run the analyzer on sample data
python amazon_report_analyzer.py --dir amazon/

# Verify HTML output is generated
ls -la *.html
```

### Linting

No formal linting is configured. You may use pylint or ruff optionally:
```bash
# Optional: run ruff
ruff check amazon_report_analyzer.py

# Optional: run pylint
pylint amazon_report_analyzer.py
```

## Code Style Guidelines

### General Rules

- **Language**: Python 3 with UTF-8 encoding (`# -*- coding: utf-8 -*-`)
- **Encoding**: Use `encoding='utf-8-sig'` when reading CSV files to handle BOM
- **Line length**: Keep lines under 120 characters when practical
- **No external dependencies**: Use only Python standard library

### Imports

- Use explicit imports: `from datetime import datetime` (not wildcard)
- Group imports in order: stdlib, third-party, local
- Example:
  ```python
  import os
  import re
  import csv
  import json
  import argparse
  from datetime import datetime
  from collections import defaultdict
  from html import escape
  ```

### Naming Conventions

- **Functions/variables**: snake_case (e.g., `parse_number`, `reports_dir`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_REPORTS_DIR`, `FALLBACK_RATES`)
- **Classes**: PascalCase (if any added in future)
- **File paths**: Use `os.path.join()` for path construction

### Type Hints

- Add type hints for function parameters and return types when beneficial
- Example: `def parse_number(value) -> float:`

### Functions

- Use docstrings (Chinese is acceptable as project is Chinese-focused)
- Keep functions focused on single responsibility
- Use early returns to reduce nesting
- Example structure:
  ```python
  def parse_number(value):
      """解析各种格式数字"""
      if not value or value == "":
          return 0.0
      # ... implementation
  ```

### Error Handling

- Use specific exception types when possible (avoid bare `except:`)
- Handle missing files gracefully with warnings
- Return empty/safe defaults on errors (e.g., `return [], {}`)
- Example:
  ```python
  try:
      return float(value)
  except ValueError:
      return 0.0
  ```

### CSV Handling

- Always use `encoding='utf-8-sig'` to handle BOM
- Use `csv.reader()` for reading
- Skip comment/description rows at start of files
- Use header row index mapping for column access

### HTML Generation

- Use `from html import escape` to escape user data
- Use f-strings for HTML template construction
- Keep HTML templates readable with proper indentation

### Git & Version Control

- Do not commit large CSV data files or generated HTML reports
- Add generated files to `.gitignore`:
  ```
  *.html
  amazon/*.csv
  __pycache__/
  ```

## Project Structure

```
amazon_report_tool/
├── run.py                      # Entry point for double-click run
├── run_analyzer.bat            # Windows batch runner
├── amazon_report_analyzer.py   # Main application (~900 lines)
├── amazon_analysis.py          # Legacy/alternative analyzer
├── README.md                   # User documentation
├── 开发记录.md                 # Development notes
└── amazon/                     # Report data directory
    ├── 202510BusinessReport-*.csv
    ├── 2025Oct1-*Transaction.csv
    └── DE202510returns.csv
```

## Common Tasks

### Adding New Report Type Support

1. Add file type detection in `scan_reports_directory()` function
2. Create loader function like `load_<type>_report()`
3. Add to `generate_country_report()` to include in HTML output

### Adding New Country Support

Add to `COUNTRY_MAP` dictionary:
```python
COUNTRY_MAP = {
    'DE': {'name': '德国', 'currency': 'EUR', 'symbol': '€'},
    # Add new country here
}
```

### Modifying HTML Report Template

Find the HTML generation section (search for `generate_country_report` or HTML string literals) and modify the template structure. Always escape user data with `escape()` function.

## Notes for AI Agents

- This is a personal utility project, not a large-scale application
- No tests exist; verify changes by running the analyzer
- The code handles German (DE) Amazon reports specifically but is extensible
- CSV files contain multi-language headers (German/English)
- Some Amazon CSV files have description rows before actual headers that need skipping
