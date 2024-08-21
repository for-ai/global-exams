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


pre_prompt = """Please extract the answer key from the attached image below. Extract the answer option of each of the questions and provide the response as a json with the key representing the question and its value the multiple choice option. Do not provide anything else.
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


def encode_image(image_path):
    """
    Function to encode the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


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


def main(pdf_path, api_key):
    """
    It performs the main text extraction pipeline of the script.

    :param dir_path: str
    :param openai_key: str
    """
    client = OpenAI(api_key=api_key)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Define paths for 'imgs' and 'results' folders
    parent_directory = os.path.dirname(os.path.dirname(pdf_path))
    imgs_folder = os.path.join(parent_directory, "imgs", pdf_name)
    result_path = os.path.join(parent_directory, "answer_key")
    # Create directories if they don't exist
    os.makedirs(imgs_folder, exist_ok=True)
    os.makedirs(result_path, exist_ok=True)
    images = convert_from_path(pdf_path, first_page=1)

    # Step 2: Preprocess the image (deskew)
    for page_num, image in enumerate(images):
        print("Page: {} / {}".format(page_num + 1, len(images)))
        image_path = os.path.join(imgs_folder, f"page_{page_num+1}.png")
        image.save(image_path, "PNG")
        base64_image = encode_image(image_path)

        try:
            message = [
                {"type": "text", "text": pre_prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
            ]
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
        output_file = os.path.join(
            result_path, pdf_name + f"_page_{page_num}.json"
        )
        # Save the results to a JSON file
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(response, json_file, indent=4, ensure_ascii=False)
        print("Data saved: {}".format(output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pdf_path", type=str, help="Path to the txt file from tesseract."
    )
    parser.add_argument(
        "-k",
        "--key",
        help="OpenAI API Key or Cohere Key",
    )

    args = parser.parse_args()
    main(pdf_path=args.pdf_path, api_key=args.key)
