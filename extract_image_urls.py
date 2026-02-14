import glob
import re
import json
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

# Regex for markdown image links: ![alt](url)
# Capture group 1 is the URL
md_link_pattern = re.compile(r'!\[.*?\]\((.*?)\)')
# Regex for HTML img tags: src="url"
html_src_pattern = re.compile(r'src=["\'](.*?)["\']')

results = []
seen = set()

for file_path in files:
    if not os.path.exists(file_path):
        continue
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Find Markdown links
            for match in md_link_pattern.finditer(content):
                url = match.group(1)
                # Check for Japanese/non-ascii
                if any(ord(c) > 127 for c in url):
                    # We accept it if it looks like an image
                    if url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif')):
                        if url not in seen:
                            results.append({"file": file_path, "url": url})
                            seen.add(url)
                            
            # Find HTML src
            for match in html_src_pattern.finditer(content):
                url = match.group(1)
                if any(ord(c) > 127 for c in url):
                     if url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.svg', '.gif')):
                        if url not in seen:
                            results.append({"file": file_path, "url": url})
                            seen.add(url)

    except Exception as e:
        print(f"Error reading {file_path}: {e}")

with open('japanese_image_urls.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
