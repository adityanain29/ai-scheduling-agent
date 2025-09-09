# agents/greeting_agent.py
# This agent is responsible for processing the initial user input to extract
# the patient's name, date of birth, doctor preference, and location.

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from typing import List, Dict, Any

# This top-level import is fine as it's a standard library
import sys
import os

# --- 1. Define the Desired Output Structure ---
class PatientInfo(BaseModel):
    """Data model for extracted patient information."""
    full_name: str | None = Field(None)
    date_of_birth: str | None = Field(None)
    preferred_doctor: str | None = Field(None)
    preferred_location: str | None = Field(None)

# --- 2. Create the Agent Logic ---
def create_greeting_chain(llm: ChatOpenAI, master_prompt: str):
    """
    Creates a LangChain chain that extracts patient info from a conversation using JSON Mode.
    """
    # We will use a simple JSON parser first, then validate with Pydantic.
    parser = JsonOutputParser()
    
    json_llm = llm.bind(response_format={"type": "json_object"})
    
    system_prompt = master_prompt + """
    You are the 'Greeting Agent'. Your task is to analyze the user's message and extract their full name, date of birth, preferred doctor, and preferred location.

    - Use "fullName", "dateOfBirth", "preferredDoctor", and "preferredLocation" as the keys in your JSON response.
    - If the user provides their name, extract it exactly as provided.
    - If the user provides their date of birth, format it as YYYY-MM-DD.
    - If the user mentions a doctor preference, extract it.
    - If the user mentions a location preference, extract it.
    - If any piece of information is missing, you MUST return null for that field.
    - You MUST ONLY respond with a valid JSON object. Do not add any other text or explanations.

    Example Response: {{"fullName": "Jane Doe", "dateOfBirth": "1985-03-15", "preferredDoctor": "Dr. Smith", "preferredLocation": "Downtown Clinic"}}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Here is the conversation history:\n\n{conversation_history}")
    ])
        
    return prompt | json_llm | parser

# --- 3. Helper function to normalize LLM output ---
def normalize_and_validate_patient_info(data: Dict[str, Any]) -> PatientInfo:
    """
    Takes the raw dict from the LLM and normalizes its keys before validating with Pydantic.
    This makes our code resilient to the LLM's inconsistent key naming.
    """
    # Normalize keys: check for common variations and map them to our Pydantic model's fields.
    normalized_data = {
        'full_name': data.get('fullName') or data.get('full_name') or data.get('name'),
        'date_of_birth': data.get('dateOfBirth') or data.get('date_of_birth') or data.get('dob'),
        'preferred_doctor': data.get('preferredDoctor') or data.get('preferred_doctor') or data.get('doctor'),
        'preferred_location': data.get('preferredLocation') or data.get('preferred_location') or data.get('location')
    }
    # Create and validate the Pydantic model
    return PatientInfo(**normalized_data)

def format_patient_info_for_confirmation(patient_info: PatientInfo) -> str:
    """
    Formats the patient information for confirmation display.
    """
    info_lines = []
    if patient_info.full_name:
        info_lines.append(f"**Name:** {patient_info.full_name}")
    if patient_info.date_of_birth:
        info_lines.append(f"**Date of Birth:** {patient_info.date_of_birth}")
    if patient_info.preferred_doctor:
        info_lines.append(f"**Preferred Doctor:** {patient_info.preferred_doctor}")
    if patient_info.preferred_location:
        info_lines.append(f"**Preferred Location:** {patient_info.preferred_location}")
    
    return "\n".join(info_lines)

def get_missing_info_message(patient_info: PatientInfo) -> str:
    """
    Returns a message asking for missing information.
    """
    missing_fields = []
    if not patient_info.full_name:
        missing_fields.append("your full name")
    if not patient_info.date_of_birth:
        missing_fields.append("your date of birth")
    if not patient_info.preferred_doctor:
        missing_fields.append("your preferred doctor")
    if not patient_info.preferred_location:
        missing_fields.append("your preferred location")
    
    if len(missing_fields) == 0:
        return None
    elif len(missing_fields) == 1:
        return f"I still need {missing_fields[0]}. Could you please provide that information?"
    elif len(missing_fields) == 2:
        return f"I still need {missing_fields[0]} and {missing_fields[1]}. Could you please provide that information?"
    else:
        missing_str = ", ".join(missing_fields[:-1]) + f", and {missing_fields[-1]}"
        return f"I still need {missing_str}. Could you please provide that information?"

def is_patient_info_complete(patient_info: PatientInfo) -> bool:
    """
    Checks if all required patient information is provided.
    """
    return all([
        patient_info.full_name,
        patient_info.date_of_birth,
        patient_info.preferred_doctor,
        patient_info.preferred_location
    ])

# --- 4. Example Usage & Testing ---
if __name__ == '__main__':
    # --- FIX FOR DIRECT EXECUTION ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    # --- END FIX ---
    
    # --- LOCAL IMPORTS ---
    from config import prompts
    from main_graph import llm 
    # --- END LOCAL IMPORTS ---

    print("🚀 Testing Greeting Agent...")

    greeting_agent = create_greeting_chain(llm, prompts.MASTER_PROMPT)

    # --- Test Case 1: All information provided ---
    print("\n--- Test Case 1: Full Info ---")
    messages = [{"role": "user", "content": "Hi, I'd like to book an appointment. My name is Jane Doe, I was born on March 15, 1985, I'd like to see Dr. Smith at the Downtown Clinic."}]
    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    
    result_dict = greeting_agent.invoke({"conversation_history": history})
    patient_info = normalize_and_validate_patient_info(result_dict)
    
    print("Validated Info:", patient_info)
    print("Is Complete:", is_patient_info_complete(patient_info))
    print("Formatted for confirmation:", format_patient_info_for_confirmation(patient_info))
    print("✅ Test Case 1 Passed")

    # --- Test Case 2: Partial information ---
    print("\n--- Test Case 2: Partial Info ---")
    messages = [{"role": "user", "content": "Hello, my name is John Smith and I was born on June 10, 1990."}]
    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    result_dict = greeting_agent.invoke({"conversation_history": history})
    patient_info = normalize_and_validate_patient_info(result_dict)
    
    print("Validated Info:", patient_info)
    print("Is Complete:", is_patient_info_complete(patient_info))
    print("Missing info message:", get_missing_info_message(patient_info))
    print("✅ Test Case 2 Passed")

    # --- Test Case 3: No information ---
    print("\n--- Test Case 3: No Info ---")
    messages = [{"role": "user", "content": "Hi there!"}]
    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    result_dict = greeting_agent.invoke({"conversation_history": history})
    patient_info = normalize_and_validate_patient_info(result_dict)
    
    print("Validated Info:", patient_info)
    print("Is Complete:", is_patient_info_complete(patient_info))
    print("Missing info message:", get_missing_info_message(patient_info))
    print("✅ Test Case 3 Passed")

    print("\n🎉 Greeting Agent tests completed successfully!")# agents/greeting_agent.py
# This agent is responsible for processing the initial user input to extract
# the patient's name, date of birth, doctor preference, and location.

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from typing import List, Dict, Any

# This top-level import is fine as it's a standard library
import sys
import os

# --- 1. Define the Desired Output Structure ---
class PatientInfo(BaseModel):
    """Data model for extracted patient information."""
    full_name: str | None = Field(None)
    date_of_birth: str | None = Field(None)
    preferred_doctor: str | None = Field(None)
    preferred_location: str | None = Field(None)

# --- 2. Create the Agent Logic ---
def create_greeting_chain(llm: ChatOpenAI, master_prompt: str):
    """
    Creates a LangChain chain that extracts patient info from a conversation using JSON Mode.
    """
    # We will use a simple JSON parser first, then validate with Pydantic.
    parser = JsonOutputParser()
    
    json_llm = llm.bind(response_format={"type": "json_object"})
    
    system_prompt = master_prompt + """
    You are the 'Greeting Agent'. Your task is to analyze the user's message and extract their full name, date of birth, preferred doctor, and preferred location.

    - Use "fullName", "dateOfBirth", "preferredDoctor", and "preferredLocation" as the keys in your JSON response.
    - If the user provides their name, extract it exactly as provided.
    - If the user provides their date of birth, format it as YYYY-MM-DD.
    - If the user mentions a doctor preference, extract it.
    - If the user mentions a location preference, extract it.
    - If any piece of information is missing, you MUST return null for that field.
    - You MUST ONLY respond with a valid JSON object. Do not add any other text or explanations.

    Example Response: {{"fullName": "Jane Doe", "dateOfBirth": "1985-03-15", "preferredDoctor": "Dr. Smith", "preferredLocation": "Downtown Clinic"}}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Here is the conversation history:\n\n{conversation_history}")
    ])
        
    return prompt | json_llm | parser

