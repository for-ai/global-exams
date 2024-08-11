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

pre_prompt = """Below provided is an answer key. Extract the answer option of each of the questions and provide the response as a json with the key representing the question and its value the multiple choice option. Do not provide anything else.

{}
"""

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
    client, messages, model, return_text=True, return_usage=True, model_args=None
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


def main(txt_path, api_key, api_type="openai"):
    """
    It performs the main text extraction pipeline of the script.

    :param dir_path: str
    :param openai_key: str
    """

    if "cohere" in api_type:
        client = CohereClient(api_key=api_key)
    else:
        client = OpenAI(api_key=api_key)
    f = open(txt_path, "r")
    answer_txt = f.read()
    print(answer_txt)

    txt_path_parts = os.path.normpath(txt_path).split(os.sep)
    txt_file_name = "_".join(txt_path_parts)
    txt_file_name = os.path.splitext(txt_file_name)[0]

    answer_key_folder = os.path.join("answer_keys", api_type)
    os.makedirs(answer_key_folder, exist_ok=True)

    try:
        if "openai" in api_type:
            message = [{"type": "text", "text": pre_prompt.format(answer_txt)}]
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
            message = [pre_prompt.format(answer_txt)]
            response = chat_completion_cohere(
                client,
                message[0],
                temperature=0.0,
                max_tokens=4096
            )

    except openai.BadRequestError:
        pass
    # store extracted questions
    response = (
        response.replace("```", "")
        .replace("json", "")
        .replace(" ", "")
        .replace("\n", "")
    )
    try:
        response = json.loads(response)
    except Exception as e:
        raise ValueError(e)
    output_file = os.path.join(answer_key_folder, txt_file_name + ".json")

    # Save the results to a JSON file
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(response, json_file, indent=4, ensure_ascii=False)

    print("Data saved: {}".format(output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "txt_path", type=str, help="Path to the txt file from tesseract."
    )
    parser.add_argument(
        "--api_type", type=str, help="openai or cohere.", default="openai"
    )
    parser.add_argument(
        "-k",
        "--key",
        help="OpenAI API Key or Cohere Key",
    )

    args = parser.parse_args()
    main(txt_path=args.txt_path, api_key=args.key, api_type=args.api_type)
