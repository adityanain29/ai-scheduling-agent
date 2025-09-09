# tools/database_tools.py
# This file contains functions for interacting with the mock patient database.

import pandas as pd
from thefuzz import process

# Note: We will import 'settings' later, inside the test block,
# to solve the path issue for direct script execution.

class PatientDB:
    """A class to handle patient data operations."""

    def __init__(self, filepath: str):
        """
        Initializes the PatientDB by loading the patient data from a CSV file.
        """
        try:
            self.df = pd.read_csv(filepath)
            # Ensure date_of_birth is a string for consistent comparison
            self.df['date_of_birth'] = self.df['date_of_birth'].astype(str)
            print("✅ Patient database loaded successfully.")
        except FileNotFoundError:
            print(f"❌ ERROR: Patient data file not found at {filepath}")
            self.df = pd.DataFrame()

    def search_patient(self, full_name: str, dob: str):
        """
        Searches for a patient by full name and date of birth using fuzzy matching for the name.

        Args:
            full_name (str): The patient's full name.
            dob (str): The patient's date of birth in 'YYYY-MM-DD' format.

        Returns:
            dict: The patient's record as a dictionary if found, otherwise None.
        """
        if self.df.empty:
            return None

        # Create a 'full_name' column for easier searching
        self.df['full_name'] = self.df['first_name'] + ' ' + self.df['last_name']
        
        # --- Fuzzy Name Matching ---
        names = self.df['full_name'].tolist()
        best_match = process.extractOne(full_name, names, score_cutoff=80)
        
        if not best_match:
            print(f"No close name match found for '{full_name}'.")
            return None
            
        matched_name = best_match[0]
        
        # --- DOB and Name Matching ---
        patient_record = self.df[
            (self.df['full_name'] == matched_name) & 
            (self.df['date_of_birth'] == dob)
        ]

        if not patient_record.empty:
            print(f"✅ Patient found for '{full_name}' and DOB '{dob}'.")
            return patient_record.iloc[0].to_dict()
        else:
            print(f"Patient with name match '{matched_name}' found, but DOB '{dob}' does not match.")
            return None

    def is_returning_patient(self, patient_id: str) -> bool:
        """
        Checks if a patient is a returning patient based on their visit history.
        """
        if self.df.empty:
            return False
            
        patient_record = self.df[self.df['patient_id'] == patient_id]
        
        if not patient_record.empty:
            visit_history = patient_record.iloc[0]['visit_history']
            return visit_history > 0
        
        return False

# Example usage for testing
if __name__ == '__main__':
    # --- FIX FOR DIRECT EXECUTION ---
    # This block allows the script to be run directly for testing purposes.
    # It adds the project's root directory to Python's path, so it can find 'config'.
    import sys
    import os
    # Get the absolute path of the current file's directory (tools)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory (the project root, ai-scheduling-agent)
    project_root = os.path.dirname(current_dir)
    # Add the project root to the system path
    sys.path.append(project_root)
    
    from config import settings
    # --- END FIX ---

    # Now we can initialize the DB using the path from our settings file
    db = PatientDB(filepath=settings.PATIENTS_CSV_PATH)

    if not db.df.empty:
        print("\n--- Running Test Cases ---")
        # --- Test Case 1: Successful lookup of an existing patient ---
        sample_patient = db.df.iloc[10]
        test_name = f"{sample_patient['first_name']} {sample_patient['last_name']}"
        test_dob = sample_patient['date_of_birth']
        found_patient = db.search_patient(test_name, test_dob)
        assert found_patient is not None
        
        # --- Test Case 2 & 3 & 4... (Your other tests will run now) ---
        print("✅ All test cases passed!")

