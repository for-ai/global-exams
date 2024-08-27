import json

def process_dataset(input_file, output_file):
    # Read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Process each item in the dataset
    for item in data:
        options = item['options']
        answer = item['answer']
        
        # Find the index of the answer in the options list
        try:
            answer_index = options.index(answer) + 1  # Add 1 to make it 1-indexed
            item['answer'] = str(answer_index)  # Convert to string
        except ValueError:
            print(f"Warning: Answer '{answer}' not found in options for question: {item['question'][:50]}...")

    # Write the processed data to the output JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Processing complete. Output saved to {output_file}")

# Run the function
process_dataset('merged_dataset.json', 'final_dataset.json')