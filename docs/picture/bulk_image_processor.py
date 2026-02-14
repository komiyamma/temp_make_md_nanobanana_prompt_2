import json
import os
import re
import sys

PLAN_FILE = "docs/picture/image_generation_plan.md"

def read_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return None

def write_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def get_next_id():
    if not os.path.exists(PLAN_FILE):
        return 0

    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in reversed(lines):
        match = re.search(r'^\|\s*(\d+)\s*\|', line)
        if match:
            return int(match.group(1)) + 1
    return 0

def check_uniqueness(filename, content, plan_content):
    # Check in content
    if filename in content:
        return False
    # Check in plan
    if filename in plan_content:
        return False
    return True

def append_to_plan(plan_id, filename, proposed_filename, relative_link, prompt, insertion_point):
    formatted_prompt = prompt.replace('\n', '<br>')
    row = f"| {plan_id} | {filename} | {proposed_filename} | {relative_link} | {formatted_prompt} | {insertion_point} |\n"
    with open(PLAN_FILE, 'a', encoding='utf-8') as f:
        f.write(row)

def insert_image_tag(filepath, content, insertion_point, relative_link, description):
    # Escape special characters for regex
    escaped_point = re.escape(insertion_point)
    # Flexible whitespace matching
    pattern = re.compile(f"({escaped_point})", re.MULTILINE)

    if not pattern.search(content):
        print(f"Warning: Insertion point '{insertion_point}' not found in {filepath}")
        return False

    image_tag = f"\n\n![{description}]({relative_link})\n\n"
    new_content = pattern.sub(f"\\1{image_tag}", content, count=1)

    write_file(filepath, new_content)
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python bulk_image_processor.py <json_file>")
        sys.exit(1)

    json_file = sys.argv[1]
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    plan_content = read_file(PLAN_FILE) or ""
    next_id = get_next_id()

    for file_task in data['files']:
        file_path = file_task['file_path']
        filename = os.path.basename(file_path)
        content = read_file(file_path)

        if not content:
            print(f"Error: Could not read {file_path}")
            continue

        print(f"Processing {filename}...")

        for image in file_task['images']:
            description = image.get('description_suffix', 'image').replace(' ', '_').lower()
            base_name = os.path.splitext(filename)[0]
            proposed_filename = f"{base_name}_{description}.png"

            # Uniqueness check with versioning
            version = 1
            final_filename = proposed_filename
            while not check_uniqueness(final_filename, content, plan_content):
                version += 1
                final_filename = f"{base_name}_{description}_v{version}.png"
                if version > 10: # Safety break
                    print(f"Skipping {proposed_filename} due to uniqueness failure")
                    break

            if version > 10: continue

            relative_link = f"./picture/{final_filename}"
            prompt = image['prompt']
            insertion_point = image['insertion_point']

            # Append to plan
            append_to_plan(next_id, filename, final_filename, relative_link, prompt, insertion_point)

            # Update Markdown
            if insert_image_tag(file_path, content, insertion_point, relative_link, image.get('alt_text', description)):
                # Refresh content for next iteration in same file
                content = read_file(file_path)
                # Update plan content in memory to prevent dups in same run
                plan_content += f"| {next_id} | {filename} | {final_filename} | ...\n"
                print(f"  Added {final_filename}")
                next_id += 1
            else:
                print(f"  Failed to insert {final_filename}")

if __name__ == "__main__":
    main()
