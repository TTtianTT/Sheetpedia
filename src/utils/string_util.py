def generate_sheet_string_without_address_content(data, formula_address):
    """
    Generate a string representation of the sheet without the content of the cell at the formula_address.

    Args:
        data (dict): A dictionary representing the sheet data.
        formula_address (str): A string representing the cell address of the formula.

    Returns:
        str: A string representation of the sheet.
    """
    rows = data.get('Cells', [])
    merged_regions = data.get('MergedRegions', [])
    row_string_list = []

    for row in rows:
        cell_string_list = []
        for cell in row:
            # If the cell address is the formula address, the cell content is empty.
            cell_str = "{},{}".format(cell['Address'], '') if cell['Address'] == formula_address else "{},{}".format(
                cell['Address'], cell['Text'].replace('\n', ' '))
            cell_string_list.append(cell_str)
        row_string_list.append('|'.join(cell_string_list))

    sheet_string = '\n'.join(row_string_list)

    if merged_regions:  # If MergedRegions is not empty
        merged_region_address_list = [mr.get('Address', '') for mr in merged_regions]
        sheet_string += '\n' + 'Merged Ranges:\n' + '\n'.join(merged_region_address_list)

    return sheet_string

