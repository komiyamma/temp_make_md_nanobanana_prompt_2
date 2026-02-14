from __future__ import annotations

import re
from pathlib import Path


def split_image_generation_plan_by_family(source: Path) -> list[tuple[str, int]]:
    lines = source.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        raise ValueError(f"Source markdown is too short: {source}")

    header = lines[0]
    separator = lines[1]
    rows = lines[2:]

    pattern = re.compile(r"([A-Za-z0-9]+_(?:cs|ts))_")
    groups: dict[str, list[str]] = {}

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

    written: list[tuple[str, int]] = []
    for key, grouped_rows in sorted(groups.items()):
        out = source.parent / f"image_generation_plan.{key}.md"
        out.write_text("\n".join([header, separator, *grouped_rows]) + "\n", encoding="utf-8")
        written.append((out.name, len(grouped_rows)))

    return written


def main() -> None:
    source = Path("docs/picture/image_generation_plan.md")
    written = split_image_generation_plan_by_family(source)

    total = 0
    for name, count in written:
        print(f"{name}\t{count}")
        total += count
    print(f"TOTAL_GROUPS\t{len(written)}")
    print(f"TOTAL_ROWS\t{total}")


if __name__ == "__main__":
    main()
