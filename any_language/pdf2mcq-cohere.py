import pandas as pd
import os
from os import listdir
from os.path import isfile, join
import argparse
from tqdm import tqdm
import cohere
from PyPDF2 import PdfReader

def extract_text_from_pdf_page(pdf_path, page_num):
    reader = PdfReader(pdf_path)
    return reader.pages[page_num].extract_text()

# Define the question format as it appears in the pdf.
QUESTION_FORMAT = """
Pyetja [number]
[Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
"""

def extract_questions(text: str, co: cohere.Client, language: str) -> str:
    prompt = f"""Please extract the multiple-choice questions from the following text. The questions are in {language} and follow this format:

{QUESTION_FORMAT}

Please maintain this exact format in your response, including the prefix and the lettered options. Here's the text:

{text}"""

    response = co.chat(
        model="command-r-plus",
        message=prompt
    )
    return response.text

def parse_cohere_output(output: str):
    questions = []
    current_question = None
    for line in output.split('\n'):
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith('pyetja') or line.lower().startswith('question'):
            if current_question:
                questions.append(current_question)
            current_question = {'question_number': line, 'question_text': '', 'choices': []}
        elif current_question and not current_question['question_text']:
            current_question['question_text'] = line
        elif line.startswith(('A)', 'B)', 'C)', 'D)')):
            if current_question is None:
                current_question = {'question_number': 'Unknown', 'question_text': 'Unknown', 'choices': []}
            current_question['choices'].append(line)
    
    if current_question:
        questions.append(current_question)
    
    return questions

def main(dir_path: str, cohere_api_key: str, language: str):
    co = cohere.Client(api_key=cohere_api_key)
    
    onlyfiles = [f for f in listdir(dir_path) if isfile(join(dir_path, f)) and f.endswith('.pdf')]
    
    for f in onlyfiles:
        print(f"Processing file: {f}")
        pdf_file = f"{dir_path}/{f}"
        reader = PdfReader(pdf_file)
        
        all_questions = []
        for page_num in tqdm(range(len(reader.pages))):
            text = extract_text_from_pdf_page(pdf_file, page_num)
            response = extract_questions(text, co, language)
            questions = parse_cohere_output(response)
            all_questions.extend(questions)
        
        # Save extracted questions
        output_file = f"{f.split('.')[0]}_questions.csv"
        df = pd.DataFrame(all_questions)
        os.makedirs(os.path.join(dir_path, "parsed"), exist_ok=True)
        df.to_csv(os.path.join(dir_path, "parsed", output_file), index=False)
        print(f"Data saved: {output_file}")
        print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", help="Directory containing PDF files", default="pdf")
    parser.add_argument("-k", "--key", help="Cohere API Key", required=True)
    parser.add_argument("-l", "--lang", help="Language of the questions", required=True)
    args = parser.parse_args()
    
    main(dir_path=args.dir, cohere_api_key=args.key, language=args.lang)