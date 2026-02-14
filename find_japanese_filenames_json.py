import glob
import re
import os
import json

files = [
    'docs/picture/image_generation_plan.md',
    'docs/idem_ts_study_017.md',
    'docs/idem_ts_study_018.md',
    'docs/idem_ts_study_019.md',
    'docs/idem_ts_study_020.md',
    'docs/idem_ts_study_021.md',
    'docs/idem_ts_study_022.md',
    'docs/idem_ts_study_023.md'
]

pattern = re.compile(r'([a-zA-Z0-9_\-\./\\]*[^\x00-\x7f]+[a-zA-Z0-9_\-\./\\]*\.(?:png|jpg|jpeg|webp))')

results = []

for file_path in files:
    if not os.path.exists(file_path):
        continue
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                matches = pattern.findall(line)
                for match in matches:
                    results.append({
                        "file": file_path,
                        "line": i + 1,
                        "match": match.strip()
                    })
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

with open('japanese_filenames.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Done writing to japanese_filenames.json")
