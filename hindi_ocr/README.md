### Requirements

```bash
pip install openai cohere pdf2image
```

To install Tesseract, follow the instructions provided [here](https://tesseract-ocr.github.io/tessdoc/Installation.html).

### Directory Structure

1. **`parse_pdfs_tesseract.py`** - Processes PDFs page by page and parses them using Tesseract OCR.
2. **`text2mcq.py`** - Takes the extracted OCR text from the above script and uses Command-R or GPT-4 to generate questions and options.
3. **`pdf2mcq.py`** - Directly extracts questions and choices from PDFs page by page using GPT-4.
4. **`extract_answer_key_text.py`** - A standalone script for extracting answer keys.
5. **`papers`** - Contains all the exam PDFs and their corresponding answer keys.
6. **`imgs`** - Stores the page-by-page images of each exam.
7. **`results`** - Contains the results from Tesseract + OpenAI & GPT-4.
8. **`results_cohere`** - Contains the results from Tesseract + Command-R & GPT-4.
9. **`answer_keys`** - Stores the extracted answer keys in JSON format.
