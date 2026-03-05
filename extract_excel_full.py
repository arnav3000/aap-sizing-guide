#!/usr/bin/env python3
"""
Extract and analyze all data from AAP sizing Excel reference sheet
"""
import pandas as pd
import json

# Read the Excel file
excel_file = '/Users/arbhati/project/git/aap-sizing-guide/docs/AAp-sizing-sheet-reference.xlsx'

df = pd.read_excel(excel_file, sheet_name='Sheet1', header=None)

# Print all rows
print("COMPLETE EXCEL CONTENT")
print("=" * 120)
for idx, row in df.iterrows():
    print(f"Row {idx:3d}: {list(row)}")

print("\n" + "=" * 120)
print("EXTRACTING PARAMETERS AND FORMULAS")
print("=" * 120)

# Extract parameters (rows with values)
parameters = {}
formulas = {}

for idx, row in df.iterrows():
    # Check if row has parameter name and value
    if pd.notna(row[1]) and pd.notna(row[2]):
        param_name = str(row[1]).strip()
        param_value = row[2]
        description = str(row[3]) if pd.notna(row[3]) else ""
        note = str(row[4]) if pd.notna(row[4]) else ""

        if param_name and param_value != 'NaN':
            parameters[param_name] = {
                'value': param_value,
                'description': description,
                'note': note,
                'row': idx
            }

print("\nEXTRACTED PARAMETERS:")
print(json.dumps(parameters, indent=2, default=str))

# Save to JSON
with open('/Users/arbhati/project/git/aap-sizing-guide/docs/extracted_excel_parameters.json', 'w') as f:
    json.dump(parameters, f, indent=2, default=str)

print("\n\nSaved to: docs/extracted_excel_parameters.json")