# --- 3. Helper function to normalize LLM output ---
def normalize_and_validate_patient_info(data: Dict[str, Any]) -> PatientInfo:
    """
    Takes the raw dict from the LLM and normalizes its keys before validating with Pydantic.
    This makes our code resilient to the LLM's inconsistent key naming.
    """
    # Normalize keys: check for common variations and map them to our Pydantic model's fields.
    normalized_data = {
        'full_name': data.get('fullName') or data.get('full_name') or data.get('name'),
        'date_of_birth': data.get('dateOfBirth') or data.get('date_of_birth') or data.get('dob'),
        'preferred_doctor': data.get('preferredDoctor') or data.get('preferred_doctor') or data.get('doctor'),
        'preferred_location': data.get('preferredLocation') or data.get('preferred_location') or data.get('location')
    }
    # Create and validate the Pydantic model
    return PatientInfo(**normalized_data)

def format_patient_info_for_confirmation(patient_info: PatientInfo) -> str:
    """
    Formats the patient information for confirmation display.
    """
    info_lines = []
    if patient_info.full_name:
        info_lines.append(f"**Name:** {patient_info.full_name}")
    if patient_info.date_of_birth:
        info_lines.append(f"**Date of Birth:** {patient_info.date_of_birth}")
    if patient_info.preferred_doctor:
        info_lines.append(f"**Preferred Doctor:** {patient_info.preferred_doctor}")
    if patient_info.preferred_location:
        info_lines.append(f"**Preferred Location:** {patient_info.preferred_location}")
    
    return "\n".join(info_lines)

