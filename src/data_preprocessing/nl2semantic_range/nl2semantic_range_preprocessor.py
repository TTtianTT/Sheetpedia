import os
import sys
import json

current_script_path = os.path.abspath(__file__)
project_root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.append(project_root_path)

from src.data_preprocessing.split_dataset import split_data_keep_test_info


class NL2SemanticRangePreprocessor:

    def __init__(self, input_file_path, output_file_path, num_shot=0):
        self.current_script_path = os.path.abspath(__file__)
        project_root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(self.current_script_path))))
        self.input_file_path = os.path.join(project_root_path, input_file_path)
        self.output_file_path = os.path.join(project_root_path, output_file_path)
        self.num_shot = num_shot

        # Create output directory if it doesn't exist
        if not os.path.exists(os.path.dirname(self.output_file_path)):
            os.makedirs(os.path.dirname(self.output_file_path))

        # Load templates
        self.system_message_template = self.load_system_message_template(
            os.path.join(os.path.dirname(self.current_script_path), 'resources/system_message_prompts.json'))
        self.example_query_template = self.load_user_message_template(
            os.path.join(os.path.dirname(self.current_script_path), 'resources/example_query_template.txt'))
        self.example_answer_template = self.load_user_message_template(
            os.path.join(os.path.dirname(self.current_script_path), 'resources/example_answer_template.txt'))
        self.user_message_template = self.load_user_message_template(
            os.path.join(os.path.dirname(self.current_script_path), 'resources/user_message_template.txt'))

        # Remove existing output file if it exists
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
            print(f"Deleted existing file: {self.output_file_path}")
        else:
            print(f"Creating new file: {self.output_file_path}")

    def load_system_message_template(self, template_file_path):
        with open(template_file_path, 'r') as file:
            template = json.load(file)
        return template

    def load_user_message_template(self, template_file_path):
        with open(template_file_path, 'r') as file:
            template = file.read()
        return template

    def generate_json(self, sheet_string, query, cell_range):
        messages = []

        # System Message
        instruction = self.system_message_template['instruction']
        spreadsheet_data_format_description = self.system_message_template['spreadsheet_data_format_description']
        mandatory_rules = self.system_message_template['mandatory_rules']
        output_format = self.system_message_template['output_format']
        system_message = f"{instruction}\n\n{spreadsheet_data_format_description}\n\n{mandatory_rules}\n\n{output_format}"
        messages.append({"role": "system", "content": system_message})

        # Examples (only include the specified number of shots)
        examples = self.system_message_template['examples'][:self.num_shot]
        for i, example in enumerate(examples, 1):
            # Example_User
            messages.append({"role": "system", "name": "example_user",
                             "content": self.example_query_template.format(
                                 sheet_string=example['sheet_string'],
                                 query=example['query'])})
            # Example_Assitant
            messages.append({"role": "system", "name": "example_assistant",
                             "content": self.example_answer_template.format(
                                 query=example['query'],
                                 cell_range=example['range_info'])})

        # User Message
        user_message = self.user_message_template.format(
            sheet_string=sheet_string, query=query)
        messages.append({"role": "user", "content": user_message})

        # Label
        label = self.example_answer_template.format(cell_range=cell_range)
        messages.append({"role": "assistant", "content": label})

        return messages

    def preprocess_and_split_data(self):
        data = []

        with open(self.input_file_path, 'r') as file:
            for line in file:
                data.append(json.loads(line))

        for item in data:
            file_path = item['fileName']
            sheet_name = item['sheetName']
            query = item['best_query']
            range_info = item['range']
            sheet_string = item['sheet_string']

            if not sheet_string:
                print(f'Empty SheetString in file {file_path}, sheet {sheet_name}')
                continue

            if not query:
                continue

            message_list = self.generate_json(sheet_string, query, range_info)

            result = {
                "messages": message_list,
                "fileName": file_path,
                "sheetName": sheet_name,
                'query': query,
                'rangeInfo': range_info,
            }

            with open(self.output_file_path, 'a') as outfile:
                outfile.write(json.dumps(result) + '\n')

        # Split the data (90% train, 10% test)
        split_data_keep_test_info(self.output_file_path, 0.9, 0.1, 0)


if __name__ == "__main__":
    input_file_path = 'data/interim/task_specific/nl2semantic_range/nl2semantic_range_rs_2025-03-23_20-18.jsonl'

    config_list = [
        {"num_shot": 0},
        {"num_shot": 1},
        # {"num_shot": 2},
        {"num_shot": 3},
    ]

    for config in config_list:
        num_shot = config["num_shot"]
        output_file_path = f'data/processed/nl2semantic_range/nl2semantic_range_testset_{num_shot}shot.jsonl'

        print(f"\nProcessing {num_shot}-shot configuration...")
        preprocessor = NL2SemanticRangePreprocessor(
            input_file_path=input_file_path,
            output_file_path=output_file_path,
            num_shot=num_shot)
        preprocessor.preprocess_and_split_data()
        print(f"Completed {num_shot}-shot configuration\n")