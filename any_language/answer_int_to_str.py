import json
import sys
from pathlib import Path

def convert_answers(input_file):
    # Load the JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Convert answers to strings
    for entry in data:
        if 'answer' in entry:
            if isinstance(entry['answer'], int):
                entry['answer'] = str(entry['answer'])

    # Create output filename
    input_path = Path(input_file)
    output_file = input_path.with_name(f"{input_path.stem}_converted{input_path.suffix}")

    # Save the updated data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Conversion complete. Updated file saved as: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python convert_answers.py <input_json_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    convert_answers(input_file)
