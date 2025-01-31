import pandas as pd
import psycopg2
import os
import sys
from config import DATABASE_URL  # Import DATABASE_URL from config.py

def get_user_inputs():
    """Get all necessary inputs from user"""
    print("\n=== CSV File Details ===")
    while True:
        csv_path = input("Enter the full path to your CSV file: ")
        if os.path.exists(csv_path) and csv_path.lower().endswith('.csv'):
            break
        print("Invalid file path or not a CSV file. Please try again.")
    
    table_name = input("Enter the desired PostgreSQL table name: ")
    
    return csv_path, table_name

def preview_csv(df):
    """Show preview of CSV data"""  
    print("\n=== CSV Preview ===")
    print("\nFirst few rows of your CSV file:")
    print(df.head())
    print("\nColumns in your CSV file:")
    print(df.columns.tolist())
    print("\nData Info:")
    print(df.info())

def create_table_if_not_exists(cursor, table_name, df):
    """Create the table if it doesn't exist"""
    columns_with_types = []
    for col in df.columns:
        columns_with_types.append(f'"{col}" TEXT')  # Adjust column types as needed (e.g., TEXT, INTEGER)
    
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        {', '.join(columns_with_types)}
    );
    """
    cursor.execute(create_table_query)
    print(f"Table '{table_name}' checked/created successfully.")

def csv_to_postgresql():
    try:
        # Get user inputs
        csv_path, table_name = get_user_inputs()
        
        # Read CSV file
        print("\nReading CSV file...")
        try:
            df = pd.read_csv(csv_path)
            print(f"Successfully read CSV file with {len(df)} rows and {len(df.columns)} columns.")
            
            # Show preview
            preview_csv(df)
            
            # Confirm with user
            confirm = input("\nDo you want to proceed with the import? (yes/no): ").lower()
            if confirm != 'yes':
                print("Import cancelled by user.")
                return
            
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return

        # Create PostgreSQL connection
        print("\nConnecting to PostgreSQL...")
        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            print("Successfully connected to PostgreSQL database!")
        except Exception as e:
            print(f"Error connecting to PostgreSQL: {str(e)}")
            return

        # Create the table if it doesn't exist
        create_table_if_not_exists(cursor, table_name, df)

        # Import data to PostgreSQL
        print("\nImporting data to PostgreSQL...")
        print("This may take a while depending on the file size...")
        
        # Handle data import
        try:
            for i, row in df.iterrows():
                columns = ', '.join([f'"{col}"' for col in df.columns])  # Ensure columns are quoted
                values = ', '.join([f'%s' for _ in row])
                insert_query = f'INSERT INTO "{table_name}" ({columns}) VALUES ({values})'
                cursor.execute(insert_query, tuple(row))
                if i % 1000 == 0:
                    conn.commit()
                    print(f"Progress: {i}/{len(df)} rows inserted", end='\r')
            conn.commit()
            print("\nData import completed!")
        except Exception as e:
            print(f"Error inserting data: {str(e)}")
            conn.rollback()
        
        # Verify the import
        try:
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            print(f"\nVerification: {count} rows imported to PostgreSQL table '{table_name}'")
        except Exception as e:
            print(f"\nError verifying data: {str(e)}")

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
            print("\nPostgreSQL connection closed")

def main():
    print("=== CSV to PostgreSQL Import Tool ===")
    
    while True:
        csv_to_postgresql()
        
        retry = input("\nWould you like to import another CSV file? (yes/no): ").lower()
        if retry != 'yes':
            break
    
    print("\nThank you for using CSV to PostgreSQL Import Tool!")

if __name__ == "__main__":
    main()
