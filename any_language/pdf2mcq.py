from os import listdir
from os.path import isfile, join
import os
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

from utils import parse_gpt_output


pre_prompt = """Please extract the multiple-choice questions in the attached image in the {} language in which they appear. The question should be inside the tags  <question> </question> and the choices inside the tags <choices> </choices>. Additionally, the correct answer might be present in the image either explicitly provided or by a mark next to the correct answer of the multiple choices. Provide the number or letter of the correct answer between the tags <answer> </answer>. If no answer is present, leave empty.
The output format should be the following, depending on the number of choices present:
<question> </question>
<choices>
</choices>
<answer> </answer>
"""


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


def main(dir_path, openai_key, language):
    """
    It performs the main text extraction pipeline of the script.

    :param dir_path: str
    :param openai_key: str
    """
    # create client with openai credentials
    client = OpenAI(api_key=openai_key)

    # get files to be processed
    onlyfiles = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
    if ".DS_Store" in onlyfiles:
        onlyfiles.remove(".DS_Store")

    for f in onlyfiles:
        # check the file has the .pdf extension
        if f.endswith(".pdf"):
            # Step 1: Reads the pdf file
            print("Parsing file: {}".format(f))
            pdf_file = "{}/{}".format(dir_path, f)
            pages = convert_from_path(pdf_file)

            # Step 2: Preprocess the image (deskew)
            results = list()
            for i, page in enumerate(pages):
                print("Page: {} / {}".format(i, len(pages)))
                img_name = "{}/imgs/{}_{}.jpg".format(dir_path, f, i)
                page.save(img_name)
                base64_image = encode_image(img_name)

                # Step 3: Pass img to gpt-4 for mcq extraction
                try:
                    message = [
                        {"type": "text", "text": pre_prompt.format(language)},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
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
                                "source": f,
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
            output_file = os.path.join(
                dir_path, "mcq", "{}.json".format(f.split(".")[0])
            )
            output_data = pd.DataFrame(results)
            output_data.to_json(output_file, orient="records")
            print("Data saved: {}".format(output_file))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", help="", default="pdfs")

    parser.add_argument("-k", "--key", help="", default="")

    parser.add_argument("-l", "--lang", help="", default="")

    args = parser.parse_args()
    main(dir_path=args.dir, openai_key=args.key, language=args.lang)
