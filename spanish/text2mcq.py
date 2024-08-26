import re
import json
import pandas as pd
import argparse
from openai import (
    OpenAI,
    AzureOpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)
from tqdm import tqdm
import time
from os import listdir
from os.path import isfile, join
import os


pre_prompt = """Please extract the multiple-choice questions that are present in the following text. 
Do not modify the original text in any form. It housl be copied as it is.
If you find text unrelated to the questions, please ignore it.
The output format should be the following:
<Question>
1. <Choice 1>
2. <Choice 2>
3. <Choice 3>
4. <Choice 4>

The text is the following:"""


def chat_completion(
    client, messages, model, return_text=True, return_usage=True, model_args=None
):
    if model_args is None:
        model_args = {}

    while True:
        try:
            response = client.chat.completions.create(
                model=model, messages=messages, **model_args
            )
            text = response.choices[0].message.content.strip()
            usage = response.usage

            if return_text and return_usage:
                return text, dict(usage)

            if return_text:
                return text

            if return_usage:
                return usage

            return response
        except (
            APITimeoutError,
            APIConnectionError,
            RateLimitError,
            InternalServerError,
        ) as e:
            print(f"OpenAI error: {str(e)}. Waiting for 1 minute.")
            time.sleep(60)
            continue

def remove_initial_number(option):
    # if first character is a number, remove it
    option = option.strip()
    if option[0].isdigit():
        return option[2:].strip()
    return option.strip()

def remove_options(text):
    cleaned_text = re.sub(r'\b[a-z]\)\s*', '', text)
    return cleaned_text

def parse_gpt_output(q):
    parts = q.split("\n")
    try:
        question = parts[0]
        question = remove_initial_number(question)
        question = question.strip(",. ")
    except:
        question = None

    try:
        choice_1 = parts[1]
        choice_1 = remove_initial_number(choice_1)
        choice_1 = remove_options(choice_1)
    except:
        choice_1 = None

    try:
        choice_2 = parts[2]
        choice_2 = remove_initial_number(choice_2)
        choice_2 = remove_options(choice_2)
    except:
        choice_2 = None

    try:
        choice_3 = parts[3]
        choice_3 = remove_initial_number(choice_3)
        choice_3 = remove_options(choice_3)
    except:
        choice_3 = None

    try:
        choice_4 = parts[4]
        choice_4 = remove_initial_number(choice_4)
        choice_4 = remove_options(choice_4)
    except:
        choice_4 = None

    return question, choice_1, choice_2, choice_3, choice_4


def split_text_into_chunks(text, max_length=1500):
    # Use a regular expression to identify the start of each question
    question_pattern = re.compile(r'^\d+\.\s', re.MULTILINE)
    
    # Split the text based on the pattern that matches the start of a question
    parts = question_pattern.split(text)
    
    # Reattach the question number to the beginning of each block
    question_blocks = []
    matches = list(question_pattern.finditer(text))
    
    for i, part in enumerate(parts):
        if i < len(matches):
            question_blocks.append(matches[i].group(0) + part.strip())
        else:
            if part.strip():
                question_blocks.append(part.strip())
    
    chunks = []
    current_chunk = ""

    for block in question_blocks:
        block = block.strip()
        # If adding the next block would exceed the max_length, store the current chunk and start a new one
        if len(current_chunk) + len(block) + 2 > max_length:  # 2 accounts for added "\n\n"
            chunks.append(current_chunk.strip())
            current_chunk = ""

        # Add the question block to the current chunk
        current_chunk += block + "\n\n"

    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
        

def main(dir_path):
    # client = OpenAI(api_key=openai_key)
    client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-abc123"
    )

    dir_path_parsed = dir_path + "/processed"
    onlyfiles = [
        f for f in listdir(dir_path_parsed) if isfile(join(dir_path_parsed, f))
    ]
    # remove files containing "respuestas"
    onlyfiles = [f for f in onlyfiles if "respuestas" not in f]
    
    for f in onlyfiles:
        file_path = os.path.join(dir_path_parsed, f)
        print("Parsing file: {}".format(f))

        results = list()

        # read txt file
        with open(file_path, "r") as file:
            text = file.read()

        # split text 
        texts = split_text_into_chunks(text)
        # print("Number of text blocks: ", len(texts))
        # print("Chars in last block: ", len(texts[-1]))
        # print("i blocks: ", texts[-3])


        q_id = 1
        for text_block in tqdm(texts):
            prompt = "{}\n\n{}".format(pre_prompt, text_block)
            response, _ = chat_completion(
                client,
                [{"role": "user", "content": prompt.strip()}],
                model="meta-llama/Meta-Llama-3.1-70B-Instruct",
                return_text=True,
                return_usage=True,
                model_args={
                    "temperature": 0.0,
                    "max_tokens": 4096,
                    "top_p": 1,
                    "frequency_penalty": 0,
                    "presence_penalty": 0,
                },
            )

            for q in response.split("\n\n"):
                if q:
                    (
                        question,
                        choice_1,
                        choice_2,
                        choice_3,
                        choice_4,
                    ) = parse_gpt_output(q)
                    if question is None or choice_1 is None or choice_2 is None \
                        or choice_3 is None or choice_4 is None:
                        continue

                    new_row = {
                        "question": question,
                        "options": [choice_1, choice_2, choice_3, choice_4],
                        "answer": None,
                        "language": "es", 
                        "country": "Spain",
                        "file_name": f,
                        "source": "https://sede.inap.gob.es/en/procesos-selectivos",
                        "license": "AGPL (Affero General Public License) , GPL (GNU General Public License)",
                        "level": "Professional",
                        "category_en": "Law and Government",
                        "category_original_lang": "Derecho y Gobierno",
                        "original_question_num": q_id,
                    }
                    q_id += 1
                    results.append(new_row)

                    if q_id == 70:
                        break

        # save data in jsonl format
        output_file = os.path.join(dir_path, "mcq", f)
        output_file = output_file.replace(".txt", ".jsonl")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            for item in results:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print("Data saved: {}".format(output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", help="", default="../data/spanish/")
    # parser.add_argument("-k", "--key", help="", default="")

    args = parser.parse_args()
    main(dir_path=args.dir)
