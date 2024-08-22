import os
import openai
import json
import re
import time

client = openai.OpenAI(api_key='<enter your key'>)
def parse_gpt_output_batch(response):
    category_en_pattern = re.compile(r"<category_en>(.*?)</category_en>", re.DOTALL)
    category_original_lang_pattern = re.compile(r"<category_original_lang>(.*?)</category_original_lang>", re.DOTALL)

    category_en_matches = category_en_pattern.findall(response)
    category_original_lang_matches = category_original_lang_pattern.findall(response)

    return list(zip(category_en_matches, category_original_lang_matches))

def classify_questions_batch(questions_batch, language, max_retries=3):
    """Classify a batch of questions using OpenAI's API."""

    pre_prompt = """Please infer english category of question, as well as category in Telugu language and they should be within <category_en> </category_en> and <category_original_lang> </category_original_lang> tags respectively.
                Category has to be from:
                categories = {
                    "Physics": "భౌతిక శాస్త్రం",
                    "Civics": "పౌరశాస్త్రం",
                    "History": "చరిత్ర",
                    "Biology": "జీవవిజ్ఞానం",
                    "Reasoning": "తార్కికత",
                    "Telugu Language and Literature": "తెలుగు భాష మరియు సాహిత్యం",
                    "Mathematics": "గణితం",
                    "Economics": "ఆర్థిక శాస్త్రం",
                    "Political Science": "రాజకీయ శాస్త్రం",
                    "Current Affairs": "ప్రస్తుత వ్యవహారాలు",
                    "Geography": "భూగోళశాస్త్రం",
                    "Chemistry": "రసాయన శాస్త్రం"
                }
                Pack the answer into:
                <category_en> </category_en>
                <category_original_lang> </category_original_lang>
                <question_num> </question_num>
                """
    retry_count = 0
    while retry_count < max_retries:
        try:
            batch_prompt = pre_prompt
            for idx, item in enumerate(questions_batch):
                question = item["question"]
                options = item["options"]
                batch_prompt += f"Question {idx+1}: {question}\nOptions: {', '.join(options)}\n"        
        
            messages = [{"role": "system", "content": batch_prompt}]
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=1000,
                temperature=0.1
            )
            response_text = response.choices[0].message.content.strip()
            return parse_gpt_output_batch(response_text)

        except (openai.OpenAIError, KeyError, ValueError, IndexError) as e:
            retry_count += 1
            print(f"Error: {str(e)}. Retrying... ({retry_count}/{max_retries})")
            time.sleep(1)
        return []
        

def process_json_file(input_file, output_file, language, batch_size=5, max_retries=3):
    with open(input_file, "r", encoding="utf-8") as file:
        try:
            json_list = json.load(file)
        except json.JSONDecodeError:
            print("Failed to decode JSON")
            return

    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as outfile:
            try:
                updated_json_list = json.load(outfile)
                processed_items = len(updated_json_list)
                print(f"Resuming from item {processed_items}...")
            except json.JSONDecodeError:
                print("Failed to decode JSON from output file. Starting from scratch.")
                updated_json_list = []
                processed_items = 0
    else:
        updated_json_list = []
        processed_items = 0

    total_batches = len(json_list) // batch_size + (1 if len(json_list) % batch_size != 0 else 0)

    for batch_idx in tqdm.tqdm(range(processed_items // batch_size, total_batches)):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(json_list))
        batch = json_list[start_idx:end_idx]
        
        for retry in range(max_retries):
            try:
                classifications = classify_questions_batch(batch, language)

                if classifications and len(classifications) == len(batch):
                    for i, (category_en, category_original_lang) in enumerate(classifications):
                        if not category_en or not category_original_lang:
                            raise ValueError(f"Empty category found in question {batch[i]['question']}")

                        batch[i]["category_en"] = category_en
                        batch[i]["category_original_lang"] = category_original_lang
                    break
                else:
                    raise ValueError("Mismatch between batch size and classifications.")
            except Exception as e:
                print(f"Error on batch {batch_idx+1}, retry {retry+1}/{max_retries}: {e}")
                if retry == max_retries - 1:
                    print("Max retries reached. Moving to the next batch.")
                    return

        updated_json_list.extend(batch)
        #print(f"Batch {batch_idx+1} processed. Total processed so far: {len(updated_json_list)}")

        # Dump the current state to the output file after each successful batch
        with open(output_file, "w", encoding="utf-8") as outfile:
            json.dump(updated_json_list, outfile, ensure_ascii=False, indent=4)
        #print(f"Progress saved. Updated JSON saved to {output_file} after batch {batch_idx+1}.")

    print("Finished processing all batches.")
    
if __name__ == "__main__":
    exam_name = 'exam-name'
    input_file = f"{exam_name}.json"
    output_file = f"{exam_name}.json"
    language = "Telugu"
    batch_size = 15 
    process_json_file(input_file, output_file, language, batch_size=1)

