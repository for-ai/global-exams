import os
import json

categories = {
    "physics": "भौतिकी",
    "chemistry": "रसायन विज्ञान",
    "maths": "गणित",
    "mathematics": "गणित",
    "biology": "जीवविज्ञान",
    "reasoning": "तर्कशक्ति",
    "numerical ability": "संख्यात्मक योग्यता",
    "scientific aptitude": "वैज्ञानिक अभिरुचि",
    "general knowledge": "सामान्य ज्ञान",
    "english language": "अंग्रेजी भाषा",
    "drawing aptitude": "चित्रकला अभिरुचि",
    "computer concepts": "कंप्यूटर अवधारणाएँ",
    "pharmacy": "फार्मेसी",
}
answer_map = ["A", "B", "C", "D", "E", "F"]
answer_map_jee = ["1", "2", "3", "4", "5", "6"]
# Define the paths to the folders


def jee_main(results_folder, answer_keys_folder):
    # Get a list of all JSON files in the results folder
    result_files = [
        f for f in os.listdir(results_folder) if f.endswith(".json")
    ]
    answer_files = [
        f for f in os.listdir(answer_keys_folder) if f.endswith(".json")
    ]
    answer_key = {}
    # if "2015" in answer_keys_folder or "2013" in answer_keys_folder or "2014" in answer_keys_folder:
    for file_name in answer_files:
        file_path = os.path.join(answer_keys_folder, file_name)
        with open(file_path, "r") as f:
            answer_dict = json.load(f)
        for k in answer_dict:
            # if len(str(answer_dict[k])) > 1:
            #     continue
            answer_key[str(int(k))] = str(answer_dict[k])

    # Iterate through each paper's files
    final_questions = []
    questions = []
    cntr = 0
    print(len(result_files))
    for file_name in result_files:
        # for file_name in files:
        file_path = os.path.join(results_folder, file_name)
        with open(file_path, "r") as f:
            paper_json = json.load(f)
        for question in paper_json:
            question["original_question_idx"] = str(
                int(question["original_question_idx"]) + cntr
            )
        questions = questions + paper_json
        # cntr+=30

    for question in questions:
        assert isinstance(question.get("original_question_idx"), str)
        question_idx = str(int(question.get("original_question_idx")))
        if question_idx in answer_key:
            try:
                question["answer"] = str(
                    answer_map_jee.index(answer_key[question_idx]) + 1
                )
            except Exception as e:
                print(answer_key[question_idx])
                continue
                # raise Warning(e)
        else:
            breakpoint()
            # print(question_idx, question["file_name"])
            # raise Warning("Question without key in answer")
    ans = []
    for question in questions:
        assert isinstance(question["answer"], str)
        if len(question["answer"]) > 1 or len(question["answer"]) == 0:
            print(question["answer"])
            continue
        ans.append(question["answer"])
        if question["requires_image"] == "yes":
            continue
        if question["answer"] == "":
            continue
        if len(question["options"]) == 0:
            continue
        if question["context"] == "yes":
            print("Context")
            continue
        if "english language" in question["category_en"]:
            print(question["category_en"])
            continue
        question["category_original_lang"] = categories[
            question["category_en"].lower()
        ]
        question["license"] = "unknown"
        question["original_question_num"] = question["original_question_idx"]
        question["language"] = "hi"
        del question["region_related"]
        del question["original_question_idx"]
        del question["requires_image"]
        del question["context"]
        del question["page_num"]
        del question["response"]
        final_questions.append(question)

    print(set(ans))
    return final_questions


def main(results_folder, answer_keys_folder):
    # Get a list of all JSON files in the results folder
    result_files = [
        f for f in os.listdir(results_folder) if f.endswith(".json")
    ]

    # Group result files by paper number
    papers = {}
    for file_name in result_files:
        parts = file_name.split("_")
        paper_num = parts[2]
        if paper_num not in papers:
            papers[paper_num] = []
        papers[paper_num].append(file_name)

    # Iterate through each paper's files
    final_questions = []
    for paper_num, files in papers.items():
        # Construct the corresponding answer key file name
        year = files[0].split("_")[
            0
        ]  # Assuming all files of the paper have the same year
        answer_key_file = f"{year}_KEY_{paper_num}_page_0.json"
        answer_key_path = os.path.join(answer_keys_folder, answer_key_file)

        # Load the answer key JSON file
        if os.path.exists(answer_key_path):
            with open(answer_key_path, "r") as f:
                answer_key = json.load(f)

            # Iterate through all pages of the paper
            questions = []
            for file_name in files:
                file_path = os.path.join(results_folder, file_name)
                with open(file_path, "r") as f:
                    paper_json = json.load(f)
                questions = questions + paper_json
            if len(questions) % 10 != 0:
                print(files)
            for question in questions:
                assert isinstance(question.get("original_question_idx"), str)
                question_idx = str(int(question.get("original_question_idx")))
                if question_idx in answer_key:
                    try:
                        question["answer"] = str(
                            answer_map.index(answer_key[question_idx]) + 1
                        )
                    except Exception as e:
                        try:
                            question["answer"] = str(
                                answer_map.index(
                                    answer_key[question_idx].upper()
                                )
                                + 1
                            )
                        except Exception as e:
                            raise ValueError(e)
                else:
                    breakpoint()
                    raise ValueError("Question without key in answer")
            for question in questions:
                if question["requires_image"] == "yes":
                    continue
                if question["answer"] == "":
                    continue
                if len(question["options"]) == 0:
                    continue
                if question["context"] == "yes":
                    print("Context")
                    continue
                if "english language" in question["category_en"]:
                    print(question["category_en"])
                    continue
                question["category_original_lang"] = categories[
                    question["category_en"].lower()
                ]
                question["license"] = "unknown"
                question["original_question_num"] = question[
                    "original_question_idx"
                ]
                question["language"] = "hi"
                del question["region_related"]
                del question["original_question_idx"]
                del question["requires_image"]
                del question["context"]
                del question["page_num"]
                del question["response"]
                final_questions.append(question)
            #     # Write the updated JSON back to the file
            # with open("UP-CET-2020.json", 'w') as f:
            #     json.dump(final_questions, f, indent=4)
    return final_questions


result_folders = [
    # path to gpt4-o result folders
]

key_folders = [
    # path to keys extracted from gpt4-o
]

all_questions = []
for result_folder, key_folder in zip(result_folders, key_folders):
    all_questions.extend(jee_main(result_folder, key_folder))

    with open("JEE-Main-Hindi.json", "w") as f:
        json.dump(all_questions, f, indent=4)
