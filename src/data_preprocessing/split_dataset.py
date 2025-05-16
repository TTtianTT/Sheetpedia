import json
import os
import jsonlines
from sklearn.model_selection import train_test_split

def split_data_keep_test_info(file_path, train_size=0.8, val_size=0.1, test_size=0.1):
    with jsonlines.open(file_path, 'r') as file:
        data = [line for line in file]
        print(len(data))
        # Remove duplicates
        data = list({json.dumps(item): item for item in data}.values())
        print(len(data))

        # Group data by file name and sheet name
        grouped_data = {}
        for item in data:
            key = item['fileName'] + item['sheetName']
            if key not in grouped_data:
                grouped_data[key] = []
            grouped_data[key].append(item)

        if train_size == 1 or test_size == 1:
            target_data = [item for sublist in list(grouped_data.values()) for item in sublist]
            # Only keep 'messages', 'fileName', and 'sheetName' fields in target data
            target_data = [{'messages': item['messages'], 'fileName': item['fileName'], 'sheetName': item['sheetName']}
                           for item in target_data]

            dir_name, base_name = os.path.split(file_path)
            base_name = os.path.splitext(base_name)[0]

            # Write target set to a new .jsonl file
            target_file_name = f'{base_name}_train.jsonl' if train_size == 1 else f'{base_name}_test.jsonl'
            with jsonlines.open(os.path.join(dir_name, target_file_name), mode='w') as writer:
                writer.write_all(target_data)

        elif test_size == 0:
            train_data, val_data = train_test_split(list(grouped_data.values()), train_size=train_size, shuffle=True)

            train_data = [item for sublist in train_data for item in sublist]
            val_data = [item for sublist in val_data for item in sublist]

            train_data = [{'messages': item['messages']} for item in train_data]
            val_data = [{'messages': item['messages']} for item in val_data]

            dir_name, base_name = os.path.split(file_path)
            base_name = os.path.splitext(base_name)[0]

            with jsonlines.open(os.path.join(dir_name, f'{base_name}_train.jsonl'), mode='w') as writer:
                writer.write_all(train_data)

            with jsonlines.open(os.path.join(dir_name, f'{base_name}_val.jsonl'), mode='w') as writer:
                writer.write_all(val_data)

        else:
            train_data, test_val_data = train_test_split(list(grouped_data.values()), train_size=train_size,
                                                         shuffle=True)
            val_data, test_data = train_test_split(test_val_data, train_size=val_size / (val_size + test_size),
                                                   shuffle=True)

            # Flatten nested lists
            train_data = [item for sublist in train_data for item in sublist]
            val_data = [item for sublist in val_data for item in sublist]
            test_data = [item for sublist in test_data for item in sublist]

            # Only keep 'messages' field in train, val and test data
            train_data = [{'messages': item['messages']} for item in train_data]
            val_data = [{'messages': item['messages']} for item in val_data]
            test_data = [{'messages': item['messages']} for item in test_data]

            dir_name, base_name = os.path.split(file_path)
            base_name = os.path.splitext(base_name)[0]

            # Write training set to a new .jsonl file
            with jsonlines.open(os.path.join(dir_name, f'{base_name}_train.jsonl'), mode='w') as writer:
                writer.write_all(train_data)

                # Write validation set to a new .jsonl file
            with jsonlines.open(os.path.join(dir_name, f'{base_name}_val.jsonl'), mode='w') as writer:
                writer.write_all(val_data)

                # Write test set to a new .jsonl file
            with jsonlines.open(os.path.join(dir_name, f'{base_name}_test.jsonl'), mode='w') as writer:
                writer.write_all(test_data)
