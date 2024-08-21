import json

def validate_json_format(json_data):
    errors = []
    
    required_keys = ["language", "country", "file_name", "source", "license", "level", "category_en", "category_original_lang", "original_question_num", "question", "options", "answer"]

    for i, entry in enumerate(json_data):
        missing_keys = [key for key in required_keys if key not in entry]
        if missing_keys:
            errors.append(f"Entry {i} is missing keys: {missing_keys}")
            print(entry)
        #if not isinstance(entry.get("original_question_num"), int):
        #    errors.append(f"Entry {i} has an invalid 'original_question_num': {entry.get('original_question_num')}")
        
        #if not isinstance(entry.get("options"), list):
        #    errors.append(f"Entry {i} has an invalid 'options' field: {entry.get('options')}")

    return errors


with open('<path_to_json>', 'r') as f:
    ntse_data = json.load(f)

# Check for errors in JSON format
errors = validate_json_format(ntse_data)
if errors:
    for error in errors:
        print(error)
else:
    print("No errors found in the JSON format.")