import json
import re
from datetime import datetime

def evaluate_nl2formula(file_path):
    total_count = 0
    correct_count = 0

    results = []

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
                formula_json_str = matches[0]
                try:
                    formula_json = json.loads(formula_json_str)
                    label =  formula_json.get('formula').strip()
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from string: {formula_json_str}")
                    return None
            else:
                return None
            is_correct = label in prediction

            if is_correct:
                correct_count += 1
                # print(f"Label {label} is in prediction: {prediction}")
            else:
                print(f"Label {label} is NOT in prediction: {prediction}")

            total_count += 1
            results.append({
                'label': label,
                'prediction': prediction,
                'is_correct': is_correct
            })

    if total_count > 0:
        accuracy = correct_count / total_count
        print(f"\nTotal data count: {total_count}")
        print(f"Correct count: {correct_count}")
        print(f"Accuracy: {accuracy:.4f} ({(accuracy * 100):.2f}%)")
    else:
        print("No data found in the file.")

    output_file_path = f"nl2formula_evaluation_results_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump({
                'total_count': total_count,
                'correct_count': correct_count,
                'accuracy': accuracy if total_count > 0 else None,
                'results': results
            }, output_file, ensure_ascii=False, indent=4)
        print(f"\nResults have been saved to {output_file_path}")
    except Exception as e:
        print(f"Failed to save results to file: {e}")

if __name__ == '__main__':
    file_path = "data/nl2formula_test_0shot_vanilla.jsonl"
    evaluate_nl2formula(file_path)