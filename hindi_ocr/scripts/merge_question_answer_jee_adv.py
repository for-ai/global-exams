import os
import json

categories = {
    "physics": "भौतिकी",
    "chemistry": "रसायन विज्ञान",
    "maths": "गणित",
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
# Define the paths to the folders
results_folder = "<path_to_folder>"

# List to store the paths of all JSON files
json_files = []

# Walk through the directory and its subdirectories
for root, dirs, files in os.walk(results_folder):
    for file in files:
        if file.endswith(".json"):
            json_files.append(os.path.join(root, file))


final_questions = []
questions = []
for file_path in json_files:
    # Construct the corresponding answer key file name
    with open(file_path, "r") as f:
        paper_json = json.load(f)
    if len(paper_json) > 0:
        questions = questions + paper_json

for question in questions:
    if question["answer"] == "":
        continue
    if "," in question["answer"]:
        continue
    if "requires_image" not in question:
        print(question)
        continue
    if question["requires_image"] == "yes":
        continue
    if len(question["options"]) == 0:
        continue
    if question["context"] == "yes":
        continue
    question["category_original_lang"] = categories[
        question["category_en"].lower()
    ]
    question["license"] = "unknown"
    question["original_question_num"] = str(question["original_question_idx"])
    del question["original_question_idx"]
    del question["requires_image"]
    del question["context"]
    del question["page_num"]
    del question["response"]
    del question["region_related"]
    final_questions.append(question)
    # Write the updated JSON back to the file
print(len(final_questions))
with open("output.json", "w") as f:
    json.dump(final_questions, f, indent=4)

print("Answer mapping completed.")
