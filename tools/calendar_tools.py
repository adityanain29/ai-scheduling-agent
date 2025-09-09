# tools/calendar_tools.py
# This tool handles reading doctor schedules and finding available appointment slots.

import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import re

class CalendarTools:
    def __init__(self, schedules_filepath: str, appointments_filepath: str, appointment_durations: dict):
        """
        Initializes the CalendarTools.

        Args:
            schedules_filepath: Path to the doctor schedules Excel file.
            appointments_filepath: Path to the appointments CSV file.
            appointment_durations: A dictionary with durations for new/returning patients.
        """
        self.appointment_durations = appointment_durations
        self.appointments_file = appointments_filepath
        try:
            self.df = pd.read_excel(schedules_filepath)
            # Convert schedule times to datetime objects
            self.df['start_datetime'] = pd.to_datetime(self.df['date'].astype(str) + ' ' + self.df['start_time'].astype(str))
            self.df['end_datetime'] = pd.to_datetime(self.df['date'].astype(str) + ' ' + self.df['end_time'].astype(str))
        except FileNotFoundError:
            print(f"Error: The schedule file '{schedules_filepath}' was not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error loading or processing the Excel file: {e}")
            sys.exit(1)

        self._load_booked_slots()

    def _load_booked_slots(self):
        """
        Loads already booked appointments to prevent double booking.
        Creates a set of datetime objects for quick lookup.
        """
        self.booked_slots = set()
        try:
            if os.path.exists(self.appointments_file):
                app_df = pd.read_csv(self.appointments_file)
                for _, row in app_df.iterrows():
                    booked_time = pd.to_datetime(f"{row['appointment_date']} {row['appointment_time']}")
                    self.booked_slots.add(booked_time)
        except Exception as e:
            print(f"Warning: Could not load booked appointments. {e}")

    def find_available_slots(self, is_new_patient: bool, start_date: datetime, end_date: datetime) -> list:
        """
        Finds available appointment slots, excluding any that are already booked.
        """
        duration_key = "new_patient" if is_new_patient else "returning_patient"
        duration_minutes = self.appointment_durations[duration_key]
        appointment_duration = timedelta(minutes=duration_minutes)
        
        available_slots = []

        mask = (self.df['start_datetime'] >= start_date) & (self.df['start_datetime'] < end_date)
        relevant_schedule = self.df.loc[mask]

        for _, row in relevant_schedule.iterrows():
            slot_start = row['start_datetime']
            block_end = row['end_datetime']

            while slot_start + appointment_duration <= block_end:
                # --- CONFLICT PREVENTION CHECK ---
                # Check if this specific start time is already in our set of booked slots.
                if slot_start not in self.booked_slots:
                    formatted_slot = (
                        f"{row['doctor_name']} on {slot_start.strftime('%A, %B %d')} "
                        f"at {slot_start.strftime('%I:%M %p')}"
                    )
                    available_slots.append(formatted_slot)
                
                slot_start += appointment_duration
        
        return available_slots

# --- Example Usage & Testing ---
if __name__ == '__main__':
    # --- FIX FOR DIRECT EXECUTION ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    # --- END FIX ---

    # --- LOCAL IMPORTS ---
    from config import settings
    # --- END LOCAL IMPORTS ---

    print("🚀 Testing Calendar Tools with Conflict Prevention...")
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    next_week = today + timedelta(days=7)

    # --- Test Case 1 & 2 remain the same ---
    print("\n--- Test Case 1 & 2: Basic Slot Finding ---")
    calendar = CalendarTools(
        schedules_filepath=settings.DOCTOR_SCHEDULES_PATH,
        appointments_filepath=settings.APPOINTMENTS_CSV_PATH,
        appointment_durations=settings.APPOINTMENT_DURATIONS
    )
    new_patient_slots = calendar.find_available_slots(True, today, next_week)
    assert len(new_patient_slots) > 0
    print("✅ Basic slot finding tests passed.")

    # --- Test Case 3: Verify Conflict Prevention ---
    print("\n--- Test Case 3: Verifying Conflict Prevention ---")
    # Manually create a fake booked appointment for testing
    first_available_slot = new_patient_slots[0]
    
    # Extract details from the slot string to create a dummy appointment file
    match = re.search(r"on (.+?) at (.+)", first_available_slot)
    date_str = match.group(1).strip()
    time_str = match.group(2).strip()
    full_date_str = f"{date_str}, {datetime.now().year}"
    dt_object = datetime.strptime(full_date_str + " " + time_str, "%A, %B %d, %Y %I:%M %p")
    
    # Create a dummy appointments.csv for this test
    dummy_app_path = os.path.join(settings.DATA_DIR, 'dummy_appointments.csv')
    dummy_appointment = {
        "appointment_id": "DUMMY001", "patient_id": "P001", "doctor_name": "Dr. Evelyn Reed",
        "appointment_date": dt_object.strftime("%Y-%m-%d"),
        "appointment_time": dt_object.strftime("%H:%M:%S"),
        "is_new_patient": True, "status": "Confirmed"
    }
    pd.DataFrame([dummy_appointment]).to_csv(dummy_app_path, index=False)

    # Now, initialize a new CalendarTools instance that reads our dummy file
    conflict_calendar = CalendarTools(
        schedules_filepath=settings.DOCTOR_SCHEDULES_PATH,
        appointments_filepath=dummy_app_path,
        appointment_durations=settings.APPOINTMENT_DURATIONS
    )
    
    # Find slots again
    slots_after_booking = conflict_calendar.find_available_slots(True, today, next_week)

    print(f"Slot to check: '{first_available_slot}'")
    print(f"Original slot count: {len(new_patient_slots)}")
    print(f"New slot count: {len(slots_after_booking)}")
    
    assert first_available_slot not in slots_after_booking
    assert len(slots_after_booking) < len(new_patient_slots)
    
    # Clean up the dummy file
    os.remove(dummy_app_path)
    print("✅ Test Case 3 Passed: Booked slot was successfully excluded.")
    
    print("\n🎉 Calendar Tools tests completed successfully!")

