import psycopg2
from psycopg2 import sql
import random

# Data
classes = ['Class 1', 'Class 2', 'Class 3', 'Class 4', 'Class 5',
           'Class 6', 'Class 7', 'Class 8', 'Class 9', 'Class 10']  # List of 10 classes
courses = ['Math', 'Physics', 'Chemistry', 'Biology', 'History', 'English', 'Geography', 'Computer Science', 'Art', 'Physical Education']  # List of courses
teachers = ['T1', 'T2', 'T3', 'T4', 'T5']  # List of teachers
time_slots = [
    '8:00-8:50', '8:50-9:40', '9:40-9:50',  # Morning sessions with short break
    '9:50-10:40', '10:40-11:30', '11:30-12:20',  # Before and during lunch
    '12:20-1:10', '1:10-2:00', '2:00-2:50', '2:50-3:40'  # Afternoon sessions
]
days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']  # Days of the week

# Timetable dictionary to store the schedule
timetable = {day: {class_name: {slot: None for slot in time_slots} for class_name in classes} for day in days}

# Break times
short_break = '9:40-9:50'
lunch_break = '11:30-12:20'

def main():
    conn = psycopg2.connect(config.DATABASE_URL)
    cursor = conn.cursor()

    # Loop through each day and each class
    for day in days:
        random.shuffle(courses)  # Shuffle courses at the start of each day
        course_index = 0
        teacher_index = 0

        for class_name in classes:
            for slot in time_slots:
                if slot == short_break:
                    timetable[day][class_name][slot] = "Short Break"
                elif slot == lunch_break:
                    timetable[day][class_name][slot] = "Lunch Break"
                else:
                    # Assign courses and rotate through teachers
                    timetable[day][class_name][slot] = {
                        'Course': courses[course_index % len(courses)],
                        'Teacher': teachers[teacher_index % len(teachers)]
                    }
                    course_index += 1
                    teacher_index += 1

            # Create table for the class if it doesn't exist
            cursor.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    id SERIAL PRIMARY KEY,
                    day VARCHAR(20),
                    "8:00-8:50" VARCHAR(50),
                    "8:50-9:40" VARCHAR(50),
                    "9:40-9:50" VARCHAR(50),
                    "9:50-10:40" VARCHAR(50),
                    "10:40-11:30" VARCHAR(50),
                    "11:30-12:20" VARCHAR(50),
                    "12:20-1:10" VARCHAR(50),
                    "1:10-2:00" VARCHAR(50),
                    "2:00-2:50" VARCHAR(50),
                    "2:50-3:40" VARCHAR(50)
                );
            """).format(sql.Identifier(class_name.replace(' ', '_').lower())))

            # Insert timetable data into the database
            row_data = [day]
            for slot in time_slots:
                details = timetable[day][class_name][slot]
                if isinstance(details, str):  # Breaks
                    row_data.append(details)
                else:  # Classes
                    row_data.append(f"{details['Course']} ({details['Teacher']})")

            cursor.execute(
                sql.SQL("""
                    INSERT INTO {} (day, "8:00-8:50", "8:50-9:40", "9:40-9:50", "9:50-10:40", "10:40-11:30", "11:30-12:20", "12:20-1:10", "1:10-2:00", "2:00-2:50", "2:50-3:40")
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """).format(
                    sql.Identifier(class_name.replace(' ', '_').lower())
                ),
                row_data
            )

    # Commit the transaction and close the connection
    conn.commit()
    cursor.close()
    conn.close()

    print("Timetable stored in the database.")

if __name__ == "__main__":
    main()
