import sys
import os

PLAN_FILE = "docs/picture/image_generation_plan.md"

def get_next_id():
    if not os.path.exists(PLAN_FILE):
        return 1
    with open(PLAN_FILE, "r") as f:
        lines = f.readlines()

    # Skip header and find last ID
    last_id = 0
    for line in lines:
        if line.strip().startswith("|") and not line.strip().startswith("| ID"):
            try:
                parts = line.split("|")
                if len(parts) > 1:
                    current_id = int(parts[1].strip())
                    if current_id > last_id:
                        last_id = current_id
            except ValueError:
                continue
    return last_id + 1

def append_plan(filename, proposed_filename, relative_link, prompt, insertion_point):
    next_id = get_next_id()
    # Format prompt: replace newlines with <br>
    formatted_prompt = prompt.replace("\n", "<br>").replace("\\n", "<br>")

    # Escape pipes in content if any (though unlikely for these fields, good practice)
    # But usually we just assume content doesn't have pipes or we'd need more complex csv handling.
    # Markdown tables use pipes.

    row = f"| {next_id} | {filename} | {proposed_filename} | {relative_link} | {formatted_prompt} | {insertion_point} |\n"

    with open(PLAN_FILE, "a") as f:
        f.write(row)
    print(f"Appended plan ID {next_id}")

def insert_tag(filepath, relative_link, insertion_point, description):
    with open(filepath, "r") as f:
        content = f.read()

    if relative_link in content:
        print(f"Image already exists in {filepath}")
        return

    # Create image tag
    image_tag = f"\n\n![{description}]({relative_link})\n\n"

    # Find insertion point
    if insertion_point not in content:
        print(f"Error: Insertion point '{insertion_point}' not found in {filepath}")
        sys.exit(1)

    # Replace
    new_content = content.replace(insertion_point, insertion_point + image_tag)

    with open(filepath, "w") as f:
        f.write(new_content)
    print(f"Inserted tag into {filepath}")

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "append_plan":
        # args: filename, proposed_filename, relative_link, prompt, insertion_point
        append_plan(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
    elif mode == "insert_tag":
        # args: filepath, relative_link, insertion_point, description
        insert_tag(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    else:
        print("Unknown mode")
        sys.exit(1)
