# CS/TS Prefix Family Split Workflow

## Name
- Algorithm: `CS/TS Prefix Family Split (CT-PFS)`

## Goal
- Split a large markdown table (`image_generation_plan.md`) into multiple markdown files by the `File Name` family key.
- Family key rule: prefix up to `_cs_` or `_ts_` (examples: `solid_cs`, `solid_ts`).

## Input
- Source markdown table with header:
  - `| ID | File Name | Proposed Image Filename | Relative Link Path | Prompt | Insertion Point |`
- Target column:
  - `File Name`

## Output
- One file per family key:
  - `image_generation_plan.<family>.md`
- Examples:
  - `image_generation_plan.solid_cs.md`
  - `image_generation_plan.solid_ts.md`

## Core Idea
1. Keep the first two lines (table header and separator).
2. Parse each row and read the `File Name` column.
3. Extract family key by regex:
   - `([A-Za-z0-9]+_(?:cs|ts))_`
4. Group rows by that key.
5. Write grouped rows into separate markdown files with the same header.

## Deterministic Rules
- Group key is extracted only from `File Name`.
- Rows without a valid key are skipped.
- Source file is never modified.
- Output files are overwritten if already present.

## Stable Runner
- Script path: `docs/picture/split_image_plan_by_family.py`
- Run:

```powershell
python docs/picture/split_image_plan_by_family.py
```

## Reference Logic (Python)
```python
import re
from pathlib import Path

src = Path("docs/picture/image_generation_plan.md")
out_dir = src.parent
lines = src.read_text(encoding="utf-8").splitlines()

header = lines[0]
separator = lines[1]
rows = lines[2:]

pattern = re.compile(r"([A-Za-z0-9]+_(?:cs|ts))_")
groups = {}

for row in rows:
    if not row.strip().startswith("|"):
        continue

    cols = [c.strip() for c in row.strip().strip("|").split("|")]
    if len(cols) < 2:
        continue

    file_name = cols[1]
    matched = pattern.search(file_name)
    if not matched:
        continue

    key = matched.group(1)
    groups.setdefault(key, []).append(row)

for key, grouped_rows in sorted(groups.items()):
    out = out_dir / f"image_generation_plan.{key}.md"
    out.write_text("\n".join([header, separator, *grouped_rows]) + "\n", encoding="utf-8")
    print(f"{out} ({len(grouped_rows)} rows)")
```

## Validation Checklist
- Output file names follow `image_generation_plan.<family>.md`.
- Each file starts with exactly the same first 2 header lines.
- A file contains only one family key.
- Total row count across split files equals the number of matched rows in source.

## Extension
- If future suffix families are needed (example: `_py_`), extend regex:
  - from `(?:cs|ts)` to `(?:cs|ts|py)`
