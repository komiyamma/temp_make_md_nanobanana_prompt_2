import re

PLAN_FILE = "docs/picture/image_generation_plan.md"

def clean_plan():
    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    header_lines = []
    data_lines = []

    for line in lines:
        if line.strip().startswith('|'):
            # Check if header or separator
            if 'ID' in line or '---' in line:
                header_lines.append(line)
            else:
                data_lines.append(line)
        else:
            header_lines.append(line)

    # Process data lines to remove duplicates
    unique_rows = []
    seen_keys = set()

    # Existing IDs might be messed up, so we will renumber.
    # Key for uniqueness: (Markdown File Name, Image Filename)

    for line in data_lines:
        parts = [p.strip() for p in line.split('|')]
        if len(parts) < 7: # | ID | File | Image | ... | |
            continue

        md_file = parts[2]
        img_file = parts[3]

        key = (md_file, img_file)

        if key not in seen_keys:
            seen_keys.add(key)
            unique_rows.append(parts)

    # Renumber
    new_lines = header_lines[:]
    current_id = 1

    # The header has ID=1, wait.
    # Usually header is | ID | ... | and separator |---|...|
    # The existing file starts with IDs from 1.
    # We should renumber starting from 1 for the whole file or just append?
    # The file has existing content (IDs 1-371). We should preserve them if possible,
    # but renumbering everything ensures consistency.
    # Let's renumber everything to be safe and clean.

    for parts in unique_rows:
        # Construct new line
        # parts[0] is empty string (before first |)
        # parts[1] is old ID
        # parts[2] is File Name
        # ...

        new_id = str(current_id)
        current_id += 1

        # Reconstruct the line preserving formatting roughly
        # content is indices 2 to 6.
        # | ID | File Name | Proposed Image Filename | Relative Link Path | Prompt | Insertion Point |

        row = f"| {new_id} | {parts[2]} | {parts[3]} | {parts[4]} | {parts[5]} | {parts[6]} |\n"
        new_lines.append(row)

    with open(PLAN_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"Cleaned plan file. Total rows: {len(unique_rows)}")

if __name__ == "__main__":
    clean_plan()
