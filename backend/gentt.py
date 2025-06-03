import os
import json
import random
import sqlalchemy
from sqlalchemy import create_engine, text
from datetime import datetime
import pandas as pd
from typing import Dict, List
from collections import defaultdict
from flask import Flask, request, jsonify
import traceback
from flask_cors import CORS
import logging


class GlobalTimeTableGenerator:
    def __init__(self, section_config=None):
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        self.slots = [
            "8:00-8:50", "8:50-9:40", 
            "BREAK",
            "9:50-10:40", "10:40-11:30", 
            "LUNCH",
            "12:20-1:10", "1:10-2:00", "2:00-2:50", "2:50-3:40"
        ]
        self.morning_slots = ["8:00-8:50", "8:50-9:40", "9:50-10:40", "10:40-11:30"]
        self.afternoon_slots = ["12:20-1:10", "1:10-2:00", "2:00-2:50", "2:50-3:40"]
        self.all_teaching_slots = self.morning_slots + self.afternoon_slots
        
        self.all_timetables = {}
        self.global_teacher_schedule = defaultdict(lambda: defaultdict(set))
        self.global_venue_schedule = defaultdict(lambda: defaultdict(set))

        # Use provided section config or default
        default_sections = {
            1: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],
            2: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'],
            3: ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
        }
        
        logger.info(f"Initializing with section configuration: {section_config}")
        self.sections = section_config if section_config else default_sections
        logger.info(f"Using sections: {self.sections}")

    def initialize_empty_timetables(self):
        for year in self.sections:
            for section in self.sections[year]:
                timetable = {}
                for day in self.days:
                    timetable[day] = {}
                    for slot in self.slots:
                        if slot == "BREAK" or slot == "LUNCH":
                            timetable[day][slot] = slot
                        else:
                            timetable[day][slot] = "FREE"
                self.all_timetables[(year, section)] = timetable

    def is_teacher_globally_available(self, teacher: str, day: str, slot: str) -> bool:
        return slot not in self.global_teacher_schedule[teacher][day]

    def update_global_teacher_schedule(self, teacher: str, day: str, slot: str):
        self.global_teacher_schedule[teacher][day].add(slot)

    def is_venue_available(self, venue: str, day: str, slots: List[str]) -> bool:
        is_available = not any(slot in self.global_venue_schedule[venue][day] for slot in slots)
        current_bookings = self.global_venue_schedule[venue][day]
        print(f"Checking venue {venue} for {day} {slots}")
        print(f"Current bookings: {current_bookings}")
        print(f"Available: {is_available}")
        return is_available

    def update_venue_schedule(self, venue: str, day: str, slots: List[str]):
        for slot in slots:
            self.global_venue_schedule[venue][day].add(slot)

    def check_global_constraints(self, year: int, section: str, subject: Dict, 
                               day: str, slot: str) -> bool:
        # Check if slot is already occupied
        if self.all_timetables[(year, section)][day][slot] != "FREE":
            return False

        # Check if subject already exists in that day
        for existing_slot in self.all_teaching_slots:
            existing_class = self.all_timetables[(year, section)][day][existing_slot]
            if isinstance(existing_class, dict) and existing_class['code'] == subject['code']:
                return False

        # Enhanced teacher gap constraint check
        teacher = subject['teacher']
        slot_index = self.all_teaching_slots.index(slot) if slot in self.all_teaching_slots else -1
        
        if slot_index != -1:
            # Check previous slot (if exists)
            if slot_index > 0:
                prev_slot = self.all_teaching_slots[slot_index - 1]
                if prev_slot in self.global_teacher_schedule[teacher][day]:
                    return False
            
            # Check next slot (if exists)
            if slot_index < len(self.all_teaching_slots) - 1:
                next_slot = self.all_teaching_slots[slot_index + 1]
                if next_slot in self.global_teacher_schedule[teacher][day]:
                    return False

        return True

    def check_consecutive_slots_available(self, teacher: str, day: str, slot1: str, slot2: str) -> bool:
        slot1_index = self.all_teaching_slots.index(slot1)
        
        # Check slot before first slot (if exists)
        if slot1_index > 0:
            prev_slot = self.all_teaching_slots[slot1_index - 1]
            if prev_slot in self.global_teacher_schedule[teacher][day]:
                return False
        
        # Check slot after second slot (if exists)
        slot2_index = self.all_teaching_slots.index(slot2)
        if slot2_index < len(self.all_teaching_slots) - 1:
            next_slot = self.all_teaching_slots[slot2_index + 1]
            if next_slot in self.global_teacher_schedule[teacher][day]:
                return False
        
        return True

    # Include methods for scheduling JP and theory subjects
    def schedule_jp_subject(self, year: int, section: str, subject: Dict, venues: Dict) -> bool:
        print(f"\nAttempting to schedule {subject['code']}")
        print(f"Subject details: {subject}")
        print(f"Available venues: {venues}")
        
        # Check if it's actually a practical subject
        if not (subject['type'] in ['P', 'J'] or subject.get('needs_lab', False)):
            print(f"WARNING: Non-practical subject {subject['code']} in schedule_jp_subject")
            return self.schedule_theory_subject(year, section, subject)

        consecutive_scheduled = False
        available_days = self.days.copy()
        random.shuffle(available_days)

        morning_pairs = [
            ("8:00-8:50", "8:50-9:40"),
            ("9:50-10:40", "10:40-11:30")
        ]
        early_afternoon_pair = [("12:20-1:10", "1:10-2:00")]
        late_afternoon_pair = [("2:00-2:50", "2:50-3:40")]

        # First try morning slots on all days
        for day in available_days.copy():  # Use copy so we can modify the original safely
            for slot1, slot2 in morning_pairs:
                if (self.check_global_constraints(year, section, subject, day, slot1) and 
                    self.check_global_constraints(year, section, subject, day, slot2) and
                    self.check_consecutive_slots_available(subject['teacher'], day, slot1, slot2)):
                    
                    available_venue = None
                    for venue_no in venues.keys():
                        if self.is_venue_available(venue_no, day, [slot1, slot2]):
                            available_venue = venue_no
                            break
                    
                    if available_venue:
                        for slot in [slot1, slot2]:
                            self.all_timetables[(year, section)][day][slot] = {
                                'code': subject['code'],
                                'teacher': subject['teacher'],
                                'type': subject['type'],
                                'venue': f"{available_venue} - {venues[available_venue]}"
                            }
                            self.update_global_teacher_schedule(subject['teacher'], day, slot)
                        self.update_venue_schedule(available_venue, day, [slot1, slot2])
                        consecutive_scheduled = True
                        available_days.remove(day)
                        break
            
            if consecutive_scheduled:
                break

        # If morning scheduling failed, try early afternoon slots
        if not consecutive_scheduled:
            # Reshuffle days for the next attempt
            random.shuffle(available_days)
            
            for day in available_days.copy():
                for slot1, slot2 in early_afternoon_pair:
                    if (self.check_global_constraints(year, section, subject, day, slot1) and 
                        self.check_global_constraints(year, section, subject, day, slot2) and
                        self.check_consecutive_slots_available(subject['teacher'], day, slot1, slot2)):
                        
                        available_venue = None
                        for venue_no in venues.keys():
                            if self.is_venue_available(venue_no, day, [slot1, slot2]):
                                available_venue = venue_no
                                break
                        
                        if available_venue:
                            for slot in [slot1, slot2]:
                                self.all_timetables[(year, section)][day][slot] = {
                                    'code': subject['code'],
                                    'teacher': subject['teacher'],
                                    'type': subject['type'],
                                    'venue': f"{available_venue} - {venues[available_venue]}"
                                }
                                self.update_global_teacher_schedule(subject['teacher'], day, slot)
                            self.update_venue_schedule(available_venue, day, [slot1, slot2])
                            consecutive_scheduled = True
                            available_days.remove(day)
                            break
                
                if consecutive_scheduled:
                    break
        
        # Only try late afternoon as a last resort
        if not consecutive_scheduled:
            # Reshuffle days for the final attempt
            random.shuffle(available_days)
            
            for day in available_days.copy():
                for slot1, slot2 in late_afternoon_pair:
                    if (self.check_global_constraints(year, section, subject, day, slot1) and 
                        self.check_global_constraints(year, section, subject, day, slot2) and
                        self.check_consecutive_slots_available(subject['teacher'], day, slot1, slot2)):
                        
                        available_venue = None
                        for venue_no in venues.keys():
                            if self.is_venue_available(venue_no, day, [slot1, slot2]):
                                available_venue = venue_no
                                break
                        
                        if available_venue:
                            for slot in [slot1, slot2]:
                                self.all_timetables[(year, section)][day][slot] = {
                                    'code': subject['code'],
                                    'teacher': subject['teacher'],
                                    'type': subject['type'],
                                    'venue': f"{available_venue} - {venues[available_venue]}"
                                }
                                self.update_global_teacher_schedule(subject['teacher'], day, slot)
                            self.update_venue_schedule(available_venue, day, [slot1, slot2])
                            consecutive_scheduled = True
                            available_days.remove(day)
                            break
                    
                if consecutive_scheduled:
                    break

        if not consecutive_scheduled:
            return False

        # Schedule remaining hours (without venue requirement)
        remaining_hours = subject['hours'] - 2
        
        # Try to use all morning slots first across all days
        for day in available_days.copy():
            if remaining_hours <= 0:
                break

            morning_slots = [slot for slot in self.morning_slots 
                        if self.check_global_constraints(year, section, subject, day, slot)]
            
            if morning_slots:  # If morning slots available, use them
                slot = random.choice(morning_slots)
                self.all_timetables[(year, section)][day][slot] = {
                    'code': subject['code'],
                    'teacher': subject['teacher'],
                    'type': subject['type']
                }
                self.update_global_teacher_schedule(subject['teacher'], day, slot)
                remaining_hours -= 1
                
                if remaining_hours <= 0:
                    break
        
        # If we still have hours to schedule, try afternoon slots
        if remaining_hours > 0:
            # Reshuffle days to avoid bias
            random.shuffle(available_days)
            
            for day in available_days:
                if remaining_hours <= 0:
                    break

                # For remaining hours, prioritize early afternoon slots
                early_afternoon_slots = ["12:20-1:10", "1:10-2:00"]
                available_early_slots = [slot for slot in early_afternoon_slots 
                                    if slot in self.afternoon_slots and 
                                    self.check_global_constraints(year, section, subject, day, slot)]
                
                if available_early_slots:
                    slot = random.choice(available_early_slots)
                    self.all_timetables[(year, section)][day][slot] = {
                        'code': subject['code'],
                        'teacher': subject['teacher'],
                        'type': subject['type']
                    }
                    self.update_global_teacher_schedule(subject['teacher'], day, slot)
                    remaining_hours -= 1
                    continue
                    
                # Only if no early slots available, try late afternoon slots
                late_afternoon_slots = ["2:00-2:50", "2:50-3:40"]
                available_late_slots = [slot for slot in late_afternoon_slots 
                                    if slot in self.afternoon_slots and 
                                    self.check_global_constraints(year, section, subject, day, slot)]
                
                if available_late_slots:
                    slot = random.choice(available_late_slots)
                    self.all_timetables[(year, section)][day][slot] = {
                        'code': subject['code'],
                        'teacher': subject['teacher'],
                        'type': subject['type']
                    }
                    self.update_global_teacher_schedule(subject['teacher'], day, slot)
                    remaining_hours -= 1

        return remaining_hours == 0

    def schedule_theory_subject(self, year: int, section: str, subject: Dict) -> bool:
        # Special handling for CDC subjects
        if subject['code'] == 'CDC':
            # Find a single 2-hour slot for CDC
            available_days = self.days.copy()
            random.shuffle(available_days)

            # Prioritize morning pairs first
            morning_pairs = [
                ("8:00-8:50", "8:50-9:40"),
                ("9:50-10:40", "10:40-11:30")
            ]
            afternoon_pairs = [
                ("12:20-1:10", "1:10-2:00"),
                ("2:00-2:50", "2:50-3:40")
            ]
            
            # Try morning pairs first for all days
            for day in available_days:
                for slot1, slot2 in morning_pairs:
                    if (self.check_global_constraints(year, section, subject, day, slot1) and 
                        self.check_global_constraints(year, section, subject, day, slot2)):
                        
                        # Schedule the consecutive slots
                        for slot in [slot1, slot2]:
                            self.all_timetables[(year, section)][day][slot] = {
                                'code': subject['code'],
                                'teacher': subject['teacher'],
                                'type': subject['type']
                            }
                            self.update_global_teacher_schedule(subject['teacher'], day, slot)
                        
                        return True
            
            # Only if no morning pairs available, try afternoon pairs
            for day in available_days:
                for slot1, slot2 in afternoon_pairs:
                    if (self.check_global_constraints(year, section, subject, day, slot1) and 
                        self.check_global_constraints(year, section, subject, day, slot2)):
                        
                        # Schedule the consecutive slots
                        for slot in [slot1, slot2]:
                            self.all_timetables[(year, section)][day][slot] = {
                                'code': subject['code'],
                                'teacher': subject['teacher'],
                                'type': subject['type']
                            }
                            self.update_global_teacher_schedule(subject['teacher'], day, slot)
                        
                        return True

            return False

        # Regular theory subject scheduling
        hours_remaining = subject['hours']
        available_days = self.days.copy()
        
        # First try to fill morning slots across all days
        for day in available_days:
            if hours_remaining <= 0:
                break
                
            morning_slots = [slot for slot in self.morning_slots 
                            if self.check_global_constraints(year, section, subject, day, slot)]
            
            while morning_slots and hours_remaining > 0:
                slot = random.choice(morning_slots)
                morning_slots.remove(slot)  # Remove used slot
                
                self.all_timetables[(year, section)][day][slot] = {
                    'code': subject['code'],
                    'teacher': subject['teacher'],
                    'type': subject['type']
                }
                self.update_global_teacher_schedule(subject['teacher'], day, slot)
                hours_remaining -= 1
        
        # Only if we still have hours to schedule, try afternoon slots
        if hours_remaining > 0:
            # Shuffle days again to avoid bias in afternoon scheduling
            random.shuffle(available_days)
            
            for day in available_days:
                if hours_remaining <= 0:
                    break
                    
                # For afternoon slots, prioritize early afternoon slots
                early_afternoon_slots = ["12:20-1:10", "1:10-2:00"]
                late_afternoon_slots = ["2:00-2:50", "2:50-3:40"]
                
                # First check early afternoon slots
                available_early_slots = [slot for slot in early_afternoon_slots 
                                    if slot in self.afternoon_slots and 
                                    self.check_global_constraints(year, section, subject, day, slot)]
                
                while available_early_slots and hours_remaining > 0:
                    slot = random.choice(available_early_slots)
                    available_early_slots.remove(slot)  # Remove used slot
                    
                    self.all_timetables[(year, section)][day][slot] = {
                        'code': subject['code'],
                        'teacher': subject['teacher'],
                        'type': subject['type']
                    }
                    self.update_global_teacher_schedule(subject['teacher'], day, slot)
                    hours_remaining -= 1
                
                # Only if no early afternoon slots available or hours still remain, try late afternoon slots
                if hours_remaining > 0:
                    available_late_slots = [slot for slot in late_afternoon_slots 
                                        if slot in self.afternoon_slots and 
                                        self.check_global_constraints(year, section, subject, day, slot)]
                    
                    while available_late_slots and hours_remaining > 0:
                        slot = random.choice(available_late_slots)
                        available_late_slots.remove(slot)  # Remove used slot
                        
                        self.all_timetables[(year, section)][day][slot] = {
                            'code': subject['code'],
                            'teacher': subject['teacher'],
                            'type': subject['type']
                        }
                        self.update_global_teacher_schedule(subject['teacher'], day, slot)
                        hours_remaining -= 1

        return hours_remaining == 0
    def validate_venue_schedules(self) -> Dict:
        venue_usage = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        
        for (year, section) in self.all_timetables:
            for day in self.days:
                for slot in self.all_teaching_slots:
                    cell = self.all_timetables[(year, section)][day][slot]
                    if isinstance(cell, dict) and 'venue' in cell:
                        venue_no = cell['venue'].split(' - ')[0]
                        venue_usage[venue_no][day][slot].append({
                            'year': year,
                            'section': section,
                            'subject': cell['code'],
                            'teacher': cell['teacher']
                        })
        
        clashes_found = False
        clash_details = []
        for venue in venue_usage:
            for day in venue_usage[venue]:
                for slot in venue_usage[venue][day]:
                    if len(venue_usage[venue][day][slot]) > 1:
                        clashes_found = True
                        clash_info = {
                            'venue': venue,
                            'day': day,
                            'slot': slot,
                            'classes': [
                                f"Year {c['year']} Section {c['section']} ({c['subject']})"
                                for c in venue_usage[venue][day][slot]
                            ]
                        }
                        clash_details.append(clash_info)
        
        return {
            'has_clashes': clashes_found,
            'clash_details': clash_details
        }

    def validate_all_timetables(self, all_sections_data: Dict) -> bool:
        # Validate subject hours
        for (year, section), subjects in all_sections_data.items():
            subject_hours = {subject['code']: 0 for subject in subjects}
            
            for day in self.days:
                for slot in self.all_teaching_slots:
                    cell = self.all_timetables[(year, section)][day][slot]
                    if isinstance(cell, dict):
                        subject_hours[cell['code']] += 1

            for subject in subjects:
                if subject_hours[subject['code']] != subject['hours']:
                    return False

        # Validate teacher schedules and gaps
        teacher_slots = defaultdict(lambda: defaultdict(list))
        for (year, section) in self.all_timetables:
            for day in self.days:
                for slot in self.all_teaching_slots:
                    cell = self.all_timetables[(year, section)][day][slot]
                    if isinstance(cell, dict):
                        teacher = cell['teacher']
                        teacher_slots[teacher][day].append((slot, year, section))

        # Check for consecutive classes
        for teacher in teacher_slots:
            for day in teacher_slots[teacher]:
                # Sort slots for this teacher on this day
                day_slots = sorted(teacher_slots[teacher][day], 
                                 key=lambda x: self.all_teaching_slots.index(x[0]))
                
                # Check consecutive slots
                for i in range(len(day_slots) - 1):
                    curr_slot_idx = self.all_teaching_slots.index(day_slots[i][0])
                    next_slot_idx = self.all_teaching_slots.index(day_slots[i + 1][0])
                    
                    # If slots are consecutive (allowing for J/P subjects)
                    if next_slot_idx - curr_slot_idx == 1:
                        # Check if it's not part of the same J/P subject
                        curr_class = self.all_timetables[(day_slots[i][1], day_slots[i][2])][day][day_slots[i][0]]
                        next_class = self.all_timetables[(day_slots[i+1][1], day_slots[i+1][2])][day][day_slots[i+1][0]]
                        
                        if curr_class['code'] != next_class['code']:
                            return False

        return True



    def generate_all_timetables(self, all_sections_data: Dict, venues: Dict) -> bool:
        self.initialize_empty_timetables()
        max_attempts = 5
        print("Generating timetables with sections:", self.sections)
        for attempt in range(max_attempts):
            print(f"Attempt {attempt + 1} of {max_attempts}")
            
            self.initialize_empty_timetables()
            self.global_teacher_schedule.clear()
            self.global_venue_schedule.clear()
            
            scheduling_successful = True
            
            # Schedule J/P subjects first
            for year in self.sections:
                for section in self.sections[year]:
                    if (year, section) in all_sections_data:
                        subjects = all_sections_data[(year, section)]
                        jp_subjects = [s for s in subjects if s['type'] in ['J', 'P']]
                        random.shuffle(jp_subjects)
                        
                        for subject in jp_subjects:
                            if not self.schedule_jp_subject(year, section, subject, venues):
                                print(f"Failed to schedule {subject['code']} for {year}-{section}")
                                scheduling_successful = False
                                break

            # Then schedule theory subjects
            if scheduling_successful:
                for year in self.sections:
                    for section in self.sections[year]:
                        if (year, section) in all_sections_data:
                            subjects = all_sections_data[(year, section)]
                            theory_subjects = [s for s in subjects if s['type'] == 'T']
                            random.shuffle(theory_subjects)
                            
                            for subject in theory_subjects:
                                if not self.schedule_theory_subject(year, section, subject):
                                    print(f"Failed to schedule {subject['code']} for {year}-{section}")
                                    scheduling_successful = False
                                    break

            if scheduling_successful and self.validate_all_timetables(all_sections_data):
                if self.validate_venue_schedules():
                    print("Successfully generated all timetables with no venue clashes!")
                    return True
                else:
                    scheduling_successful = False

        print("Failed to generate valid timetables after maximum attempts")
        return False
    
