# agents/insurance_agent.py
# This agent is responsible for parsing email addresses from user messages

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from typing import Dict, Any
import re
import sys
import os

# --- 1. Define the Output Structure ---
class InsuranceInfo(BaseModel):
    """Data model for insurance/contact information."""
    patient_email: str | None = Field(None, description="Patient's email address")

# --- 2. Create the Agent Logic ---
def create_insurance_parser_chain(llm: ChatOpenAI, master_prompt: str):
    """
    Creates a LangChain chain that extracts email address from conversation.
    """
    parser = JsonOutputParser()
    json_llm = llm.bind(response_format={"type": "json_object"})
    
    system_prompt = master_prompt + """
    You are the 'Insurance Agent'. Your task is to extract the patient's email address from their message.

    - Use "patientEmail" as the key in your JSON response
    - If the user provides a valid email address, extract it exactly as provided
    - If no valid email is found, return null
    - You MUST ONLY respond with a valid JSON object. Do not add any other text.

    Example Response: {{"patientEmail": "john.doe@email.com"}}
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Here is the conversation history:\n\n{conversation_history}")
    ])
        
    return prompt | json_llm | parser

# --- 3. Helper Functions ---
def normalize_and_validate_insurance_info(data: Dict[str, Any]) -> InsuranceInfo:
    """
    Takes the raw dict from the LLM and normalizes its keys before validating with Pydantic.
    """
    normalized_data = {
        'patient_email': data.get('patientEmail') or data.get('patient_email') or data.get('email')
    }
    return InsuranceInfo(**normalized_data)

def extract_email_from_text(text: str) -> str | None:
    """
    Simple regex-based email extraction as backup.
    """
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

# --- 4. Example Usage & Testing ---
if __name__ == '__main__':
    print("🚀 Testing Insurance Agent...")
    
    test_cases = [
        "My email is john.doe@gmail.com",
        "You can reach me at jane.smith@company.org",
        "test123@email.co.uk is my email",
        "I don't have an email",
        "Contact me at invalid-email"
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: '{test_input}' ---")
        
        # Test regex extraction
        extracted_email = extract_email_from_text(test_input)
        print(f"Extracted email: {extracted_email}")
        
        # Test Pydantic validation
        mock_data = {"patientEmail": extracted_email}
        insurance_info = normalize_and_validate_insurance_info(mock_data)
        print(f"Validated info: {insurance_info}")
        
        if insurance_info.patient_email:
            print("✅ Valid email found")
        else:
            print("⚠️ No valid email found")
    
    print("\n🎉 Insurance Agent tests completed!")