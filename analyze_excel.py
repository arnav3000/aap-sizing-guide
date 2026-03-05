#!/usr/bin/env python3
"""
Analyze the AAP sizing Excel reference sheet
"""
import pandas as pd
import json

# Read the Excel file
excel_file = '/Users/arbhati/project/git/aap-sizing-guide/docs/AAp-sizing-sheet-reference.xlsx'

# Get all sheet names
xl = pd.ExcelFile(excel_file)
print("=" * 80)
print("EXCEL FILE ANALYSIS: AAp-sizing-sheet-reference.xlsx")
print("=" * 80)
print(f"\nSheet Names: {xl.sheet_names}\n")

# Read and display each sheet
for sheet_name in xl.sheet_names:
    print("\n" + "=" * 80)
    print(f"SHEET: {sheet_name}")
    print("=" * 80)

    df = pd.read_excel(excel_file, sheet_name=sheet_name)

    print(f"\nShape: {df.shape[0]} rows × {df.shape[1]} columns")
    print(f"\nColumns: {list(df.columns)}")

    print("\n--- First 20 rows ---")
    print(df.head(20).to_string())

    print("\n--- Data Info ---")
    print(df.info())

    # Check for formulas or special patterns
    print("\n--- Non-null value summary ---")
    print(df.count())

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
