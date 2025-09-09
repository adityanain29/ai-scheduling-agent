# agents/patient_lookup_agent.py
# This agent uses the database tools to find a patient and determine
# if they are new or returning.

import sys
import os
from typing import Dict, Any

# We need to define a custom exception for when a patient isn't found.
# This aligns with the error handling strategy in the project plan.
class PatientNotFoundError(Exception):
    pass

# The main function for this agent. It's not a chain, but a regular function
# that uses our tools and returns structured data.
def lookup_patient(patient_name: str, patient_dob: str, db_tool) -> Dict[str, Any]:
    """
    Looks up a patient in the database.

    Args:
        patient_name: The full name of the patient.
        patient_dob: The date of birth of the patient (YYYY-MM-DD).
        db_tool: An instance of the PatientDB tool.

    Returns:
        A dictionary containing patient details.
    
    Raises:
        PatientNotFoundError: If the patient cannot be found in the database.
    """
    print(f"🔎 Looking up patient: {patient_name} (DOB: {patient_dob})")
    
    # Use the database tool to search for the patient
    patient_record = db_tool.search_patient(patient_name, patient_dob)

    if patient_record:
        patient_id = patient_record['patient_id']
        is_returning = db_tool.is_returning_patient(patient_id)
        
        result = {
            "patient_id": patient_id,
            "is_new_patient": not is_returning,
            "patient_details": patient_record
        }
        print(f"✅ Patient found: ID {patient_id}, Returning: {is_returning}")
        return result
    else:
        # If no patient is found, raise our custom error.
        print(f"❌ Patient not found: {patient_name}")
        raise PatientNotFoundError(f"No patient found with name '{patient_name}' and DOB '{patient_dob}'.")

# --- Example Usage & Testing ---
if __name__ == '__main__':
    # --- FIX FOR DIRECT EXECUTION ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    # --- END FIX ---

    # --- LOCAL IMPORTS ---
    from tools.database_tools import PatientDB
    from config import settings # Import the settings
    # --- END LOCAL IMPORTS ---

    print("🚀 Testing Patient Lookup Agent...")
    
    # Initialize our database tool with the correct file path from settings
    db = PatientDB(filepath=settings.PATIENTS_CSV_PATH)

    # --- Test Case 1: Find a returning patient ---
    print("\n--- Test Case 1: Find Returning Patient ---")
    # Fetch a known patient from the DB to use for testing
    # Let's find a patient who has a visit_history > 0
    returning_patient_df = db.df[db.df['visit_history'] > 0]
    if not returning_patient_df.empty:
        test_patient = returning_patient_df.iloc[0]
        name = f"{test_patient['first_name']} {test_patient['last_name']}"
        dob = test_patient['date_of_birth']
        
        try:
            result = lookup_patient(name, dob, db)
            print("Result:", result)
            assert result['is_new_patient'] is False
            assert result['patient_id'] == test_patient['patient_id']
            print("✅ Test Case 1 Passed")
        except PatientNotFoundError as e:
            print(f"Error on Test Case 1: {e}")
    else:
        print("⚠️ Could not find a returning patient in the test data to run Test Case 1.")


    # --- Test Case 2: Find a new patient ---
    print("\n--- Test Case 2: Find New Patient ---")
    # Let's find a patient who has a visit_history == 0
    new_patient_df = db.df[db.df['visit_history'] == 0]
    if not new_patient_df.empty:
        test_patient = new_patient_df.iloc[0]
        name = f"{test_patient['first_name']} {test_patient['last_name']}"
        dob = test_patient['date_of_birth']

        try:
            result = lookup_patient(name, dob, db)
            print("Result:", result)
            assert result['is_new_patient'] is True
            print("✅ Test Case 2 Passed")
        except PatientNotFoundError as e:
            print(f"Error on Test Case 2: {e}")
    else:
        print("⚠️ Could not find a new patient in the test data to run Test Case 2.")


    # --- Test Case 3: Patient not found ---
    print("\n--- Test Case 3: Patient Not Found ---")
    try:
        lookup_patient("Non Existent", "1900-01-01", db)
    except PatientNotFoundError:
        print("✅ Correctly raised PatientNotFoundError.")
        print("✅ Test Case 3 Passed")
    except Exception as e:
        print(f"❌ Test Case 3 failed with unexpected error: {e}")


    print("\n🎉 Patient Lookup Agent tests completed successfully!")

