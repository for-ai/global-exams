---
language:
- sv
license: unknown
---

# Dataset Card for Swedish Medical Exam MCQs

## Dataset Description

This dataset contains multiple-choice questions from Swedish medical exams.

### Languages

The dataset is in Swedish (sv).

## Dataset Structure

Each entry in the dataset contains the following fields:
- question: The question
- options: An array of possible answers
- answer: The correct answer
- language: The language of the question (always "sv" for Swedish)
- country: The country of origin (always "Sweden")
- file_name: The original file name
- source: The source of the questions
- license: The license of the dataset
- level: The educational level (graduate)
- category_en: The category in English (Medicine)
- category_original_lang: The category in the original language (Medicin)
- original_question_num: The original question number


### Source Data

The questions were extracted from Swedish medical exam papers. Each instance in the file contains relevant information to see where the question is from. 

The questions here are a collection of the Swedish medical exams between 2020-02-10 and 2022-05-24.

All questions here have been obtained from the official website of Umea University. 
Link: https://www.umu.se/utbildning/sok/kunskapsprov/kunskapsprov-for-lakare/teoretiskt-delprov/