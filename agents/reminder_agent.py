# agents/reminder_agent.py
# This agent simulates a background job that checks for upcoming appointments
# and sends out reminders via SMS and email.

import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time

# --- FIX FOR DIRECT EXECUTION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)
# --- END FIX ---

# Import tools and settings
from config import settings
from tools.sms_tools import SMSTools
from tools.email_tools import EmailTools

class ReminderAgent:
    def __init__(self):
        """Initializes the reminder agent and its tools."""
        self.sms_tool = SMSTools(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN,
            settings.TWILIO_PHONE_NUMBER
        )
        self.email_tool = EmailTools(
            settings.SMTP_SERVER,
            settings.SMTP_PORT,
            settings.EMAIL_ADDRESS,
            settings.EMAIL_PASSWORD
        )
        self.appointments_df = self._load_appointments()
        self.patients_df = self._load_patients()
        self.sent_reminders = set() # To avoid sending the same reminder multiple times

    def _load_appointments(self):
        """Loads confirmed appointments from the CSV."""
        try:
            df = pd.read_csv(settings.APPOINTMENTS_CSV_PATH)
            df['appointment_datetime'] = pd.to_datetime(df['appointment_date'] + ' ' + df['appointment_time'])
            return df[df['status'] == 'Confirmed']
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            print(f"Error loading appointments: {e}")
            return pd.DataFrame()
            
    def _load_patients(self):
        """Loads patient contact info."""
        try:
            return pd.read_csv(settings.PATIENTS_CSV_PATH)
        except FileNotFoundError:
            return pd.DataFrame()

    def check_and_send_reminders(self, demo_phone=None, demo_email=None):
        """
        Checks all appointments and sends reminders if they are due.
        """
        if self.appointments_df.empty:
            print("No confirmed appointments found.")
            return

        now = datetime.now()
        
        for _, appointment in self.appointments_df.iterrows():
            appointment_id = appointment['appointment_id']
            appointment_time = appointment['appointment_datetime']
            time_to_appointment = appointment_time - now
            
            patient_details_result = self.patients_df[self.patients_df['patient_id'] == appointment['patient_id']]
            if patient_details_result.empty:
                print(f"⚠️ Warning: Could not find details for patient_id {appointment['patient_id']}.")
                continue
            
            patient_details = patient_details_result.iloc[0]
            patient_name = f"{patient_details['first_name']} {patient_details['last_name']}"
            patient_phone = demo_phone or patient_details['phone']
            patient_email = demo_email or patient_details['email']

            # --- DEMO REMINDER LOGIC (in Seconds) ---
            
            # Reminder 1: 15 seconds before
            if timedelta(seconds=14) < time_to_appointment <= timedelta(seconds=15) and (appointment_id, 1) not in self.sent_reminders:
                print(f"INFO: Sending 15-second reminder for {appointment_id}")
                subject = f"Appointment Reminder: Today at {appointment_time.strftime('%I:%M %p')}"
                body = f"Hi {patient_name}, this is a reminder for your appointment today at {appointment_time.strftime('%I:%M %p')} with {appointment['doctor_name']}."
                self.sms_tool.send_sms(patient_phone, body)
                self.email_tool.send_reminder_email(patient_email, subject, body)
                self.sent_reminders.add((appointment_id, 1))

            # Reminder 2: 10 seconds before
            elif timedelta(seconds=9) < time_to_appointment <= timedelta(seconds=10) and (appointment_id, 2) not in self.sent_reminders:
                print(f"INFO: Sending 10-second reminder for {appointment_id}")
                subject = f"Action Required: Your Appointment in 10 minutes (Simulated)"
                body = f"Hi {patient_name}, your appointment with {appointment['doctor_name']} is soon. Have you filled out the patient intake form? Please reply YES to confirm, or NO [REASON] to cancel."
                self.sms_tool.send_sms(patient_phone, body)
                self.email_tool.send_reminder_email(patient_email, subject, body)
                self.sent_reminders.add((appointment_id, 2))

            # Reminder 3: 5 seconds before
            elif timedelta(seconds=4) < time_to_appointment <= timedelta(seconds=5) and (appointment_id, 3) not in self.sent_reminders:
                print(f"INFO: Sending 5-second reminder for {appointment_id}")
                subject = f"FINAL REMINDER: Your Appointment is very soon"
                body = f"FINAL REMINDER: Your appointment with {appointment['doctor_name']} is in a few moments at {appointment_time.strftime('%I:%M %p')}. Please reply YES to confirm."
                self.sms_tool.send_sms(patient_phone, body)
                self.email_tool.send_reminder_email(patient_email, subject, body)
                self.sent_reminders.add((appointment_id, 3))


if __name__ == '__main__':
    # --- !! IMPORTANT: SET YOUR DEMO DETAILS HERE !! ---
    # Phone number MUST be in E.164 format (e.g., +919876543210 for India).
    DEMO_RECIPIENT_PHONE = "+919610729029"  
    DEMO_RECIPIENT_EMAIL = "nainaditya29@gmail.com"
    # --- !! END DEMO DETAILS !! ---

    print("🚀 Initializing DEMO Reminder Agent...")
    agent = ReminderAgent()
    
    if agent.patients_df.empty:
        print("⚠️ Cannot run simulation, no patient data found.")
    else:
        now = datetime.now()
        test_patient = agent.patients_df.iloc[0]
        
        # Create fake appointments for the demo
        appointments_to_add = [
            {"appointment_id": "DEMO001", "patient_id": test_patient['patient_id'], "doctor_name": "Dr. Demo One", "appointment_datetime": now + timedelta(seconds=15), "status": "Confirmed"},
            {"appointment_id": "DEMO002", "patient_id": test_patient['patient_id'], "doctor_name": "Dr. Demo Two", "appointment_datetime": now + timedelta(seconds=10), "status": "Confirmed"},
            {"appointment_id": "DEMO003", "patient_id": test_patient['patient_id'], "doctor_name": "Dr. Demo Three", "appointment_datetime": now + timedelta(seconds=5), "status": "Confirmed"},
        ]
        agent.appointments_df = pd.concat([agent.appointments_df, pd.DataFrame(appointments_to_add)], ignore_index=True)
        
        print(f"\n--- Starting 20-second simulation loop. Get ready! ---")
        print(f"Reminders will be sent to Phone: {DEMO_RECIPIENT_PHONE} and Email: {DEMO_RECIPIENT_EMAIL}")
        
        for i in range(20):
            print(f"\n--- Check #{i+1} ---")
            agent.check_and_send_reminders(demo_phone=DEMO_RECIPIENT_PHONE, demo_email=DEMO_RECIPIENT_EMAIL)
            time.sleep(1)

    print("\n🎉 Reminder Agent DEMO complete.")

