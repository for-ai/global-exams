# PDF Multiple Choice Question Extractor

This Python script extracts multiple-choice questions from PDF files using OpenAI's GPT-4o vision model. It's designed to process Swedish medical exam questions but can be adapted for other languages and subjects.

## Features

- Extracts multiple-choice questions from PDF files
- Maintains the original language (Swedish by default)
- Handles special cases such as invalid questions or multiple correct answers
- Saves extracted questions in JSON format

## Sample data row: 

```json
{
  "language": "sv",
  "country": "Sweden",
  "file_name": "example_exam.pdf",
  "source": "https://www.umu.se/utbildning/sok/kunskapsprov/kunskapsprov-for-lakare/teoretiskt-delprov/",
  "license": "unknown",
  "level": "graduate",
  "category_en": "Medicine",
  "category_original_lang": "Medicin",
  "original_question_num": 1,
  "question": "En 45-årig kvinna söker på vårdcentralen för trötthet och viktuppgång. Hon har också noterat att hon fryser lätt. Vilken av följande laboratorieundersökningar är mest lämplig att beställa initialt?",
  "options": [
    "A. TSH",
    "B. T3",
    "C. T4",
    "D. TPO-antikroppar",
    "E. Kortisol"
  ],
  "answer": "A. TSH"
}
```

By automating the extraction process, it saves significant time and effort compared to manual transcription.

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/for-ai/global-exams.git
   cd global-exams/swedish_multimodal
   ```

2. Create a virtual environment (optional but recommended):
    ```
    conda create -n mcq python=3.10
    ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your OpenAI API key:
   - Create a `.env` file in the project root (don't forget to add it to .gitignore!)
   - Add your API key: `OPENAI_API_KEY=your_api_key_here`

## Usage

1. Use `pdf_parser.py` to extract questions from PDF files:
```
python pdf_parser.py -d /path/to/pdf/directory -l language
```

- `-d` or `--dir`: Directory containing the PDF files (default is "pdfs")
- `-l` or `--lang`: Language of the questions (default is "swedish")

or if you have specified the default language and directory: 
```
python pdf_parser.py
```
The script will process all PDF files in the specified directory and save the extracted questions as JSON files in the `pdfs/mcq` subdirectory.

2. Clean the extracted data using `pdf_cleaner.py`:
   ```python
   # In pdf_cleaner.py
   INPUT_FILE = "pdfs/mcq/your_input_file.json"
   OUTPUT_FILE = "pdfs/mcq/cleaned_output_file.json"
   EXCLUDE_NUMBERS = [90, 91, 94, 118, 125, 128]  # Adjust as needed
   
   # Run the script
   python pdf_cleaner.py
   ```

3. Merge cleaned JSON files using `merge_json_files.py`:
   ```python
   # In merge_json_files.py
   INPUT_FOLDER = "checked" # or "pdfs/mcq", or wherever you have the checked and cleaned json files.
   OUTPUT_FILE = "merged_dataset.json"
   
   # Run the script
   python merge_json_files.py
   ```

4. Format the answer column: 
Due to the response format of the dataset_checker.py file, we need to format the answer column to indicate the number of the correct answer among the options, and not the answer itself.
This is done in the json_formatter.py file. Set the dataset names as follows, where the first is the input file and the second is the output file, and run the script:
   ```python
   process_dataset('merged_dataset.json', 'final_dataset.json')
   ```

5. Checking the dataset: 
Check the dataset formatting by comparing with the desired format for any inconsistencies or errors. Do this by running the dataset_checker.py file. Specify the json file you want to check:
   ```
   python dataset_checker.py --json_file your_dataset.json
   ```

### Publishing to Hugging Face

To publish the dataset to Hugging Face, use the `publish_to_huggingface.py` script:

1. Log in to Hugging Face from the terminal:
   ```
   huggingface-cli login
   ```

2. Set up your Hugging Face token as an environment variable:
   ```
   export HF_TOKEN=your_token_here
   ```

3. Update the `publish_to_huggingface.py` script with your details:
   ```python
   INPUT_FILE = "merged_dataset.json"
   DATASET_NAME = "swedish-medical-exam-mcqs"
   DATASET_DESCRIPTION = "Multiple-choice questions from Swedish medical exams"
   YOUR_USERNAME = "your_huggingface_username"
   ```

4. Update the README.md file in the huggingface folder with the correct dataset description.

5. Run the script:
   ```
   python publish_to_huggingface.py
   ```

After running the script, your dataset will be available on Hugging Face at:
https://huggingface.co/datasets/your_username/swedish-medical-exam-mcqs

## Usage

You can load this dataset using the Hugging Face `datasets` library:

```python
from datasets import load_dataset
dataset = load_dataset("your_username/swedish-medical-exam-mcqs")
```