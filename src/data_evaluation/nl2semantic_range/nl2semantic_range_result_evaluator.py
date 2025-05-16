import json
import re


def evaluate_nl2semantic_range(file_path):
    total_count = 0
    correct_count = 0

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            data = json.loads(line)
            label = data['label']
            prediction = data['predict']

            label = label.replace('<|eot_id|>\n', '')
            pattern = r'```Json\n(.*?)\n```'
            matches = re.findall(pattern, label, re.DOTALL)
            if matches:
                # The first match is the content between ```Json and ```
                range_json_str = matches[0]
                try:
                    range_json = json.loads(range_json_str)
                    label =  range_json.get('cell range').strip()
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from string: {range_json_str}")
                    return None
            else:
                return None
            if label in prediction:
                correct_count += 1
                # print(f"Label {label} is in prediction: {prediction}")
            else:
                print(f"Label {label} is NOT in prediction: {prediction}")

            total_count += 1

    if total_count > 0:
        accuracy = correct_count / total_count
        print(f"\nTotal data count: {total_count}")
        print(f"Correct count: {correct_count}")
        print(f"Accuracy: {accuracy:.4f} ({(accuracy * 100):.2f}%)")
    else:
        print("No data found in the file.")

if __name__ == '__main__':
    file_path = "data/nl2SR_test.jsonl"

    evaluate_nl2semantic_range(file_path)