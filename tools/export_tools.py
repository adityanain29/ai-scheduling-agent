# tools/export_tools.py
# This tool handles booking the appointment by writing to a CSV and
# generating an Excel report for admin review.

import pandas as pd
import os
import sys
from datetime import datetime
import re

class ExportTools:
    def __init__(self, appointments_filepath: str, patients_filepath: str, exports_dir: str):
        """
        Initializes the ExportTools.

        Args:
            appointments_filepath: Path to the appointments CSV file.
            patients_filepath: Path to the patients CSV file for report generation.
            exports_dir: Directory to save the admin reports.
        """
        self.appointments_file = appointments_filepath
        self.patients_file = patients_filepath
        self.exports_dir = exports_dir
        
        # Ensure the exports directory exists
        os.makedirs(self.exports_dir, exist_ok=True)
        
        # Ensure the appointments file exists with headers
        if not os.path.exists(self.appointments_file):
            pd.DataFrame(columns=[
                "appointment_id", "patient_id", "doctor_name", 
                "appointment_date", "appointment_time", "is_new_patient", "status"
            ]).to_csv(self.appointments_file, index=False)

    def _parse_slot_string(self, slot_string: str) -> dict:
        """
        Parses the user-friendly slot string into structured data.
        Example: "Dr. Evelyn Reed on Monday, September 08 at 10:30 AM"
        """
        try:
            # Regex to capture the doctor's name, the date part, and the time part
            match = re.search(r"(Dr\. .+?) on (.+?) at (.+)", slot_string)
            if not match:
                raise ValueError("Slot string format is incorrect.")
                
            doctor_name = match.group(1).strip()
            date_str = match.group(2).strip()
            time_str = match.group(3).strip()

            # Combine date and time and parse into a datetime object
            # We need to add the current year to the date string for parsing
            full_date_str = f"{date_str}, {datetime.now().year}"
            dt_object = datetime.strptime(full_date_str + " " + time_str, "%A, %B %d, %Y %I:%M %p")
            
            return {
                "doctor_name": doctor_name,
                "appointment_date": dt_object.strftime("%Y-%m-%d"),
                "appointment_time": dt_object.strftime("%H:%M:%S")
            }
        except Exception as e:
            print(f"Error parsing slot string: {e}")
            return {}

    def book_appointment(self, patient_id: str, chosen_slot: str, is_new_patient: bool) -> str:
        """
        Books an appointment by appending it to the appointments CSV.
        This is the core of our "Appointment Conflict Prevention".

        Returns:
            The new appointment_id.
        """
        parsed_slot = self._parse_slot_string(chosen_slot)
        if not parsed_slot:
            raise ValueError("Could not book appointment due to invalid slot format.")

        # Generate a unique appointment ID
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        appointment_id = f"APP{timestamp}{patient_id[-4:]}"

        new_appointment = {
            "appointment_id": appointment_id,
            "patient_id": patient_id,
            "doctor_name": parsed_slot["doctor_name"],
            "appointment_date": parsed_slot["appointment_date"],
            "appointment_time": parsed_slot["appointment_time"],
            "is_new_patient": is_new_patient,
            "status": "Confirmed"
        }
        
        # Append to the CSV file
        df = pd.DataFrame([new_appointment])
        df.to_csv(self.appointments_file, mode='a', header=False, index=False)
        
        print(f"✅ Appointment {appointment_id} booked successfully.")
        return appointment_id

    def generate_admin_report(self) -> str:
        """
        Generates an Excel report of all appointments for admin review.
        
        Returns:
            The filepath of the generated report.
        """
        try:
            appointments_df = pd.read_csv(self.appointments_file)
            patients_df = pd.read_csv(self.patients_file)
            
            # Merge appointment data with patient data for a comprehensive report
            report_df = pd.merge(
                appointments_df,
                patients_df[['patient_id', 'first_name', 'last_name', 'phone', 'email']],
                on='patient_id',
                how='left'
            )
            
            # Reorder columns for clarity
            report_df = report_df[[
                'appointment_id', 'patient_id', 'first_name', 'last_name',
                'appointment_date', 'appointment_time', 'doctor_name', 
                'status', 'is_new_patient', 'phone', 'email'
            ]]
            
            # Generate a unique filename for the report
            report_filename = f"admin_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            report_filepath = os.path.join(self.exports_dir, report_filename)
            
            report_df.to_excel(report_filepath, index=False)
            print(f"📄 Admin report generated successfully at '{report_filepath}'.")
            return report_filepath
        except Exception as e:
            print(f"Error generating admin report: {e}")
            return ""

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

    print("🚀 Testing Export Tools...")
    
    # Initialize the tool
    exporter = ExportTools(
        appointments_filepath=settings.APPOINTMENTS_CSV_PATH,
        patients_filepath=settings.PATIENTS_CSV_PATH,
        exports_dir=settings.EXPORTS_DIR
    )

    # --- Test Case 1: Book a new appointment ---
    print("\n--- Test Case 1: Book a new appointment ---")
    test_slot = "Dr. Evelyn Reed on Monday, September 08 at 10:30 AM"
    test_patient_id = "P001" # Using a patient ID from your synthetic data plan
    try:
        new_id = exporter.book_appointment(test_patient_id, test_slot, is_new_patient=False)
        assert new_id is not None
        # Check if the appointment exists in the file
        app_df = pd.read_csv(settings.APPOINTMENTS_CSV_PATH)
        assert not app_df[app_df['appointment_id'] == new_id].empty
        print("✅ Test Case 1 Passed")
    except Exception as e:
        print(f"❌ Test Case 1 Failed: {e}")

    # --- Test Case 2: Generate an admin report ---
    print("\n--- Test Case 2: Generate an admin report ---")
    try:
        report_path = exporter.generate_admin_report()
        assert os.path.exists(report_path)
        print("✅ Test Case 2 Passed")
    except Exception as e:
        print(f"❌ Test Case 2 Failed: {e}")

    print("\n🎉 Export Tools tests completed successfully!")