#Helper Functions
def create_sample_data(subject_file, faculty_df):
    try:
        df = pd.read_csv(subject_file)
        subject_year_mapping = {}
        
        for i in range(1, 4): 
            sub_col = f'SUB_{i}'
            year_col = f'SUB_{i}_Year'
            
            valid_rows = faculty_df[faculty_df[sub_col].notna()]
            
            for _, row in valid_rows.iterrows():

                subject_str = row[sub_col]
                subject_code = subject_str.split('/')[0].strip()
                subject_year_mapping[subject_code] = row[year_col]


        subjects_data = {
            'Subject Code': df['SubjectCode'].values,
            'Hours': df['Hours'].values,
            'Subject Type': [code[-1] if pd.notna(code) else None for code in df['SubjectCode']], 
            'Subject Year': [subject_year_mapping.get(code, None) for code in df['SubjectCode']]  
        }
        
        # Create DataFrame and filter out rows where Subject Year is None
        result_df = pd.DataFrame(subjects_data)
        result_df = result_df[result_df['Subject Year'].notna()]
        
        # Convert Subject Year to int
        result_df['Subject Year'] = result_df['Subject Year'].astype(int)
        
        return result_df
    
    except Exception as e:
        raise ValueError(f"Error processing subject list file: {str(e)}")
    
