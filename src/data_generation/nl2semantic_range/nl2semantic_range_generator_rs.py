import sys
import os
import json
import re
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
from functools import lru_cache

current_script_path = os.path.abspath(__file__)
project_root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))
sys.path.append(project_root_path)

from src.utils.api_util import request_and_log_api_openrouter,request_and_log_api_openrouter_parallel
from src.utils.jsonl2csv import jsonl_to_csv
from src.utils.formula_util import extract_range_from_formula


class PromptTooLongError(Exception):
    pass


class NL2SemanticRangeGenerator:
    def __init__(self, api_request_limit, json_directory, processed_file_path=None,
                 generation_model="google/gemini-2.0-flash-001", generation_max_tokens=256, generation_temperature=0.7,
                 scoring_model="anthropic/claude-3-opus", scoring_max_tokens=256, scoring_temperature=0.0,
                 candidate_num=3, min_accept_score=0.7):
        """
        Initialize the NL2Formula generator with configurable models and parameters.

        Args:
            api_request_limit (int): Maximum number of API requests allowed.
            json_directory (str): Directory containing the input JSON files.
            processed_file_path (str, optional): Path to the file tracking processed sheets.
            generation_model (str): Model for generating queries. Default is "google/gemini-2.0-flash-001".
            generation_max_tokens (int): Max tokens for query generation. Default is 256.
            generation_temperature (float): Temperature for query generation. Default is 0.7.
            scoring_model (str): Model for rejection sampling. Default is "anthropic/claude-3-opus".
            scoring_max_tokens (int): Max tokens for scoring. Default is 256.
            scoring_temperature (float): Temperature for scoring. Default is 0.0.
            candidate_num (int): Number of candidates for rejection sampling. Default is 3.
            min_accept_score (float): Minimum score to accept a candidate. Default is 0.7.
        """
        current_script_path = os.path.abspath(__file__)
        project_root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_script_path))))

        # API and processing limits
        self.api_request_limit = api_request_limit
        self.json_directory = os.path.join(project_root_path, json_directory)

        # Query generation parameters
        self.generation_model = generation_model
        self.generation_max_tokens = generation_max_tokens
        self.generation_temperature = generation_temperature

        # Rejection sampling parameters
        self.scoring_model = scoring_model
        self.scoring_max_tokens = scoring_max_tokens
        self.scoring_temperature = scoring_temperature
        self.candidate_num = candidate_num
        self.min_accept_score = min_accept_score

        # File paths setup
        current_date = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = f"nl2semantic_range_rs_{current_date}.jsonl"
        self.result_file_path = os.path.join(project_root_path, 'data', 'interim', 'task_specific', 'nl2semantic_range',
                                             filename)
        os.makedirs(os.path.dirname(self.result_file_path), exist_ok=True)

        # Load templates
        current_script_dir = os.path.dirname(current_script_path)
        self.system_message_template = self._load_template(
            os.path.join(current_script_dir, 'resources/system_message_prompts.json'))
        self.user_prompt_template = self._load_template(
            os.path.join(current_script_dir, 'resources/user_message_template.txt'))
        self.scoring_prompt_template = self._load_template(
            os.path.join(current_script_dir, 'resources/scoring_prompt.txt'))

        # Initialize state
        self.processed_files = set()
        if processed_file_path:
            self._load_processed_files(os.path.join(project_root_path, processed_file_path))

    def _load_template(self, template_path):
        """Load a template from a file."""
        with open(template_path, 'r') as f:
            return json.load(f) if template_path.endswith('.json') else f.read()

    def _load_processed_files(self, file_path):
        """Load the set of already processed files."""
        with open(file_path, 'r') as f:
            for line in f:
                item = json.loads(line)
                self.processed_files.add((item['fileName'], item['sheetName']))

    def build_generation_prompts(self, sheet_string, range_info):
        """Construct prompts for query generation"""
        messages = []
        instruction = self.system_message_template['instruction']
        spreadsheet_data_format_description = self.system_message_template['spreadsheet_data_format_description']
        system_message = f"{instruction}\n\n{spreadsheet_data_format_description}"

        # System Message
        messages.append({"role": "system", "content": system_message})

        # Examples
        for i, example in enumerate(self.system_message_template['examples'], 1):
            example_sheet = example['sheet']
            example_range_info = example['range_info']
            example_query = example['query']
            example_content = f"Example {i}:\nOriginal Sheet Content:\n{example_sheet}\n\nThe selected cell ranges: {example_range_info}"
            example_response = f"Corresponding Query: {example_query}"
            messages.append({"role": "system", "name": "example_user", "content": example_content})
            messages.append({"role": "system", "name": "example_assistant", "content": example_response})

        # User Message
        user_message = self.user_prompt_template.format(sheet_string=sheet_string, range_info=range_info)
        messages.append({"role": "user", "content": user_message})
        return messages

    @lru_cache(maxsize=1000)
    def evaluate_query_quality(self, query, range_str, context):
        """Evaluate query quality using the scoring model."""
        try:
            prompt = self.scoring_prompt_template.format(
                cell_range=range_str,
                context=context,
                query=query
            )

            response = request_and_log_api_openrouter(
                messages=[{"role": "user", "content": prompt}],
                model=self.scoring_model,
                max_tokens=self.scoring_max_tokens,
                temperature=self.scoring_temperature
            )

            response = response.strip()
            json_match = re.search(r'(?i)(?:```json)?\s*(\{[\s\S]*\})(?:```)?', response, re.DOTALL)
            if not json_match:
                return {"score": 0, "details": {}, "rationale": "No valid JSON found in response"}

            json_str = json_match.group(1)

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON decoding failed: {e}")
            return {"score": 0, "details": {}, "rationale": "Invalid JSON format"}
        except Exception as e:
            print(f"Scoring failed: {e}")
            return {"score": 0, "details": {}, "rationale": "Evaluation failed"}

    def generate_candidates(self, messages):
        """Generate multiple candidate queries in parallel"""
        responses = request_and_log_api_openrouter_parallel(
            messages=messages,
            model=self.generation_model,
            max_tokens=self.generation_max_tokens,
            temperature=self.generation_temperature,
            concurrency=self.candidate_num
        )
        candidates = []
        for response in responses:
            try:
                response = response.strip()
                json_match = re.search(r'(?i)(?:```json)?\s*(\{[\s\S]*\})(?:```)?', response, re.DOTALL)
                if not json_match:
                    return {"score": 0, "details": {}, "rationale": "No valid JSON found in response"}

                json_str = json_match.group(1)

                candidates.append(json.loads(json_str)["query"])
            except:
                continue
        return candidates

    def rejection_sampling(self, candidates, range_str, context):
        """Perform rejection sampling with model scoring in parallel"""
        scored_candidates = []

        # Parrallel
        with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            futures = [
                executor.submit(self.evaluate_query_quality, query, range_str, context)
                for query in candidates
            ]

            for future, query in zip(as_completed(futures), candidates):
                try:
                    score_result = future.result()
                    normalized_score = score_result["score"] / 10  # Scale to 0-1
                    if normalized_score >= self.min_accept_score:
                        scored_candidates.append((
                            normalized_score,
                            query,
                            score_result
                        ))
                except Exception as e:
                    print(f"Scoring failed for query '{query}': {e}")

        return sorted(scored_candidates, key=lambda x: x[0], reverse=True)

    def process_ranges(self, data):
        results = []
        sheet_str = data['SheetString']
        sheet_name = data['sheetname']
        valid_ranges = set()
        max_ranges = 1

        for formula_info in data['FilteredFormulas']:
            formula = formula_info["Value"]

            try:
                ranges = extract_range_from_formula(formula, sheet_name)
                valid_ranges.update(ranges)

                if len(valid_ranges) >= max_ranges:
                    break
            except Exception as e:
                print(f"Error extracting ranges from formula {formula}: {e}")
                continue

        if not valid_ranges:
            print("No valid ranges found for any formula")
            return results

        ranges_to_process = list(valid_ranges)[:max_ranges]

        for range_str in ranges_to_process:

            try:
                messages = self.build_generation_prompts(sheet_str, range_str)
                candidates = self.generate_candidates(messages)
            except Exception as e:
                print(f"Query generation failed for range {range_str}: {e}")
                continue

            if not candidates:
                print(f"No candidates generated for range {range_str}")
                continue

            try:
                scored_candidates = self.rejection_sampling(
                    candidates, range_str,
                    f"Range: {range_str} | Sheet: {sheet_str}"
                )
            except Exception as e:
                print(f"Rejection sampling failed for range {range_str}: {e}")
                continue

            if not scored_candidates:
                print(f"No scored candidates for range {range_str}")
                continue

            queries_with_scores = []
            for score, query, score_details in scored_candidates:
                queries_with_scores.append({
                    "query": query,
                    "score": score,
                    "score_details": score_details
                })

            if queries_with_scores:
                best_query = max(queries_with_scores, key=lambda x: x["score"])["query"]

                results.append({
                    "range": range_str,
                    "best_query": best_query,
                    "queries": queries_with_scores,
                    "sheet_string": sheet_str
                })

        return results



    def generate_dataset(self):
        """Main generation workflow"""
        processed_count = 0
        files = glob.glob(os.path.join(self.json_directory, "*.json"))

        with tqdm(total=min(self.api_request_limit, len(files) * 4), desc="Generating") as pbar:
            for file_path in files:
                if processed_count >= self.api_request_limit:
                    break

                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Skip processed sheets
                file_id = (data['filename'], data['sheetname'])
                if file_id in self.processed_files:
                    continue

                # Process formulas
                results = self.process_ranges(data)
                processed_count += len(results)
                pbar.update(len(results))

                # Save results
                self._save_results(data['filename'], data['sheetname'], results)

        jsonl_to_csv(self.result_file_path)

    def _save_results(self, filename, sheetname, results):
        """Save simplified results to JSONL"""
        with open(self.result_file_path, 'a') as f:
            for result in results:
                record = {
                    "fileName": filename,
                    "sheetName": sheetname,
                    "range": result["range"],
                    "best_query": result["best_query"],
                    "queries": result["queries"],
                    "sheet_string": result["sheet_string"],
                }
                f.write(json.dumps(record) + '\n')
if __name__ == '__main__':
    generator = NL2SemanticRangeGenerator(
        api_request_limit=2200,
        json_directory="data/output_json_formula",
        processed_file_path=None,
        generation_model="google/gemini-2.0-flash-001",
        generation_max_tokens=512,
        generation_temperature=0.7,
        scoring_model="anthropic/claude-3.7-sonnet",  # Rejection Sampling
        scoring_max_tokens=512,
        scoring_temperature=0.0,
        candidate_num=5,
        min_accept_score=0.7
    )
    generator.generate_dataset()