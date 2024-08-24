### Cohere For AI Community, Sree Harsha Nelaturu, 2024

import json
from prettytable import PrettyTable, ALL
import os
import json
from datetime import datetime
import argparse

class JSONEvaluator:
    def __init__(self, json_file=None, purge_error_entries=False):
        self.json_file = json_file
        self.json_data = []
        self.purge_error_entries = purge_error_entries
        self.output_file = None
        self.schema = {
            "language": str,
            "country": str,
            "file_name": str,
            "source": str,
            "license": str,
            "level": str,
            "category_en": str,
            "category_original_lang": str,
            "original_question_num": int,
            "question": str,
            "options": list,
            "answer": int,
        }

    def load_json_file(self):
        """Loads JSON data from the file."""
        print(f"Loading JSON file: {self.json_file}")
        if not self.json_file:
            print("No file path provided.")
            return False

        try:
            with open(self.json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if not isinstance(data, list):
                    raise ValueError(f"File {self.json_file}: JSON should be a list of entries.")
                self.json_data = data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in file {self.json_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error loading file {self.json_file}: {e}")
        return True

    def validate_schema(self):
        """Validates if each entry in the JSON data follows the predefined schema."""
        errors = []

        for idx, entry in enumerate(self.json_data):
            for key, expected_type in self.schema.items():
                if key not in entry:
                    errors.append({
                        "entry": idx,
                        "message": f"Missing key '{key}'."
                    })
                elif not isinstance(entry[key], expected_type):
                    errors.append({
                        "entry": idx,
                        "message": f"Key '{key}' should be of type {expected_type.__name__}, got {type(entry[key]).__name__} (value: {entry[key]})."
                    })
                elif entry[key] is None or (isinstance(entry[key], str) and entry[key].strip() == ""):
                    errors.append({
                        "entry": idx,
                        "message": f"Key '{key}' cannot be null, empty, or whitespace only (value: '{entry[key]}')."
                    })

        if errors:
            self.display_errors_pretty(errors)
            if self.purge_error_entries:
                self.remove_problematic_entries(errors)
            else:
                raise ValueError("Validation failed.")
        return True

    def validate_options(self):
        """Ensures 'options' field is a list of exactly 4 non-empty, non-duplicate strings."""
        errors = []

        for idx, entry in enumerate(self.json_data):
            options = entry.get("options", None)
            if options is None:
                errors.append({
                    "entry": idx,
                    "message": "Missing 'options' key."
                })
            elif not isinstance(options, list):
                errors.append({
                    "entry": idx,
                    "message": f"'options' should be a list (value: {options})."
                })
            elif len(options) != 4:
                errors.append({
                    "entry": idx,
                    "message": f"'options' should be a list of 4 items (found {len(options)} items)."
                })
            elif len(set(options)) == 1:
                errors.append({
                    "entry": idx,
                    "message": f"All options are identical (value: '{options[0]}')."
                })
            else:
                for opt_idx, option in enumerate(options):
                    if not option.strip():
                        errors.append({
                            "entry": idx,
                            "message": f"Option {opt_idx} in 'options' is empty or contains only whitespace (value: '{option}')."
                        })

        if errors:
            self.display_errors_pretty(errors)
            if self.purge_error_entries:
                self.remove_problematic_entries(errors)
            else:
                raise ValueError("Validation failed.")
        return True

    def validate_answer(self):
        """Ensures 'answer' is an integer and within the range [1, 2, 3, 4]."""
        errors = []

        for idx, entry in enumerate(self.json_data):
            if "answer" not in entry:
                errors.append({
                    "entry": idx,
                    "message": "Missing key 'answer'."
                })
            else:
                answer = entry["answer"]
                if not isinstance(answer, int):
                    errors.append({
                        ""
                        "entry": idx,
                        "message": f"'answer' should be an integer (value: {answer})."
                    })
                elif answer < 1 or answer > 4:
                    errors.append({
                        "entry": idx,
                        "message": f"'answer' must be between 1 and 4 (value: {answer})."
                    })

        if errors:
            self.display_errors_pretty(errors)
            if self.purge_error_entries:
                self.remove_problematic_entries(errors)
            else:
                raise ValueError("Validation failed.")
        return True

    def display_errors_pretty(self, errors):
        """Displays errors in a formatted table using PrettyTable."""
        table = PrettyTable()
        table.hrules = ALL
        table.field_names = ["Entry", "Error Message", "Question", "Options", "Answer"]
        table._max_width = {"Entry" : 100, "Question" : 50, "Error Message" : 50, "Options" : 50, "Answer" : 10}
        table.align["Question"] = "l"
        table.align["Error Message"] = "l"
        for error in errors:
            question_text = self.json_data[error["entry"]].get("question", "N/A")
            options = self.json_data[error["entry"]].get("options", [])
            answer = self.json_data[error["entry"]].get("answer", "N/A")
            table.add_row([error["entry"], error["message"], question_text, options, answer])

        print(table)

    def check_for_duplicates(self):
        """Identifies and optionally removes duplicate question and options sets, ignoring leading/trailing whitespace."""
        seen_questions = {}
        duplicates = []

        for idx, entry in enumerate(self.json_data):
            question = entry["question"].strip()
            options = tuple(option.strip() for option in entry["options"])
            question_combination = (question, options)

            if question_combination in seen_questions:
                original_idx = seen_questions[question_combination]
                duplicates.append({
                    "entry": idx,
                    "duplicate_with_entry": original_idx,
                    "message": "Duplicate entry.",
                    "question": question
                })
            else:
                seen_questions[question_combination] = idx

        if duplicates:
            self.display_duplicates_pretty(duplicates)
            if self.purge_error_entries:
                self.remove_problematic_entries(duplicates)
            self.save_cleaned_data()
            self.revalidate_cleaned_data()


    def display_duplicates_pretty(self, duplicates):
        """Displays duplicate questions side by side in a formatted table using PrettyTable."""
        table = PrettyTable()
        table.hrules = ALL
        table.align = "l"
        table.max_width = 50
        table.field_names = ["Original Entry", "Duplicate Entry", "Original Question", "Duplicate Question"]
        table._max_width = {"Original Entry" : 100, "Duplicate Entry" : 50, "Original Question" : 50, "Duplicate Question" : 50}

        for duplicate in duplicates:
            original_idx = duplicate["duplicate_with_entry"]
            duplicate_idx = duplicate["entry"]

            original_question = self.json_data[original_idx]["question"].strip()
            duplicate_question = self.json_data[duplicate_idx]["question"].strip()

            table.add_row([original_idx, duplicate_idx, original_question, duplicate_question])

        print(table)


    def remove_problematic_entries(self, errors):
        """Removes problematic entries based on errors identified."""
        error_indices = set([error['entry'] for error in errors])
        self.json_data = [entry for idx, entry in enumerate(self.json_data) if idx not in error_indices]

    def save_cleaned_data(self):
        """Saves the cleaned JSON data to a new file with a timestamp to avoid overwriting."""
        
        base_filename = os.path.basename(self.json_file).split('.')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = f"cleaned_{base_filename}_{timestamp}.json"

        with open(self.output_file, 'w', encoding='utf-8') as outfile:
            json.dump(self.json_data, outfile, ensure_ascii=False, indent=4)
        
        print(f"Cleaned data saved to {self.output_file}")

        self.revalidate_cleaned_data()

    def revalidate_cleaned_data(self):
        """Re-validates cleaned JSON data to ensure no remaining errors."""
        print('Re-validating cleaned JSON data...')
        
        self.json_file = self.output_file 
        self.json_data = []
        self.errors = []

        self.load_json_file()
        
        self.clean_whitespace()
        self.validate_schema()
        self.validate_options()
        self.validate_answer()
        
        if not self.errors:
            print("Re-validation of cleaned data passed successfully.")
        else:
            self.display_errors_pretty(self.errors)
            print("Re-validation failed. Errors found in the cleaned data.")

    def clean_whitespace(self):
        """Cleans up trailing whitespaces in all string fields."""
        for entry in self.json_data:
            for key, value in entry.items():
                if isinstance(value, str):
                    entry[key] = value.strip()
                elif isinstance(value, list):
                    entry[key] = [item.strip() if isinstance(item, str) else item for item in value]
        return True

    def run_all_checks(self):
        """Runs all checks on the JSON data."""
        self.load_json_file()
        self.clean_whitespace()
        self.validate_schema()
        self.validate_options()
        self.validate_answer()
        self.check_for_duplicates()

        if not self.purge_error_entries:
            print("All checks passed successfully.")
        else:
            self.save_cleaned_data()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JSON Evaluator')
    parser.add_argument('--json_file', type=str, help='Path to the JSON file to evaluate')
    parser.add_argument('--purge_error_entries', action='store_true', help='Remove entries with errors')
    args = parser.parse_args()

    print("Starting Evaluation!")
    print(f"JSON file: {args.json_file}")
    print(f"Should entries with errors simply be purged?: {args.purge_error_entries}")

    try:
        evaluator = JSONEvaluator(json_file=args.json_file, purge_error_entries=args.purge_error_entries)
        evaluator.run_all_checks()
    except Exception as e:
        print(f"Check failed: {e}")

