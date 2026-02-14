import json

try:
    with open('japanese_filenames.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    unique_matches = sorted(list(set(item['match'] for item in data)))
    
    # Print as JSON for easy reading
    print(json.dumps(unique_matches, ensure_ascii=False, indent=2))
except Exception as e:
    print(f"Error: {e}")