def load_venue_data(venue_file):
    try:
        df = pd.read_csv(venue_file)
        return dict(zip(df['Venue No'], df['Venue Name']))
    except Exception as e:
        raise ValueError(f"Error processing venue list file: {str(e)}")
    
def process_faculty_data(faculty_df: pd.DataFrame) -> Dict:
    faculty_allocations = {}
    
    for _, row in faculty_df.iterrows():
        for sub_num in [1, 2, 3]:
            sub_col = f'SUB_{sub_num}'
            class_col = f'SUB_{sub_num}_Class'
            
            if pd.notna(row[sub_col]):
                subject_code = row[sub_col].split('/')[0].strip()
                section = row[class_col]
                if section not in faculty_allocations:
                    faculty_allocations[section] = {}
                faculty_allocations[section][subject_code] = row['Name']
    
    return faculty_allocations


def get_subjects_for_section(year: int, section: str, subjects_df: pd.DataFrame, 
                           faculty_allocations: Dict) -> List[Dict]:
    section_subjects = []
    section_key = f'CSE-{section}'
    
    year_subjects = subjects_df[subjects_df['Subject Year'] == year]
    print(f"\nProcessing subjects for {section_key}, Year {year}")
    
    for _, subject in year_subjects.iterrows():
        if section_key in faculty_allocations and subject['Subject Code'] in faculty_allocations[section_key]:
            # Get the last character of subject code
            subject_code = subject['Subject Code']
            subject_type = subject_code[-1]  # This will be P, J, or T
            needs_lab = subject_type in ['P', 'J']
            
            print(f"Subject: {subject_code}, Type: {subject_type}, Needs Lab: {needs_lab}")
            
            section_subjects.append({
                'code': subject_code,
                'type': subject_type,
                'hours': subject['Hours'],
                'teacher': faculty_allocations[section_key][subject_code],
                'needs_lab': needs_lab
            })
    
    return section_subjects

