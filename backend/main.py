from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import mysql.connector
from mysql.connector import Error as MySQLError
import os
import re
import traceback    
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import subprocess
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging():
    logger = logging.getLogger('timetable_api')
    logger.setLevel(logging.INFO)
    
    # File handler with log rotation
    file_handler = RotatingFileHandler(
        'timetable_api.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

# Predefined Slots and Days
PREDEFINED_SLOTS = [
    "8:00-8:50", "8:50-9:40", 
    "BREAK",
    "9:50-10:40", "10:40-11:30", 
    "LUNCH",
    "12:20-1:10", "1:10-2:00", "2:00-2:50", "2:50-3:40"
]

PREDEFINED_DAYS = [
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
]

# Create FastAPI app
app = FastAPI(
    title="Timetable and Allocator API",
    description="Comprehensive API for timetable management and department allocation",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React default
        "http://127.0.0.1:3000",
        "*"  # Be cautious with this in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def get_db_connection():
    """
    Establish database connection
    """
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT'))
        )
        return conn
    except MySQLError as err:
        logger.error(f"Database connection error: {err}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database connection error: {str(err)}"
        )

def find_latest_timetable_schema(cursor):
    """
    Find the most recent timetable schema
    """
    try:
        # Directly show databases
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        logger.info(f"Available databases: {databases}")

        # Find databases starting with 'timetable_'
        timetable_schemas = [
            db['Database'] for db in databases if str(db['Database']).startswith('timetable_')
        ]

        if not timetable_schemas:
            raise HTTPException(
                status_code=404, 
                detail="No timetable schema found"
            )

        # Sort and get the most recent schema
        latest_schema = sorted(timetable_schemas, reverse=True)[0]
        logger.info(f"Selected schema: {latest_schema}")

        return latest_schema
    
    except Exception as e:
        logger.error(f"Error finding timetable schema: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error finding timetable schema: {str(e)}"
        )

def rearrange_timetable_data(timetable_data):
    """
    Rearrange timetable data to match predefined slots and days
    """
    try:
        # Create a new ordered timetable
        ordered_timetable = {}
        
        for day in PREDEFINED_DAYS:
            ordered_timetable[day] = {}
            
            for slot in PREDEFINED_SLOTS:
                # If slot is a break or lunch, keep it as is
                if slot in ["BREAK", "LUNCH"]:
                    ordered_timetable[day][slot] = slot
                    continue
                
                # Try to find the corresponding slot in the original data
                original_slot_data = timetable_data.get(day, {}).get(slot)
                ordered_timetable[day][slot] = original_slot_data or None

        return ordered_timetable
    except Exception as e:
        logger.error(f"Error rearranging timetable data: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing timetable data: {str(e)}"
        )

def safe_json_parse(json_data):
    """
    Safely parse JSON data
    """
    try:
        if not json_data:
            return {}
        
        if isinstance(json_data, str):
            return json.loads(json_data)
        
        return json_data
    except json.JSONDecodeError:
        logger.error(f"JSON decoding error for data: {json_data}")
        return {}

@app.get("/api/timetables/classes")
def get_class_timetables():
    """
    Retrieve class timetables
    """
    conn = None
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find the latest schema
        latest_schema = find_latest_timetable_schema(cursor)
        
        # Switch to the specific database
        conn.database = latest_schema
        cursor = conn.cursor(dictionary=True)
        
        # Fetch class timetables
        cursor.execute("""
            SELECT 
                year, 
                section, 
                timetable_data, 
                free_hours, 
                generated_at
            FROM class_timetables
            ORDER BY year, section
        """)
        
        class_timetables = cursor.fetchall()
        
        # Transform results
        formatted_timetables = [
            {
                "year": row['year'],
                "section": row['section'],
                "timetable": rearrange_timetable_data(safe_json_parse(row['timetable_data'])),
                "free_hours": safe_json_parse(row['free_hours']),
                "generated_at": str(row['generated_at']) if row['generated_at'] else None
            }
            for row in class_timetables
        ]
        
        return formatted_timetables
    
    except Exception as e:
        logger.error(f"Error retrieving class timetables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()

@app.get("/api/timetables/teachers")
def get_teacher_timetables():
    """
    Retrieve teacher timetables
    """
    conn = None
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find the latest schema
        latest_schema = find_latest_timetable_schema(cursor)
        
        # Switch to the specific database
        conn.database = latest_schema
        cursor = conn.cursor(dictionary=True)
        
        # Fetch teacher timetables
        cursor.execute("""
            SELECT 
                employee_id, 
                teacher_name, 
                timetable_data, 
                free_hours, 
                generated_at
            FROM teacher_timetables
            ORDER BY teacher_name
        """)
        
        teacher_timetables = cursor.fetchall()
        
        # Transform results
        formatted_timetables = [
            {
                "employee_id": row['employee_id'],
                "teacher_name": row['teacher_name'],
                "timetable": rearrange_timetable_data(safe_json_parse(row['timetable_data'])),
                "free_hours": safe_json_parse(row['free_hours']),
                "generated_at": str(row['generated_at']) if row['generated_at'] else None
            }
            for row in teacher_timetables
        ]
        
        return formatted_timetables
    
    except Exception as e:
        logger.error(f"Error retrieving teacher timetables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()

@app.get("/api/timetables/venues")
def get_venue_timetables():
    """
    Retrieve venue timetables
    """
    conn = None
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find the latest schema
        latest_schema = find_latest_timetable_schema(cursor)
        
        # Switch to the specific database
        conn.database = latest_schema
        cursor = conn.cursor(dictionary=True)
        
        # Fetch venue timetables
        cursor.execute("""
            SELECT 
                venue_id, 
                venue_name, 
                timetable_data, 
                free_hours, 
                generated_at
            FROM venue_timetables
            ORDER BY venue_name
        """)
        
        venue_timetables = cursor.fetchall()
        
        # Transform results
        formatted_timetables = [
            {
                "venue_id": row['venue_id'],
                "venue_name": row['venue_name'],
                "timetable": rearrange_timetable_data(safe_json_parse(row['timetable_data'])),
                "free_hours": safe_json_parse(row['free_hours']),
                "generated_at": str(row['generated_at']) if row['generated_at'] else None
            }
            for row in venue_timetables
        ]
        
        return formatted_timetables
    
    except Exception as e:
        logger.error(f"Error retrieving venue timetables: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()
@app.get("/api/schemas")
async def get_schemas():
    """
    Retrieve all available database schemas
    """
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query to get all schemas
        cursor.execute('SHOW DATABASES')
        databases = cursor.fetchall()
        
        # Log available databases
        logger.info(f"Available databases: {databases}")
        
        # Filter out system schemas
        system_schemas = [
            'defaultdb', 'information_schema', 
            'mysql', 'performance_schema', 'sys'
        ]
        
        # Filter schemas, excluding system schemas and those with 'timetable' prefix
        filtered_schemas = [
            db['Database'] for db in databases 
            if db['Database'].lower() not in system_schemas 
            and not db['Database'].lower().startswith('timetable')
        ]
        
        # Close cursor and connection
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "schemas": filtered_schemas
        }
    
    except mysql.connector.Error as err:
        logger.error(f"Database error: {err}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database connection error: {str(err)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )

@app.post("/api/process-year-files")
async def process_year_files(
    department_name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Process year files for a specific department
    """
    try:
        # Ensure uploads directory exists
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filenames and save files
        file_paths = []
        for file in files:
            # Generate unique filename
            import uuid
            unique_filename = f"{uuid.uuid4()}_{file.filename}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            file_paths.append(file_path)
        
        # Run Python script
        process = subprocess.Popen([
            'python', 
            'process_year_files.py',
            '--schema', department_name,
            '--files', *file_paths
        ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        # Capture output
        stdout, stderr = process.communicate()
        
        # Clean up files
        for file_path in file_paths:
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")
        
        # Check process result
        if process.returncode == 0:
            return {
                "success": True,
                "message": "Year files processed successfully",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr
                }
            }
        else:
            return {
                "success": False,
                "error": "Python script execution failed",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr
                },
                "exit_code": process.returncode
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Server error: {str(e)}"
        )
@app.post("/api/process-faculty-files")
async def process_faculty_files(
    department_name: str = Form(...),
    faculty_list: UploadFile = File(...),
    faculty_preferences: UploadFile = File(...)
):
    """
    Process faculty files for a specific department
    """
    try:
        # Create uploads directory
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Use original filenames (sanitized)
        faculty_list_filename = re.sub(r'\W+', '_', faculty_list.filename)
        faculty_pref_filename = re.sub(r'\W+', '_', faculty_preferences.filename)
        
        # Full paths for saving files
        faculty_list_path = os.path.join(upload_dir, faculty_list_filename)
        faculty_pref_path = os.path.join(upload_dir, faculty_pref_filename)
        
        # Logging file details
        logger.info(f"Saving faculty list file: {faculty_list_path}")
        logger.info(f"Saving faculty preferences file: {faculty_pref_path}")
        
        # Save faculty list file
        with open(faculty_list_path, "wb") as buffer:
            content = await faculty_list.read()
            buffer.write(content)
            logger.info(f"Faculty list file saved. Size: {len(content)} bytes")
        
        # Save faculty preferences file
        with open(faculty_pref_path, "wb") as buffer:
            content = await faculty_preferences.read()
            buffer.write(content)
            logger.info(f"Faculty preferences file saved. Size: {len(content)} bytes")
        
        # Run Python script
        process = subprocess.Popen([
            'python', 
            'process_faculty_files.py',
            '--schema', department_name,
            '--faculty-list', faculty_list_path,
            '--faculty-pref', faculty_pref_path
        ], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        # Capture output with timeout
        try:
            stdout, stderr = process.communicate(timeout=600)  # 10-minute timeout
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            logger.error("Faculty files processing timed out")
            return {
                "success": False,
                "error": "Processing timed out",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr
                }
            }
        
        # Log raw outputs for debugging
        logger.info(f"STDOUT: {stdout}")
        logger.error(f"STDERR: {stderr}")
        
        # Clean up files
        try:
            os.unlink(faculty_list_path)
            os.unlink(faculty_pref_path)
        except Exception as cleanup_err:
            logger.error(f"Error during file cleanup: {cleanup_err}")
        
        # Check process result
        if process.returncode == 0:
            return {
                "success": True,
                "message": "Faculty files processed successfully",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr
                }
            }
        else:
            return {
                "success": False,
                "error": "Python script execution failed",
                "details": {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": process.returncode
                }
            }
    
    except Exception as e:
        # Comprehensive error logging
        logger.error(f"Server error during faculty files processing: {e}")
        logger.error(traceback.format_exc())
        
        # Clean up files in case of error
        try:
            if 'faculty_list_path' in locals():
                os.unlink(faculty_list_path)
            if 'faculty_pref_path' in locals():
                os.unlink(faculty_pref_path)
        except Exception as cleanup_err:
            logger.error(f"Error during error cleanup: {cleanup_err}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Server error: {str(e)}"
        )
# Health Check Endpoint
@app.get("/health")
def health_check():
    """
    Simple health check endpoint
    """
    try:
        # Attempt database connection
        conn = get_db_connection()
        
        # Find the latest schema
        cursor = conn.cursor()
        cursor.execute('SHOW DATABASES')
        databases = cursor.fetchall()
        
        conn.close()
        return {
            "status": "healthy", 
            "database": "connected",
            "current_time": datetime.now().isoformat(),
            "predefined_slots": PREDEFINED_SLOTS,
            "predefined_days": PREDEFINED_DAYS,
            "available_schemas": [
                db[0] for db in databases 
                if not str(db[0]).lower().startswith(('information_schema', 'mysql', 'performance_schema', 'sys'))
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e)
        }

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions
    """
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error"
    )

# Startup Event Handler
@app.on_event("startup")
async def startup_event():
    """
    Perform setup tasks when the server starts
    """
    logger.info("Starting Timetable Allocation API")
    logger.info(f"Predefined Slots: {PREDEFINED_SLOTS}")
    logger.info(f"Predefined Days: {PREDEFINED_DAYS}")

    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)

# Shutdown Event Handler
@app.on_event("shutdown")
async def shutdown_event():
    """
    Perform cleanup tasks when the server shuts down
    """
    logger.info("Shutting down Timetable Allocation API")
    
    # Clean up uploads directory
    uploads_dir = "uploads"
    try:
        for filename in os.listdir(uploads_dir):
            file_path = os.path.join(uploads_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.error(f"Error cleaning up {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {e}")

@app.get("/api/schema/{schema_name}/sortedtable")
async def get_sorted_table(
    schema_name: str,
    limit: Optional[int] = Query(default=100, ge=1, le=1000),
    offset: Optional[int] = Query(default=0, ge=0),
    sort_by: Optional[str] = Query(default=None),
    order: Optional[str] = Query(default='ASC', regex='^(ASC|DESC)$')
):
    """
    Retrieve SortedTable data dynamically
    """
    conn = None
    try:
        # Establish database connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query to get all schemas
        cursor.execute('SHOW DATABASES')
        databases = cursor.fetchall()
        
        # Convert to list of database names
        available_schemas = [
            db['Database'] for db in databases 
            if db['Database'].lower() not in ['information_schema', 'mysql', 'performance_schema', 'sys', 'defaultdb']
        ]
        
        # Check if schema exists (case-insensitive)
        matching_schemas = [
            schema for schema in available_schemas 
            if schema.lower() == schema_name.lower()
        ]
        
        if not matching_schemas:
            raise HTTPException(
                status_code=404, 
                detail=f"Schema '{schema_name}' not found. Available schemas: {available_schemas}",
                headers={"X-Available-Schemas": json.dumps(available_schemas)}
            )
        
        # Use the matched schema (preserving original case)
        actual_schema = matching_schemas[0]
        
        # Switch to the specific database
        conn.database = actual_schema
        cursor = conn.cursor(dictionary=True)
        
        # Check if table exists
        cursor.execute('SHOW TABLES')
        tables = [table['Tables_in_' + actual_schema] for table in cursor.fetchall()]
        
        # Check for possible table variations
        possible_table_names = [
            'SortedTable_SortedTable_xlsx',
            'SortedTable_SortedTable', 
            'sorted_table', 
            'sorted_tables', 
            'sortedtable'
        ]
        
        matching_tables = [
            table for table in tables 
            for possible_name in possible_table_names 
            if table.lower() == possible_name.lower()
        ]
        
        if not matching_tables:
            raise HTTPException(
                status_code=404, 
                detail=f"No sorted table found in schema '{actual_schema}'. Available tables: {tables}",
                headers={"X-Available-Tables": json.dumps(tables)}
            )
        
        # Use the first matching table
        table_name = matching_tables[0]
        
        # Get table columns
        cursor.execute(f'DESCRIBE `{table_name}`')
        columns = cursor.fetchall()
        
        # Determine sort column
        sort_column = sort_by or columns[0]['Field']
        
        # Validate sort column exists
        if not any(col['Field'].lower() == sort_column.lower() for col in columns):
            sort_column = columns[0]['Field']
        
        # Count total rows
        cursor.execute(f'SELECT COUNT(*) as total FROM `{table_name}`')
        total_rows = cursor.fetchone()['total']
        
        # Construct dynamic query
        query = f"""
        SELECT * FROM `{table_name}`
        ORDER BY `{sort_column}` {order}
        LIMIT %s OFFSET %s
        """
        
        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "database": actual_schema,
            "tableName": table_name,
            "columns": [
                {
                    "name": col['Field'],
                    "type": col['Type'],
                    "nullable": col['Null'] == 'YES',
                    "key": col['Key']
                } for col in columns
            ],
            "pagination": {
                "total": total_rows,
                "limit": limit,
                "offset": offset,
                "hasMore": offset + len(rows) < total_rows
            },
            "data": rows
        }
    
    except HTTPException as he:
        raise he
    
    except Exception as e:
        logger.error(f"Error retrieving SortedTable: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database error: {str(e)}"
        )
    
    finally:
        if conn:
            conn.close()

# Run the server (if script is run directly)
if __name__ == "__main__":
    import uvicorn
    
    # Configure logging for uvicorn
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("server.log"),
            logging.StreamHandler()
        ]
    )
    
    # Run the server
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )