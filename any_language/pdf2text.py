import pandas as pd
from pdf2image import convert_from_path
import cv2
import numpy as np
import pytesseract
import pandas as pd
from tqdm import tqdm
from os import listdir
import os
from os.path import isfile, join
import argparse


def deskew(image):
    """
    It corrects the orientation of the image. It takes the input image and returns the deskewed image.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(gray > 0))
    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    return rotated


def extract_text_from_image(image):
    """
    It performs OCR on the input image and return the extracted text as a string.
    """
    text = pytesseract.image_to_string(image)
    return text


def main(dir_path):
    """
    It performs the main text extraction pipeline of the script.

    :param dir_path: str
    """
    onlyfiles = [f for f in listdir(dir_path) if isfile(join(dir_path, f))]
    for f in onlyfiles:
        # Step 1: Reads the pdf file
        print("Parsing file: {}".format(f))
        pdf_file = "{}/{}".format(dir_path, f)
        pages = convert_from_path(pdf_file)

        # Create a list to store extracted text from all pages
        extracted_text = list()

        for i, page in tqdm(enumerate(pages)):
            # Step 2: Preprocess the image (deskew)
            preprocessed_image = deskew(np.array(page))

            # Step 3: Extract text using OCR
            text = extract_text_from_image(preprocessed_image)
            extracted_text.append({"page_num": i, "parsed_text": text})

        # save file
        data = pd.DataFrame(extracted_text)
        output_file = '{}.csv'.format(f.split('.')[0])
        parsed_path = os.path.join(dir_path, 'parsed')
        if not os.path.isdir(parsed_path):
            os.makedirs(parsed_path)
        data.to_csv(os.path.join(parsed_path, output_file), index=False)
        print('Data saved: {}'.format(output_file))
        print("-" * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dir", help="", default="pfds")

    args = parser.parse_args()
    main(dir_path=args.dir)
