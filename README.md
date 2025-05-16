# Sheetpedia
• `src/`: Main Python source code.


Source Code (`src/`)
Core Files
• `__init__.py`: Marks the directory as a Python package.

• `utils/`: Shared utility functions.

  • Modules:

    ◦ `string_util.py`: String manipulation helpers.

    ◦ `jsonl2csv.py`, `jsonl2json.py`: Data format converters.

    ◦ `formula_util.py`: Formula checking logic.

    ◦ `api_util.py`: API interaction helpers.


Functional Modules
1. `data_evaluation/`
   • `nl2formula/`: Evaluates "natural language to formula" on test set.

     ◦ `nl2formula_result_evaluator.py`: Evaluates "natural language to formula" on test set.

   • `nl2semantic_range/`: Evaluates "natural language to semantic range" on test set.

     ◦ `nl2semantic_range_result_evaluator.py`: Evaluates "natural language to semantic range" on test set.


2. `data_preprocessing/`
   • `split_dataset.py`: Dataset splitting utilities.

   • Submodules (`nl2formula/`, `nl2semantic_range/`):

     ◦ Preprocessor scripts (e.g., `*_preprocessor.py`) for task-specific test set data generation.

     ◦ `resources/`: Templates/prompts for LLM interactions:

       ◦ `system_message_prompts.json`: LLM system role definitions.

       ◦ `*_template.txt`: User query/answer templates.


3. `data_generation/`
   • Task-specific train set generators (`nl2formula/`, `nl2semantic_range/`):

     ◦ `*_generator_rs.py`: Likely generates synthetic data ("rs" indicate "rejection sampling").

     ◦ `resources/`: Similar to preprocessing but includes:

       ◦ `scoring_prompt.txt`: Criteria for LLM self-evaluation.

