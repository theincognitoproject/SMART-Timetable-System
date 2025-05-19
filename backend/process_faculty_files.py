import mysql.connector
import pandas as pd
import os
import re
import random
import sys
import traceback
import argparse
from dotenv import load_dotenv

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process faculty files and allocate subjects')
    parser.add_argument('--schema', required=True, help='Schema name to use')
    parser.add_argument('--faculty-list', required=True, help='Path to faculty list Excel file')
    parser.add_argument('--faculty-pref', required=True, help='Path to faculty preferences Excel file')
    args = parser.parse_args()

    schema_name = args.schema
    faculty_list_path = args.faculty_list
    faculty_pref_path = args.faculty_pref

    # Initialize variables to avoid UnboundLocalError
    conn = None
    cursor = None
    
    try:
        # Connect to database
        conn, cursor, schema_name, allsubjects_table = connect_to_database(schema_name)
        
        # Check if connection was successful
        if conn is None or cursor is None:
            print("Failed to connect to database or retrieve necessary information.")
            return 1

        # Create tables from Excel files with fixed names
        print("\nCreating tables from Excel files...")
        
        # Use fixed table names instead of dynamically generated ones
        sortedtable_name = create_fixed_table_from_excel(conn, cursor, faculty_list_path, "SortedTable_SortedTable")
        facultypreferences_name = create_fixed_table_from_excel(conn, cursor, faculty_pref_path, "FacultyPreferences_FacultyPreferences")

        if not sortedtable_name or not facultypreferences_name:
            print("Failed to create required tables")
            return 1

        # Rest of the function remains the same
        # ...

        # Create duplicate of AllSubjects table
        print(f"\nCreating duplicate of {allsubjects_table} table...")
        create_allsubjects_duplicate(cursor, allsubjects_table)

        # Create preference columns
        print("\nCreating preference columns...")
        create_preference_columns(cursor, sortedtable_name)

        # Calculate x
        x = calculate_x(cursor, sortedtable_name)
        print(f"\nCalculated initial x value: {x}")
        
        # Count professors and modify x value
        professor_count = count_professors(cursor, facultypreferences_name)
        print(f"Number of professors found: {professor_count}")
        
        x = x - professor_count
        print(f"Modified x value after subtracting professor count: {x}")

        # Initial subject allocation (SUB_1 and SUB_2)
        print("\nPerforming initial subject allocation...")
        allocate_subjects(cursor, x, sortedtable_name, facultypreferences_name)
        print("Initial subject allocation completed")

        # Create SUB_3 column
        print("\nCreating SUB_3 column...")
        create_sub3_column(cursor, sortedtable_name)

        # Fill empty SUB_2 after x-th row
        print("\nFilling empty SUB_2 slots after x-th row...")
        fill_empty_sub2_after_x(cursor, x, sortedtable_name)
        print("Filled empty SUB_2 slots after x-th row")

        # Check for conflicts after initial allocation
        find_existing_conflicts(cursor, sortedtable_name)

        # Display intermediate allocation status
        print("\nIntermediate Allocation Status:")
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_faculty,
                COUNT(SUB_1) as sub1_allocated,
                COUNT(SUB_2) as sub2_allocated
            FROM {sortedtable_name}
        """)
        interim_summary = cursor.fetchone()
        print(f"""
