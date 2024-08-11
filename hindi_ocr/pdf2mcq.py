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
from openai import (
    OpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)
from pdf2image import convert_from_path

# from utils import parse_gpt_output


pre_prompt = """Please extract the multiple-choice questions in the attached image in the {} language in which they appear. The question should be inside the tags  <question> </question> and the choices inside the tags <choices> </choices>. Additionally, the correct answer might be present in the image either explicitly provided or by a mark next to the correct answer of the multiple choices. Provide the number or letter of the correct answer between the tags <answer> </answer>. If no answer is present, leave empty.
The output format should be the following, depending on the number of choices present:
<question> </question>
<choices>
</choices>
<answer> </answer>
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


def chat_completion(
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


def encode_image(image_path):
    """
    Function to encode the image
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def main(pdf_path, openai_key, language, pages=1000):
    """
    It performs the main text extraction pipeline of the script.

    :param dir_path: str
    :param openai_key: str
    """
    # create client with openai credentials
    client = OpenAI(api_key=openai_key)

    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]

    # Define paths for 'imgs' and 'results' folders
    imgs_folder = os.path.join("imgs", pdf_name)
    parsed_folder = os.path.join("results", pdf_name)
    # Create directories if they don't exist
    os.makedirs(imgs_folder, exist_ok=True)
    os.makedirs(parsed_folder, exist_ok=True)
    images = convert_from_path(pdf_path, first_page=1, last_page=pages)

    # Step 2: Preprocess the image (deskew)
    results = list()
    for i, image in enumerate(images):
        print("Page: {} / {}".format(i, len(images)))
        image_path = os.path.join(imgs_folder, f"page_{i+1}.png")
        image.save(image_path, "PNG")
        base64_image = encode_image(image_path)

        # Step 3: Pass img to gpt-4 for mcq extraction
        try:
            message = [
                {"type": "text", "text": pre_prompt.format(language)},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
            response, _ = chat_completion(
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
            # Step 4: Process gpt-4 output
            questions, choices = parse_gpt_output(response)
            if len(questions) > 0 and len(choices) > 0:
                for question, options in zip(questions, choices):
                    new_row = {
                        "language": language,
                        "category_en": None,
                        "category_original_lang": None,
                        "level": None,
                        "region_related": None,
                        "source": pdf_name,
                        "page_num": i,
                        "response": response,
                        "question": question,
                        "options": options,
                        "answer": None,
                    }

                    results.append(new_row)
            print("Questions extracted: {}".format(len(results)))

        except openai.BadRequestError:
            pass
    # store extracted questions
    output_folder = os.path.join(parsed_folder, "gpt4_o")
    os.makedirs(output_folder, exist_ok=True)
    output_file = os.path.join(output_folder, pdf_name + ".json")

    # Save the results to a JSON file
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, indent=4, ensure_ascii=False)

    print("Data saved: {}".format(output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("pdf_path", type=str, help="Path to the PDF file.")
    parser.add_argument(
        "-l", "--lang", type=str, default="english", help="Language(s) for the PDF"
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1000,
        help="Maximum number of pages to process (default: 1000).",
    )
    parser.add_argument(
        "-k",
        "--key",
        help="OpenAI API Key",
    )

    args = parser.parse_args()
    main(
        pdf_path=args.pdf_path,
        openai_key=args.key,
        language=args.lang,
        pages=args.pages,
    )
