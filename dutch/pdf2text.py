#!/usr/bin/env python

"""
Description: Extract plain text from exam PDFs.
Usage: pdf2text.py
"""

import os
from tika import parser
import tqdm

import time
start = time.time()


def main():
    for folder in ["exams", "answers"]:
        for subdir, dirs, files in os.walk(folder):
            os.makedirs(f"./{folder}-text/{subdir.replace(folder, '')}")
            for file in tqdm.tqdm(files):
                parsed = parser.from_file(os.path.join(subdir, file))
                text = parsed["content"]
                if text:
                    with open(os.path.join(subdir, file).replace(folder, f"{folder}-text").replace(".pdf", ".txt"), "w") as text_file:
                        text_file.write(text)
                else:
                    print(f"Something is wrong with {file}")

        print(f"Processing time: {time.time()-start} seconds.")


if __name__ == '__main__':
    main()
