import re
import json

categories_urdu = {
    "physics": "طبیعیات",
    "chemistry": "کیمیا",
    "maths": "ریاضی",
    "biology": "حیاتیات",
    "agriculture": "زراعت",
    "reasoning": "استدلال",
    "pharmacy": "فارمیسی",
    "medical": "طبی",
}


# Function to parse the text file and extract the information
def parse_questions(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()

    # Define regex patterns to extract the desired fields
    question_num_pattern = re.compile(r"<question_num>(.*?)</question_num>", re.DOTALL)
    question_pattern = re.compile(r"<question>(.*?)</question>", re.DOTALL)
    choices_pattern = re.compile(r"<choices>(.*?)</choices>", re.DOTALL)
    answer_pattern = re.compile(r"<answer>(.*?)</answer>")
    category_pattern = re.compile(r"<category>(.*?)</category>")
    image_pattern = re.compile(r"<image>(.*?)</image>")
    context_pattern = re.compile(r"<context>(.*?)</context>")

    # Initialize list to hold parsed questions
    questions_data = []

    # Extract all matches
    question_nums = question_num_pattern.findall(content)
    questions = question_pattern.findall(content)
    choices = choices_pattern.findall(content)
    answers = answer_pattern.findall(content)
    categories = category_pattern.findall(content)
    images = image_pattern.findall(content)
    contexts = context_pattern.findall(content)

    # Parse each question block
    cntr = 0
    print(len(question_nums))
    print(len(choices))
    print(len(answers))
    print(len(categories))
    print(len(images))
    print(len(contexts))
    print(len(questions))
    for i in range(len(questions)):
        # Skip if any required field is empty
        if (
            not question_nums[i].strip()
            or not questions[i].strip()
            or not choices[i].strip()
            or not answers[i].strip()
        ):
            cntr += 1
            continue

        # Handle Urdu in question
        question_lines = questions[i].strip().split("\n")
        urdu_question = question_lines[-1].strip()

        # Extract choices with Urdu handling
        choice_lines = choices[i].strip().split("\n")
        parsed_choices = []
        j = 0
        while j < len(choice_lines):
            line = choice_lines[j].strip()
            if re.match(
                r"\d+\.", line
            ):  # Check if the line starts with a choice number
                if j + 1 < len(choice_lines) and not re.match(
                    r"\d+\.", choice_lines[j + 1].strip()
                ):
                    # If the next line isn't a choice number, it’s the Urdu translation
                    parsed_choices.append(choice_lines[j + 1].strip())
                    j += 1  # Skip the next line as it’s already processed
                else:
                    # No Urdu translation; use the original text
                    parsed_choices.append(line)
            j += 1

        # Skip if choices don't have exactly 4 options
        if len(parsed_choices) != 4:
            cntr += 1
            continue
        if "06_aug2021" in file_path:
            src = "previouspapers-eamcet-ts_eamcet_2021-06_aug2021_an_e_u.pdf"
            link = "https://education.sakshi.com/en/eamcet/previous-papers-2021/ts-eamcet-2021-engineering-question-paper-final-key-06-aug-2021-afternoonenglish-urdu-90203"
        else:
            src = "previouspapers-eamcet-ts_eamcet_2021-10_aug2021_an_e_u.pdf"
            link = "https://education.sakshi.com/en/eamcet/previous-papers-2021/ts-eamcet-2021-agriculture-and-medical-question-paper-final-key10-aug-2021-forenoonenglish-urdu-90211"

        # Store extracted data
        question_data = {
            "language": "ur",
            "country": "India",
            "file_name": src,
            "source": link,
            "license": "unknown",
            "level": "high school",
            "category_en": categories[i].strip(),
            "category_original_lang": categories_urdu[categories[i].strip()],
            "original_question_num": question_nums[i].strip(),
            "question": urdu_question,
            "options": parsed_choices,
            "answer": answers[i].strip(),
        }
        questions_data.append(question_data)
    print(cntr)
    return questions_data


# Example usage
file_path = "previouspapers-eamcet-ts_eamcet_2021-06_aug2021_an_e_u.txt"
parsed_data = parse_questions(file_path)
print(len(parsed_data))
# Display the parsed data
with open("EAMCET-Urdu.json", "w") as json_file:
    json.dump(parsed_data, json_file, indent=2)