Interim Status:
-------------
Total Faculty: {interim_summary[0]}
SUB_1 Allocated: {interim_summary[1]}
SUB_2 Allocated: {interim_summary[2]}
        """)

        # Allocate SUB_3, skipping the first y (professor_count) rows
        print(f"\nAllocating SUB_3 for faculty (skipping first {professor_count} rows)...")
        allocate_sub3(cursor, sortedtable_name, facultypreferences_name, professor_count)
        print("SUB_3 allocation completed")

        # Check for faculty without SUB_3 and optimize allocations
        optimize_allocations(cursor, sortedtable_name)

        # Check for conflicts after optimization
        find_existing_conflicts(cursor, sortedtable_name)

        # Display final allocation summary
        print("\nGenerating final allocation summary...")
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_faculty,
                COUNT(SUB_1) as sub1_allocated,
                COUNT(SUB_2) as sub2_allocated,
                COUNT(SUB_3) as sub3_allocated
            FROM {sortedtable_name}
        """)
        summary = cursor.fetchone()
        print(f"""
Final Allocation Summary:
----------------------
Total Faculty: {summary[0]}
SUB_1 Allocated: {summary[1]}
SUB_2 Allocated: {summary[2]}
SUB_3 Allocated: {summary[3]}
        """)

        # Create Sortedtableformatted with primary key
        print("\nCreating formatted table...")
        cursor.execute("DROP TABLE IF EXISTS Sortedtableformatted")
        cursor.execute(f"""
            CREATE TABLE Sortedtableformatted (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Name TEXT,
                Employee_ID TEXT,
                SUB_1 TEXT,
                SUB_1_Year TEXT,
                SUB_1_Class TEXT,
                SUB_2 TEXT,
                SUB_2_Year TEXT,
                SUB_2_Class TEXT,
                SUB_3 TEXT,
                SUB_3_Year TEXT,
                SUB_3_Class TEXT
            ) AS
            SELECT 
                NULL as id,
                Name,
                Employee_ID,
                SUB_1,
                SUBSTRING(
                    SUBSTRING_INDEX(
                        SUBSTRING_INDEX(
                            SUBSTRING_INDEX(SUB_1, '(', -2),  -- Get last two parentheses contents
                            ')', 1),                          -- Get first parenthesis content
                        'year', 1),                          -- Get part before 'year'
                    1, 1                                     -- Take first character
                ) AS SUB_1_Year,
                SUBSTRING_INDEX(SUBSTRING_INDEX(SUB_1, '(', -1), ')', 1) AS SUB_1_Class,
                SUB_2,
                CASE 
                    WHEN SUB_2 IS NOT NULL THEN 
                        SUBSTRING(
                            SUBSTRING_INDEX(
                                SUBSTRING_INDEX(
                                    SUBSTRING_INDEX(SUB_2, '(', -2),
                                    ')', 1),
                                'year', 1),
                            1, 1
                        )
                    ELSE NULL 
                END AS SUB_2_Year,
                CASE 
                    WHEN SUB_2 IS NOT NULL THEN 
                        SUBSTRING_INDEX(SUBSTRING_INDEX(SUB_2, '(', -1), ')', 1)
                    ELSE NULL 
                END AS SUB_2_Class,
                SUB_3,
                CASE 
                    WHEN SUB_3 IS NOT NULL THEN 
                        SUBSTRING(
                            SUBSTRING_INDEX(
                                SUBSTRING_INDEX(
                                    SUBSTRING_INDEX(SUB_3, '(', -2),
                                    ')', 1),
                                'year', 1),
                            1, 1
                        )
                    ELSE NULL 
                END AS SUB_3_Year,
                CASE 
                    WHEN SUB_3 IS NOT NULL THEN 
                        SUBSTRING_INDEX(SUBSTRING_INDEX(SUB_3, '(', -1), ')', 1)
                    ELSE NULL 
                END AS SUB_3_Class
            FROM {sortedtable_name}
        """)
        print("Formatted table created successfully!")

        # Count swapped subjects
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM {sortedtable_name}
            WHERE SUB_3 LIKE '%+'
        """)
        
        swapped_count = cursor.fetchone()[0]
        
        if swapped_count > 0:
            print(f"\nNote: {swapped_count} subjects were swapped during optimization (marked with '+').")
            
            # Show details of swapped subjects
            cursor.execute(f"""
                SELECT Name, Employee_ID, SUB_3
                FROM {sortedtable_name}
                WHERE SUB_3 LIKE '%+'
            """)
            
            swapped_subjects = cursor.fetchall()
            print("\nFaculty with swapped subjects:")
            for name, emp_id, subject in swapped_subjects:
                print(f"  {name} ({emp_id}): {subject}")

        # Commit changes and close connection
        conn.commit()
        print("\nAll operations completed successfully!")
        return 0

    except mysql.connector.Error as err:
        print(f"\nDatabase error occurred: {err}")
        if conn:
            conn.rollback()
        return 1
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        traceback.print_exc()  # Print full traceback for better debugging
        return 1
    finally:
        if conn:
            if cursor:
                cursor.close()
            conn.close()
            print("\nDatabase connection closed.")

def count_professors(cursor, facultypreferences_name):
    """Count the number of professors in the faculty preferences table"""
    try:
        # Check if the Designation column exists
        cursor.execute(f"SHOW COLUMNS FROM {facultypreferences_name} LIKE 'Designation'")
        designation_column = cursor.fetchone()
        
        if not designation_column:
            # Try alternative column names
            cursor.execute(f"DESCRIBE {facultypreferences_name}")
            columns = cursor.fetchall()
            designation_col = None
            
            for col in columns:
                if 'design' in col[0].lower():
                    designation_col = col[0]
                    break
            
            if not designation_col:
                print("Could not find Designation column in faculty preferences table. Assuming 0 professors.")
                return 0
            
            # Count professors using the found column name
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {facultypreferences_name} 
                WHERE {designation_col} LIKE '%Professor%' 
                AND {designation_col} NOT LIKE '%Associate%' 
                AND {designation_col} NOT LIKE '%Assistant%'
            """)
        else:
            # Use the standard Designation column name
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {facultypreferences_name} 
                WHERE Designation LIKE '%Professor%' 
                AND Designation NOT LIKE '%Associate%' 
                AND Designation NOT LIKE '%Assistant%'
            """)
        
        professor_count = cursor.fetchone()[0]
        return professor_count
        
    except mysql.connector.Error as err:
        print(f"Error counting professors: {err}")
        return 0

def connect_to_database(schema_name):
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
        
        # Check if schema exists
        cursor.execute(f"SHOW SCHEMAS LIKE '{schema_name}'")
        if not cursor.fetchone():
            print(f"Schema '{schema_name}' does not exist.")
            cursor.close()
            conn.close()
            return None, None, None, None
        
        # Use the schema
        cursor.execute(f"USE {schema_name}")
        
        # Check if AllSubjects table exists - case insensitive approach
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            print("No tables found in the schema.")
            cursor.close()
            conn.close()
            return None, None, None, None
            
        tables_lower = [table[0].lower() for table in tables]
        all_tables_original = [table[0] for table in tables]
        
        # Try to find AllSubjects table (case insensitive)
        allsubjects_table = None
        
        if 'allsubjects' in tables_lower:
            # Find the original case version
            idx = tables_lower.index('allsubjects')
            allsubjects_table = all_tables_original[idx]
        else:
            # No match found, show available tables
            print(f"Available tables: {', '.join(all_tables_original)}")
            allsubjects_table = "AllSubjects"  # Default name
            
            # Verify the table exists
            cursor.execute(f"SHOW TABLES LIKE '{allsubjects_table}'")
            if not cursor.fetchone():
                print(f"Table '{allsubjects_table}' not found in the schema.")
                cursor.close()
                conn.close()
                return None, None, None, None
        
        print(f"Using AllSubjects table: '{allsubjects_table}'")
        return conn, cursor, schema_name, allsubjects_table
        
    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL server: {err}")
        if 'conn' in locals() and conn:
            if 'cursor' in locals() and cursor:
                cursor.close()
            conn.close()
        return None, None, None, None

def has_same_class_and_section(subject1, subject2):
    """Check if two subjects have the same class and section"""
    if not subject1 or not subject2:
        return False
    
    print(f"Comparing: '{subject1}' and '{subject2}'")
    
    # Extract year using direct string search
    year1 = None
    year2 = None
    for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
        if year_pattern in subject1:
            year1 = year_pattern
        if year_pattern in subject2:
            year2 = year_pattern
    
    # Extract section using direct string search for CSE-X pattern
    section1 = None
    section2 = None
    
    # Look for CSE-X pattern
    cse_match1 = re.search(r'CSE-[A-Z]', subject1)
    if cse_match1:
        section1 = cse_match1.group(0)
    
    cse_match2 = re.search(r'CSE-[A-Z]', subject2)
    if cse_match2:
        section2 = cse_match2.group(0)
    
    print(f"  Subject 1: year={year1}, section={section1}")
    print(f"  Subject 2: year={year2}, section={section2}")
    
    # Check if both year and section match
    if year1 and year2 and section1 and section2:
        if year1 == year2 and section1 == section2:
            print(f"  CONFLICT DETECTED: Same year ({year1}) and section ({section1})")
            return True
    
    print("  No conflict detected")
    return False

def find_existing_conflicts(cursor, sortedtable_name):
    """Find faculty with conflicts between SUB_1, SUB_2, and SUB_3"""
    print("\nChecking for existing conflicts...")
    
    cursor.execute(f"""
        SELECT Name, Employee_ID, SUB_1, SUB_2, SUB_3
        FROM {sortedtable_name}
        WHERE SUB_1 IS NOT NULL OR SUB_2 IS NOT NULL OR SUB_3 IS NOT NULL
    """)
    
    faculties = cursor.fetchall()
    conflicts = []
    
    for faculty in faculties:
        faculty_name, emp_id, sub1, sub2, sub3 = faculty
        
        if sub1 and sub2 and has_same_class_and_section(sub1, sub2):
            conflicts.append({
                'faculty': faculty_name,
                'emp_id': emp_id,
                'conflict_between': 'SUB_1 and SUB_2',
                'sub1': sub1,
                'sub2': sub2
            })
        
        if sub1 and sub3 and has_same_class_and_section(sub1, sub3):
            conflicts.append({
                'faculty': faculty_name,
                'emp_id': emp_id,
                'conflict_between': 'SUB_1 and SUB_3',
                'sub1': sub1,
                'sub3': sub3
            })
        
        if sub2 and sub3 and has_same_class_and_section(sub2, sub3):
            conflicts.append({
                'faculty': faculty_name,
                'emp_id': emp_id,
                'conflict_between': 'SUB_2 and SUB_3',
                'sub2': sub2,
                'sub3': sub3
            })
    
    if conflicts:
        print(f"Found {len(conflicts)} conflicts:")
        for conflict in conflicts:
            print(f"  Faculty: {conflict['faculty']} ({conflict['emp_id']})")
            print(f"  Conflict between: {conflict['conflict_between']}")
            if 'sub1' in conflict:
                print(f"    SUB_1: {conflict['sub1']}")
            if 'sub2' in conflict:
                print(f"    SUB_2: {conflict['sub2']}")
            if 'sub3' in conflict:
                print(f"    SUB_3: {conflict['sub3']}")
            print()
    else:
        print("No conflicts found.")
    
    return conflicts

def create_table_from_excel(conn, cursor, file_path, table_name_prefix):
    if not os.path.exists(file_path):
        print(f"File '{file_path}' not found.")
        return None

    table_name = f"{table_name_prefix}_{os.path.splitext(os.path.basename(file_path))[0]}"
    table_name = re.sub(r'\W+', '_', table_name.strip())

    try:
        df = pd.read_excel(file_path)
        df.columns = [re.sub(r'\W+', '_', str(col).strip()) for col in df.columns]

        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

        # Create table with primary key
        create_table_query = f"CREATE TABLE {table_name} ("
        create_table_query += "id INT AUTO_INCREMENT PRIMARY KEY,"  # Add primary key
        for col in df.columns:
            create_table_query += f"{col} TEXT,"
        create_table_query = create_table_query.rstrip(",") + ")"
        cursor.execute(create_table_query)

        # Insert data
        for _, row in df.iterrows():
            columns = ", ".join(df.columns)
            placeholders = ", ".join(["%s"] * len(df.columns))
            values = tuple(None if pd.isna(val) else str(val) for val in row)
            cursor.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)

        conn.commit()
        print(f"Created and populated table '{table_name}'")
        return table_name
    except Exception as e:
        print(f"Error creating table from Excel: {e}")
        conn.rollback()
        return None
    
def create_fixed_table_from_excel(conn, cursor, file_path, fixed_table_name):
    if not os.path.exists(file_path):
        print(f"File '{file_path}' not found.")
        return None

    try:
        df = pd.read_excel(file_path)
        df.columns = [re.sub(r'\W+', '_', str(col).strip()) for col in df.columns]

        cursor.execute(f"DROP TABLE IF EXISTS {fixed_table_name}")

        # Create table with primary key
        create_table_query = f"CREATE TABLE {fixed_table_name} ("
        create_table_query += "id INT AUTO_INCREMENT PRIMARY KEY,"  # Add primary key
        for col in df.columns:
            create_table_query += f"{col} TEXT,"
        create_table_query = create_table_query.rstrip(",") + ")"
        cursor.execute(create_table_query)

        # Insert data
        for _, row in df.iterrows():
            columns = ", ".join(df.columns)
            placeholders = ", ".join(["%s"] * len(df.columns))
            values = tuple(None if pd.isna(val) else str(val) for val in row)
            cursor.execute(f"INSERT INTO {fixed_table_name} ({columns}) VALUES ({placeholders})", values)

        conn.commit()
        print(f"Created and populated table '{fixed_table_name}'")
        return fixed_table_name
    except Exception as e:
        print(f"Error creating table from Excel: {e}")
        conn.rollback()
        return None

def create_allsubjects_duplicate(cursor, allsubjects_table):
    try:
        cursor.execute("DROP TABLE IF EXISTS allsubjectsduplicate")
        cursor.execute(f"""
            CREATE TABLE allsubjectsduplicate (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sections TEXT,
                subjects TEXT
            ) AS
            SELECT id, sections, subjects FROM {allsubjects_table}
        """)
        print(f"Created {allsubjects_table} duplicate table")
    except mysql.connector.Error as err:
        print(f"Error creating AllSubjects duplicate: {err}")
        raise err

def calculate_x(cursor, sortedtable_name):
    try:
        cursor.execute("SELECT COUNT(*) FROM allsubjectsduplicate")
        total_subjects = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM {sortedtable_name}")
        total_faculties = cursor.fetchone()[0]

        if total_subjects > 2 * total_faculties:
            x = total_faculties - (total_subjects - 2 * total_faculties)
        else:
            x = total_faculties

        return x
    except mysql.connector.Error as err:
        print(f"Error calculating x: {err}")
        raise err

def create_preference_columns(cursor, sortedtable_name):
    try:
        cursor.execute(f"DESCRIBE {sortedtable_name}")
        existing_columns = [column[0] for column in cursor.fetchall()]
        
        if 'SUB_1_PREF' not in existing_columns:
            cursor.execute(f"ALTER TABLE {sortedtable_name} ADD COLUMN SUB_1_PREF TEXT")
        
        if 'SUB_2_PREF' not in existing_columns:
            cursor.execute(f"ALTER TABLE {sortedtable_name} ADD COLUMN SUB_2_PREF TEXT")
        
        if 'SUB_3_PREF' not in existing_columns:
            cursor.execute(f"ALTER TABLE {sortedtable_name} ADD COLUMN SUB_3_PREF TEXT")
            
        print(f"Created preference columns in {sortedtable_name}")
    except mysql.connector.Error as err:
        print(f"Error creating preference columns: {err}")
        raise err

def create_sub3_column(cursor, sortedtable_name):
    try:
        cursor.execute(f"DESCRIBE {sortedtable_name}")
        existing_columns = [column[0] for column in cursor.fetchall()]
        
        if 'SUB_3' not in existing_columns:
            cursor.execute(f"ALTER TABLE {sortedtable_name} ADD COLUMN SUB_3 TEXT")
            print(f"Created SUB_3 column in {sortedtable_name}")
        else:
            print("SUB_3 column already exists")
            
    except mysql.connector.Error as err:
        print(f"Error creating SUB_3 column: {err}")
        raise err
    
def find_alternative_subject(cursor, subject_code, subject_to_avoid):
    """Find subject with same code but different year/section"""
    try:
        print(f"Finding alternative for {subject_code}, avoiding {subject_to_avoid}")
        
        cursor.execute("""
            SELECT subjects 
            FROM allsubjectsduplicate 
            WHERE LEFT(subjects, 9) = %s
            AND subjects != %s
        """, (subject_code[:9], subject_to_avoid))
        
        available_subjects = cursor.fetchall()
        print(f"Found {len(available_subjects)} potential alternatives")
        
        for subject in available_subjects:
            # Check if this subject has the same class and section as the one to avoid
            if not has_same_class_and_section(subject[0], subject_to_avoid):
                print(f"  Valid alternative found: {subject[0]}")
                return subject[0]
            else:
                print(f"  Not a valid alternative: {subject[0]} - same class and section")
        
        print("No valid alternative found")
        return None
    except Exception as e:
        print(f"Error in find_alternative_subject: {e}")
        return None
    
def allocate_subjects(cursor, x, sortedtable_name, facultypreferences_name):
    try:
        cursor.execute(f"SELECT Name, Employee_ID FROM {sortedtable_name}")
        faculties = cursor.fetchall()

        # Define the preference checking order
        pref_order = [
            ('1_1', '1.1'), ('2_1', '2.1'),
            ('1_2', '1.2'), ('2_2', '2.2'),
            ('1_3', '1.3'), ('2_3', '2.3'),
            ('1_4', '1.4'), ('2_4', '2.4'),
            ('1_5', '1.5')
        ]

        for i, (faculty_name, emp_id) in enumerate(faculties):
            if i < x:
                # For rows before x, only assign SUB_1
                subjects_assigned = False
                
                for pref_col, pref_label in pref_order:
                    if subjects_assigned:
                        break
                        
                    cursor.execute(f"""
                        SELECT {pref_col} 
                        FROM {facultypreferences_name} 
                        WHERE Employee_ID = %s
                    """, (emp_id,))
                    pref_result = cursor.fetchone()
                    if not pref_result:
                        continue
                    
                    preferred_subject = pref_result[0]
                    
                    if preferred_subject and preferred_subject.lower() != 'nan':
                        cursor.execute("""
                            SELECT subjects 
                            FROM allsubjectsduplicate 
                            WHERE LEFT(subjects, 9) = LEFT(%s, 9) 
                            LIMIT 1
                        """, (preferred_subject,))
                        
                        available_subject = cursor.fetchone()
                        
                        if available_subject:
                            cursor.execute(f"""
                                UPDATE {sortedtable_name} 
                                SET SUB_1 = %s, SUB_1_PREF = %s
                                WHERE Employee_ID = %s
                            """, (available_subject[0], pref_label, emp_id))
                            
                            cursor.execute("""
                                DELETE FROM allsubjectsduplicate 
                                WHERE subjects = %s 
                                LIMIT 1
                            """, (available_subject[0],))
                            
                            subjects_assigned = True
                            break
                        
            else:
                # For rows after x, try to assign both SUB_1 and SUB_2
                subjects_assigned = False
                
                for pref_col, pref_label in pref_order:
                    if subjects_assigned:
                        break
                        
                    cursor.execute(f"""
                        SELECT {pref_col} 
                        FROM {facultypreferences_name} 
                        WHERE Employee_ID = %s
                    """, (emp_id,))
                    pref_result = cursor.fetchone()
                    if not pref_result:
                        continue
                    
                    preferred_subject = pref_result[0]
                    
                    if preferred_subject and preferred_subject.lower() != 'nan':
                        cursor.execute("""
                            SELECT subjects 
                            FROM allsubjectsduplicate 
                            WHERE LEFT(subjects, 9) = LEFT(%s, 9)
                        """, (preferred_subject,))
                        
                        available_subjects = cursor.fetchall()
                        
                        if len(available_subjects) >= 2:
                            sub1 = available_subjects[0][0]
                                                              
                            # Find a SUB_2 that doesn't have the same class and section as SUB_1
                            sub2 = None
                            for potential_sub2 in available_subjects[1:]:
                                if not has_same_class_and_section(sub1, potential_sub2[0]):
                                    sub2 = potential_sub2[0]
                                    break
                            
                            if sub2:
                                cursor.execute(f"""
                                    UPDATE {sortedtable_name} 
                                    SET SUB_1 = %s, SUB_1_PREF = %s,
                                        SUB_2 = %s, SUB_2_PREF = %s
                                    WHERE Employee_ID = %s
                                """, (sub1, pref_label, sub2, pref_label, emp_id))
                                
                                # Use parameterized queries for each deletion
                                cursor.execute("DELETE FROM allsubjectsduplicate WHERE subjects = %s LIMIT 1", (sub1,))
                                cursor.execute("DELETE FROM allsubjectsduplicate WHERE subjects = %s LIMIT 1", (sub2,))
                                
                                subjects_assigned = True
                                print(f"Assigned SUB_1: {sub1} and SUB_2: {sub2} to {faculty_name}")
                                break
                            else:
                                print(f"Could not find a SUB_2 with different class/section for {faculty_name}")
                
                # If no pair found, try to assign just SUB_1
                if not subjects_assigned:
                    for pref_col, pref_label in pref_order:
                        cursor.execute(f"""
                            SELECT {pref_col} 
                            FROM {facultypreferences_name} 
                            WHERE Employee_ID = %s
                        """, (emp_id,))
                        pref_result = cursor.fetchone()
                        if not pref_result:
                            continue
                        
                        preferred_subject = pref_result[0]
                        
                        if preferred_subject and preferred_subject.lower() != 'nan':
                            cursor.execute("""
                                SELECT subjects 
                                FROM allsubjectsduplicate 
                                WHERE LEFT(subjects, 9) = LEFT(%s, 9) 
                                LIMIT 1
                            """, (preferred_subject,))
                            
                            available_subject = cursor.fetchone()
                            
                            if available_subject:
                                cursor.execute(f"""
                                    UPDATE {sortedtable_name} 
                                    SET SUB_1 = %s, SUB_1_PREF = %s,
                                        SUB_2 = NULL, SUB_2_PREF = NULL
                                    WHERE Employee_ID = %s
                                """, (available_subject[0], pref_label, emp_id))
                                
                                cursor.execute("""
                                    DELETE FROM allsubjectsduplicate 
                                    WHERE subjects = %s 
                                    LIMIT 1
                                """, (available_subject[0],))
                                break
    except mysql.connector.Error as err:
        print(f"Error allocating subjects: {err}")
        raise err

def allocate_sub3(cursor, sortedtable_name, facultypreferences_name, professor_count):
    try:
        print("\nStarting SUB_3 allocation...")
        cursor.execute(f"""
            SELECT Name, Employee_ID, SUB_1, SUB_2, SUB_3
            FROM {sortedtable_name}
            WHERE SUB_3 IS NULL
            LIMIT {professor_count}, 18446744073709551615
        """)
        
        faculties = cursor.fetchall()
        print(f"Found {len(faculties)} faculties needing SUB_3 allocation (skipping first {professor_count} rows)")
        
        # Define the preference checking order
        pref_order = [
            ('1_1', '1.1'), ('2_1', '2.1'),
            ('1_2', '1.2'), ('2_2', '2.2'),
            ('1_3', '1.3'), ('2_3', '2.3'),
            ('1_4', '1.4'), ('2_4', '2.4'),
            ('1_5', '1.5')
        ]
        
        for faculty in faculties:
            faculty_name, emp_id, current_sub1, current_sub2, _ = faculty
            print(f"\nProcessing faculty: {faculty_name} ({emp_id})")
            print(f"  Current SUB_1: {current_sub1}")
            print(f"  Current SUB_2: {current_sub2}")
            
            # Try to allocate SUB_3 based on preferences
            subject_assigned = False
            
            # Check preferences in the specified order
            for pref_col, pref_label in pref_order:
                if subject_assigned:
                    break
                    
                cursor.execute(f"""
                    SELECT {pref_col} 
                    FROM {facultypreferences_name} 
                    WHERE Employee_ID = %s
                """, (emp_id,))
                preferred_subject = cursor.fetchone()
                
                if preferred_subject and preferred_subject[0] and preferred_subject[0].lower() != 'nan':
                    preferred_subject = preferred_subject[0]
                    print(f"Checking preference {pref_label}: {preferred_subject}")
                    
                    # Check if subject exists in allsubjectsduplicate
                    cursor.execute("""
                        SELECT subjects 
                        FROM allsubjectsduplicate 
                        WHERE LEFT(subjects, 9) = LEFT(%s, 9)
                    """, (preferred_subject,))
                    
                    available_subjects = cursor.fetchall()
                    
                    for available_subject in available_subjects:
                        subject = available_subject[0]
                        print(f"  Checking candidate: {subject}")
                        
                        # Check conflicts with SUB_1 and SUB_2
                        has_conflict = False
                        
                        if current_sub1:
                            conflict_with_sub1 = has_same_class_and_section(current_sub1, subject)
                            if conflict_with_sub1:
                                has_conflict = True
                                print(f"  CONFLICT: Candidate has same class and section as SUB_1")
                        
                        if current_sub2 and not has_conflict:
                            conflict_with_sub2 = has_same_class_and_section(current_sub2, subject)
                            if conflict_with_sub2:
                                has_conflict = True
                                print(f"  CONFLICT: Candidate has same class and section as SUB_2")
                        
                        if not has_conflict:
                            # Allocate the subject
                            print(f"  NO CONFLICTS FOUND - Allocating subject")
                            cursor.execute(f"""
                                UPDATE {sortedtable_name} 
                                SET SUB_3 = %s, SUB_3_PREF = %s
                                WHERE Employee_ID = %s
                            """, (subject, pref_label, emp_id))
                            
                            # Remove from allsubjectsduplicate
                            cursor.execute("""
                                DELETE FROM allsubjectsduplicate 
                                WHERE subjects = %s
                                LIMIT 1
                            """, (subject,))
                            
                            subject_assigned = True
                            print(f"Assigned SUB_3: {subject}")
                            break
                    
                    if subject_assigned:
                        break
            
            # If still no subject assigned, try random allocation
            if not subject_assigned:
                print("Attempting random allocation...")
                cursor.execute("""
                    SELECT subjects 
                    FROM allsubjectsduplicate
                    ORDER BY RAND()
                """)
                
                available_subjects = cursor.fetchall()
                
                for available_subject in available_subjects:
                    subject = available_subject[0]
                    print(f"  Checking random candidate: {subject}")
                    
                    # Check conflicts with SUB_1 and SUB_2
                    has_conflict = False
                    
                    if current_sub1:
                        conflict_with_sub1 = has_same_class_and_section(current_sub1, subject)
                        if conflict_with_sub1:
                            has_conflict = True
                            print(f"  CONFLICT: Candidate has same class and section as SUB_1")
                    
                    if current_sub2 and not has_conflict:
                        conflict_with_sub2 = has_same_class_and_section(current_sub2, subject)
                        if conflict_with_sub2:
                            has_conflict = True
                            print(f"  CONFLICT: Candidate has same class and section as SUB_2")
                    
                    if not has_conflict:
                        # Allocate the subject
                        print(f"  NO CONFLICTS FOUND - Allocating subject")
                        cursor.execute(f"""
                            UPDATE {sortedtable_name} 
                            SET SUB_3 = %s, SUB_3_PREF = 'Random'
                            WHERE Employee_ID = %s
                        """, (subject, emp_id))
                        
                        # Remove from allsubjectsduplicate
                        cursor.execute("""
                            DELETE FROM allsubjectsduplicate 
                            WHERE subjects = %s
                            LIMIT 1
                        """, (subject,))
                        
                        subject_assigned = True
                        print(f"Assigned SUB_3 randomly: {subject}")
                        break
            
            if not subject_assigned:
                print(f"Warning: Could not assign SUB_3 for faculty {faculty_name} ({emp_id})")

        # Verification step
        print("\nVerifying SUB_3 allocations for conflicts...")
        cursor.execute(f"""
            SELECT Name, Employee_ID, SUB_1, SUB_2, SUB_3
            FROM {sortedtable_name}
            WHERE SUB_3 IS NOT NULL
        """)

        faculty_with_sub3 = cursor.fetchall()
        conflicts_found = 0

        for faculty in faculty_with_sub3:
            faculty_name, emp_id, sub1, sub2, sub3 = faculty
            
            if sub1 and sub3 and has_same_class_and_section(sub1, sub3):
                print(f"WARNING: Faculty {faculty_name} ({emp_id}) has conflict between SUB_1 and SUB_3:")
                print(f"  SUB_1: {sub1}")
                print(f"  SUB_3: {sub3}")
                conflicts_found += 1
            
            if sub2 and sub3 and has_same_class_and_section(sub2, sub3):
                print(f"WARNING: Faculty {faculty_name} ({emp_id}) has conflict between SUB_2 and SUB_3:")
                print(f"  SUB_2: {sub2}")
                print(f"  SUB_3: {sub3}")
                conflicts_found += 1

        print(f"Verification complete. Found {conflicts_found} conflicts.")

    except mysql.connector.Error as err:
        print(f"Database error in allocate_sub3: {err}")
        raise err
    except Exception as e:
        print(f"Error in allocate_sub3: {e}")
        traceback.print_exc()  # Print full traceback for better debugging
        raise e
    
def fill_empty_sub2_after_x(cursor, x, sortedtable_name):
    try:
        cursor.execute(f"""
            SELECT Name, Employee_ID, SUB_1 
            FROM {sortedtable_name} 
            WHERE SUB_2 IS NULL 
            LIMIT %s, 18446744073709551615
        """, (x,))
        
        faculties_with_empty_sub2 = cursor.fetchall()
        print(f"Found {len(faculties_with_empty_sub2)} faculties needing SUB_2 allocation")
        
        for faculty_name, emp_id, sub1 in faculties_with_empty_sub2:
            print(f"Processing faculty {emp_id}")
            
            if sub1:
                cursor.execute("""
                    SELECT subjects
                    FROM allsubjectsduplicate
                    WHERE LEFT(subjects, 9) = LEFT(%s, 9)
                    AND subjects != %s
                    LIMIT 1
                """, (sub1, sub1))
                
                available_subjects = cursor.fetchall()
                
                # Find a SUB_2 that doesn't have the same class and section as SUB_1
                sub2 = None
                for potential_sub2 in available_subjects:
                    if not has_same_class_and_section(sub1, potential_sub2[0]):
                        sub2 = potential_sub2[0]
                        break
                
                if sub2:
                    print(f"Assigning SUB_2: {sub2} to faculty {emp_id}")
                    
                    cursor.execute(f"""
                        UPDATE {sortedtable_name} 
                        SET SUB_2 = %s, SUB_2_PREF = 'Random'
                        WHERE Employee_ID = %s
                    """, (sub2, emp_id))
                    
                    cursor.execute("""
                        DELETE FROM allsubjectsduplicate 
                        WHERE subjects = %s
                        LIMIT 1
                    """, (sub2,))
                    
                    print(f"Successfully assigned SUB_2 for faculty {emp_id}")
                else:
                    print(f"Could not find a SUB_2 with different class/section for faculty {emp_id}")
    except mysql.connector.Error as err:
        print(f"Error filling empty SUB_2: {err}")
        raise err

def optimize_allocations(cursor, sortedtable_name):
    print("\n=== OPTIMIZING ALLOCATIONS ===")
    
    # Check for faculty without SUB_3
    cursor.execute(f"""
        SELECT Name, Employee_ID, SUB_1, SUB_2
        FROM {sortedtable_name}
        WHERE SUB_3 IS NULL
    """)
    
    unallocated_faculty = cursor.fetchall()
    if not unallocated_faculty:
        print("All faculty have SUB_3 allocated. No optimization needed.")
        return
    
    print(f"Found {len(unallocated_faculty)} faculty without SUB_3. Attempting to optimize allocations.")
    
    # Get remaining subjects
    cursor.execute("SELECT subjects FROM allsubjectsduplicate")
    remaining_subjects = [row[0] for row in cursor.fetchall()]
    
    if not remaining_subjects:
        print("No subjects left in the pool. Cannot optimize further.")
        return
    
    # Get faculty with SUB_3 already allocated
    cursor.execute(f"""
        SELECT Name, Employee_ID, SUB_1, SUB_2, SUB_3, SUB_3_PREF
        FROM {sortedtable_name}
        WHERE SUB_3 IS NOT NULL
    """)
    
    allocated_faculty = cursor.fetchall()
    
    # For each unallocated faculty, try to find a swap
    for unalloc_name, unalloc_id, unalloc_sub1, unalloc_sub2 in unallocated_faculty:
        print(f"\nTrying to find allocation for {unalloc_name} ({unalloc_id})")
        
        # Extract year and section from unallocated faculty's subjects
        unalloc_years = []
        unalloc_sections = []
        
        for subject in [unalloc_sub1, unalloc_sub2]:
            if subject:
                year = None
                for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                    if year_pattern in subject:
                        year = year_pattern
                        unalloc_years.append(year)
                        break
                
                section_match = re.search(r'CSE-[A-Z]', subject)
                if section_match:
                    section = section_match.group(0)
                    unalloc_sections.append(section)
        
        print(f"  Faculty has years: {unalloc_years}, sections: {unalloc_sections}")
        
        # Try each remaining subject directly first
        direct_allocation = False
        for subject in remaining_subjects:
            # Check if subject conflicts with unallocated faculty's subjects
            subject_year = None
            for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                if year_pattern in subject:
                    subject_year = year_pattern
                    break
            
            subject_section = None
            section_match = re.search(r'CSE-[A-Z]', subject)
            if section_match:
                subject_section = section_match.group(0)
            
            # Check for conflicts
            has_conflict = False
            if subject_year in unalloc_years and subject_section in unalloc_sections:
                has_conflict = True
            
            if not has_conflict:
                # We can allocate this subject directly
                cursor.execute(f"""
                    UPDATE {sortedtable_name} 
                    SET SUB_3 = %s, SUB_3_PREF = 'Optimized-Direct'
                    WHERE Employee_ID = %s
                """, (subject, unalloc_id))
                
                # Remove from remaining subjects
                remaining_subjects.remove(subject)
                
                print(f"  Directly allocated: {subject}")
                direct_allocation = True
                break
        
        if direct_allocation:
            continue
        
        # If direct allocation not possible, try swapping with same subject code
        print("  Direct allocation not possible. Trying swaps with same subject code...")
        
        # Group remaining subjects by subject code (first 9 characters)
        subject_codes = {}
        for subject in remaining_subjects:
            code = subject[:9] if len(subject) >= 9 else subject
            if code not in subject_codes:
                subject_codes[code] = []
            subject_codes[code].append(subject)
        
        # For each allocated faculty, check if we can swap
        swap_found = False
        for alloc_name, alloc_id, alloc_sub1, alloc_sub2, alloc_sub3, alloc_sub3_pref in allocated_faculty:
            if swap_found:
                break
                
            # Get the subject code of allocated faculty's SUB_3
            alloc_sub3_code = alloc_sub3[:9] if len(alloc_sub3) >= 9 else alloc_sub3
            
            # Check if we have any remaining subjects with the same code
            if alloc_sub3_code in subject_codes and subject_codes[alloc_sub3_code]:
                # Extract year and section from allocated faculty's SUB_3
                alloc_sub3_year = None
                for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                    if year_pattern in alloc_sub3:
                        alloc_sub3_year = year_pattern
                        break
                
                alloc_sub3_section = None
                section_match = re.search(r'CSE-[A-Z]', alloc_sub3)
                if section_match:
                    alloc_sub3_section = section_match.group(0)
                
                # Check if allocated faculty's SUB_3 conflicts with unallocated faculty's subjects
                has_conflict_with_unalloc = False
                if alloc_sub3_year in unalloc_years and alloc_sub3_section in unalloc_sections:
                    has_conflict_with_unalloc = True
                
                if has_conflict_with_unalloc:
                    continue  # This SUB_3 would conflict with unallocated faculty
                
                # Extract years and sections from allocated faculty's SUB_1 and SUB_2
                alloc_years = []
                alloc_sections = []
                
                for subj in [alloc_sub1, alloc_sub2]:
                    if subj:
                        year = None
                        for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                            if year_pattern in subj:
                                year = year_pattern
                                alloc_years.append(year)
                                break
                        
                        section_match = re.search(r'CSE-[A-Z]', subj)
                        if section_match:
                            section = section_match.group(0)
                            alloc_sections.append(section)
                
                # Try each remaining subject with the same code
                for subject in subject_codes[alloc_sub3_code]:
                    # Extract year and section from the subject
                    subject_year = None
                    for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                        if year_pattern in subject:
                            subject_year = year_pattern
                            break
                    
                    subject_section = None
                    section_match = re.search(r'CSE-[A-Z]', subject)
                    if section_match:
                        subject_section = section_match.group(0)
                    
                    # Check if subject conflicts with allocated faculty's subjects
                    has_conflict_with_alloc = False
                    if subject_year in alloc_years and subject_section in alloc_sections:
                        has_conflict_with_alloc = True
                    
                    if not has_conflict_with_alloc:
                        # We can swap! Add + to the end of both subjects to mark them as swapped
                        swapped_alloc_sub3 = f"{alloc_sub3}+"
                        swapped_subject = f"{subject}+"
                        
                        print(f"  Found swap with same subject code: {alloc_name} gives {alloc_sub3} to {unalloc_name}, gets {subject}")
                        
                        # Update unallocated faculty with allocated faculty's SUB_3
                        cursor.execute(f"""
                            UPDATE {sortedtable_name} 
                            SET SUB_3 = %s, SUB_3_PREF = %s
                            WHERE Employee_ID = %s
                        """, (swapped_alloc_sub3, alloc_sub3_pref, unalloc_id))  # Keep original preference
                        
                        # Update allocated faculty with the new subject
                        cursor.execute(f"""
                            UPDATE {sortedtable_name} 
                            SET SUB_3 = %s, SUB_3_PREF = %s
                            WHERE Employee_ID = %s
                        """, (swapped_subject, alloc_sub3_pref, alloc_id))  # Keep original preference
                        
                        # Remove the subject from remaining subjects
                        remaining_subjects.remove(subject)
                        
                        # Update subject_codes dictionary
                        subject_codes[alloc_sub3_code].remove(subject)
                        
                        swap_found = True
                        direct_allocation = True  # Mark as allocated to break the outer loop
                        break
            
            if swap_found:
                break
        
        # If no swap with same subject code found, try any swap as a fallback
        if not direct_allocation:
            print("  No swap with same subject code found. Trying any possible swap...")
            
            for alloc_name, alloc_id, alloc_sub1, alloc_sub2, alloc_sub3, alloc_sub3_pref in allocated_faculty:
                # Extract year and section from allocated faculty's SUB_3
                alloc_sub3_year = None
                for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                    if year_pattern in alloc_sub3:
                        alloc_sub3_year = year_pattern
                        break
                
                alloc_sub3_section = None
                section_match = re.search(r'CSE-[A-Z]', alloc_sub3)
                if section_match:
                    alloc_sub3_section = section_match.group(0)
                
                # Check if allocated faculty's SUB_3 conflicts with unallocated faculty's subjects
                has_conflict_with_unalloc = False
                if alloc_sub3_year in unalloc_years and alloc_sub3_section in unalloc_sections:
                    has_conflict_with_unalloc = True
                
                if has_conflict_with_unalloc:
                    continue  # This SUB_3 would conflict with unallocated faculty
                
                # Extract years and sections from allocated faculty's SUB_1 and SUB_2
                alloc_years = []
                alloc_sections = []
                
                for subj in [alloc_sub1, alloc_sub2]:
                    if subj:
                        year = None
                        for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                            if year_pattern in subj:
                                year = year_pattern
                                alloc_years.append(year)
                                break
                        
                        section_match = re.search(r'CSE-[A-Z]', subj)
                        if section_match:
                            section = section_match.group(0)
                            alloc_sections.append(section)
                
                # Try each remaining subject
                for subject in remaining_subjects:
                    # Extract year and section from the subject
                    subject_year = None
                    for year_pattern in ["1stYear", "2ndYear", "3rdYear", "4thYear"]:
                        if year_pattern in subject:
                            subject_year = year_pattern
                            break
                    
                    subject_section = None
                    section_match = re.search(r'CSE-[A-Z]', subject)
                    if section_match:
                        subject_section = section_match.group(0)
                    
                    # Check if subject conflicts with allocated faculty's subjects
                    has_conflict_with_alloc = False
                    if subject_year in alloc_years and subject_section in alloc_sections:
                        has_conflict_with_alloc = True
                    
                    if not has_conflict_with_alloc:
                        # We can swap! Add + to the end of both subjects to mark them as swapped
                        swapped_alloc_sub3 = f"{alloc_sub3}+"
                        swapped_subject = f"{subject}+"
                        
                        print(f"  Found general swap: {alloc_name} gives {alloc_sub3} to {unalloc_name}, gets {subject}")
                        
                        # Update unallocated faculty with allocated faculty's SUB_3
                        cursor.execute(f"""
                            UPDATE {sortedtable_name} 
                            SET SUB_3 = %s, SUB_3_PREF = 'Optimized-Swap'
                            WHERE Employee_ID = %s
                        """, (swapped_alloc_sub3, unalloc_id))
                        
                        # Update allocated faculty with the new subject
                        cursor.execute(f"""
                            UPDATE {sortedtable_name} 
                            SET SUB_3 = %s, SUB_3_PREF = 'Optimized-Swap'
                            WHERE Employee_ID = %s
                        """, (swapped_subject, alloc_id))
                        
                        # Remove the subject from remaining subjects
                        remaining_subjects.remove(subject)
                        
                        swap_found = True
                        direct_allocation = True  # Mark as allocated to break the outer loop
                        break
                
                if swap_found:
                    break
        
        if not direct_allocation:
            print(f"  Could not find allocation for {unalloc_name} after trying all swaps")
    
    # Check if we still have unallocated faculty
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM {sortedtable_name}
        WHERE SUB_3 IS NULL
    """)
    
    remaining_unallocated = cursor.fetchone()[0]
    if remaining_unallocated > 0:
        print(f"\nAfter optimization, still have {remaining_unallocated} faculty without SUB_3.")
        print("Consider using fallback allocation for these faculty.")
    else:
        print("\nOptimization successful! All faculty now have SUB_3 allocated.")
    
    # Count how many subjects were swapped (have + at the end)
    cursor.execute(f"""
        SELECT COUNT(*) 
        FROM {sortedtable_name}
        WHERE SUB_3 LIKE '%+'
    """)
    
    swapped_count = cursor.fetchone()[0]
    print(f"Total subjects swapped during optimization: {swapped_count}")

if __name__ == "__main__":
    print("Starting subject allocation process...")
    print("=====================================")
    sys.exit(main())