def get_cdc_subjects_for_section(year: int, section: str, cdc_df: pd.DataFrame, 
                                  faculty_allocations: Dict) -> List[Dict]:
    cdc_subjects = []
    section_key = f'CSE-{section}'
    
    year_cdc_subjects = cdc_df[
        (cdc_df['SUB_Year'] == year) & 
        (cdc_df['SUB_Classes'] == section_key)
    ]
    
    for _, subject in year_cdc_subjects.iterrows():
        cdc_subjects.append({
            'code': 'CDC',
            'type': 'T',
            'hours': 2,
            'teacher': subject['Name']
        })
    
    return cdc_subjects

#Database Storage Functions
def save_timetables_to_database(generator, all_sections_data, faculty_df, cdc_df, venues, connection_uri):
    try:
        # Create SQLAlchemy engine
        engine = create_engine(connection_uri)
        
        # Create a connection
        with engine.connect() as connection:
            # Start a transaction
            with connection.begin():
                # Create a unique schema for this timetable generation
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                schema_name = f"timetable_{timestamp}"

                # Create schema
                connection.execute(text(f"CREATE SCHEMA {schema_name}"))

                # Create tables within the schema
                connection.execute(text(f"""
                CREATE TABLE {schema_name}.class_timetables (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    year INT,
                    section VARCHAR(10),
                    timetable_data JSON,
                    free_hours JSON,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """))

                connection.execute(text(f"""
                CREATE TABLE {schema_name}.teacher_timetables (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    employee_id VARCHAR(20),
                    teacher_name VARCHAR(100),
                    timetable_data JSON,
                    free_hours JSON,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """))

                connection.execute(text(f"""
                CREATE TABLE {schema_name}.venue_timetables (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    venue_id VARCHAR(20),
                    venue_name VARCHAR(100),
                    timetable_data JSON,
                    free_hours JSON,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """))

                # Save Class Timetables with explicit venue information
                for (year, section), timetable in generator.all_timetables.items():
                    formatted_timetable = {}
                    free_hours = defaultdict(list)
                    
                    for day in generator.days:
                        formatted_timetable[day] = {}
                        for slot in generator.slots:
                            cell = timetable[day][slot]
                            if isinstance(cell, dict):
                                formatted_timetable[day][slot] = {
                                    'code': cell.get('code', 'N/A'),
                                    'teacher': cell.get('teacher', 'N/A'),
                                    'type': cell.get('type', 'N/A'),
                                    'venue': cell.get('venue', 'N/A')  # Ensure venue is included
                                }
                                # Print debug information
                                if 'venue' in cell:
                                    print(f"Saving venue {cell['venue']} for {year}-{section} {day} {slot}")
                            else:
                                formatted_timetable[day][slot] = cell
                                if cell == "FREE" and slot not in ["BREAK", "LUNCH"]:
                                    free_hours[day].append(slot)

                    # Insert class timetable
                    connection.execute(text(f"""
                    INSERT INTO {schema_name}.class_timetables 
                    (year, section, timetable_data, free_hours)
                    VALUES (:year, :section, :timetable_data, :free_hours)
                    """), {
                        'year': year,
                        'section': section,
                        'timetable_data': json.dumps(formatted_timetable),
                        'free_hours': json.dumps(dict(free_hours))
                    })

                # Save Teacher Timetables with venue information
                teacher_schedules = defaultdict(lambda: defaultdict(dict))
                teacher_free_hours = defaultdict(lambda: defaultdict(list))

                for (year, section), timetable in generator.all_timetables.items():
                    for day in generator.days:
                        for slot in generator.slots:
                            cell = timetable[day][slot]
                            if isinstance(cell, dict):
                                teacher = cell['teacher']
                                teacher_schedules[teacher][day][slot] = {
                                    'year': year,
                                    'section': section,
                                    'code': cell['code'],
                                    'type': cell['type'],
                                    'venue': cell.get('venue', 'N/A')  # Include venue
                                }
                            elif slot not in ["BREAK", "LUNCH"]:
                                for teacher in teacher_schedules:
                                    if slot not in teacher_schedules[teacher].get(day, {}):
                                        teacher_free_hours[teacher][day].append(slot)

                # Save teacher timetables
                for teacher in teacher_schedules:
                    connection.execute(text(f"""
                    INSERT INTO {schema_name}.teacher_timetables 
                    (teacher_name, timetable_data, free_hours)
                    VALUES (:teacher_name, :timetable_data, :free_hours)
                    """), {
                        'teacher_name': teacher,
                        'timetable_data': json.dumps(dict(teacher_schedules[teacher])),
                        'free_hours': json.dumps(dict(teacher_free_hours[teacher]))
                    })

                # Save Venue Timetables
                venue_schedules = defaultdict(lambda: defaultdict(dict))
                venue_free_hours = defaultdict(lambda: defaultdict(list))

                for (year, section), timetable in generator.all_timetables.items():
                    for day in generator.days:
                        for slot in generator.slots:
                            cell = timetable[day][slot]
                            if isinstance(cell, dict) and 'venue' in cell:
                                venue = cell['venue'].split(' - ')[0]  # Get venue number
                                venue_schedules[venue][day][slot] = {
                                    'year': year,
                                    'section': section,
                                    'code': cell['code'],
                                    'teacher': cell['teacher']
                                }
                            elif slot not in ["BREAK", "LUNCH"]:
                                for venue in venues:
                                    if slot not in venue_schedules[venue].get(day, {}):
                                        venue_free_hours[venue][day].append(slot)

                # Save venue timetables
                for venue_id, venue_name in venues.items():
                    connection.execute(text(f"""
                    INSERT INTO {schema_name}.venue_timetables 
                    (venue_id, venue_name, timetable_data, free_hours)
                    VALUES (:venue_id, :venue_name, :timetable_data, :free_hours)
                    """), {
                        'venue_id': venue_id,
                        'venue_name': venue_name,
                        'timetable_data': json.dumps(dict(venue_schedules[str(venue_id)])),
                        'free_hours': json.dumps(dict(venue_free_hours[str(venue_id)]))
                    })

                print(f"Timetables saved in schema: {schema_name}")
                return True

    except Exception as e:
        print(f"Database save error: {str(e)}")
        traceback.print_exc()
        return False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='timetable_generator.log'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables with type hints