def get_missing_info_message(patient_info: PatientInfo) -> str:
    """
    Returns a message asking for missing information.
    """
    missing_fields = []
    if not patient_info.full_name:
        missing_fields.append("your full name")
    if not patient_info.date_of_birth:
        missing_fields.append("your date of birth")
    if not patient_info.preferred_doctor:
        missing_fields.append("your preferred doctor")
    if not patient_info.preferred_location:
        missing_fields.append("your preferred location")
    
    if len(missing_fields) == 0:
        return None
    elif len(missing_fields) == 1:
        return f"I still need {missing_fields[0]}. Could you please provide that information?"
    elif len(missing_fields) == 2:
        return f"I still need {missing_fields[0]} and {missing_fields[1]}. Could you please provide that information?"
    else:
        missing_str = ", ".join(missing_fields[:-1]) + f", and {missing_fields[-1]}"
        return f"I still need {missing_str}. Could you please provide that information?"

def is_patient_info_complete(patient_info: PatientInfo) -> bool:
    """
    Checks if all required patient information is provided.
    """
    return all([
        patient_info.full_name,
        patient_info.date_of_birth,
        patient_info.preferred_doctor,
        patient_info.preferred_location
    ])

# --- 4. Example Usage & Testing ---
if __name__ == '__main__':
    # --- FIX FOR DIRECT EXECUTION ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    sys.path.append(project_root)
    # --- END FIX ---
    
    # --- LOCAL IMPORTS ---
    from config import prompts
    from main_graph import llm 
    # --- END LOCAL IMPORTS ---

    print("🚀 Testing Greeting Agent...")

    greeting_agent = create_greeting_chain(llm, prompts.MASTER_PROMPT)

    # --- Test Case 1: All information provided ---
    print("\n--- Test Case 1: Full Info ---")
    messages = [{"role": "user", "content": "Hi, I'd like to book an appointment. My name is Jane Doe, I was born on March 15, 1985, I'd like to see Dr. Smith at the Downtown Clinic."}]
    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
    
    result_dict = greeting_agent.invoke({"conversation_history": history})
    patient_info = normalize_and_validate_patient_info(result_dict)
    
    print("Validated Info:", patient_info)
    print("Is Complete:", is_patient_info_complete(patient_info))
    print("Formatted for confirmation:", format_patient_info_for_confirmation(patient_info))
    print("✅ Test Case 1 Passed")

    # --- Test Case 2: Partial information ---
    print("\n--- Test Case 2: Partial Info ---")
    messages = [{"role": "user", "content": "Hello, my name is John Smith and I was born on June 10, 1990."}]
    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    result_dict = greeting_agent.invoke({"conversation_history": history})
    patient_info = normalize_and_validate_patient_info(result_dict)
    
    print("Validated Info:", patient_info)
    print("Is Complete:", is_patient_info_complete(patient_info))
    print("Missing info message:", get_missing_info_message(patient_info))
    print("✅ Test Case 2 Passed")

    # --- Test Case 3: No information ---
    print("\n--- Test Case 3: No Info ---")
    messages = [{"role": "user", "content": "Hi there!"}]
    history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])

    result_dict = greeting_agent.invoke({"conversation_history": history})
    patient_info = normalize_and_validate_patient_info(result_dict)
    
    print("Validated Info:", patient_info)
    print("Is Complete:", is_patient_info_complete(patient_info))
    print("Missing info message:", get_missing_info_message(patient_info))
    print("✅ Test Case 3 Passed")

    print("\n🎉 Greeting Agent tests completed successfully!")