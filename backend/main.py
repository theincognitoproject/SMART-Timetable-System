from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector
from mysql.connector import Error as MySQLError
import os
import json
import logging
from typing import List, Dict, Any
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Configure logging with file rotation
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

# Create FastAPI app
app = FastAPI(
    title="Timetable Scheduler API",
    description="API for retrieving timetable information",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Databases: {databases}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error finding timetable schema: {str(e)}"
        )

# Modify the database connection method to use dictionary cursor
def get_db_connection():
    """
    Establish database connection using DATABASE_URI
    """
    try:
        # Retrieve connection parameters from environment variables
        conn_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'database': os.getenv('DB_NAME'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'charset': 'utf8mb4',
            'connection_timeout': 10,
            'use_pure': True  # Use pure Python implementation
        }
        
        # Establish connection
        conn = mysql.connector.connect(**conn_params)
        
        logger.info("Database connection established successfully")
        
        return conn
    
    except MySQLError as err:
        logger.error(f"Database connection error: {err}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database connection error: {str(err)}"
        )

# Modify the endpoints to use more robust error handling
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
        logger.error(f"Error type: {type(e)}")
        
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()

# Similar modifications for teachers and venues endpoints
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
        logger.error(f"Error type: {type(e)}")
        
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
        logger.error(f"Error type: {type(e)}")
        
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if conn:
            conn.close()
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
        latest_schema = find_latest_timetable_schema(cursor)
        
        conn.close()
        return {
            "status": "healthy", 
            "database": "connected",
            "latest_schema": latest_schema,
            "predefined_slots": PREDEFINED_SLOTS,
            "predefined_days": PREDEFINED_DAYS
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e)
        }

# Run the server (if script is run directly)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )