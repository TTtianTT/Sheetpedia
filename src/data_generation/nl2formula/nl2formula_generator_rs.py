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
from src.utils.string_util import generate_sheet_string_without_address_content


class PromptTooLongError(Exception):
    pass


class NewNL2FormulaGenerator:
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
        filename = f"nl2formula_rs_{current_date}.jsonl"
        self.result_file_path = os.path.join(project_root_path, 'data', 'interim', 'task_specific', 'nl2formula',
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

    def build_generation_prompts(self, sheet_str, formula, address):
        """Construct prompts for query generation"""
        messages = [{
            "role": "system",
            "content": "\n\n".join([
                self.system_message_template["instruction"],
                self.system_message_template["spreadsheet_data_format_description"],
                self.system_message_template["output_format"],
                self.system_message_template["guidelines"]
            ])
        }]

        # Add examples
        for example in self.system_message_template["examples"]:
            messages.extend([
                {"role": "user", "content": self.user_prompt_template.format(
                    sheet_string=example["sheet_string"],
                    formula=example["formula"],
                    address=example["address"]
                )},
                {"role": "assistant", "content": json.dumps({
                    "query": example["query"],
                    "explanation": example["explanation"]
                })}
            ])

        # Add current task
        messages.append({
            "role": "user",
            "content": self.user_prompt_template.format(
                sheet_string=sheet_str,
                formula=formula,
                address=address
            )
        })

        return messages

    @lru_cache(maxsize=1000)
    def evaluate_query_quality(self, query, formula, context):
        """Evaluate query quality using the scoring model."""
        try:
            prompt = self.scoring_prompt_template.format(
                formula=formula,
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
                candidates.append(json.loads(response)["query"])
            except:
                continue
        return candidates

    def rejection_sampling(self, candidates, formula, context):
        """Perform rejection sampling with model scoring in parallel"""
        scored_candidates = []

        with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
            futures = [
                executor.submit(self.evaluate_query_quality, query, formula, context)
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

    def process_formulas(self, data):
        """Process formulas in a sheet and return simplified results"""
        results = []
        sheet_str = data['SheetString']

        for formula_info in data['FilteredFormulas'][:1]:  # Process first 3 formulas
            formula = formula_info["Value"]
            address = formula_info["Address"]

            # Generate the sheet string without the address content
            sheet_str_without_address = generate_sheet_string_without_address_content(data, address)

            # Generate candidates
            messages = self.build_generation_prompts(
                sheet_str_without_address,
                formula,
                address
            )
            candidates = self.generate_candidates(messages)

            # Skip if no candidates were generated
            if not candidates:
                print(f"No candidates generated for formula: {formula} at address: {address}")
                continue

            # Score all candidates
            scored_candidates = self.rejection_sampling(
                candidates, formula,
                f"Address: {address} | Sheet: {sheet_str}"
            )

            # Save all candidates with their scores as a list
            queries_with_scores = []
            for score, query, score_details in scored_candidates:
                queries_with_scores.append({
                    "query": query,
                    "score": score,
                    "score_details": score_details
                })

            # Save the entire formula result as one record
            if queries_with_scores:
                # Find the best query (highest score)
                best_query = max(queries_with_scores, key=lambda x: x["score"])["query"]

                results.append({
                    "formula": formula,
                    "address": address,
                    "queries": queries_with_scores,
                    "best_query": best_query,
                    "sheet_string": sheet_str,
                    "sheet_string_without_address": sheet_str_without_address
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
                results = self.process_formulas(data)
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
                    "formula": result["formula"],
                    "address": result["address"],
                    "best_query": result["best_query"],
                    "queries": result["queries"],
                    "sheet_string": result["sheet_string"],
                    "sheet_string_without_address": result["sheet_string_without_address"]
                }
                f.write(json.dumps(record) + '\n')
if __name__ == '__main__':
    generator = NewNL2FormulaGenerator(
        api_request_limit=120,
        json_directory="data/raw/raw_data_json_0219_processed",
        processed_file_path='data/interim/task_specific/nl2formula/nl2formula_0322_0shot.jsonl',
        generation_model="anthropic/claude-3.7-sonnet",
        generation_max_tokens=512,
        generation_temperature=0.7,
        scoring_model="anthropic/claude-3.7-sonnet",
        scoring_max_tokens=512,
        scoring_temperature=0.0,
        candidate_num=10,
        min_accept_score=0.7
    )
    generator.generate_dataset()