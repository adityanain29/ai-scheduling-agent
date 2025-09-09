import re
from datetime import datetime, timedelta

def validate_date_of_birth(dob_string: str) -> bool:
    """Validate DOB format and constraints"""
    try:
        dob = datetime.strptime(dob_string, '%Y-%m-%d')
        today = datetime.now()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        return (
            dob.year >= 1900 and 
            dob <= today and 
            0 <= age <= 120
        )
    except ValueError:
        return False

def validate_full_name(name: str) -> bool:
    """Validate full name format"""
    if not name or len(name.strip()) < 2:
        return False
    
    # Allow letters, spaces, hyphens, apostrophes only
    pattern = r"^[a-zA-Z\s\-']+$"
    if not re.match(pattern, name):
        return False
    
    # Must have at least first and last name
    parts = name.strip().split()
    return len(parts) >= 2

def validate_doctor_and_location(doctor: str, location: str, doctor_list=None, location_list=None) -> dict:
    """Validate doctor and location against available lists"""
    result = {"doctor_valid": True, "location_valid": True, "messages": []}
    
    if doctor_list and doctor not in doctor_list:
        result["doctor_valid"] = False
        result["messages"].append(f"Doctor '{doctor}' not found. Available options: {', '.join(doctor_list[:3])}")
    
    if location_list and location not in location_list:
        result["location_valid"] = False
        result["messages"].append(f"Location '{location}' not found. Available options: {', '.join(location_list[:3])}")
    
    return result
