import json
import os
import sys

IMAGE_TASKS_FILE = "image_tasks.json"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 append_task.py <temp_json_file>")
        sys.exit(1)

    temp_file = sys.argv[1]

    if not os.path.exists(temp_file):
        print(f"Error: Temp file {temp_file} does not exist.")
        sys.exit(1)

    with open(temp_file, "r", encoding="utf-8") as f:
        new_tasks = json.load(f)

    if not isinstance(new_tasks, list):
        new_tasks = [new_tasks]

    existing_tasks = []
    if os.path.exists(IMAGE_TASKS_FILE):
        try:
            with open(IMAGE_TASKS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    existing_tasks = json.loads(content)
        except json.JSONDecodeError:
            print("Warning: image_tasks.json was empty or invalid. Starting fresh.")
            existing_tasks = []

    existing_tasks.extend(new_tasks)

    with open(IMAGE_TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_tasks, f, indent=4, ensure_ascii=False)

    print(f"Appended tasks from {temp_file} to {IMAGE_TASKS_FILE}")

if __name__ == "__main__":
    main()
