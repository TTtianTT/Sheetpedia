import os
import json
import sys

# 获取当前脚本路径和项目根路径
current_script_path = os.path.abspath(__file__)
project_root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.append(project_root_path)
from src.data_preprocessing.split_dataset import split_data_keep_test_info


class NL2FormulaPreprocessor:
    def __init__(self, input_file_path, output_file_path, num_shot):
        self.current_script_path = os.path.abspath(__file__)
        self.project_root_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(self.current_script_path))))
        self.input_file_path = os.path.join(self.project_root_path, input_file_path)
        self.output_file_path = os.path.join(self.project_root_path, output_file_path)

        # 加载系统消息模板
        self.system_message_template = self.load_system_message_template(
            os.path.join(os.path.dirname(self.current_script_path), 'resources/system_message_prompts.json'))

        # 加载用户消息模板
        self.example_query_template = self.load_user_message_template(
            os.path.join(os.path.dirname(self.current_script_path), 'resources/example_query_template.txt'))
        self.user_message_template = self.example_query_template

        # 加载示例答案模板
        self.example_answer_template = self.load_user_message_template(
            os.path.join(os.path.dirname(self.current_script_path), 'resources/example_answer_template.txt'))

        self.num_shot = num_shot

        # 如果输出文件已存在，则删除旧文件
        if os.path.exists(self.output_file_path):
            os.remove(self.output_file_path)
            print("Deleted the old version of the file.")
        else:
            print(f"Generating {self.output_file_path}...")

    def load_system_message_template(self, template_file_path):
        """加载系统消息模板"""
        with open(template_file_path, 'r') as file:
            template = json.load(file)
        return template

    def load_user_message_template(self, template_file_path):
        """加载用户消息模板"""
        with open(template_file_path, 'r') as file:
            template = file.read()
        return template

    def generate_json(self, sheet_string, query, address, formula):
        """生成 JSON 格式的消息列表"""
        messages = []

        # 系统消息
        instruction = self.system_message_template['instruction']
        output_format = self.system_message_template['output_format']
        spreadsheet_data_format_description = self.system_message_template['spreadsheet_data_format_description']
        system_message = f"{instruction}\n\n{spreadsheet_data_format_description}\n\n{output_format}"
        messages.append({"role": "system", "content": system_message})

        # 示例消息
        examples = self.system_message_template['examples']
        for i, example in enumerate(examples, 1):
            if i > self.num_shot:
                break
            example_address = example['address']
            example_text = example['text']
            messages.append({"role": "system", "name": "example_user", "content": self.example_query_template.format(
                sheet_string=example['sheet_string'].replace(f"{example_address},{example_text}",
                                                             f"{example_address},"), address=example_address,
                query=example['query']
            )})
            example_formula_json = json.dumps(example['formula'])
            messages.append(
                {"role": "system", "name": "example_assistant", "content": self.example_answer_template.format(
                    query=example['query'], address=example['address'], formula=example_formula_json
                )})

        # 用户消息
        user_message = self.user_message_template.format(sheet_string=sheet_string, address=address, query=query)
        messages.append({"role": "user", "content": user_message})

        # 助手消息（标签）
        formula_json = json.dumps(formula)
        label = self.example_answer_template.format(address=address, formula=formula_json)
        messages.append({"role": "assistant", "content": label})

        return messages

    def preprocess_and_split_data(self):
        """预处理数据并拆分数据集"""
        data = []

        # 读取输入文件
        with open(self.input_file_path, 'r', encoding='utf-8') as file:
            for line in file:
                data.append(json.loads(line))

        # 确保输出文件的目录存在
        output_dir = os.path.dirname(self.output_file_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 处理每条数据
        for item in data:
            file_path = item.get('FileName', item.get('fileName'))
            sheet_name = item.get('SheetName', item.get('sheetName'))
            formula = item.get('Formula', item.get('formula'))
            address = item.get('Address', item.get('address'))
            query = item.get('Query', item.get('best_query'))
            sheet_string = item.get('sheet_string')
            sheet_string_without_address = item.get('sheet_string_without_address')

            if not query:
                continue

            # 生成消息列表并保存结果
            message_list = self.generate_json(sheet_string_without_address, query, address=address, formula=formula)
            result = {
                "messages": message_list,
                "fileName": file_path,
                "sheetName": sheet_name
            }
            with open(self.output_file_path, 'a') as outfile:
                outfile.write(json.dumps(result) + '\n')

        # 拆分数据集
        split_data_keep_test_info(self.output_file_path, 0.9, 0.1, 0)


if __name__ == "__main__":
    config_list = [
        {"num_shot": 0},
        {"num_shot": 1},
        {"num_shot": 3},
    ]

    for config in config_list:
        num_shot = config["num_shot"]
        output_file_path = f'data/processed/nl2formula/nl2formula_testset_{num_shot}shot.jsonl'
        preprocessor = NL2FormulaPreprocessor(
            input_file_path='data/interim/task_specific/nl2formula/nl2formula_rs_2025-03-23_19-20.jsonl',
            output_file_path=output_file_path,
            num_shot=num_shot)
        preprocessor.preprocess_and_split_data()