current_generator: GlobalTimeTableGenerator = None
current_all_sections_data: Dict = None
current_faculty_df: pd.DataFrame = None
current_cdc_df: pd.DataFrame = None
current_venues: Dict = None

@app.route('/generate_timetable', methods=['POST'])
def generate_timetable():
    global current_generator, current_all_sections_data, current_faculty_df, current_cdc_df, current_venues
    
    try:
        # Get section configuration from request
        section_config = None
        if 'sectionConfig' in request.form:
            try:
                section_config = json.loads(request.form['sectionConfig'])
                # Convert string keys to integers
                section_config = {int(k): v for k, v in section_config.items()}
                logger.info(f"Received section configuration: {section_config}")
            except Exception as e:
                logger.error(f"Error parsing section configuration: {e}")
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid section configuration: {str(e)}'
                }), 400

        # Validate file uploads
        required_files = ['faculty', 'subjects', 'venues', 'cdc']
        for file_key in required_files:
            if file_key not in request.files:
                logger.error(f'Missing {file_key} file')
                return jsonify({
                    'status': 'error', 
                    'message': f'Missing {file_key} file'
                }), 400

        # Save uploaded files
        upload_dir = 'temp_uploads'
        os.makedirs(upload_dir, exist_ok=True)
        
        file_paths = {}
        for file_key in required_files:
            file = request.files[file_key]
            file_path = os.path.join(upload_dir, f'{file_key}.csv')
            file.save(file_path)
            file_paths[file_key] = file_path
            logger.info(f'Saved {file_key} file to {file_path}')

        # Initialize timetable generator with section configuration
        current_generator = GlobalTimeTableGenerator(section_config=section_config)
        current_generator.initialize_empty_timetables()

        # Process data
        current_faculty_df = pd.read_csv(file_paths['faculty'])
        # Pass faculty_df to create_sample_data
        subjects_df = create_sample_data(file_paths['subjects'], current_faculty_df)
        current_venues = load_venue_data(file_paths['venues'])
        current_cdc_df = pd.read_csv(file_paths['cdc'])
        
        # Process faculty allocations
        faculty_allocations = process_faculty_data(current_faculty_df)

        # Prepare sections data using the configured sections
        current_all_sections_data = {}
        for year, sections in current_generator.sections.items():
            for section in sections:
                # Get regular subjects
                section_subjects = get_subjects_for_section(
                    year, section, subjects_df, faculty_allocations
                )
                
                # Add CDC subjects
                cdc_subjects = get_cdc_subjects_for_section(
                    year, section, current_cdc_df, faculty_allocations
                )
                
                # Combine subjects
                if section_subjects or cdc_subjects:
                    current_all_sections_data[(year, section)] = (
                        section_subjects + cdc_subjects
                    )

        # Generate timetables
        if current_generator.generate_all_timetables(current_all_sections_data, current_venues):
            # Prepare timetable data for frontend
            timetable_data = {}
            for (year, section), timetable in current_generator.all_timetables.items():
                formatted_timetable = {}
                for day, day_schedule in timetable.items():
                    formatted_timetable[day] = {}
                    for slot, slot_data in day_schedule.items():
                        if isinstance(slot_data, dict):
                            formatted_timetable[day][slot] = {
                                'code': slot_data.get('code', 'N/A'),
                                'teacher': slot_data.get('teacher', 'N/A'),
                                'type': slot_data.get('type', 'N/A'),
                                'venue': slot_data.get('venue', 'N/A')
                            }
                        else:
                            formatted_timetable[day][slot] = slot_data
                
                timetable_data[f"Year {year} Section {section}"] = formatted_timetable

            # Perform validation
            validation_result = current_generator.validate_all_timetables(current_all_sections_data)
            venue_validation = current_generator.validate_venue_schedules()

            logger.info('Timetables generated successfully')
            return jsonify({
                'status': 'success',
                'timetables': timetable_data,
                'validation': {
                    'subject_hours': validation_result,
                    'venue_clashes': venue_validation
                }
            })
        else:
            logger.error('Failed to generate valid timetables')
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate valid timetables'
            }), 500

    except Exception as e:
        logger.error(f'Error in timetable generation: {str(e)}')
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    finally:
        # Cleanup temporary files
        for file_path in file_paths.values():
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f'Error removing temporary file {file_path}: {e}')

