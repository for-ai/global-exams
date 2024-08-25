### Cohere For AI Community, Sree Harsha Nelaturu, 2024 (+ ChatGPT^TM)

"""
This script ideally should check for any issues with schema, to ensure all the fields needed are present -- (basically like the doc said)
- Should ensure options are 4 only (and not more)
- This script will also remove questions + options combos that are exactly the same word-for-word (some might slip through the crack due to semantic changes, but what can ya do)
- Should also break if answer ain't an int (this can change if not required, lmk)
- purge_error_entries removes duplicates, removes the error'd entries and saves a new JSON -- if you don't provide it, then you gotta fix stuff manually and then re-run
- If you have suggestions/want to to improve this, send me a message on discord.
"""

import json
from prettytable import PrettyTable, ALL
import os
import json
from datetime import datetime
import argparse

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.rule import Rule

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
        self.console = Console()

    def load_json_file(self):
        """Loads JSON data from the file."""
        self.console.print(f"[cyan]Loading JSON file:[/cyan] {self.json_file}")
        if not self.json_file:
            self.console.print("[red]No file path provided.[/red]")
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
                self.console.print("[bold bright_red]Validation issues in schema.[/bold bright_red]")
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
                self.console.print("[bold bright_red]There are still validation issues in options.[/bold bright_red]")
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
                self.console.print("[bold bright_red]There are still validation issues due to problematic answers in entries.[/bold bright_red]")
        return True

    def display_errors_pretty(self, errors):
        """Displays errors in a formatted table using Rich's Table with consistent borders and wrapped text."""
        table = Table(
            title="[bold magenta]Validation Errors[/bold magenta]", 
            box=box.HEAVY_EDGE,
            header_style="bold white on blue",
            show_lines=True
        )
        
        table.add_column("Entry", justify="center", style="bold bright_cyan", max_width=8, overflow="fold")
        table.add_column("Error Message", justify="left", style="bold bright_red", max_width=30, overflow="fold")
        table.add_column("Question", justify="left", style="bold bright_green", max_width=40, overflow="fold")
        table.add_column("Options", justify="left", style="bright_yellow", max_width=30, overflow="fold")
        table.add_column("Answer", justify="center", style="bold bright_blue", max_width=8, overflow="fold")
        
        for error in errors:
            question_text = self.json_data[error["entry"]].get("question", "[N/A]")
            options = "\n".join(self.json_data[error["entry"]].get("options", [])) 
            answer = self.json_data[error["entry"]].get("answer", "[N/A]")
            
            table.add_row(
                f"[bold bright_cyan]{error['entry']}[/bold bright_cyan]",
                f"[bold bright_red]{error['message']}[/bold bright_red]",
                f"[bright_green]{question_text}[/bright_green]",
                f"[bright_yellow]{options}[/bright_yellow]",
                f"[bold bright_blue]{answer}[/bold bright_blue]"
            )
        
        self.console.print(table)

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
            return len(duplicates)
        
        return 0

    def display_duplicates_pretty(self, duplicates):
        """Displays duplicate questions side by side in a formatted table using Rich's Table with consistent borders and wrapped text."""
        table = Table(
            title="[bold blue]Duplicate Entries[/bold blue]", 
            box=box.HEAVY_EDGE,
            header_style="bold white on purple",
            show_lines=True
        )
        
        table.add_column("Original Entry", justify="center", style="bold bright_cyan", max_width=10, overflow="fold")
        table.add_column("Duplicate Entry", justify="center", style="bold bright_cyan", max_width=10, overflow="fold")
        table.add_column("Original Question", justify="left", style="bright_green", max_width=40, overflow="fold")
        table.add_column("Duplicate Question", justify="left", style="bright_green", max_width=40, overflow="fold")
        table.add_column("Original Options", justify="left", style="bright_magenta", max_width=30, overflow="fold")
        table.add_column("Duplicate Options", justify="left", style="bright_magenta", max_width=30, overflow="fold")
        
        for duplicate in duplicates:
            original_idx = duplicate["duplicate_with_entry"]
            duplicate_idx = duplicate["entry"]
            
            original_question = self.json_data[original_idx]["question"].strip()
            duplicate_question = self.json_data[duplicate_idx]["question"].strip()
            
            original_options = "\n".join(self.json_data[original_idx]["options"]) 
            duplicate_options = "\n".join(self.json_data[duplicate_idx]["options"])
            

            table.add_row(
                f"[bold bright_cyan]{original_idx}[/bold bright_cyan]",
                f"[bold bright_cyan]{duplicate_idx}[/bold bright_cyan]",
                f"[bright_green]{original_question}[/bright_green]",
                f"[bright_green]{duplicate_question}[/bright_green]",
                f"[bright_magenta]{original_options}[/bright_magenta]",
                f"[bright_magenta]{duplicate_options}[/bright_magenta]"
            )
        
        self.console.print(table)


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
        self.console.print(Panel(f"Step Three: Cleaned data saved to [green]{self.output_file}[/green]", style="bold green"))
        self.revalidate_cleaned_data()

    def revalidate_cleaned_data(self):
        """Re-validates cleaned JSON data to ensure no remaining errors."""
        self.console.print(Panel("Step Four: Re-validating cleaned JSON data...", style="bold cyan"))

        self.json_file = self.output_file  
        self.json_data = []
        self.errors = []
        self.load_json_file()
        
        self.clean_whitespace()
        self.validate_schema()
        self.validate_options()
        self.validate_answer()

        duplicates_count = self.check_for_duplicates()
        
        if self.errors or duplicates_count > 0:
            self.display_errors_pretty(self.errors)
            if duplicates_count > 0:
                self.console.print(f"[bold red]Re-validation failed. {duplicates_count} duplicate entries found in the cleaned data.[/bold red]")
            self.console.print(Panel("Re-validation failed. Errors found in the cleaned data.", style="bold red"))
        else:
            self.console.print(Panel("The re-validation of cleaned data passed successfully. New JSON should ideally be error-free", style="bold green"))

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

        try:
            self.validate_schema()
            self.validate_options()
            self.validate_answer()
            dups = self.check_for_duplicates()

            if not self.purge_error_entries:
                self.console.print(Panel(f"Found {dups} duplicate entries. They will NOT be removed.", style="bold yellow"))
            else:
                self.console.print(Rule(title="JSON Evaluation Steps"))
                self.console.print(Panel("Step One: Entries with Errors will be purged.", style="bold magenta"))
                if dups > 0:
                    self.console.print(Panel(f"Step Two: Found {dups} duplicate entries. Removing them.", style="bold magenta"))
                else:
                    self.console.print(Panel("Step Two: No duplicate entries found. Moving on...", style="bold magenta"))
                self.save_cleaned_data()
            self.console.print(Panel("Well, if there were issues found -- they would've showed as tables. This message is a good sign if there are not tables, so um....", style="bold green"))

        except ValueError as e:
            self.console.print(Panel(f"Validation failed: {e}", style="bold red"))
            if not self.purge_error_entries:
                raise

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
