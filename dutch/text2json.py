#!/usr/bin/env python

"""
Description: Extract MCQ from text files and write to json format
Usage: text2json.py

TODO:
- some issues in outputs; make filtering stricter! for example: length?
- maybe add command line arguments (paths, filtering options)
"""

import os
import re
import json
import tqdm

import time
start = time.time()


def let_to_int(letter):
    try:
        mapping = {"A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6}
        return mapping[letter]
    except KeyError:
        return False


def n_cat_to_en(nl_name):
    mapping = {
        "Biologie": "Biology", "Natuurkunde": "Physics", "Scheikunde": "Chemistry", "Aardrijkskunde": "Geography",
        "Bedrijfseconomie": "Business economics", "Economie": "Economics", "Filosofie": "Philosophy",
        "Geschiedenis": "History", "Maatschappijwetenschappen": "Social sciences",
        "Management-en-organisatie": "Management and organisation", "Natuur-en-scheikunde-1": "Physics and Chemistry 1",
        "Natuur-en-scheikunde-2": "Physics and Chemistry 2", "Maatschappijleer 2": "Social sciences 2",
        "Geschiedenis-en-staatsinrichting": "History and State Structure"
    }
    return mapping[nl_name]


def clean_line(line):
    # TODO: make stricter
    if any(ext in line for ext in ["afbeelding", "informatie", "hierboven", "letter", "bron", "bronnen", "tekst",
                                   "tabel", "stamboom", "diagram", "figuur", "gebruik", "Gebruik", "onderstaand",
                                   "genoemde", "dit", "poster", "cartoon", "tekening", "affiche",
                                   "tekenaar", "beide", "prent", "spotprent"]):
        return False

    return True


def main():

    for subdir, dirs, files in os.walk("exams-text"):
        data = []
        for file in tqdm.tqdm(files):
            if os.path.isfile(f"answers-text/{file}"):  # corresponding answer sheet available?
                with open(os.path.join(subdir, file), "r") as exam:
                    exam_lines = [line.rstrip() for line in exam.readlines()]
                with open(f"answers-text/{file}", "r") as answers:
                    answer_lines = [line.rstrip() for line in answers.readlines()]

            # get answers for mcq
            answer_dict = dict()
            answers = [tuple(x.split()) for x in answer_lines if re.search("[0-9] [A-Z]$", x) and len(tuple(x.split())) == 2]
            for x, y in answers:
                answer_dict[x] = let_to_int(y)

            output, q_ids = [], []
            for i, item in enumerate(exam_lines):
                if item.startswith('A '):

                    # get options
                    a_ctxt = exam_lines[i:i+10]
                    options = [" ".join(a.split()[1:]) for a in a_ctxt if re.search("^[A-Z] ", a)]

                    # get question ID and text
                    q_ctxt = exam_lines[i-30:i+1]
                    for s_cand in q_ctxt[::-1]:
                        valid_q = True
                        if re.search("[0-9]p [0-9]", s_cand):
                            q_start = exam_lines.index(s_cand)
                            string = " ".join(exam_lines[q_start:i])
                            q_id = string.split()[1]
                            q_text = " ".join(string.split()[2:])

                            try:
                                ans = answer_dict[q_id]
                            except KeyError:
                                pass

                            if q_id not in q_ids and valid_q and ans and clean_line(q_text):
                                q_data = {
                                    "language": "nl",
                                    "country": "Netherlands",
                                    "file_name": file,
                                    "source": "https://www.alleexamens.nl/",
                                    "license": "open",
                                    "level": "high-school",
                                    "category_en": file.split("_")[1],
                                    "category_original_lang": n_cat_to_en(file.split("_")[1]),
                                    "original_question_num": q_id,
                                    "question": q_text,
                                    "options": options,
                                    "answer": ans
                                }

                                q_ids.append(q_id)
                                output.append(q_data)

            if output:
                data.append(output)

        d = [x for xs in data for x in xs]
        with open("mcq-nl.json", "a") as f:
            json.dump(d, f, indent=4)

        print(f"Processing time: {time.time()-start} seconds.")


if __name__ == '__main__':
    main()
