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


pre_prompt = """Please extract the multiple-choice questions that are present in the following text. The out format should be the following:
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


def parse_gpt_output(q):
    parts = q.split("\n")
    try:
        question = parts[0]
    except:
        question = None

    try:
        choice_1 = parts[1]
    except:
        choice_1 = None

    try:
        choice_2 = parts[2]
    except:
        choice_2 = None

    try:
        choice_3 = parts[3]
    except:
        choice_3 = None

    try:
        choice_4 = parts[4]
    except:
        choice_4 = None

    try:
        choice_5 = parts[5]
    except:
        choice_5 = None

    return question, choice_1, choice_2, choice_3, choice_4, choice_5


def main(dir_path, openai_key):
    client = OpenAI(api_key=openai_key)

    dir_path_parsed = dir_path + "/parsed"
    onlyfiles = [
        f for f in listdir(dir_path_parsed) if isfile(join(dir_path_parsed, f))
    ]
    print(onlyfiles)
    onlyfiles = ["Ayurveda Therapist.csv", "Fire And Rescue Officer.csv"]
    for f in onlyfiles:
        file_path = os.path.join(dir_path_parsed, f)
        print("Parsing file: {}".format(f))
        pages = pd.read_csv(file_path)

        results = list()
        print(len(pages))
        for _, row in tqdm(pages.iterrows()):
            prompt = "{}\n\n{}".format(pre_prompt, row["parsed_text"])
            response, _ = chat_completion(
                client,
                [{"role": "user", "content": prompt.strip()}],
                model="gpt-4o",
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
            row["output"] = response

            for q in response.split("\n\n"):
                if q:
                    (
                        question,
                        choice_1,
                        choice_2,
                        choice_3,
                        choice_4,
                        choice_5,
                    ) = parse_gpt_output(q)

                    new_row = {
                        "category_a": None,
                        "category_b": None,
                        "category_og_en": None,
                        "category_og": None,
                        "level": None,
                        "year": None,
                        "source": None,
                        "page_num": row["page_num"],
                        "parsed_text": row["parsed_text"],
                        "response": response,
                        "question": question,
                        "choice_1": choice_1,
                        "choice_2": choice_2,
                        "choice_3": choice_3,
                        "choice_4": choice_4,
                        "choice_5": choice_5,
                        "answer": None,
                    }

                    results.append(new_row)

        output_file = os.path.join(dir_path, "mcq", f)
        output_data = pd.DataFrame(results)
        output_data.to_csv(output_file, index=False)
        print("Data saved: {}".format(output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", help="", default="pfds")

    parser.add_argument("-k", "--key", help="", default="")

    args = parser.parse_args()
    main(dir_path=args.dir, client=args.key)
