# merge all files in a directory into a single one
import os
import json

input_dir = "../data/spanish/mcq-answers"
output_path = "../data/spanish/mcq-answers-all.jsonl"

files = [file for file in os.listdir(input_dir) if file.endswith('.jsonl')]

all_questions = []
for file in files:
    file_path = os.path.join(input_dir, file)
    with open(file_path, 'r') as f:
        data = f.readlines()
        data = [json.loads(line) for line in data]
        all_questions.extend(data)

# convert answers from letter to integer
out_questions = []
for q in all_questions:
    if q['answer'] == None:
        continue

    if q['answer'].lower() == 'a':
        q['answer'] = 1
    elif q['answer'].lower() == 'b':
        q['answer'] = 2
    elif q['answer'].lower() == 'c':
        q['answer'] = 3
    elif q['answer'].lower() == 'd':
        q['answer'] = 4

    out_questions.append(q)


with open(output_path, 'w') as f:
    for d in out_questions:
        f.write(json.dumps(d, ensure_ascii=False) + '\n')