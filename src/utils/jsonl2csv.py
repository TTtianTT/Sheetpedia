import pandas as pd
import os

def jsonl_to_csv(input_file):
    """
    This function converts a JSONL file to a CSV file.

    Parameters:
    input_file (str): The path to the JSONL file to be converted.

    Returns:
    None. A message is printed indicating the successful conversion and the name of the created CSV file.
    """
    # Read the jsonl file
    data = pd.read_json(input_file, lines=True)

    # Convert to csv
    csv_file = os.path.splitext(input_file)[0] + '.csv'
    data.to_csv(csv_file, index=False)
    print(f'Successfully converted {input_file} to {csv_file}')

if __name__ == '__main__':
    jsonl_to_csv(r"C:\Users\v-zatian\PycharmProjects\SheetMontageUtility0510\SheetMontageUtility\src\data_generation\sheet_montage\chart2rt_results_1010_with_names.jsonl")