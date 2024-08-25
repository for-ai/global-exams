### Cohere For AI Community, Sree Harsha Nelaturu, 2024 (+ Cursor^TM)

"""
This script ideally should check for any issues with schema, to ensure all the fields needed are present -- (basically like the doc said)
- Should ensure options are 4 only (and not more)
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

from rich.rule import Rule
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.tree import Tree
from rich.text import Text
from rich.syntax import Syntax

class JSONEvaluator:
    def __init__(self, json_file=None, purge_error_entries=False):
        self.json_file = json_file
        self.json_data = []
        self.purge_error_entries = purge_error_entries
        self.output_file = None
        self.schema = {
            "language": str, "country": str, "file_name": str, "source": str,
            "license": str, "level": str, "category_en": str,
            "category_original_lang": str, "original_question_num": Union[int, str],
            "question": str, "options": list, "answer": int,
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

    def validate_entry(self, idx, entry):
        errors = []
        for key, expected_type in self.schema.items():
            value = entry.get(key)
            if value is None or (isinstance(value, str) and not value.strip()):
                errors.append({"entry": idx, "message": f"Missing or empty key '{key}'."})
            elif not isinstance(value, expected_type):
                errors.append({"entry": idx, "message": f"Invalid type for '{key}': expected {expected_type.__name__}, got {type(value).__name__}."})
        
        options = entry.get("options", [])
        if not isinstance(options, list) or any(not opt.strip() for opt in options):
            errors.append({"entry": idx, "message": "Invalid 'options': must be a list of non-empty strings."})
        elif len(set(options)) == 1:
            errors.append({"entry": idx, "message": "All options are identical."})
        
        answer = entry.get("answer")
        if not isinstance(answer, int) or answer < 1 or answer > len(options):
            errors.append({"entry": idx, "message": f"Invalid 'answer': must be an integer between 1 and {len(options)}."})
        
        return errors

    def validate_all(self):
        seen_entries = {}
        all_errors = []
        for idx, entry in enumerate(self.json_data):
            # Create a hashable representation of the entry
            entry_hash = (entry['question'].strip(), tuple(opt.strip() for opt in entry['options']))
            
            # Check for duplicates
            if entry_hash in seen_entries:
                all_errors.append({"entry": idx, "message": f"Duplicate of entry {seen_entries[entry_hash]}."})
            else:
                seen_entries[entry_hash] = idx

            # Validate the entry regardless of whether it's a duplicate
            all_errors.extend(self.validate_entry(idx, entry))

        if all_errors:
            self.display_errors_pretty(all_errors)
            if self.purge_error_entries:
                self.remove_problematic_entries(all_errors)
            else:
                self.console.print("[bold bright_red]Validation issues found. Please fix them manually.[/bold bright_red]")
        return len(all_errors) == 0

    def display_errors_pretty(self, errors):
        console = Console()
        
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
            
            console.print(Panel(tree, expand=False, border_style="red"))
            console.print()  # Add a blank line between entries

    def check_for_duplicates(self):
        seen = {}
        duplicates = []
        for idx, entry in enumerate(self.json_data):
            key = (entry["question"].strip(), tuple(opt.strip() for opt in entry["options"]))
            if key in seen:
                duplicates.append({"entry": idx, "duplicate_with_entry": seen[key], "message": "Duplicate entry."})
            else:
                seen[key] = idx
        
        if duplicates:
            self.display_duplicates_pretty(duplicates)
            if self.purge_error_entries:
                self.remove_problematic_entries(duplicates)
        return len(duplicates)

    def display_duplicates_pretty(self, duplicates):
        console = Console()
        
        for duplicate in duplicates:
            original_idx = duplicate["duplicate_with_entry"]
            duplicate_idx = duplicate["entry"]
            original_entry = self.json_data[original_idx]
            duplicate_entry = self.json_data[duplicate_idx]
            
            tree = Tree(f"[bold blue]Duplicate Entry Found[/bold blue]")
            
            original_node = tree.add(f"Original Entry (Index: {original_idx})")
            duplicate_node = tree.add(f"Duplicate Entry (Index: {duplicate_idx})")
            
            for node, entry in [(original_node, original_entry), (duplicate_node, duplicate_entry)]:
                question_node = node.add("Question")
                question_node.add(Syntax(entry['question'], "text", theme="monokai", word_wrap=True))
                
                options_node = node.add("Options")
                for i, option in enumerate(entry['options'], 1):
                    options_node.add(f"{i}. {option}")
            
            console.print(Panel(tree, expand=False, border_style="blue"))
            console.print()  # Add a blank line between entries

    def remove_problematic_entries(self, errors):
        self.json_data = [entry for idx, entry in enumerate(self.json_data) if idx not in {error['entry'] for error in errors}]

    def save_cleaned_data(self):
        base_filename = os.path.basename(self.json_file).split('.')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = f"cleaned_{base_filename}_{timestamp}.json"
        with open(self.output_file, 'w', encoding='utf-8') as outfile:
            json.dump(self.json_data, outfile, ensure_ascii=False, indent=4)
        self.console.print(Panel(f"Step Three: Cleaned data saved to [green]{self.output_file}[/green]", style="bold green"))

    def run_all_checks(self):
        if not self.load_json_file():
            return
        self.clean_whitespace()

        is_valid = self.validate_all()

        if not is_valid:
            if self.purge_error_entries:
                self.console.print(Rule(title="JSON Evaluation Steps"))
                self.console.print(Panel("Step One: Entries with Errors will be purged.", style="bold magenta"))
                self.save_cleaned_data()
                self.revalidate_cleaned_data()
            else:
                self.console.print("[bold red]Issues found. They will NOT be automatically removed.[/bold red]")
        else:
            self.console.print(Panel("No issues found. JSON data is valid.", style="bold green"))

    def revalidate_cleaned_data(self):
        self.console.print(Panel("Step Four: Re-validating cleaned JSON data...", style="bold cyan"))
        is_valid = self.validate_all()
        
        if not is_valid:
            self.console.print(Panel("Re-validation failed. Errors found in the cleaned data.", style="bold red"))
        else:
            self.console.print(Panel("The re-validation of cleaned data passed successfully. New JSON should be error-free", style="bold green"))

    def clean_whitespace(self):
        for entry in self.json_data:
            entry.update({k: v.strip() if isinstance(v, str) else [i.strip() if isinstance(i, str) else i for i in v] if isinstance(v, list) else v for k, v in entry.items()})



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JSON Evaluator')
    parser.add_argument('--json_file', type=str, help='Path to the JSON file to evaluate', required=True)
    parser.add_argument('--purge_error_entries', action='store_true', help='Remove entries with errors')
    args = parser.parse_args()

    console = Console()
    console.print(Rule(title="Starting Evaluation!", style="bold green"))
    console.print(f"JSON file: [cyan]{args.json_file}[/cyan]")
    console.print(f"Should entries with errors simply be purged?: [cyan]{args.purge_error_entries}[/cyan]")

    evaluator = JSONEvaluator(json_file=args.json_file, purge_error_entries=args.purge_error_entries)
    evaluator.run_all_checks()
