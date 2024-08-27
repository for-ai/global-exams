import json
from datasets import Dataset
from huggingface_hub import HfApi, DatasetCard

# Load the dataset
with open('final_dataset.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create a Hugging Face dataset
dataset = Dataset.from_list(data)

# Initialize the Hugging Face API
api = HfApi()

# Push the dataset to the Hugging Face Hub
api.create_repo(
    repo_id="serhany/swedish-medical-exams-mcq-1002",
    repo_type="dataset",
    private=False
)

dataset.push_to_hub("serhany/swedish-medical-exams-mcq-1002")

# Load and update the README.md file
with open('README.md', 'r', encoding='utf-8-sig') as f:
    readme_content = f.read()

# Create a dataset card
card = DatasetCard.load("serhany/swedish-medical-exams-mcq-1002")
card.language = ['sv']
card.license = 'unknown'
card.task_categories = ['question-answering']
card.size_categories = ['1K<n<10K']
card.tags = ['domain:medicine', 'language:swedish', 'task:multiple-choice-qa']

# Set the card content
card.text = readme_content

# Push the dataset card to the Hub
card.push_to_hub("serhany/swedish-medical-exams-mcq-1002")

print("Dataset successfully published to Hugging Face Hub!")
