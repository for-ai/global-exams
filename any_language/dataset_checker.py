### Cohere For AI Community, Sree Harsha Nelaturu, 2024 (+ Cursor^TM)

"""
This script ideally should check for any issues with schema, to ensure all the fields needed are present -- (basically like the doc said)
- Should ensure options are non-empty and answer is in the range of 1, len(options)
- This script will also remove questions + options combos that are exactly the same word-for-word (some might slip through the crack due to semantic changes, but what can ya do)
- Should also break if answer ain't an int (this can change if not required, lmk)
- purge_error_entries removes duplicates, removes the error'd entries and saves a new JSON -- if you don't provide it, then you gotta fix stuff manually and then re-run
- If you have suggestions/want to to improve this, send me a message on discord.
"""

import json
import os
from datetime import datetime
import argparse
from typing import Union
import re

from rich.rule import Rule
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.text import Text
from rich.syntax import Syntax

class JSONEvaluator:
    def __init__(self, json_file, language_code, purge_error_entries=False):
        self.json_file = json_file
        self.json_data = []
        self.purge_error_entries = purge_error_entries
        self.output_file = None
        self.language_code = language_code.lower()
        self.schema = {
            "language": str, "country": str, "file_name": str, "source": str,
            "license": str, "level": str, "category_en": str,
            "category_original_lang": str, "original_question_num": Union[int, str],
            "question": str, "options": list, "answer": str,
        }
        self.console = Console()

    def load_json_file(self):
        self.console.print(f"[cyan]Loading JSON file:[/cyan] {self.json_file}")
        try:
            with open(self.json_file, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if not isinstance(data, list):
                    raise ValueError(f"File {self.json_file}: JSON should be a list of entries.")
                self.json_data = data
            return True
        except (json.JSONDecodeError, Exception) as e:
            self.console.print(f"[red]Error loading file {self.json_file}: {e}[/red]")
            return False

    def clean_data(self):
        schema_keys = set(self.schema.keys())
        def clean_value(v):
            return v.strip() if isinstance(v, str) else [clean_value(i) for i in v] if isinstance(v, list) else v
        cleaned_data = [{k: clean_value(v) for k, v in entry.items() if k in schema_keys} for entry in self.json_data]
        has_changes = any(cleaned != original for cleaned, original in zip(cleaned_data, self.json_data))   
        if has_changes:
            self.json_data = cleaned_data
        
        return has_changes

    def validate_all(self):
        all_errors = []
        seen_entries = {}
        for idx, entry in enumerate(self.json_data):
            entry_hash = (entry['question'].strip(), tuple(opt.strip() for opt in entry['options']))
            if entry_hash in seen_entries:
                all_errors.append({"entry": idx, "message": f"Duplicate of entry {seen_entries[entry_hash]}."})
            else:
                seen_entries[entry_hash] = idx
            all_errors.extend(self.validate_entry(idx, entry))

        if all_errors:
            self.display_errors_pretty(all_errors)
        return len(all_errors) == 0

    def validate_entry(self, idx, entry):
        errors = []
        for key, expected_type in self.schema.items():
            value = entry.get(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append({"entry": idx, "message": f"Missing or empty key '{key}'."})
            elif not isinstance(value, expected_type):
                errors.append({"entry": idx, "message": f"Invalid type for '{key}': expected {expected_type.__name__}, got {type(value).__name__}."})

        lang = entry.get('language', '').lower()
        if lang != self.language_code:
            errors.append({"entry": idx, "message": f"Invalid language code: expected '{self.language_code}', got '{lang}'."})

        options = entry.get("options", [])
        if not isinstance(options, list) or any(not isinstance(opt, str) or not opt.strip() for opt in options):
            errors.append({"entry": idx, "message": "Invalid 'options': must be a list of non-empty strings."})
        elif len(set(options)) == 1:
            errors.append({"entry": idx, "message": "All options are identical."})

        answer = entry.get("answer", "")
        if not isinstance(answer, str):
            errors.append({"entry": idx, "message": "Invalid 'answer': must be a string."})
        else:
            try:
                answer_ints = [int(a.strip()) for a in answer.split(',')]
                valid_range = set(range(1, len(options) + 1))
                if not set(answer_ints).issubset(valid_range):
                    errors.append({"entry": idx, "message": f"Invalid 'answer': Answer cannot be more than number of options: {len(options)}."})
            except ValueError:
                errors.append({"entry": idx, "message": "Invalid 'answer': must be comma-separated integers."})

        return errors

    def display_errors_pretty(self, errors):
        for error in errors:
            entry = self.json_data[error["entry"]]
            tree = Tree(f"[bold red]Error in Entry {error['entry']}[/bold red]")
            tree.add(Text(error['message'], style="bold yellow"))
            question_node = tree.add("Question")
            question_node.add(Syntax(entry.get('question', '[N/A]'), "text", theme="monokai", word_wrap=True))
            options_node = tree.add("Options")
            options = entry.get('options', [])
            for i, option in enumerate(options, 1):
                options_node.add(f"{i}. {option}")
            answer_node = tree.add("Answer")
            answer_node.add(str(entry.get('answer', '[N/A]')))
            self.console.print(Panel(tree, expand=False, border_style="red"))
            self.console.print()

    def save_cleaned_data(self, name='cleaned'):
        base_filename = os.path.basename(self.json_file).split('.')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = f"{name}_{base_filename}_{timestamp}.json"
        with open(self.output_file, 'w', encoding='utf-8') as outfile:
            json.dump(self.json_data, outfile, ensure_ascii=False, indent=4)
        message = f"Cleaned data saved to [green]{self.output_file}[/green]"
        self.console.print(Panel(message, title=f"Step: {name.capitalize()}", style="bold green"))

    def run_all_checks(self):
        if not self.load_json_file():
            return

        has_changes = self.clean_data()
        if has_changes:
            self.save_cleaned_data('cleaned_no_spurious_fields')
        
        is_valid = self.validate_all()
        if not is_valid and self.purge_error_entries:
            self.remove_problematic_entries()
            self.save_cleaned_data('cleaned_all_errors_removed')
            is_valid = self.validate_all()
        
        self.report_results(is_valid, has_changes)

    def remove_problematic_entries(self):
        self.json_data = [entry for idx, entry in enumerate(self.json_data) if not self.validate_entry(idx, entry)]

    def report_results(self, is_valid, has_changes):
        if is_valid and not has_changes:
            self.console.print(Panel("JSON data is valid and no cleaning was necessary.", style="bold green"))
        elif is_valid and has_changes:
            self.console.print(Panel("JSON data is valid after cleaning (spurious fields removed and/or whitespace cleaned).", style="bold green"))
        else:
            self.console.print("[bold red]Issues found in the JSON data.[/bold red]")
            if has_changes:
                self.console.print("[yellow]Spurious fields were removed and/or whitespace was cleaned.[/yellow]")
            if self.purge_error_entries:
                self.console.print("[yellow]Invalid entries have been purged.[/yellow]")
            else:
                self.console.print("[yellow]Invalid entries were not removed. Use --purge_error_entries to remove them.[/yellow]")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JSON Evaluator')
    parser.add_argument('--json_file', type=str, help='Path to the JSON file to evaluate', required=True)
    parser.add_argument('--purge_error_entries', action='store_true', help='Remove entries with errors')
    parser.add_argument('--language_code', type=str, help='Language code for the dataset', required=True)
    args = parser.parse_args()

    console = Console()
    console.print(Rule(title="Starting Evaluation!", style="bold green"))
    console.print(f"JSON file: [cyan]{args.json_file}[/cyan]")
    console.print(f"Should entries with errors simply be purged?: [cyan]{args.purge_error_entries}[/cyan]")
    console.print(f"Language code: [cyan]{args.language_code}[/cyan]")
    evaluator = JSONEvaluator(json_file=args.json_file, purge_error_entries=args.purge_error_entries, language_code=args.language_code)
    evaluator.run_all_checks()
