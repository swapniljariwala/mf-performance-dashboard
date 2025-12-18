"""
Script to convert CSV files in output/ folder to Parquet format
"""
import os
import pandas as pd
from pathlib import Path


def convert_csv_to_parquet(input_folder='output', output_file='output/all_funds.parquet'):
    """
    Convert all CSV files in the specified folder to a single Parquet file.
    
    Args:
        input_folder: Path to folder containing CSV files (default: 'output')
        output_file: Path to output Parquet file (default: 'output/all_funds.parquet')
    """
    # Create Path object for the input folder
    input_path = Path(input_folder)
    
    # Check if folder exists
    if not input_path.exists():
        print(f"Error: Folder '{input_folder}' does not exist")
        return
    
    # Find all CSV files
    csv_files = list(input_path.glob('*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in '{input_folder}' folder")
        return
    
    print(f"Found {len(csv_files)} CSV file(s) to convert")
    
    # List to store all dataframes
    all_dfs = []
    
    # Read each CSV and add fund category
    for csv_file in csv_files:
        try:
            # Read CSV
            print(f"Reading {csv_file.name}...", end=' ')
            df = pd.read_csv(csv_file)
            
            # Extract fund name from filename (e.g., etmoney_largecap.csv -> largecap)
            fund_name = csv_file.stem.replace('etmoney_', '')
            
            # Add fund_name column to the dataframe
            df['fund_category'] = fund_name
            
            all_dfs.append(df)
            print(f"✓ ({len(df)} rows, category: {fund_name})")
            
        except Exception as e:
            print(f"✗ Error reading {csv_file.name}: {str(e)}")
    
    # Concatenate all dataframes
    if all_dfs:
        print(f"\nCombining {len(all_dfs)} dataframes...")
        combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # Save to Parquet
        print(f"Saving to {output_file}...")
        combined_df.to_parquet(output_file, index=False, engine='pyarrow')
        
        print(f"\n✓ Successfully created {output_file}")
        print(f"  Total rows: {len(combined_df)}")
        print(f"  Total columns: {len(combined_df.columns)}")
        print(f"  Categories: {combined_df['fund_category'].nunique()}")
    else:
        print("\nNo data to save")
    
    print("\nConversion complete!")


if __name__ == '__main__':
    convert_csv_to_parquet()
