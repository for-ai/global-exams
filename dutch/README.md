# exam-mcq-nl

---

This repository contains code to extract multiple choice questions from Dutch high school exams.

### Usage

1. Download selected PDFs: ``download_pdfs.py``
2. Extract plain text from PDFs: ``pdf2text.py``
3. Extract multiple choice questions and answers from plain text: ``text2json.py``


This code could be used to extract and process data from [Examenblad.nl](https://www.examenblad.nl), as published on [alleexamens.nl](alleexamens.nl). The rights of these exams belong to the State of The Netherlands. Please refer to their [copyright statement](https://www.examenblad.nl/over-examenblad/copyright) for more information.

**Note**: The question filtering part should be improved before using these questions directly: e.g. adding more keywords that refer to outside sources and length filtering to avoid concatenated questions.
**Note2**: Most questions are filtered by hand, as there were no keywords present.

### Dataset

Find the dataset on [Huggingface](https://huggingface.co/datasets/jjzha/dutch-central-exam-mcq).
