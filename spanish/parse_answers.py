import os
import re
import json
import argparse
from os import listdir
from os.path import isfile, join

def parse_answers(text):
    result = []
    current_section = None
    section_counter = 1
    
    for line in text.strip().split('\n'):
        # Match lines like "1. A"
        match = re.match(r'^\s*(\d+)\.\s*([A-D])\s*$', line.strip(), re.IGNORECASE)
        if match:
            question_number, answer = match.groups()
            question_number = int(question_number)
            result.append({
                "qid": question_number,
                "answer": answer
            })
    return result


def main(dir_path):

    dir_path_mcq = dir_path + "/mcq"
    onlyfiles = [f for f in listdir(dir_path_mcq) if isfile(join(dir_path_mcq, f))]
    jsonl_files = [f for f in onlyfiles if f.endswith(".jsonl")]

    for file in jsonl_files:
        print("Processing file: ", file)
        file_path = join(dir_path_mcq, file)

        # read file 
        questions = []
        with open(file_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                questions.append(data)

        # read answers file
        answers_file = file.replace(".jsonl", "-respuestas.txt")
        answers_file_path = join(dir_path, "processed",  answers_file)
        with open(answers_file_path, 'r') as f:
            answers_text = f.read()

        # parse answers
        answers = parse_answers(answers_text)
        print("Questions Length: ", len(questions))
        print("Answers Length: ", len(answers))

        for i in range(len(questions)):
            q = questions[i]
            ans_id = answers[i]["qid"]
            if (i+1) % 10 == ans_id:
                pass
            elif ans_id != i+1:
                print(f"Error: qid mismatch: {ans_id} != {i+1}")
                continue
            q["answer"] = answers[i]["answer"]
        
        # write to file
        out_dir = join(dir_path, "mcq-answers")
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        out_path = join(out_dir, file)
        with open(out_path, 'w') as f:
            for q in questions:
                f.write(json.dumps(q, ensure_ascii=False) + '\n')
            print("File written: ", file_path)



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dir', type=str,  default="../data/spanish/")
    args = parser.parse_args()
    
    main(args.dir)
