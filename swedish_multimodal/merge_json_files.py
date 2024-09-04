import json
import os
from typing import List, Dict

# Input and output paths
INPUT_FOLDER = "checked"
OUTPUT_FILE = "merged_dataset.json"

def read_json_file(file_path: str) -> List[Dict]:
    """Read and return data from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json_file(file_path: str, data: List[Dict]):
    """Write data to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def merge_json_files(folder_path: str) -> List[Dict]:
    """Merge all JSON files in the given folder."""
    merged_data = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            file_path = os.path.join(folder_path, filename)
            data = read_json_file(file_path)
            merged_data.extend(data)
    return merged_data

def main():
    # Merge all JSON files in the input folder
    merged_data = merge_json_files(INPUT_FOLDER)

    # Write merged data to output file
    write_json_file(OUTPUT_FILE, merged_data)

    print(f"Merged dataset saved to {OUTPUT_FILE}")
    print(f"Total questions in merged dataset: {len(merged_data)}")

if __name__ == "__main__":
    main()