@app.route('/save_timetables', methods=['POST'])
def save_timetables():
    global current_generator, current_all_sections_data, current_faculty_df, current_cdc_df, current_venues
    
    try:
        # Retrieve connection URI from environment variables
        connection_uri = os.getenv('DATABASE_URI')
        
        if not connection_uri:
            logger.error("DATABASE_URI not found in environment variables")
            return jsonify({
                'status': 'error',
                'message': 'Database configuration not found'
            }), 400
        
        # Validate that all required data is available
        if not all([
            current_generator, 
            current_all_sections_data, 
            current_faculty_df is not None,
            current_cdc_df is not None,
            current_venues
        ]):
            missing_data = []
            if not current_generator:
                missing_data.append("timetable generator")
            if not current_all_sections_data:
                missing_data.append("sections data")
            if current_faculty_df is None:
                missing_data.append("faculty data")
            if current_cdc_df is None:
                missing_data.append("CDC data")
            if not current_venues:
                missing_data.append("venue data")
            
            logger.error(f"Missing required data: {', '.join(missing_data)}")
            return jsonify({
                'status': 'error',
                'message': f'Missing required data: {", ".join(missing_data)}'
            }), 400
        
        # Save timetables to database
        success = save_timetables_to_database(
            generator=current_generator,
            all_sections_data=current_all_sections_data,
            faculty_df=current_faculty_df,
            cdc_df=current_cdc_df,
            venues=current_venues,
            connection_uri=connection_uri
        )
        
        if success:
            # Get the schema name (it's the most recent one)
            engine = create_engine(connection_uri)
            with engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT SCHEMA_NAME 
                    FROM INFORMATION_SCHEMA.SCHEMATA 
                    WHERE SCHEMA_NAME LIKE 'timetable_%' 
                    ORDER BY SCHEMA_NAME DESC 
                    LIMIT 1
                """))
                schema_name = result.fetchone()[0]

            logger.info(f"Timetables saved successfully in schema: {schema_name}")
            return jsonify({
                'status': 'success',
                'message': 'Timetables saved to database',
                'schema': schema_name
            })
        else:
            logger.error("Failed to save timetables")
            return jsonify({
                'status': 'error',
                'message': 'Failed to save timetables'
            }), 500
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in save_timetables: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Database error: {str(e)}'
        }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in save_timetables: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Unexpected error: {str(e)}'
        }), 500


@app.route('/validate_timetables', methods=['GET'])
def validate_timetables():
    global current_generator, current_all_sections_data
    
    try:
        if not current_generator or not current_all_sections_data:
            logger.error('Timetables not generated for validation')
            return jsonify({
                'status': 'error',
                'message': 'Generate timetables first'
            }), 400
        
        # Perform validation
        subject_hours_validation = current_generator.validate_all_timetables(current_all_sections_data)
        venue_validation = current_generator.validate_venue_schedules()
        
        logger.info('Timetables validated successfully')
        return jsonify({
            'status': 'success',
            'validation': {
                'subject_hours': subject_hours_validation,
                'venue_clashes': venue_validation
            }
        })
    
    except Exception as e:
        logger.error(f'Validation error: {str(e)}')
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Error handler for 404
@app.errorhandler(404)
def not_found(error):
    logger.error(f'404 error: {error}')
    return jsonify({
        'status': 'error',
        'message': 'Endpoint not found'
    }), 404

# Error handler for 500
@app.errorhandler(500)
def server_error(error):
    logger.error(f'500 error: {error}')
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Ensure temp_uploads directory exists
    os.makedirs('temp_uploads', exist_ok=True)
    
    # Run the app
    app.run(
        debug=True, 
        host='0.0.0.0',  # Make server publicly available
        port=5000,
        threaded=True  # Enable threading for better performance
    )