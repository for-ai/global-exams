import os
from os import listdir
from os.path import isfile, join
import PyPDF2
import argparse
from tqdm import tqdm

def pdf_to_text(pdf_path):
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        # Create a PDF reader object
        reader = PyPDF2.PdfReader(file)
        # Initialize text variable
        text = ''
        
        # Iterate through all the pages
        for page_num in range(len(reader.pages)):
            # Extract text from each page
            page = reader.pages[page_num]
            text += page.extract_text()
        
    return text

def main(input_dir, output_dir):
    # read pdf files in the input directory
    onlyfiles = [f for f in listdir(input_dir) if isfile(join(input_dir, f))]
    onlyfiles = [f for f in onlyfiles if f.endswith(".pdf")]
    for f in tqdm(onlyfiles):
        # Step 1: Reads the pdf file
        print("Parsing file: {}".format(f))
        pdf_file = "{}/{}".format(input_dir, f)

        # Step 2: Extract text from PDF
        text = pdf_to_text(pdf_file)

        # save file
        # create output directory if it does not exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_file = "{}.txt".format(f.split(".")[0])
        with open(join(output_dir, output_file), 'w') as file:
            file.write(text)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input_dir", help="", default="../data/spanish/raw")
    parser.add_argument("-o", "--output_dir", help="", default="../data/spanish/processed")

    args = parser.parse_args()
    main(input_dir=args.input_dir, output_dir=args.output_dir)