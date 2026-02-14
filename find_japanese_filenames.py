import glob
import re
import os

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

# Regex for non-ascii characters followed by image extension
# We look for a sequence that contains at least one non-ascii char and ends with an image extension.
# It should probably be part of a path or filename.
# Simplest: capture the whole string that looks like a filename with non-ascii.
pattern = re.compile(r'([a-zA-Z0-9_\-\./\\]*[^\x00-\x7f]+[a-zA-Z0-9_\-\./\\]*\.(?:png|jpg|jpeg|webp))')

for file_path in files:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                matches = pattern.findall(line)
                for match in matches:
                    print(f"{file_path}:{i+1}: {match.strip()}")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
