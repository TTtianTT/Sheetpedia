import json


def jsonl2json(jsonl_path):
    data = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))

    json_path = jsonl_path.rsplit('.', 1)[0] + '.json'
    with open(json_path, 'w') as f:
        json.dump(data, f)

if __name__ == '__main__':
    jsonl2json(r'C:\Users\v-zatian\PycharmProjects\SheetMontageUtility0510\SheetMontageUtility\data\processed\nl2semantic_range\nl2taskOne1009_train_4500_messages.jsonl')
    jsonl2json(r'C:\Users\v-zatian\PycharmProjects\SheetMontageUtility0510\SheetMontageUtility\data\processed\nl2semantic_range\nl2taskOne1009_val_500_messages.jsonl')
