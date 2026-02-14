import json
import os
import sys
import re

PLAN_FILE = "docs/picture/image_generation_plan.md"

def get_next_id():
    if not os.path.exists(PLAN_FILE):
        return 1

    last_id = 0
    with open(PLAN_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        for line in reversed(lines):
            match = re.match(r"\|\s*(\d+)\s*\|", line)
            if match:
                last_id = int(match.group(1))
                break
    return last_id + 1

def append_to_plan(entry):
    # entry: {id, filename, proposed_filename, relative_link, prompt, insertion_point}
    # Format: | ID | File Name | Proposed Image Filename | Relative Link Path | Prompt | Insertion Point |

    # Escape pipes in prompt and insertion point to avoid breaking table structure
    prompt = entry['prompt'].replace("|", "&#124;").replace("\n", "<br>")
    insertion_point = entry['insertion_point'].replace("|", "&#124;").replace("\n", "<br>")

    row = f"| {entry['id']} | {entry['filename']} | {entry['proposed_filename']} | {entry['relative_link']} | {prompt} | {insertion_point} |\n"

    with open(PLAN_FILE, "a", encoding="utf-8") as f:
        f.write(row)

def update_markdown_file(file_path, insertion_point, relative_link, description):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Create the image tag
    image_tag = f"\n\n![{description}]({relative_link})\n"

    # Check if the exact image tag already exists to avoid double insertion
    if image_tag.strip() in content:
        print(f"Skipping insertion: Image tag already exists in {file_path}")
        return

    # Check if the insertion point exists
    if insertion_point not in content:
        print(f"Error: Insertion point not found in {file_path}")
        print(f"Looking for: {insertion_point[:50]}...")
        return

    # Replace insertion point with insertion point + image tag
    # We use replace with count=1 to only replace the first occurrence if multiple exist,
    # but ideally insertion points should be unique.
    new_content = content.replace(insertion_point, insertion_point + image_tag, 1)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Updated {file_path} with image {description}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bulk_image_processor.py <tasks_json>")
        sys.exit(1)

    tasks_file = sys.argv[1]
    with open(tasks_file, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    current_id = get_next_id()

    # Read existing plan to check for duplicate filenames
    existing_plan_filenames = set()
    if os.path.exists(PLAN_FILE):
        with open(PLAN_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            # extract all filenames from the 3rd column
            matches = re.findall(r"\|\s*\d+\s*\|\s*[^|]+\s*\|\s*([^|]+)\s*\|", content)
            existing_plan_filenames.update([m.strip() for m in matches])

    for task in tasks:
        file_path = task['file_path']
        filename_base = os.path.basename(file_path)

        if not os.path.exists(file_path):
            print(f"Error: File {file_path} does not exist.")
            continue

        for img in task['images']:
            description = img['description']
            prompt = img['prompt']
            insertion_point = img['insertion_point']

            # Construct proposed filename
            # base name without extension
            base_name_no_ext = os.path.splitext(filename_base)[0]
            proposed_filename = f"{base_name_no_ext}_{description}.png"

            # Uniqueness check
            if proposed_filename in existing_plan_filenames:
                print(f"Skipping duplicate filename: {proposed_filename}")
                continue

            relative_link = f"./picture/{proposed_filename}"

            # Add to plan
            entry = {
                "id": current_id,
                "filename": filename_base,
                "proposed_filename": proposed_filename,
                "relative_link": relative_link,
                "prompt": prompt,
                "insertion_point": insertion_point
            }
            append_to_plan(entry)
            existing_plan_filenames.add(proposed_filename)
            current_id += 1

            # Update Markdown
            update_markdown_file(file_path, insertion_point, relative_link, description)

if __name__ == "__main__":
    main()
