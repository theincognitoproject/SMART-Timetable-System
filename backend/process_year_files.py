import mysql.connector
import pandas as pd
import os
import re
import sys
import argparse
from dotenv import load_dotenv

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process year files and create database tables')
    parser.add_argument('--schema', required=True, help='Schema name to create/use')
    parser.add_argument('--files', nargs='+', required=True, help='Paths to Excel files')
    args = parser.parse_args()

    schema_name = args.schema
    file_paths = args.files

    # Connect to MySQL server
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Connect to Aiven MySQL server using environment variables
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()
        print("Connected to Aiven MySQL server successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL server: {err}")
        sys.exit(1)

    # Create schema if it doesn't exist
    try:
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS `{schema_name}`")
        cursor.execute(f"USE `{schema_name}`")
        
        # Add these two lines to grant privileges
        cursor.execute(f"GRANT ALL PRIVILEGES ON `{schema_name}`.* TO 'avnadmin'@'%'")
        cursor.execute("FLUSH PRIVILEGES")
        
        print(f"Schema '{schema_name}' is ready with permissions granted.")
    except mysql.connector.Error as err:
        print(f"Error creating/using schema: {err}")
        if "access denied" in str(err).lower():
            print("You may not have schema creation privileges. Try using table prefixes instead.")
            prefix = f"{schema_name}_"
        else:
            sys.exit(1)

    # Predefined table names
    predefined_tables = ["1stYear", "2ndYear", "3rdYear", "4thYear"]
    
    # Process each file
    for i, file_path in enumerate(file_paths):
        if i >= len(predefined_tables):
            print(f"Warning: Only processing first {len(predefined_tables)} files.")
            break
            
        if not os.path.exists(file_path):
            print(f"File '{file_path}' not found. Skipping.")
            continue

        # Use predefined table name
        table_name = predefined_tables[i]
        
        # Apply prefix if needed (in case schema creation failed)
        if 'prefix' in locals():
            table_name = f"{prefix}{table_name}"

        # Read the first sheet of the Excel file
        try:
            df = pd.read_excel(file_path, sheet_name=0)  # Read first sheet
        except Exception as e:
            print(f"Error reading Excel file: {e}")
            continue

        # Ensure column names are valid SQL identifiers
        def clean_column_name(name):
            name = re.sub(r'\W+', '_', name.strip())  # Replace non-alphanumeric characters with underscores
            if name[0].isdigit():
                name = f"col_{name}"  # Prefix with 'col_' if it starts with a number
            return name

        # Clean column names and remove duplicates
        df.columns = [clean_column_name(str(col)) for col in df.columns]

        # Remove empty columns (all NaN)
        df.dropna(axis=1, how="all", inplace=True)

        # Check if the table already exists
        try:
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            table_exists = cursor.fetchone()

            if not table_exists:
                # Generate SQL query to create table dynamically WITH PRIMARY KEY
                create_table_query = f"CREATE TABLE {table_name} ("
                create_table_query += "id INT AUTO_INCREMENT PRIMARY KEY,"  # Add auto-increment primary key
                for col in df.columns:
                    create_table_query += f"{col} TEXT,"  # Use TEXT to handle variable-length data
                create_table_query = create_table_query.rstrip(",") + ")"

                cursor.execute(create_table_query)  # Create table
                print(f"Created table '{table_name}' for file '{file_path}'.")

            # Insert data into table
            columns_str = ", ".join(f"{col}" for col in df.columns)
            placeholders = ", ".join(["%s"] * len(df.columns))
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            for _, row in df.iterrows():
                values = tuple(None if pd.isna(val) else str(val) for val in row)  # Convert NaN to NULL
                cursor.execute(insert_query, values)

            conn.commit()
            print(f"Stored first sheet from '{file_path}' into table '{table_name}'.")
        except mysql.connector.Error as err:
            print(f"Error processing table {table_name}: {err}")
            conn.rollback()

    # Step 2: Generate the AllSubjects Table
    print("\nGenerating the 'AllSubjects' table...")

    # Apply prefix if needed
    all_subjects_table = "AllSubjects"
    if 'prefix' in locals():
        all_subjects_table = f"{prefix}{all_subjects_table}"

    # Drop AllSubjects table if it already exists
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {all_subjects_table}")

        # Create AllSubjects table WITH PRIMARY KEY
        cursor.execute(f"""
            CREATE TABLE {all_subjects_table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sections TEXT,
                subjects TEXT
            )
        """)

        # Get all table names in the schema (excluding 'AllSubjects')
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall() if table[0].lower() != all_subjects_table.lower()]

        # Process each table
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            if len(columns) < 3:  # Need at least id + 2 columns
                print(f"Skipping table '{table}' as it doesn't have enough columns.")
                continue

            first_col_name = columns[1]  # Name of the first data column (Subjects) - index 1 because index 0 is 'id'
            second_col_name = columns[2]  # Name of the second data column (Sections) - index 2 because index 0 is 'id'
            additional_columns = columns[3:]  # Columns beyond the second data column

            # Collect all unique values from the first and second column
            first_col_values = []
            second_col_values = set()

            for row in rows:
                first_col_value = row[1]  # First data column value (Subject) - index 1 because index 0 is 'id'
                second_col_value = row[2]  # Second data column value (Section) - index 2 because index 0 is 'id'

                if first_col_value is not None:  # Ignore NULL subjects
                    first_col_values.append(first_col_value)

                if second_col_value is not None:
                    second_col_values.add(second_col_value)

            # Generate AllSubjects entries
            for section in second_col_values:
                for subject in first_col_values:
                    if subject in additional_columns:
                        # Replace subject with corresponding row value under that column
                        cursor.execute(f"SELECT {subject} FROM {table} WHERE {second_col_name} = %s", (section,))
                        subject_values = cursor.fetchall()
                        for subject_value in subject_values:
                            if subject_value[0]:  # Avoid NULL values
                                section_entry = f"{section} ({table})"
                                subject_entry = f"{subject_value[0]} ({table})({section}){'*'}"
                                cursor.execute(f"INSERT INTO {all_subjects_table} (sections, subjects) VALUES (%s, %s)", (section_entry, subject_entry))
                    else:
                        section_entry = f"{section} ({table})"
                        subject_entry = f"{subject} ({table}) ({section})"
                        cursor.execute(f"INSERT INTO {all_subjects_table} (sections, subjects) VALUES (%s, %s)", (section_entry, subject_entry))

        conn.commit()
        print(f"{all_subjects_table} table created successfully!")
    except mysql.connector.Error as err:
        print(f"Error creating {all_subjects_table}: {err}")
        conn.rollback()

    # Create UniqueSubjects table
    print("\nGenerating the 'UniqueSubjects' table...")
    unique_subjects_table = "UniqueSubjects"
    if 'prefix' in locals():
        unique_subjects_table = f"{prefix}{unique_subjects_table}"

    try:
        cursor.execute(f"DROP TABLE IF EXISTS {unique_subjects_table}")

        # Create the uniquesubjects table with Hours as INTEGER AND PRIMARY KEY
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {unique_subjects_table} (
            id INT AUTO_INCREMENT PRIMARY KEY,
            SubjectCode VARCHAR(9),
            Hours INTEGER
        )
        """
        cursor.execute(create_table_query)

        # Helper function to standardize string formatting
        def standardize_string(s):
            if s is None:
                return None
            return ' '.join(str(s).strip().split())

        # Helper function to process value with slash
        def process_slash_value(value):
            parts = value.split('/')
            if len(parts) == 2:
                subject_code = standardize_string(parts[0])[:9]
                return subject_code
            return None

        # Helper function to convert hours to integer
        def convert_to_integer(value):
            try:
                # First convert to float to handle decimal numbers
                float_val = float(str(value).strip())
                # Then convert to integer
                return int(float_val)
            except (ValueError, TypeError):
                return None

        # Get all tables except 'allsubjects' and 'uniquesubjects'
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall() 
                if table[0].lower() not in [all_subjects_table.lower(), unique_subjects_table.lower()]]

        # Set to track unique combinations
        unique_entries = set()

        # Process each table
        for table in tables:
            # Get column names for the current table
            cursor.execute(f"SHOW COLUMNS FROM {table}")
            all_columns = cursor.fetchall()
            column_names = [col[0] for col in all_columns]
            
            if len(all_columns) >= 4:  # Need at least id + 3 columns
                first_col_name = column_names[1]  # First data column (index 1 because index 0 is 'id')
                third_col_name = column_names[3]  # Third data column (index 3 because index 0 is 'id')
                
                # Get data from first and third columns of current table
                query = f"SELECT {first_col_name}, {third_col_name} FROM {table}"
                cursor.execute(query)
                rows = cursor.fetchall()

                # Prepare batch insert
                insert_data = []
                for row in rows:
                    if row[0] is not None:
                        first_column = standardize_string(row[0])
                        hours = convert_to_integer(row[1])  # Convert hours to integer

                        if hours is not None:  # Only proceed if hours conversion was successful
                            # PRIMARY CHECK: Check if value contains '/'
                            if '/' in first_column:
                                subject_code = process_slash_value(first_column)
                                if subject_code:
                                    if subject_code not in unique_entries:
                                        unique_entries.add(subject_code)
                                        insert_data.append((subject_code, hours))
                            
                            else:
                                # SECONDARY CHECK: Look for matching column name
                                search_value = standardize_string(first_column)
                                matching_columns = [col for col in column_names if standardize_string(col) == search_value]
                                
                                for matching_column in matching_columns:
                                    # Get all unique values from the matching column
                                    cursor.execute(f"SELECT DISTINCT {matching_column} FROM {table} WHERE {matching_column} IS NOT NULL")
                                    matching_values = cursor.fetchall()
                                    
                                    for value in matching_values:
                                        if value[0] and '/' in str(value[0]):
                                            standardized_value = standardize_string(value[0])
                                            subject_code = process_slash_value(standardized_value)
                                            if subject_code:
                                                if subject_code not in unique_entries:
                                                    unique_entries.add(subject_code)
                                                    insert_data.append((subject_code, hours))

                # Batch insert into uniquesubjects table
                if insert_data:
                    insert_query = f"""
                        INSERT INTO {unique_subjects_table} 
                        (SubjectCode, Hours)
                        VALUES (%s, %s)
                    """
                    cursor.executemany(insert_query, insert_data)
                    conn.commit()

        print(f"{unique_subjects_table} table created successfully!")
    except mysql.connector.Error as err:
        print(f"Error creating {unique_subjects_table}: {err}")
        conn.rollback()

    # Close the database connection
    cursor.close()
    conn.close()
    print(f"All data has been processed and stored in MySQL schema '{schema_name}'.")
    return 0

if __name__ == "__main__":
    sys.exit(main())