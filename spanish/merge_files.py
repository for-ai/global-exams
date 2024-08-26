# merge all files in a directory into a single one
import os
import json

input_dir = "data/spanish/mcq-answers"
output_path = "data/spanish/mcq-answers-all.jsonl"

files = [file for file in os.listdir(input_dir) if file.endswith('.jsonl')]

all_questions = []
for file in files:
    file_path = os.path.join(input_dir, file)
    with open(file_path, 'r') as f:
        data = f.readlines()
        data = [json.loads(line) for line in data]
        all_questions.extend(data)

with open(output_path, 'w') as f:
    for d in all_questions:
        f.write(json.dumps(d, ensure_ascii=False) + '\n')