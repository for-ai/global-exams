from os import listdir
from os.path import isfile, join
import os
import re
import json
import time
import base64
import pandas as pd
import argparse
import openai
from cohere import Client as CohereClient
from openai import (
    OpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)
from pdf2image import convert_from_path

pre_prompt = """Extract the multiple-choice questions from the text in the {} language given below. The question should be inside the tags  <question> </question> and the choices inside the tags <choices> </choices>. Additionally, the correct answer might be present in the image either explicitly provided or by a mark next to the correct answer of the multiple choices. Provide the number or letter of the correct answer between the tags <answer> </answer>. If no answer is present, leave empty.
The output format should be the following, depending on the number of choices present:
<question> </question>
<choices>
</choices>
<answer> </answer>

{}
"""


def parse_gpt_output(response):
    question_pattern = re.compile(r"<question>(.*?)</question>", re.DOTALL)
    choices_pattern = re.compile(r"<choices>(.*?)</choices>", re.DOTALL)
    answer_pattern = re.compile(r"<answer>(.*?)</answer>", re.DOTALL)

    # Find all matches for questions
    question_matches = question_pattern.findall(response)
    choices_matches = choices_pattern.findall(response)
    # answer_matches = answer_pattern.findall(response)
    return question_matches, choices_matches


def chat_completion_cohere(
    client,
    messages,
    temperature=0.0,
    max_tokens=4096,
) -> str:
    output = None
    for _ in range(10):
        try:
            response = client.chat(
                message=messages,
                # preamble="",
                model="command-r-plus",
                temperature=temperature,
                max_tokens=max_tokens,
            )
            output = response.dict().get("text")
            break
        # except any exception
        except Exception as e:
            print(f"Failed to connect to Cohere API: {e}")
            time.sleep(20)
    return output


def chat_completion_openai(
    client,
    messages,
    model,
    return_text=True,
    return_usage=True,
    model_args=None,
):
    """
    Calls openai API with the image and the prompt

    :param client: OpenAI client
    :param messages: list, array of messages
    :param model: str
    :param return_text: bool
    :param return_usage: bool
    :param model_args:
    return: dict
    """
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


def main(txt_path, api_key, lang="Hindi", api_type="openai"):
    """
    It performs the main text extraction pipeline of the script.

    :param dir_path: str
    :param openai_key: str
    """
    # create client with openai credentials
    if "cohere" in api_type:
        client = CohereClient(api_key=api_key)
    else:
        client = OpenAI(api_key=api_key)
    f = open(txt_path, "r")
    answer_txt = f.read()
    print(answer_txt)

    path_parts = txt_path.split(os.sep)

    # Construct the new path
    new_directory = os.path.join(
        "results_cohere", path_parts[-3], "mcq", path_parts[-2]
    )
    json_file_path = os.path.join(new_directory, path_parts[-1])
    json_file_path = json_file_path.replace(".txt", ".json")

    os.makedirs(new_directory, exist_ok=True)

    try:
        if "openai" in api_type:
            message = [{"type": "text", "text": pre_prompt.format(lang, answer_txt)}]
            response, _ = chat_completion_openai(
                client,
                [{"role": "user", "content": message}],
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
        else:
            message = [pre_prompt.format(lang, answer_txt)]
            response = chat_completion_cohere(
                client, message[0], temperature=0.0, max_tokens=4096
            )
        # Step 4: Process gpt-4 output

    except openai.BadRequestError:
        pass
    # store extracted questions
    results = []
    questions, choices = parse_gpt_output(response)
    if len(questions) > 0 and len(choices) > 0:
        for question, options in zip(questions, choices):
            new_row = {
                "language": lang,  # hardcode for now
                "category_en": None,
                "category_original_lang": None,
                "level": None,
                "region_related": None,
                "source": path_parts[-3],
                "page_num": txt_path[-5],
                "response": response,
                "question": question,
                "options": options,
                "answer": None,
            }

            results.append(new_row)

    # Save the results to a JSON file
    with open(json_file_path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, indent=4, ensure_ascii=False)

    print("Data saved: {}".format(json_file_path))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "txt_path", type=str, help="Path to the txt file from tesseract."
    )
    parser.add_argument(
        "--api_type", type=str, help="openai or cohere.", default="openai"
    )
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default="hindi",
        help="Language(s) for Tesseract OCR (default: eng).",
    )
    parser.add_argument(
        "-k",
        "--key",
        help="OpenAI API Key or Cohere Key",
        default="",
    )

    args = parser.parse_args()
    main(
        txt_path=args.txt_path,
        api_key=args.key,
        lang=args.lang,
        api_type=args.api_type,
    )
