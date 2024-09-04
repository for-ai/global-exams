#!/usr/bin/env python

"""
Description: Download selected exam files from alleexamens.nl
Usage: download_pdfs.py
"""

import requests
import os
import tqdm


def download_file(url, folder):
    """Given an exam pdf URL, try to download the pdf file."""

    exam_id = "_".join(url.split("/")[3:7]).replace("%20", "-")
    save_file = f"{folder}/{exam_id}.pdf"

    r = requests.get(url, allow_redirects=True)
    if r.status_code == requests.codes.ok:
        with open(save_file, "wb") as f:
            f.write(r.content)
    else:
        pass  # not all exams exist for all years


def main():

    # pre-defined: selected subjects per university sub-level
    lvl_subj = {
        "VWO": ["Biologie", "Natuurkunde", "Scheikunde", "Aardrijkskunde", "Bedrijfseconomie", "Economie",
                "Filosofie", "Geschiedenis", "Maatschappijwetenschappen", "Management%20en%20organisatie"],
        "HAVO": ["Biologie", "Natuurkunde", "Scheikunde", "Aardrijkskunde", "Bedrijfseconomie", "Economie",
                 "Filosofie", "Geschiedenis", "Maatschappijwetenschappen", "Management%20en%20organisatie"],
        "VMBO-GL": ["Biologie", "Natuur-en-scheikunde-1", "Natuur-en-scheikunde-2", "Aardrijkskunde",
                    "Economie", "Geschiedenis-en-staatsinrichting"],
        "VMBO-KB": ["Biologie", "Natuur-en-scheikunde-1", "Aardrijkskunde", "Maatschappijleer%202",
                    "Economie", "Geschiedenis%20en%20staatsinrichting"],
        "VMBO-BB": ["Biologie", "Natuur-en-scheikunde-1", "Aardrijkskunde", "Maatschappijleer%202",
                    "Economie", "Geschiedenis%20en%20staatsinrichting"],
    }

    # retrieve all hypothetical urls
    h_que_urls, h_ans_urls = [], []
    for level in lvl_subj.keys():
        for subject in lvl_subj[level]:
            for year in range(1999, 2025):
                for period in ["I", "II"]:
                    h_que_urls.append(f"https://static.alleexamens.nl/{level}/{subject}/{year}/{period}/{subject}/"
                                      f"{subject}%20{year}%20{period}_opgaven.pdf")
                    h_ans_urls.append(f"https://static.alleexamens.nl/{level}/{subject}/{year}/{period}/{subject}/"
                                      f"{subject}%20{year}%20{period}_correctievoorschrift.pdf")

    # download files
    os.mkdir("answers")
    for url in tqdm.tqdm(h_ans_urls):
        download_file(url, "answers")
    os.mkdir("exams")
    for url in tqdm.tqdm(h_que_urls):
        download_file(url, "exams")


if __name__ == '__main__':
    main()
