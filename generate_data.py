# generate_data.py
# This script creates synthetic data for patients and doctor schedules
# based on the project plan.

import pandas as pd
from faker import Faker
import random
from datetime import date, timedelta, time
import os

# --- Configuration ---
NUM_PATIENTS = 50
SCHEDULE_DAYS = 14  # Generate schedule for the next 2 weeks
OUTPUT_DIR = "data"

# Initialize Faker for data generation
fake = Faker('en_US')

def generate_patients(n=50):
    """
    Generates a DataFrame with n synthetic patients, including insurance
    and visit history, as specified in the project plan.
    """
    patients = []
    insurance_carriers = ["Blue Cross", "Aetna", "Cigna", "UnitedHealth", "Medicare"]
    
    for i in range(n):
        # Determine if the patient has a visit history to classify them as new or returning
        has_history = random.choice([True, False])
        
        patient = {
            "patient_id": f"P{i+1:03d}",
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "date_of_birth": fake.date_of_birth(minimum_age=18, maximum_age=90).strftime('%Y-%m-%d'),
            "phone": fake.phone_number(),
            "email": fake.email(),
            "address": fake.address().replace('\n', ', '),
            "insurance_carrier": random.choice(insurance_carriers),
            "member_id": fake.bothify(text='???#########', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ'),
            "visit_history": random.randint(1, 15) if has_history else 0,
            "last_visit": fake.date_between(start_date='-2y', end_date='-1w').strftime('%Y-%m-%d') if has_history else None
        }
        patients.append(patient)
    
    df = pd.DataFrame(patients)
    print(f"✅ Generated {len(df)} patient records with detailed information.")
    return df

def generate_doctor_schedules():
    """
    Generates a DataFrame with synthetic doctor schedules, including weekly
    availability, breaks, and time slots as specified in the project plan.
    """
    doctors = [
        {"doctor_id": "D001", "name": "Dr. Smith", "specialty": "General Medicine"},
        {"doctor_id": "D002", "name": "Dr. Johnson", "specialty": "Cardiology"},
        {"doctor_id": "D003", "name": "Dr. Williams", "specialty": "Dermatology"}
    ]
    
    schedules = []
    start_date = date.today()

    for doctor in doctors:
        for i in range(SCHEDULE_DAYS):
            current_date = start_date + timedelta(days=i)
            # Doctors work Monday to Friday (weekday() < 5)
            if current_date.weekday() < 5:
                # Define working sessions: 9 AM - 12 PM and 1 PM - 5 PM
                working_hours = [
                    {"start": time(9, 0), "end": time(12, 0)},
                    {"start": time(13, 0), "end": time(17, 0)}
                ]
                
                # Randomly introduce a day off or half-day
                if random.random() < 0.05: # 5% chance of a full day off
                    continue
                if random.random() < 0.1: # 10% chance of a half-day off
                    working_hours.pop(random.randrange(len(working_hours)))

                for session in working_hours:
                    schedules.append({
                        "doctor_id": doctor["doctor_id"],
                        "doctor_name": doctor["name"],
                        "date": current_date.strftime('%Y-%m-%d'),
                        "start_time": session["start"].strftime('%H:%M:%S'),
                        "end_time": session["end"].strftime('%H:%M:%S'),
                        "is_available": True
                    })
    
    df = pd.DataFrame(schedules)
    print(f"✅ Generated {len(df)} schedule slots for {len(doctors)} doctors.")
    return df

if __name__ == "__main__":
    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- Generate and Save Patient Data ---
    patients_df = generate_patients(NUM_PATIENTS)
    patients_csv_path = os.path.join(OUTPUT_DIR, "patients.csv")
    patients_df.to_csv(patients_csv_path, index=False)
    print(f"📄 Patient data saved to '{patients_csv_path}'")

    # --- Generate and Save Doctor Schedules ---
    schedules_df = generate_doctor_schedules()
    schedules_excel_path = os.path.join(OUTPUT_DIR, "doctor_schedules.xlsx")
    schedules_df.to_excel(schedules_excel_path, index=False)
    print(f"📄 Doctor schedules saved to '{schedules_excel_path}'")

    print("\n🎉 Synthetic data generation complete and aligned with the project plan!")
