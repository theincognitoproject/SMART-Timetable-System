import pandas as pd
from sqlalchemy import create_engine
import mysql.connector
import os
import getpass
import sys

def get_user_inputs():
    """Get all necessary inputs from user"""
    print("\n=== MySQL Connection Details ===")
    host = 'localhost'
    database = input("Enter database name: ")
    username = 'root'
    password = getpass.getpass("Enter MySQL password: ")  # Securely input password
    
    print("\n=== CSV File Details ===")
    while True:
        csv_path = input("Enter the full path to your CSV file: ")
        if os.path.exists(csv_path) and csv_path.lower().endswith('.csv'):
            break
        print("Invalid file path or not a CSV file. Please try again.")
    
    table_name = input("Enter the desired MySQL table name: ")
    
    return host, database, username, password, csv_path, table_name

def preview_csv(df):
    """Show preview of CSV data"""  
    print("\n=== CSV Preview ===")
    print("\nFirst few rows of your CSV file:")
    print(df.head())
    print("\nColumns in your CSV file:")
    print(df.columns.tolist())
    print("\nData Info:")
    print(df.info())

def csv_to_mysql():
    try:
        # Get user inputs
        host, database, username, password, csv_path, table_name = get_user_inputs()
        
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

        # Create MySQL connection string
        connection_string = f"mysql+mysqlconnector://{username}:{password}@{host}/{database}"
        
        # Create engine
        print("\nConnecting to MySQL...")
        engine = create_engine(connection_string)
        
        # Test connection
        try:
            with engine.connect() as conn:
                print("Successfully connected to MySQL database!")
        except Exception as e:
            print(f"Error connecting to MySQL: {str(e)}")
            return

        # Import data to MySQL
        print("\nImporting data to MySQL...")
        print("This may take a while depending on the file size...")
        
        # Handle data import with progress tracking
        total_rows = len(df)
        chunk_size = 1000
        
        for i in range(0, total_rows, chunk_size):
            chunk_df = df[i:i + chunk_size]
            if i == 0:
                # First chunk - replace table if exists
                chunk_df.to_sql(name=table_name,
                              con=engine,
                              if_exists='replace',
                              index=False)
            else:
                # Subsequent chunks - append to table
                chunk_df.to_sql(name=table_name,
                              con=engine,
                              if_exists='append',
                              index=False)
            
            # Show progress
            progress = min((i + chunk_size) / total_rows * 100, 100)
            print(f"Progress: {progress:.1f}%", end='\r')
        
        print("\nData import completed!")
        
        # Verify the import
        try:
            with engine.connect() as conn:
                result = pd.read_sql(f"SELECT COUNT(*) as count FROM {table_name}", conn)
                print(f"\nVerification: {result.iloc[0]['count']} rows imported to MySQL table '{table_name}'")
        except Exception as e:
            print(f"\nError verifying data: {str(e)}")

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        
    finally:
        if 'engine' in locals():
            engine.dispose()
            print("\nMySQL connection closed")

def main():
    print("=== CSV to MySQL Import Tool ===")
    
    while True:
        csv_to_mysql()
        
        retry = input("\nWould you like to import another CSV file? (yes/no): ").lower()
        if retry != 'yes':
            break
    
    print("\nThank you for using CSV to MySQL Import Tool!")
if __name__ == "__main__":
    main()