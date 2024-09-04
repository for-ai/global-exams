import os
import time
import base64
import json
import argparse
import re
import openai
from openai import (
    OpenAI,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
    InternalServerError,
)
import fitz  # PyMuPDF
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def parse_gpt_output(response):
    # Regular expressions to match question number, question, choices, and answer
    question_num_pattern = r'<question_number>(.*?)</question_number>'
    question_pattern = r'<question>(.*?)</question>'
    choices_pattern = r'<choices>(.*?)</choices>'
    answer_pattern = r'<answer>(.*?)</answer>'

    # Find all matches
    question_nums = re.findall(question_num_pattern, response, re.DOTALL)
    questions = re.findall(question_pattern, response, re.DOTALL)
    choices = re.findall(choices_pattern, response, re.DOTALL)
    answers = re.findall(answer_pattern, response, re.DOTALL)

    # Process the results
    parsed_data = []
    for qn, q, c, a in zip(question_nums, questions, choices, answers):
        # Strip whitespace and split choices into a list
        question_num = qn.strip()
        question = q.strip()
        choice_list = [choice.strip() for choice in c.strip().split('\n') if choice.strip()]
        answer = a.strip()

        # Handle special cases
        if question.lower() == 'invalid' or not choice_list:
            question = 'invalid'
            choice_list = ['invalid']
            answer = 'invalid'

        parsed_data.append({
            'question_number': question_num,
            'question': question,
            'choices': choice_list,
            'answer': answer
        })

    return parsed_data

pre_prompt = """Extract the multiple-choice questions from the attached image, maintaining the Swedish language in which they appear. Follow these guidelines:

1. Enclose the question number within `<question_number></question_number>` tags.
2. Enclose the full question text within `<question></question>` tags.
3. List all answer choices within `<choices></choices>` tags, with each choice on a new line.
4. If a correct answer is indicated, enclose it within `<answer></answer>` tags.
5. Include the full question with any context provided before the actual question.

Special Cases:
- If no correct answer is indicated, use `<answer>invalid</answer>`.
- If multiple correct answers are indicated, use `<answer>invalid</answer>`.
- For questions containing visual elements (graphs, charts, images, etc.), use `<question>invalid</question>`, `<choices>invalid</choices>`, and `<answer>invalid</answer>`.

Output Format:
<question_number>Question number</question_number>
<question>Full question text in Swedish</question>
<choices>
Choice 1
Choice 2
Choice 3
...
</choices>
<answer>Correct answer or "invalid"</answer>

ALWAYS DOUBLE CHECK YOUR RESPONSE FOR THE SPECIAL CASES. NO ANSWER, DOUBLE ANSWERS, QUESTIONS WITH IMAGES. YOU MUST PAY INCREDIBLE ATTENTION TO YOUR RESPONSES, AND YOU WILL BE REWARDED.
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

def process_pdf(pdf_file, dir_path, client, language):
    """
    Process a single PDF file
    """
    print(f"Parsing file: {pdf_file}")
    pdf_document = fitz.open(os.path.join(dir_path, pdf_file))
    results = []

    # Ensure the imgs folder exists
    imgs_folder = os.path.join(dir_path, "imgs")
    os.makedirs(imgs_folder, exist_ok=True)

    for i, page in enumerate(pdf_document):
        print(f"Page: {i+1} / {len(pdf_document)}")
        
        # Convert page to image
        pix = page.get_pixmap()
        img_name = os.path.join(imgs_folder, f"{pdf_file}_{i+1}.png")
        pix.save(img_name)

        base64_image = encode_image(img_name)

        # Pass img to gpt-4 for mcq extraction
        try:
            message = [
                {"type": "text", "text": pre_prompt.format(language)},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_image}"
                    },
                },
            ]
            response, _ = chat_completion(
                client,
                [{"role": "user", "content": message}],
                model="gpt-4o-2024-08-06",
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

            # Process gpt-4 output
            parsed_data = parse_gpt_output(response)
            for item in parsed_data:
                new_row = {
                    "language": "sv",
                    "country": "Sweden",
                    "file_name": pdf_file,
                    "source": "https://www.umu.se/utbildning/sok/kunskapsprov/kunskapsprov-for-lakare/teoretiskt-delprov/",
                    "license": "unknown",
                    "level": "graduate",
                    "category_en": "Medicine",
                    "category_original_lang": "Medicin",
                    "original_question_num": item['question_number'],
                    "question": item['question'],
                    "options": item['choices'],
                    "answer": item['answer'],
                }
                results.append(new_row)
            print(f"Questions extracted: {len(parsed_data)}")

        except openai.BadRequestError:
            print(f"Error processing page {i+1}")

        # Remove the temporary image file
        os.remove(img_name)

    # Close the PDF document
    pdf_document.close()

    return results

def main(dir_path, language):
    """
    It performs the main text extraction pipeline of the script.

    :param dir_path: str
    :param language: str
    """
    # Get the API key from the environment variable
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # create client with openai credentials
    client = OpenAI(api_key=openai_key)

    # get files to be processed
    pdf_files = [f for f in os.listdir(dir_path) if f.endswith(".pdf")]

    # Ensure the mcq folder exists
    mcq_folder = os.path.join(dir_path, "mcq")
    os.makedirs(mcq_folder, exist_ok=True)

    for pdf_file in pdf_files:
        results = process_pdf(pdf_file, dir_path, client, language)

        # store extracted questions
        output_file = os.path.join(mcq_folder, f"{pdf_file.split('.')[0]}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Data saved: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", help="", default="pdfs")

    parser.add_argument("-l", "--lang", help="", default="swedish")

    args = parser.parse_args()
    main(dir_path=args.dir, language=args.lang)